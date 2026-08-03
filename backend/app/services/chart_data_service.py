"""
Produces the actual data points needed to render each recommended chart
(Phase 5). The recommendation engine (Phase 4) decides *what* chart to
show; this module computes the *data* for it by aggregating the cleaned
dataframe.
"""
import pandas as pd


def _line_data(df: pd.DataFrame, x_col: str, y_col: str) -> list[dict]:
    """Groups by date and sums the measure column, sorted chronologically."""
    working = df[[x_col, y_col]].copy()
    working[x_col] = pd.to_datetime(working[x_col], errors="coerce", format="mixed")
    working = working.dropna(subset=[x_col])
    grouped = working.groupby(working[x_col].dt.date)[y_col].sum().reset_index()
    grouped.columns = ["x", "y"]
    grouped = grouped.sort_values("x")
    return [{"x": str(row["x"]), "y": float(row["y"])} for _, row in grouped.iterrows()]


def _pie_data(df: pd.DataFrame, column: str) -> list[dict]:
    counts = df[column].value_counts().head(8)
    return [{"name": str(k), "value": int(v)} for k, v in counts.items()]


def _bar_data(df: pd.DataFrame, column: str) -> list[dict]:
    """Bins a numeric column into ranges and counts how many rows fall in each."""
    series = df[column].dropna()
    if series.empty:
        return []
    bins = pd.cut(series, bins=min(8, series.nunique()) or 1)
    counts = bins.value_counts().sort_index()
    result = []
    for interval, count in counts.items():
        label = f"{interval.left:.0f}–{interval.right:.0f}"
        result.append({"name": label, "value": int(count)})
    return result


def _kpi_data(df: pd.DataFrame, column: str) -> dict:
    return {"value": float(df[column].sum())}


def _table_data(df: pd.DataFrame, columns: list[str], limit: int = 100) -> dict:
    """
    Row-level view for columns that don't suit a chart (text, ids, high-
    cardinality categoricals, booleans). Capped at `limit` rows so a
    500-row dataset doesn't ship its entire contents to the browser —
    `totalRows` tells the frontend how many rows exist beyond the cap.
    """
    known = [c for c in columns if c in df.columns]
    subset = df[known].head(limit)
    rows = subset.astype(object).where(pd.notnull(subset), None).to_dict(orient="records")
    return {"columns": known, "rows": rows, "totalRows": int(len(df))}


def build_chart_data(df: pd.DataFrame, recommendation: dict) -> dict | list:
    """
    Given a cleaned dataframe and one recommendation from recommend_charts(),
    returns the data payload the frontend needs to draw it.
    """
    chart_type = recommendation["chart"]

    if chart_type == "kpi":
        return _kpi_data(df, recommendation["column"])
    if chart_type == "line":
        return _line_data(df, recommendation["x"], recommendation["y"])
    if chart_type == "pie":
        return _pie_data(df, recommendation["column"])
    if chart_type == "bar":
        return _bar_data(df, recommendation["column"])
    if chart_type == "table":
        return _table_data(df, recommendation["columns"])

    return []


def build_custom_chart(
    df: pd.DataFrame,
    chart: str,
    column: str | None = None,
    x: str | None = None,
    y: str | None = None,
    columns: list[str] | None = None,
) -> dict:
    """
    Computes data for a chart configuration the *user* picked while editing
    a widget (Phase 7) — as opposed to build_chart_data(), which computes
    data for a configuration the *recommendation engine* picked (Phase 4).
    Validates inputs so a bad column name, or a column/chart mismatch
    (e.g. a bar chart on a text column), fails clearly instead of crashing.
    """
    known_columns = set(df.columns)

    def require_numeric(col: str):
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(
                f"Column '{col}' isn't numeric, so it can't be used for this chart type."
            )

    if chart == "kpi":
        if column not in known_columns:
            raise ValueError(f"Unknown column '{column}'")
        require_numeric(column)
        return {"value": float(df[column].sum())}

    if chart == "line":
        if x not in known_columns or y not in known_columns:
            raise ValueError("Both x and y columns are required for a line chart")
        require_numeric(y)
        return _line_data(df, x, y)

    if chart == "pie":
        if column not in known_columns:
            raise ValueError(f"Unknown column '{column}'")
        return _pie_data(df, column)

    if chart == "bar":
        if column not in known_columns:
            raise ValueError(f"Unknown column '{column}'")
        require_numeric(column)
        return _bar_data(df, column)

    if chart == "table":
        if not columns:
            raise ValueError("At least one column is required for a table")
        unknown = [c for c in columns if c not in known_columns]
        if unknown:
            raise ValueError(f"Unknown column(s): {', '.join(unknown)}")
        return _table_data(df, columns)

    raise ValueError(f"Unsupported chart type '{chart}'")


def build_all_chart_data(df: pd.DataFrame, recommendations: list[dict]) -> list[dict]:
    """Attaches a `data` field to each recommendation, ready for the frontend to render."""
    widgets = []
    for rec in recommendations:
        data = build_chart_data(df, rec)
        widgets.append({**rec, "data": data})
    return widgets