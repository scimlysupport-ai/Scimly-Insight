"""
Produces the actual data points needed to render each recommended chart
(Phase 5). The recommendation engine (Phase 4) decides *what* chart to
show; this module computes the *data* for it by aggregating the cleaned
dataframe.

Phase 14/15/16 follow-up: bar and pie now primarily mean "a measure
grouped by a category" (Sales by Category, Revenue by Region) rather
than "one numeric column's own distribution" -- the latter is kept as
a fallback for manual chart-editing (Phase 7) when someone deliberately
picks a single numeric column with no x/y pairing. Added support for
count-based aggregation (no measure column available), "Top N by
measure" tables, and sorting the leftover-columns table by date.
"""
import pandas as pd


def _coerce_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", format="mixed")


def _line_data(
    df: pd.DataFrame, x_col: str, y_col: str | None, agg: str = "sum", granularity: str = "month"
) -> list[dict]:
    """Groups by day or by month and sums (or counts) the measure
    column, sorted chronologically. y_col=None means "count records per
    bucket" -- the "Hiring Trend"/record-count-over-time case when
    there's no numeric measure to sum. `granularity` controls whether a
    bucket is a calendar day ("Daily Transaction Volume") or a calendar
    month ("Monthly Revenue") — see column_semantics.line_granularity()."""
    working = df[[x_col]].copy() if y_col is None else df[[x_col, y_col]].copy()
    working[x_col] = _coerce_datetime(working[x_col])
    working = working.dropna(subset=[x_col])

    if granularity == "day":
        bucket = working[x_col].dt.date
    else:
        bucket = working[x_col].dt.to_period("M").dt.to_timestamp().dt.date

    if y_col is None or agg == "count":
        grouped = working.groupby(bucket).size().reset_index(name="y")
        grouped.columns = ["x", "y"]
    else:
        grouped = working.groupby(bucket)[y_col].sum().reset_index()
        grouped.columns = ["x", "y"]

    grouped = grouped.sort_values("x")
    return [{"x": str(row["x"]), "y": float(row["y"])} for _, row in grouped.iterrows()]


def _grouped_bar_or_pie_data(
    df: pd.DataFrame, x_col: str, y_col: str | None, top_n: int | None = None
) -> list[dict]:
    """A measure summed per category (or a plain row count when there's
    no measure), sorted descending -- shared by both bar and pie now
    that both mean the same underlying aggregation, just rendered
    differently."""
    working = df[[x_col]] if y_col is None else df[[x_col, y_col]]
    working = working.dropna(subset=[x_col])
    if working.empty:
        return []

    if y_col is None:
        grouped = working.groupby(x_col).size().reset_index(name="value")
    else:
        grouped = working.groupby(x_col)[y_col].sum().reset_index()
        grouped.columns = [x_col, "value"]

    grouped = grouped.sort_values("value", ascending=False)
    if top_n:
        grouped = grouped.head(top_n)
    else:
        grouped = grouped.head(12)  # sane cap even for "show all" breakdowns

    return [{"name": str(row[x_col]), "value": float(row["value"])} for _, row in grouped.iterrows()]


def _pie_count_data(df: pd.DataFrame, column: str) -> list[dict]:
    """Legacy: plain value-count pie, used only when a recommendation
    or manual edit gives a single `column` with no x/y pairing."""
    counts = df[column].value_counts().head(8)
    return [{"name": str(k), "value": int(v)} for k, v in counts.items()]


def _bar_histogram_data(df: pd.DataFrame, column: str) -> list[dict]:
    """Legacy: bins a numeric column's own values into ranges and counts
    rows per bin. Kept for Phase 7 manual editing when someone picks a
    single numeric column for a bar chart with no category to group by."""
    series = df[column].dropna()
    if series.empty:
        return []
    bins = pd.cut(series, bins=min(8, series.nunique()) or 1)
    counts = bins.value_counts().sort_index()
    result = []
    for interval, count in counts.items():
        label = f"{interval.left:.0f}\u2013{interval.right:.0f}"
        result.append({"name": label, "value": int(count)})
    return result


def _rate_by_group_data(df: pd.DataFrame, group_col: str, flag_col: str, positive_value, top_n: int | None = None) -> list[dict]:
    """Percentage of rows where flag_col == positive_value, per group —
    "Attrition Rate by Department", "Default Rate by Branch". Distinct
    from _grouped_bar_or_pie_data because this is a rate (0-100), not a
    sum, so it must never be added across groups."""
    working = df[[group_col, flag_col]].dropna()
    if working.empty:
        return []
    grouped = working.groupby(group_col)[flag_col].apply(
        lambda s: 100.0 * (s == positive_value).sum() / len(s) if len(s) else 0.0
    ).reset_index(name="value")
    grouped = grouped.sort_values("value", ascending=False)
    if top_n:
        grouped = grouped.head(top_n)
    return [{"name": str(row[group_col]), "value": round(float(row["value"]), 1)} for _, row in grouped.iterrows()]


def _rate_kpi_data(df: pd.DataFrame, flag_col: str, positive_value) -> dict:
    series = df[flag_col].dropna()
    if series.empty:
        return {"value": None}
    return {"value": round(100.0 * (series == positive_value).sum() / len(series), 1)}


def _count_kpi_data(df: pd.DataFrame) -> dict:
    return {"value": int(len(df))}


def _kpi_data(df: pd.DataFrame, column: str, agg: str = "sum") -> dict:
    if agg == "avg":
        return {"value": float(df[column].mean())}
    return {"value": float(df[column].sum())}


def _table_data(df: pd.DataFrame, columns: list[str], limit: int = 100, sort_by: str | None = None) -> dict:
    """
    Row-level view for columns that don't suit a chart (text, ids, high-
    cardinality categoricals, booleans). Capped at `limit` rows so a
    500-row dataset doesn't ship its entire contents to the browser --
    `totalRows` tells the frontend how many rows exist beyond the cap.
    Sorted by `sort_by` (most recent first) when given, so it reads as
    "Recent Records" rather than an arbitrary row order.
    """
    known = [c for c in columns if c in df.columns]
    working = df
    if sort_by and sort_by in df.columns:
        working = df.copy()
        working["__sort_key"] = _coerce_datetime(working[sort_by])
        working = working.sort_values("__sort_key", ascending=False)

    subset = working[known].head(limit)
    rows = subset.astype(object).where(pd.notnull(subset), None).to_dict(orient="records")
    return {"columns": known, "rows": rows, "totalRows": int(len(df))}


def _top_entities_table(df: pd.DataFrame, entity_col: str, measure_col: str | None, top_n: int = 10) -> dict:
    """'Top Customers'/'Top Employees'-style table: the entity column
    plus its summed (or counted, with no measure) measure, ranked
    descending and capped to top_n."""
    if entity_col not in df.columns:
        return {"columns": [entity_col], "rows": [], "totalRows": 0}

    working = df[[entity_col]] if measure_col is None or measure_col not in df.columns else df[[entity_col, measure_col]]
    working = working.dropna(subset=[entity_col])

    if measure_col and measure_col in df.columns:
        grouped = working.groupby(entity_col)[measure_col].sum().reset_index()
        grouped.columns = [entity_col, measure_col]
        sort_col = measure_col
    else:
        grouped = working.groupby(entity_col).size().reset_index(name="records")
        sort_col = "records"

    grouped = grouped.sort_values(sort_col, ascending=False)
    total = int(len(grouped))
    grouped = grouped.head(top_n)
    rows = grouped.astype(object).where(pd.notnull(grouped), None).to_dict(orient="records")
    return {"columns": list(grouped.columns), "rows": rows, "totalRows": total}


def build_chart_data(df: pd.DataFrame, recommendation: dict) -> dict | list:
    """
    Given a cleaned dataframe and one recommendation from recommend_charts()
    (or a saved widget carrying the same fields), returns the data payload
    the frontend needs to draw it.
    """
    chart_type = recommendation["chart"]

    if chart_type == "kpi":
        if recommendation.get("count_kpi"):
            return _count_kpi_data(df)
        if recommendation.get("rate_column"):
            return _rate_kpi_data(df, recommendation["rate_column"], recommendation.get("rate_value"))
        return _kpi_data(df, recommendation["column"], agg=recommendation.get("agg", "sum"))

    if chart_type == "line":
        agg = recommendation.get("agg", "sum")
        granularity = recommendation.get("granularity", "month")
        return _line_data(df, recommendation["x"], recommendation.get("y"), agg=agg, granularity=granularity)

    if chart_type == "pie":
        if recommendation.get("x"):
            return _grouped_bar_or_pie_data(df, recommendation["x"], recommendation.get("y"), top_n=8)
        return _pie_count_data(df, recommendation["column"])

    if chart_type == "bar":
        if recommendation.get("rate_column") and recommendation.get("x"):
            return _rate_by_group_data(
                df, recommendation["x"], recommendation["rate_column"],
                recommendation.get("rate_value"), top_n=recommendation.get("top_n"),
            )
        if recommendation.get("x"):
            return _grouped_bar_or_pie_data(
                df, recommendation["x"], recommendation.get("y"), top_n=recommendation.get("top_n")
            )
        return _bar_histogram_data(df, recommendation["column"])

    if chart_type == "table":
        if recommendation.get("entity_column"):
            return _top_entities_table(
                df,
                recommendation["entity_column"],
                recommendation.get("measure"),
                top_n=recommendation.get("top_n", 10),
            )
        return _table_data(df, recommendation["columns"], sort_by=recommendation.get("sort_by"))

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
    a widget (Phase 7) -- as opposed to build_chart_data(), which computes
    data for a configuration the *recommendation engine* picked (Phase 4).
    Validates inputs so a bad column name, or a column/chart mismatch
    (e.g. a bar chart on a text column), fails clearly instead of crashing.

    Bar/pie now accept either the legacy single `column` (numeric
    histogram / row-count pie) or an `x` (+ optional `y`) pairing, since
    the dashboard's recommended bar/pie widgets are edited the same way
    line widgets always were -- pick a category axis and, optionally, a
    measure to sum.
    """
    known_columns = set(df.columns)

    def require_numeric(col: str):
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(
                f"Column '{col}' isn't numeric, so it can't be used for this chart type."
            )

    if chart == "kpi":
        if column is None or column == "":
            return {"value": int(len(df))}
        if column not in known_columns:
            raise ValueError(f"Unknown column '{column}'")
        require_numeric(column)
        return {"value": float(df[column].sum())}

    if chart == "line":
        if x not in known_columns:
            raise ValueError("An x (date) column is required for a line chart")
        if y is not None:
            if y not in known_columns:
                raise ValueError(f"Unknown column '{y}'")
            require_numeric(y)
        return _line_data(df, x, y)

    if chart == "pie":
        if x:
            if x not in known_columns:
                raise ValueError(f"Unknown column '{x}'")
            if y:
                if y not in known_columns:
                    raise ValueError(f"Unknown column '{y}'")
                require_numeric(y)
            return _grouped_bar_or_pie_data(df, x, y, top_n=8)
        if column not in known_columns:
            raise ValueError(f"Unknown column '{column}'")
        return _pie_count_data(df, column)

    if chart == "bar":
        if x:
            if x not in known_columns:
                raise ValueError(f"Unknown column '{x}'")
            if y:
                if y not in known_columns:
                    raise ValueError(f"Unknown column '{y}'")
                require_numeric(y)
            return _grouped_bar_or_pie_data(df, x, y)
        if column not in known_columns:
            raise ValueError(f"Unknown column '{column}'")
        require_numeric(column)
        return _bar_histogram_data(df, column)

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
        try:
            data = build_chart_data(df, rec)
        except Exception:
            data = []
        widgets.append({**rec, "data": data})
    return widgets
