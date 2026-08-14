"""
Ask Scimly (Phase 15) -- turns a free-text prompt into a chart widget.

Rewritten to be schema-driven (Phase 4/14 follow-up) instead of a fixed
set of retail keyword checks. The old version only recognized prompts
containing the literal words "revenue", "customer", or "product" --
anything else (any HR or banking question, or even a retail question
about "sales" instead of "revenue") fell through to a raw table dump.
Concretely, of the 9 example questions this was built against, only 1
worked and 1 was actively misrouted to the wrong chart.

The new approach:
  1. Resolve real column names mentioned in the prompt
     (find_mentioned_column) -- "payment_method", "department",
     "category" are recognized because they're actual columns in *this*
     dataset, not because they're on a hardcoded list.
  2. Fall back to the same measure/dimension ranking the dashboard
     recommendation engine uses (column_semantics) when the prompt
     doesn't name a column explicitly -- "show sales by region" still
     works even if the revenue column is actually named "revenue" and
     the prompt says "sales".
  3. Reuse chart_data_service.build_chart_data() for the actual
     aggregation, so a chat-generated chart and a dashboard-recommended
     chart are computed by the exact same code, not two parallel
     implementations that can drift out of sync.
"""
import re

import pandas as pd

from app.services.analysis_service import analyze_dataframe, generate_ai_insights
from app.services.chart_data_service import build_chart_data
from app.services.column_semantics import (
    rank_measure_columns,
    primary_date_column,
    rank_dimension_columns,
    rank_entity_columns,
    rank_binary_flag_columns,
    positive_flag_value,
    looks_like_entity_name,
    primary_sum_measure,
    find_mentioned_column,
    date_subject,
    line_granularity,
    pluralize,
)


def _groupable_dimensions(schema: list[dict]) -> list[dict]:
    """Any categorical column that could sensibly be a "by X" group --
    low-cardinality dimensions and high-cardinality entities alike."""
    return rank_dimension_columns(schema) + rank_entity_columns(schema)


def _fallback_table(df: pd.DataFrame, schema: list[dict]) -> dict:
    """Couldn't confidently parse an intent -- show a plain table of
    the first several columns rather than nothing. Same shape a
    dashboard's leftover-columns table uses."""
    columns = [c["name"] for c in schema][:6] or list(df.columns[:6])
    spec = {"chart": "table", "columns": columns}
    data = build_chart_data(df, spec)
    return {
        **spec,
        "title": "Data preview",
        "sql": f"SELECT {', '.join(columns)} FROM dataset LIMIT 100",
        "data": data,
    }


def _summary_widget(df: pd.DataFrame, schema: list[dict]) -> dict:
    insights = generate_ai_insights(df, schema=schema)
    return {
        "chart": "insights",
        "title": "Dataset summary",
        "sql": None,
        "data": {"insights": insights},
    }


def build_ai_chat_widget(df: pd.DataFrame, prompt: str, schema: list[dict] | None = None) -> dict:
    """
    Turns a prompt like "Show monthly revenue" or "Which region
    generated the highest sales?" into { chart, title, sql, data, ... }
    ready for the frontend to render as a dashboard widget.

    `schema` is optional (computed from `df` if omitted) so existing
    callers passing just (df, prompt) keep working.
    """
    if schema is None:
        schema = analyze_dataframe(df)["schema"]

    lowered = prompt.lower().strip()

    measures = rank_measure_columns(schema)
    date_col = primary_date_column(schema)
    dimensions = _groupable_dimensions(schema)
    sum_measure = primary_sum_measure(measures)
    flag_columns = rank_binary_flag_columns(schema)

    flag_names = {f["name"] for f in flag_columns}
    non_flag_schema = [c for c in schema if c["name"] not in flag_names]

    mentioned_measure = find_mentioned_column(lowered, schema, dtypes={"numeric"})
    mentioned_dimension = find_mentioned_column(lowered, non_flag_schema, dtypes={"categorical", "text"})
    mentioned_flag = find_mentioned_column(lowered, flag_columns) if flag_columns else None

    # 1. "Summarize this dataset" -- reuse the same Phase 14 insights
    # engine the Upload page's AI Insights panel uses, instead of
    # dumping a raw table that answers nothing.
    if "summar" in lowered:
        return _summary_widget(df, schema)

    # 2. Rate questions -- "attrition rate", "what is the churn rate" --
    # checked before the generic average/mean check since a rate isn't
    # a numeric mean, it's a share of a binary flag column.
    if mentioned_flag or (flag_columns and any(w in lowered for w in ("rate", "percentage", "percent"))):
        flag = mentioned_flag or flag_columns[0]
        positive = positive_flag_value(flag)
        if positive is not None:
            group = mentioned_dimension
            if group:
                spec = {"chart": "bar", "x": group["name"], "rate_column": flag["name"], "rate_value": positive, "top_n": 12}
                data = build_chart_data(df, spec)
                title = f"{flag['name'].title()} Rate by {group['name'].title()}"
                sql = (f"SELECT {group['name']}, 100.0 * AVG({flag['name']} = '{positive}') "
                       f"FROM dataset GROUP BY {group['name']} ORDER BY 2 DESC")
                return {**spec, "title": title, "sql": sql, "data": data}
            spec = {"chart": "kpi", "rate_column": flag["name"], "rate_value": positive}
            data = build_chart_data(df, spec)
            title = f"{flag['name'].title()} Rate"
            sql = f"SELECT 100.0 * AVG({flag['name']} = '{positive}') FROM dataset"
            return {**spec, "title": title, "sql": sql, "data": data}

    # 3. Average / mean of a numeric column -- "what is the average
    # salary?", "average order value".
    if re.search(r"\baverage\b|\bavg\b|\bmean\b", lowered):
        col = mentioned_measure or (measures[0] if measures else None)
        if col:
            spec = {"chart": "kpi", "column": col["name"], "agg": "avg"}
            data = build_chart_data(df, spec)
            return {
                **spec,
                "title": f"Average {col['name'].title()}",
                "sql": f"SELECT AVG({col['name']}) FROM dataset",
                "data": data,
            }

    # 4. Trend over time -- "show monthly revenue", "daily transaction
    # trend", "hiring trend", "revenue over time".
    if date_col and any(w in lowered for w in ("trend", "over time", "monthly", "daily", "by month", "by day", "by week")):
        if "daily" in lowered or "by day" in lowered:
            granularity, prefix = "day", "Daily"
        elif "monthly" in lowered or "by month" in lowered:
            granularity, prefix = "month", "Monthly"
        else:
            granularity, prefix = line_granularity(date_col)

        measure = mentioned_measure or sum_measure
        if measure:
            spec = {"chart": "line", "x": date_col["name"], "y": measure["name"], "granularity": granularity}
            title = f"{prefix} {measure['name'].title()}"
            sql = (f"SELECT DATE_TRUNC('{granularity}', {date_col['name']}) AS period, "
                   f"SUM({measure['name']}) FROM dataset GROUP BY period ORDER BY period")
        else:
            spec = {"chart": "line", "x": date_col["name"], "y": None, "agg": "count", "granularity": granularity}
            title = f"{prefix} {date_subject(date_col['name'])} Trend"
            sql = (f"SELECT DATE_TRUNC('{granularity}', {date_col['name']}) AS period, "
                   f"COUNT(*) FROM dataset GROUP BY period ORDER BY period")
        data = build_chart_data(df, spec)
        return {**spec, "title": title, "sql": sql, "data": data}

    # 5. "Most used/common/popular X" -- the single most frequent value
    # of a categorical column.
    if any(w in lowered for w in ("most used", "most common", "most popular", "most frequent")):
        dim = mentioned_dimension or (dimensions[0] if dimensions else None)
        if dim:
            spec = {"chart": "bar", "x": dim["name"], "y": None, "top_n": 8}
            data = build_chart_data(df, spec)
            top_label = data[0]["name"] if data else None
            title = f"Most Used {dim['name'].title()}" + (f" ({top_label})" if top_label else "")
            sql = f"SELECT {dim['name']}, COUNT(*) FROM dataset GROUP BY {dim['name']} ORDER BY 2 DESC"
            return {**spec, "title": title, "sql": sql, "data": data}

    # 6. Distribution / breakdown of a single categorical column --
    # "show booking status distribution", "gender breakdown".
    if any(w in lowered for w in ("distribution", "breakdown")):
        dim = mentioned_dimension or (dimensions[0] if dimensions else None)
        if dim:
            measure = mentioned_measure or sum_measure
            spec = {"chart": "pie", "x": dim["name"], "y": measure["name"] if measure else None}
            data = build_chart_data(df, spec)
            title = f"{dim['name'].title()} Distribution"
            sql = (f"SELECT {dim['name']}, SUM({measure['name']}) FROM dataset GROUP BY {dim['name']}"
                   if measure else f"SELECT {dim['name']}, COUNT(*) FROM dataset GROUP BY {dim['name']}")
            return {**spec, "title": title, "sql": sql, "data": data}

    # 7. "Top N" -- "top 10 customers by revenue", "top 5 products".
    top_match = re.search(r"top\s+(\d+)", lowered)
    if top_match or re.search(r"\btop\b", lowered):
        n = int(top_match.group(1)) if top_match else 10
        entity = (
            mentioned_dimension
            or (rank_entity_columns(schema)[0] if rank_entity_columns(schema) else (dimensions[0] if dimensions else None))
        )
        measure = mentioned_measure or sum_measure
        if entity:
            if looks_like_entity_name(entity["name"]):
                spec = {"chart": "table", "entity_column": entity["name"], "measure": measure["name"] if measure else None, "top_n": n}
                data = build_chart_data(df, spec)
                title = f"Top {n} {pluralize(entity['name'].title())}"
                if measure:
                    title += f" by {measure['name'].title()}"
            else:
                spec = {"chart": "bar", "x": entity["name"], "y": measure["name"] if measure else None, "top_n": n}
                data = build_chart_data(df, spec)
                title = f"Top {n} {pluralize(entity['name'].title())}"
            sql = (f"SELECT {entity['name']}, SUM({measure['name']}) FROM dataset "
                   f"GROUP BY {entity['name']} ORDER BY 2 DESC LIMIT {n}"
                   if measure else
                   f"SELECT {entity['name']}, COUNT(*) FROM dataset "
                   f"GROUP BY {entity['name']} ORDER BY 2 DESC LIMIT {n}")
            return {**spec, "title": title, "sql": sql, "data": data}

    # 8. "Which X had the highest/most/best Y", "compare Y by X", "Y by
    # X" -- the broadest catch-all grouping intent, checked last among
    # the "understood" intents so more specific patterns above (trend,
    # top-N, distribution) get first refusal.
    if any(w in lowered for w in ("highest", "lowest", "most", "best", "worst", "compare", " by ", "which")):
        dim = mentioned_dimension or (dimensions[0] if dimensions else None)
        measure = mentioned_measure or sum_measure
        if dim:
            spec = {"chart": "bar", "x": dim["name"], "y": measure["name"] if measure else None, "top_n": 12}
            data = build_chart_data(df, spec)
            if measure:
                title = f"{measure['name'].title()} by {dim['name'].title()}"
                sql = f"SELECT {dim['name']}, SUM({measure['name']}) FROM dataset GROUP BY {dim['name']} ORDER BY 2 DESC"
            else:
                title = f"{dim['name'].title()} Breakdown"
                sql = f"SELECT {dim['name']}, COUNT(*) FROM dataset GROUP BY {dim['name']} ORDER BY 2 DESC"
            return {**spec, "title": title, "sql": sql, "data": data}

    # Nothing matched confidently -- show a preview instead of nothing.
    return _fallback_table(df, schema)
