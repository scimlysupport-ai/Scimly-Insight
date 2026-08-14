"""
The Dashboard Recommendation Engine (Phase 4), curated (Phase 14/15/16
follow-up).

Takes the schema produced by the analysis engine (Phase 3) and decides
which charts best represent the dataset -- and, critically, which of
those are important enough to show *by default*. A dataset with a
dozen numeric columns and half a dozen categories used to turn into a
dashboard with 15-20 widgets; every column got a KPI, a line, or a pie
whether or not it was actually a headline metric. That's not curation,
it's just "chart everything" -- the important signal (Total Revenue,
Monthly Trend) drowns in noise (a pie chart of a rarely-used status
field).

This module still never silently drops a column: every recommendation
below is returned, always. What changed is that each one now carries an
`important: bool` -- the top few by business relevance are `True` (what
the dashboard renders immediately), the rest are `False` (offered as
"add a chart" -- see /dataset/{file_id}/dashboard, which splits on this
flag). Nothing disappears; it just doesn't all shout at once.

Chart semantics also changed:
  - Bar charts used to bin a numeric column's own values into a
    histogram. Real dashboards almost never want that -- they want a
    measure *grouped by* a category ("Revenue by Region", "Employees by
    Department"). Bar recommendations now carry x=category, y=measure.
  - Pie charts now sum the headline measure per category (falling back
    to a plain count only when there's no numeric measure at all),
    instead of always just counting rows.
  - Only measures that are actually meaningful to add up (revenue,
    deposits, transaction counts...) get used for that grouping --
    "salary" or "age" being the only numeric columns means the bar/pie
    breakdown falls back to a plain headcount instead of a nonsensical
    "Total Age by Department".
  - High-cardinality categorical columns (products, customers, branches
    -- too many slices for a pie) become a ranked "Top N" bar or table
    instead of vanishing into the leftover columns table.
"""
from app.services.column_semantics import (
    rank_measure_columns,
    primary_date_column,
    rank_dimension_columns,
    rank_entity_columns,
    rank_binary_flag_columns,
    positive_flag_value,
    looks_like_entity_name,
    preferred_agg,
    primary_sum_measure,
    entity_subject,
    date_subject,
    line_granularity,
    pluralize,
    MIN_NON_NULL_RATIO,
)

# How many of each chart type are marked `important` (shown on the
# dashboard immediately, no extra click needed). Tuned to land close to
# the ~8-9 widget dashboards real BI tools ship by default: up to 4
# KPIs, 1 trend line, 2 category breakdowns (bar + pie), 1 "Top N"
# highlight, and always exactly 1 record table.
MAX_IMPORTANT_KPIS = 4
MAX_IMPORTANT_BARS = 2
MAX_IMPORTANT_TOP_N = 2

TOP_N_DEFAULT = 10


def _is_chartable(column: dict) -> bool:
    return column["stats"].get("non_null_ratio", 1.0) >= MIN_NON_NULL_RATIO


def _kpi_title(column_name: str, agg: str) -> str:
    return f"{'Average' if agg == 'avg' else 'Total'} {column_name.title()}"


def _kpi_value(column: dict, agg: str):
    if agg == "avg":
        return column["stats"].get("mean")
    return column["stats"].get("sum")


def recommend_charts(schema: list[dict]) -> list[dict]:
    """
    schema: list of {name, dtype, stats} as produced by analyze_dataframe()
    returns: list of chart recommendations. Every item has an
      `important` flag; see module docstring. Examples:
      { "chart": "kpi", "title": "Total Revenue", "column": "revenue", "agg": "sum", "important": True }
      { "chart": "kpi", "title": "Average Salary", "column": "salary", "agg": "avg", "important": True }
      { "chart": "bar", "title": "Revenue by Category", "x": "category", "y": "revenue", "important": True }
      { "chart": "pie", "title": "Revenue by Region", "x": "region", "y": "revenue", "important": True }
      { "chart": "bar", "title": "Top 10 Products", "x": "product", "y": "revenue", "top_n": 10, "important": False }
      { "chart": "table", "title": "Top Customers", "entity_column": "customer", "measure": "revenue", "top_n": 10, "important": True }
    """
    chartable = [c for c in schema if _is_chartable(c)]

    measures = rank_measure_columns(chartable)
    date_col = primary_date_column(chartable)
    flag_names = {c["name"] for c in rank_binary_flag_columns(chartable)}
    dimensions = [c for c in rank_dimension_columns(chartable) if c["name"] not in flag_names]
    entities = rank_entity_columns(chartable)  # >12 uniques

    # The best measure to *group by category* -- only one that's
    # actually additive (revenue, deposits, ...), never "total salary"
    # or "total age". None when every measure is average-preferred, in
    # which case grouping charts fall back to a plain count.
    sum_measure = primary_sum_measure(measures)
    sum_measure_name = sum_measure["name"] if sum_measure else None

    recommendations: list[dict] = []
    charted_columns: set[str] = set()
    subject = entity_subject(chartable)
    count_subject = date_subject(date_col["name"]) if date_col else None

    # 0a. Record-count KPI -- "Total Orders", "Total Employees" -- the
    # plain "how many rows is this" headline every one of the example
    # dashboards includes and none of the measure/rate KPIs cover on
    # their own.
    recommendations.append({
        "chart": "kpi",
        "title": f"Total {pluralize(count_subject)}" if count_subject else "Total Records",
        "count_kpi": True,
        "important": True,
    })

    # 0b. Rate KPIs -- binary flag columns (attrition, churn, default,
    # ...) get a rate card instead of a meaningless headcount. These
    # share the KPI important-budget with numeric measures, but go
    # first: "Attrition Rate" is exactly as headline a metric as
    # "Total Revenue", and a dataset that has one usually doesn't have
    # many, so they rarely crowd anything out.
    flag_columns = rank_binary_flag_columns(chartable)
    for flag_col in flag_columns:
        positive = positive_flag_value(flag_col)
        if positive is None:
            continue
        recommendations.append({
            "chart": "kpi",
            "title": f"{flag_col['name'].title()} Rate",
            "rate_column": flag_col["name"],
            "rate_value": positive,
            "important": True,
        })
        charted_columns.add(flag_col["name"])

    # 1. KPI cards -- every numeric measure gets one (nothing hidden),
    # but only the top MAX_IMPORTANT_KPIS (minus the count/rate KPIs
    # above) are `important`.
    kpi_budget_used = 1 + len(flag_columns)  # 1 for the record-count KPI
    for i, col in enumerate(measures):
        agg = preferred_agg(col["name"])
        recommendations.append({
            "chart": "kpi",
            "title": _kpi_title(col["name"], agg),
            "column": col["name"],
            "agg": agg,
            "value": _kpi_value(col, agg),
            "important": (i + kpi_budget_used) < MAX_IMPORTANT_KPIS,
        })
        charted_columns.add(col["name"])

    # 2. Line chart -- the best additive measure over time. If there's a
    # date column but no summable measure (e.g. a hiring log with only
    # names/dates/salary), show a trend of *record count* over time
    # instead of skipping the line entirely -- "Hiring Trend" is exactly
    # that shape of chart.
    if date_col:
        granularity, prefix = line_granularity(date_col)
        if sum_measure_name:
            recommendations.append({
                "chart": "line",
                "title": f"{prefix} {sum_measure['name'].title()}",
                "x": date_col["name"],
                "y": sum_measure_name,
                "granularity": granularity,
                "important": True,
            })
        else:
            recommendations.append({
                "chart": "line",
                "title": f"{prefix} {date_subject(date_col['name'])} Trend",
                "x": date_col["name"],
                "y": None,
                "agg": "count",
                "granularity": granularity,
                "important": True,
            })
        charted_columns.add(date_col["name"])

        # Every other measure still gets its own trend line -- just not
        # an important one by default, so the dashboard doesn't open
        # with five near-identical timelines.
        for col in measures:
            if col["name"] == sum_measure_name:
                continue
            recommendations.append({
                "chart": "line",
                "title": f"{prefix} {col['name'].title()}",
                "x": date_col["name"],
                "y": col["name"],
                "granularity": granularity,
                "important": False,
            })

    # 3. Category breakdowns -- the lowest-cardinality dimension (fewest
    # slices) becomes the pie; the rest become grouped bars of the best
    # additive measure by that category (or a plain headcount if there
    # isn't one). Every dimension is charted, only the first couple are
    # `important`.
    pie_made = False
    bar_count = 0
    for dim in dimensions:
        if sum_measure_name:
            title = f"{sum_measure['name'].title()} by {dim['name'].title()}"
        elif subject:
            title = f"{subject}s by {dim['name'].title()}"
        else:
            title = f"{dim['name'].title()} Breakdown"
        pie_title = f"{dim['name'].title()} Distribution" if not sum_measure_name else title

        if not pie_made:
            recommendations.append({
                "chart": "pie", "title": pie_title,
                "x": dim["name"], "y": sum_measure_name,
                "important": True,
            })
            pie_made = True
        else:
            recommendations.append({
                "chart": "bar", "title": title,
                "x": dim["name"], "y": sum_measure_name,
                "important": bar_count < MAX_IMPORTANT_BARS,
            })
            bar_count += 1
        charted_columns.add(dim["name"])

    # 4. "Top N" -- high-cardinality categorical columns (too many
    # distinct values for a pie/bar-per-slice) ranked by the best
    # additive measure (or by record count with no measure). An
    # identifier-like column (customer, employee, ...) reads better as
    # a table ("Top Customers"); anything else (product, branch, sku,
    # ...) as a ranked bar ("Top 10 Products").
    for i, col in enumerate(entities):
        is_important = i < MAX_IMPORTANT_TOP_N
        title_word = col["name"].title()
        if looks_like_entity_name(col["name"]):
            recommendations.append({
                "chart": "table",
                "title": f"Top {title_word}s",
                "entity_column": col["name"],
                "measure": sum_measure_name,
                "top_n": TOP_N_DEFAULT,
                "important": is_important,
            })
        else:
            recommendations.append({
                "chart": "bar",
                "title": f"Top {TOP_N_DEFAULT} {pluralize(title_word)}",
                "x": col["name"],
                "y": sum_measure_name,
                "top_n": TOP_N_DEFAULT,
                "important": is_important,
            })
        charted_columns.add(col["name"])

    # 5. Table -- everything that isn't already represented above (text
    # columns, boolean flags, categorical columns outside the pie/bar
    # sweet spot, anything below the completeness threshold). Sorted
    # by the date column descending when one exists, so it reads as
    # "recent records" rather than an arbitrary row order.
    leftover_columns = [c["name"] for c in schema if c["name"] not in charted_columns]
    if leftover_columns:
        recommendations.append({
            "chart": "table",
            "title": "Recent Records" if date_col else "Record Details",
            "columns": leftover_columns,
            "sort_by": date_col["name"] if date_col else None,
            "important": True,
        })

    return recommendations
