"""
GET /api/dataset/{file_id} -> runs (or retrieves cached) analysis for an
uploaded file and returns { rows, columns, schema }.

Analysis runs once per file and is cached in the datasets table;
subsequent calls just return the stored result.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.file import UploadedFile
from app.models.dataset import Dataset
from app.schemas.dataset import AIInsightsResponse, DatasetResponse, ProcessingProgressResponse
from app.services.file_service import UPLOAD_DIR
from app.services.analysis_service import read_dataframe, analyze_dataframe, clean_dataframe, generate_ai_insights
from app.services.ai_chat_service import build_ai_chat_widget
from app.services.recommendation_service import recommend_charts
from app.services.chart_data_service import build_all_chart_data, build_custom_chart
from app.services.filter_service import get_filter_options, apply_filters
from app.services.progress_service import get_progress
from app.schemas.chart_preview import ChartPreviewRequest, ChartPreviewResponse
from app.schemas.filters import DashboardFilters, FilterOptionsResponse
from app.schemas.dashboard import WidgetsDataRequest

import os

router = APIRouter()


@router.get("/dataset/{file_id}/progress", response_model=ProcessingProgressResponse)
def get_processing_progress(file_id: int, db: Session = Depends(get_db)):
    """
    Phase 13 — polled by the frontend while a large file's analysis runs
    in the background. Redis (via progress_service) is the live source of
    truth while a Celery worker is actively working through the pipeline;
    the file's `status` column in Postgres is the fallback once that
    Redis key has expired (or was never written, e.g. a small file that
    was never queued in the first place).
    """
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    live = get_progress(file_id)
    if live is not None:
        return ProcessingProgressResponse(**live)

    if file_record.status == "ready":
        return ProcessingProgressResponse(status="ready", progress=100, message="Analysis complete.")
    if file_record.status == "failed":
        return ProcessingProgressResponse(status="failed", progress=0, message="Analysis failed.")
    if file_record.status == "processing":
        # Queued but the worker hasn't written a checkpoint yet (or its
        # first Redis write expired before this poll landed).
        return ProcessingProgressResponse(status="queued", progress=0, message="Waiting for a worker to pick this up…")

    # "uploaded" — a small file that was never queued in the first place;
    # its analysis happens synchronously on GET /dataset/{file_id}.
    return ProcessingProgressResponse(status="uploaded", progress=0, message=None)


@router.get("/dataset/{file_id}", response_model=DatasetResponse)
def get_dataset(file_id: int, db: Session = Depends(get_db)):
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    existing = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if existing:
        return DatasetResponse.from_dataset(existing)

    # Phase 13 — a large file's Dataset row is written by the background
    # Celery task, not this request. If it hasn't landed yet, tell the
    # caller to poll the progress endpoint instead of trying (and failing)
    # to analyze it inline here.
    if file_record.status == "processing":
        raise HTTPException(
            status_code=202,
            detail="File is still being processed in the background. Poll GET /dataset/{file_id}/progress for status.",
        )
    if file_record.status == "failed":
        raise HTTPException(status_code=422, detail="Background analysis failed for this file.")

    full_path = os.path.join(UPLOAD_DIR, file_record.stored_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Stored file is missing on disk.")

    try:
        df = read_dataframe(full_path, file_record.file_extension)
        result = analyze_dataframe(df)
    except Exception as exc:
        file_record.status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=f"Analysis failed: {exc}")

    dataset = Dataset(
        file_id=file_id,
        rows=result["rows"],
        columns=result["columns"],
        schema_json=result["schema"],
    )
    db.add(dataset)
    file_record.status = "ready"
    db.commit()
    db.refresh(dataset)

    return DatasetResponse.from_dataset(dataset)


@router.get("/dataset/{file_id}/insights", response_model=AIInsightsResponse)
def get_ai_insights(file_id: int, db: Session = Depends(get_db)):
    """Return text-only AI insights for the uploaded dataset."""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not analyzed yet. Call GET /dataset/{file_id} first.",
        )

    full_path = os.path.join(UPLOAD_DIR, file_record.stored_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Stored file is missing on disk.")

    try:
        df = read_dataframe(full_path, file_record.file_extension)
        df = clean_dataframe(df, schema=dataset.schema_json)
        insights = generate_ai_insights(df)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not generate insights: {exc}")

    return {"insights": insights}


@router.post("/dataset/{file_id}/ai-chat")
def ai_chat(file_id: int, payload: dict, db: Session = Depends(get_db)):
    """Turn a prompt like 'Show monthly revenue' into a chart widget payload."""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not analyzed yet. Call GET /dataset/{file_id} first.")

    full_path = os.path.join(UPLOAD_DIR, file_record.stored_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Stored file is missing on disk.")

    try:
        df = read_dataframe(full_path, file_record.file_extension)
        df = clean_dataframe(df, schema=dataset.schema_json)
        prompt = payload.get("prompt", "")
        widget = build_ai_chat_widget(df, prompt, schema=dataset.schema_json)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not generate chart: {exc}")

    return {"widget": widget}


@router.get("/dataset/{file_id}/recommendations")
def get_recommendations(file_id: int, db: Session = Depends(get_db)):
    """
    Returns { recommendedCharts: [...] } for the given file's dataset.
    Requires the dataset to have been analyzed already
    (i.e. GET /dataset/{file_id} must have been called at least once).
    """
    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not analyzed yet. Call GET /dataset/{file_id} first.",
        )

    recommended_charts = recommend_charts(dataset.schema_json)
    return {"recommendedCharts": recommended_charts}


@router.get("/dataset/{file_id}/filters", response_model=FilterOptionsResponse)
def get_filters(file_id: int, db: Session = Depends(get_db)):
    """
    Returns the columns that can be used as global dashboard filters
    (Phase 9) and their available values/range — every categorical column
    with a usable number of options (individual tags, for a
    delimiter-separated "flags"-style column), and every datetime
    column's min/max. Schema-driven: whatever categorical/datetime
    columns this particular dataset actually has.
    """
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not analyzed yet. Call GET /dataset/{file_id} first.",
        )

    full_path = os.path.join(UPLOAD_DIR, file_record.stored_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Stored file is missing on disk.")

    df = read_dataframe(full_path, file_record.file_extension)
    df = clean_dataframe(df, schema=dataset.schema_json)
    return get_filter_options(df, dataset.schema_json)


@router.post("/dataset/{file_id}/dashboard")
def get_dashboard(file_id: int, filters: DashboardFilters, db: Session = Depends(get_db)):
    """
    Returns { widgets: [...], moreWidgets: [...] } — each recommended
    chart plus the actual data needed to render it, narrowed to rows
    matching `filters` (Phase 9). Which charts appear is still decided
    from the full, unfiltered schema (filtering rows shouldn't make
    widgets appear/disappear) — only the data inside each one changes.

    `widgets` is the curated set the recommendation engine marked
    `important` — what the dashboard renders immediately, capped at a
    handful of the most business-relevant charts instead of one per
    column. `moreWidgets` is everything else, data already computed, so
    the frontend can offer "+ Add chart" and drop one in instantly with
    no extra request.
    """
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not analyzed yet. Call GET /dataset/{file_id} first.",
        )

    full_path = os.path.join(UPLOAD_DIR, file_record.stored_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Stored file is missing on disk.")

    try:
        df = read_dataframe(full_path, file_record.file_extension)
        df = clean_dataframe(df, schema=dataset.schema_json)
        df = apply_filters(df, filters.model_dump(), dataset.schema_json)
        recommended_charts = recommend_charts(dataset.schema_json)
        all_widgets = build_all_chart_data(df, recommended_charts)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not build dashboard: {exc}")

    widgets = [w for w in all_widgets if w.get("important", True)]
    more_widgets = [w for w in all_widgets if not w.get("important", True)]
    return {"widgets": widgets, "moreWidgets": more_widgets}


@router.post("/dataset/{file_id}/chart-preview", response_model=ChartPreviewResponse)
def preview_chart(file_id: int, request: ChartPreviewRequest, db: Session = Depends(get_db)):
    """
    Computes chart data for a configuration the user picked while editing
    a widget (Phase 7) — e.g. they changed the chart type, or swapped
    which column/axis it's plotting. Applies the same active filters
    (Phase 9) as the dashboard, if any. Does not save anything; the
    frontend holds edits until Phase 10 introduces persistent saved
    dashboards.
    """
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not analyzed yet. Call GET /dataset/{file_id} first.",
        )

    full_path = os.path.join(UPLOAD_DIR, file_record.stored_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Stored file is missing on disk.")

    df = read_dataframe(full_path, file_record.file_extension)
    df = clean_dataframe(df, schema=dataset.schema_json)
    if request.filters is not None:
        df = apply_filters(df, request.filters.model_dump(), dataset.schema_json)

    try:
        data = build_custom_chart(
            df,
            chart=request.chart,
            column=request.column,
            x=request.x,
            y=request.y,
            columns=request.columns,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"chart": request.chart, "data": data}


@router.post("/dataset/{file_id}/widgets-data")
def get_widgets_data(file_id: int, request: WidgetsDataRequest, db: Session = Depends(get_db)):
    """
    Phase 10 — Save Dashboard.

    Takes an explicit list of widget definitions (as stored on a saved
    dashboard — chart/title/column/x/y/columns/color already decided)
    and returns them with fresh `data` attached, respecting the given
    filters. This is what "opening" a saved dashboard uses instead of
    the recommendation engine: the saved widget list *is* the
    dashboard, we're just re-computing numbers against the current
    dataset (which may have changed since it was saved).
    """
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not analyzed yet. Call GET /dataset/{file_id} first.",
        )

    full_path = os.path.join(UPLOAD_DIR, file_record.stored_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Stored file is missing on disk.")

    try:
        df = read_dataframe(full_path, file_record.file_extension)
        df = clean_dataframe(df, schema=dataset.schema_json)
        df = apply_filters(df, request.filters.model_dump(), dataset.schema_json)
        widgets = build_all_chart_data(df, [w.model_dump() for w in request.widgets])
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not build widget data: {exc}")

    return {"widgets": widgets}