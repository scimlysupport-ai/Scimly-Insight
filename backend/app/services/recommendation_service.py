"""
The Dashboard Recommendation Engine (Phase 4).

Takes the schema produced by the analysis engine (Phase 3) and decides,
per column, which chart type best represents it:

  numeric column that looks like a total/measure  -> KPI card
  categorical column (few unique values)           -> Pie chart
  datetime column paired with a numeric column     -> Line chart (timeline)
  numeric column (general, not a KPI candidate)     -> Bar chart
  everything else (text, ids, high-cardinality
  categorical, booleans, e.g. name/email/position)  -> Table (record list)

Every column in the schema ends up in exactly one recommendation.
Nothing is silently dropped — columns that don't suit a chart (an
email address, a free-text note, a "position" field with 40 distinct
titles) still need to reach the dashboard, just as a table instead of
a chart.

This module only returns JSON describing the recommendation — it does
not render anything. Phase 5 (React) is responsible for drawing it.
"""

# Words that hint a numeric column represents a headline "total" metric,
# which suits a KPI card better than a bar chart.
KPI_HINT_WORDS = {
    "revenue", "sales", "total", "amount", "profit", "income",
    "count", "quantity", "cost", "price", "value",
}


def _is_kpi_candidate(column_name: str) -> bool:
    name = column_name.lower()
    return any(hint in name for hint in KPI_HINT_WORDS)


# A column with more gaps than real values makes a misleading chart —
# a "trend" that's mostly imputed, or a pie slice that's mostly "Unknown"
# isn't information, it's noise. Below this threshold a column still goes
# to the dashboard, just as a table row instead of a chart, so the data
# itself is never hidden — only the misleading visualization of it is.
MIN_NON_NULL_RATIO = 0.5


def _is_chartable(column: dict) -> bool:
    return column["stats"].get("non_null_ratio", 1.0) >= MIN_NON_NULL_RATIO


def recommend_charts(schema: list[dict]) -> list[dict]:
    """
    schema: list of {name, dtype, stats} as produced by analyze_dataframe()
    returns: list of chart recommendations, e.g.
      { "chart": "kpi", "title": "Total Revenue", "column": "revenue" }
      { "chart": "pie", "title": "Category breakdown", "column": "category" }
      { "chart": "line", "title": "Revenue over time", "x": "date", "y": "revenue" }
      { "chart": "bar", "title": "Quantity by column", "column": "quantity" }
    """
    chartable = [c for c in schema if _is_chartable(c)]

    numeric_cols = [c for c in chartable if c["dtype"] == "numeric"]
    categorical_cols = [c for c in chartable if c["dtype"] == "categorical"]
    datetime_cols = [c for c in chartable if c["dtype"] == "datetime"]

    recommendations: list[dict] = []

    # Track every column name we end up charting, so we can tell at the
    # end which ones (if any) still need to land somewhere.
    charted_columns: set[str] = set()

    # 1. KPI cards — numeric columns whose name signals a headline metric
    kpi_columns = [c for c in numeric_cols if _is_kpi_candidate(c["name"])]
    for col in kpi_columns:
        recommendations.append({
            "chart": "kpi",
            "title": f"Total {col['name'].title()}",
            "column": col["name"],
            "value": col["stats"].get("sum"),
        })
        charted_columns.add(col["name"])

    # 2. Line charts — pair each datetime column with each numeric measure
    if datetime_cols and numeric_cols:
        date_col = datetime_cols[0]  # primary timeline
        for num_col in numeric_cols:
            recommendations.append({
                "chart": "line",
                "title": f"{num_col['name'].title()} over time",
                "x": date_col["name"],
                "y": num_col["name"],
            })
            charted_columns.add(date_col["name"])
            charted_columns.add(num_col["name"])

    # 3. Pie charts — categorical columns with a reasonable number of segments
    for col in categorical_cols:
        unique_count = col["stats"].get("unique_count", 0)
        if 2 <= unique_count <= 12:
            recommendations.append({
                "chart": "pie",
                "title": f"Breakdown by {col['name'].title()}",
                "column": col["name"],
            })
            charted_columns.add(col["name"])

    # 4. Bar charts — remaining numeric columns not already used as a KPI
    # or already plotted as a line. A column that already has a trend line
    # doesn't need a second, redundant view as a histogram — that's the
    # same measure charted twice, not two different insights.
    non_kpi_numeric = [c for c in numeric_cols if c["name"] not in charted_columns]
    for col in non_kpi_numeric:
        recommendations.append({
            "chart": "bar",
            "title": f"{col['name'].title()} distribution",
            "column": col["name"],
        })
        charted_columns.add(col["name"])

    # 5. Table — everything that isn't already represented above.
    # This covers:
    #   - "text" columns (names, emails, free-text notes — never chartable)
    #   - "categorical" columns that fell outside the pie's 2–12 sweet spot
    #     (e.g. a "position" column with 40 distinct job titles, or one
    #     with only a single value)
    #   - "boolean" columns
    #   - any column (of any dtype) that failed the completeness gate above
    # Without this, any column that isn't a good chart candidate would
    # simply vanish from the dashboard instead of being shown at all.
    leftover_columns = [c["name"] for c in schema if c["name"] not in charted_columns]
    if leftover_columns:
        recommendations.append({
            "chart": "table",
            "title": "Record Details",
            "columns": leftover_columns,
        })

    return recommendations