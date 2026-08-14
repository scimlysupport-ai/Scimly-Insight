from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.database.session import get_db
from app.models.dataset import Dataset
from app.models.data_source import DataSource
from app.schemas.data_source import CreateDataSourceRequest, DataSourceResponse
from app.schemas.dataset import DatasetResponse, AIInsightsResponse
from app.schemas.chart_preview import ChartPreviewRequest, ChartPreviewResponse
from app.schemas.filters import DashboardFilters, FilterOptionsResponse
from app.services.data_source_service import (
    create_data_source,
    get_data_source,
    list_data_sources,
    ensure_source_dataset,
    source_response,
)
from app.services.recommendation_service import recommend_charts
from app.services.chart_data_service import build_all_chart_data, build_custom_chart
from app.services.filter_service import get_filter_options, apply_filters
from app.services.analysis_service import clean_dataframe, generate_ai_insights

import os

router = APIRouter()


@router.post("/datasources", response_model=DataSourceResponse)
def create_datasource(
    payload: CreateDataSourceRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        source, _dataset = create_data_source(db, user_id, payload.name, payload.source_type, payload.config)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return source_response(source)


@router.get("/datasources", response_model=list[DataSourceResponse])
def list_datasources(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    sources = list_data_sources(db, user_id)
    return [source_response(source) for source in sources]


@router.get("/datasources/{source_id}", response_model=DataSourceResponse)
def get_datasource(source_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    source = get_data_source(db, source_id)
    if not source or source.user_id != user_id:
        raise HTTPException(status_code=404, detail="Data source not found.")
    return source_response(source)


@router.get("/datasources/{source_id}/dataset", response_model=DatasetResponse)
def get_datasource_dataset(source_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    source = get_data_source(db, source_id)
    if not source or source.user_id != user_id:
        raise HTTPException(status_code=404, detail="Data source not found.")

    try:
        dataset = ensure_source_dataset(db, source)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DatasetResponse.from_dataset(dataset)


@router.get("/datasources/{source_id}/recommendations")
def get_datasource_recommendations(source_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    source = get_data_source(db, source_id)
    if not source or source.user_id != user_id:
        raise HTTPException(status_code=404, detail="Data source not found.")

    dataset = db.query(Dataset).filter(Dataset.datasource_id == source.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Data source analysis not available yet.")

    return {"recommendedCharts": recommend_charts(dataset.schema_json)}


@router.get("/datasources/{source_id}/filters", response_model=FilterOptionsResponse)
def get_datasource_filters(source_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    source = get_data_source(db, source_id)
    if not source or source.user_id != user_id:
        raise HTTPException(status_code=404, detail="Data source not found.")

    dataset = db.query(Dataset).filter(Dataset.datasource_id == source.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Data source analysis not available yet.")

    # Re-read to apply filters on the live dataset every time.
    try:
        from app.services.data_source_service import read_source_dataframe

        df = read_source_dataframe(source.source_type, source.config_json)
        df = clean_dataframe(df, schema=dataset.schema_json)
        return get_filter_options(df, dataset.schema_json)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/datasources/{source_id}/dashboard")
def get_datasource_dashboard(source_id: int, filters: DashboardFilters, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    source = get_data_source(db, source_id)
    if not source or source.user_id != user_id:
        raise HTTPException(status_code=404, detail="Data source not found.")

    dataset = db.query(Dataset).filter(Dataset.datasource_id == source.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Data source analysis not available yet.")

    try:
        from app.services.data_source_service import read_source_dataframe

        df = read_source_dataframe(source.source_type, source.config_json)
        df = clean_dataframe(df, schema=dataset.schema_json)
        df = apply_filters(df, filters.model_dump(), dataset.schema_json)
        recommended_charts = recommend_charts(dataset.schema_json)
        all_widgets = build_all_chart_data(df, recommended_charts)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not build dashboard: {exc}") from exc

    widgets = [w for w in all_widgets if w.get("important", True)]
    more_widgets = [w for w in all_widgets if not w.get("important", True)]
    return {"widgets": widgets, "moreWidgets": more_widgets}


@router.post("/datasources/{source_id}/chart-preview", response_model=ChartPreviewResponse)
def preview_datasource_chart(source_id: int, request: ChartPreviewRequest, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    source = get_data_source(db, source_id)
    if not source or source.user_id != user_id:
        raise HTTPException(status_code=404, detail="Data source not found.")

    dataset = db.query(Dataset).filter(Dataset.datasource_id == source.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Data source analysis not available yet.")

    try:
        from app.services.data_source_service import read_source_dataframe

        df = read_source_dataframe(source.source_type, source.config_json)
        df = clean_dataframe(df, schema=dataset.schema_json)
        data = build_custom_chart(
            df,
            request.chart,
            request.column,
            request.x,
            request.y,
            request.columns,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not preview chart: {exc}") from exc

    return {"chart": request.chart, "data": data}


@router.get("/datasources/{source_id}/insights", response_model=AIInsightsResponse)
def get_datasource_insights(source_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    source = get_data_source(db, source_id)
    if not source or source.user_id != user_id:
        raise HTTPException(status_code=404, detail="Data source not found.")

    dataset = db.query(Dataset).filter(Dataset.datasource_id == source.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Data source analysis not available yet.")

    try:
        from app.services.data_source_service import read_source_dataframe

        df = read_source_dataframe(source.source_type, source.config_json)
        df = clean_dataframe(df, schema=dataset.schema_json)
        insights = generate_ai_insights(df, schema=dataset.schema_json)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not generate insights: {exc}") from exc

    return {"insights": insights}


@router.post("/datasources/{source_id}/ai-chat")
def datasource_ai_chat(source_id: int, payload: dict, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Ask Scimly (Phase 15), for a live data source instead of an uploaded file."""
    source = get_data_source(db, source_id)
    if not source or source.user_id != user_id:
        raise HTTPException(status_code=404, detail="Data source not found.")

    dataset = db.query(Dataset).filter(Dataset.datasource_id == source.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Data source analysis not available yet.")

    try:
        from app.services.data_source_service import read_source_dataframe
        from app.services.ai_chat_service import build_ai_chat_widget

        df = read_source_dataframe(source.source_type, source.config_json)
        df = clean_dataframe(df, schema=dataset.schema_json)
        prompt = payload.get("prompt", "")
        widget = build_ai_chat_widget(df, prompt, schema=dataset.schema_json)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not generate chart: {exc}") from exc

    return {"widget": widget}
