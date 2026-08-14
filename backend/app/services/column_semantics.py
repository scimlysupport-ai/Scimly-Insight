"""
Domain-agnostic column semantics, built on top of the schema Phase 3
already produces (name/dtype/stats per column) — no dataset-specific
vocabulary like "revenue" or "customer" required to use this module,
though a handful of hint words *tune* the ranking so a column plainly
named "revenue" still outranks one named "misc_value".

Used by:
  - recommendation_service.py (Phase 4) — deciding which few charts are
    "important" enough to show by default.
  - ai_chat_service.py (Phase 15) — resolving "sales", "department",
    "average" etc. in a free-text prompt to actual columns.
  - analysis_service.generate_ai_insights (Phase 14) — picking a
    sensible measure/dimension pair for datasets with no revenue-style
    column (HR, banking, ...).
"""

# Tiered hint words for a numeric column's role. Tier 0 is the strongest
# signal it's a *headline* business measure (worth a KPI card / the
# primary trend line); later tiers are still plausible measures, just
# not the first one to lead with. A column only needs to match one word
# in a tier via substring — "total_revenue" matches "revenue".
MEASURE_HINT_TIERS: list[set[str]] = [
    {"revenue", "sales"},
    {"profit", "income", "total", "salary", "deposit", "balance"},
    {"amount", "transaction", "cost", "price"},
    {"quantity", "count", "rate", "age", "score", "value"},
]

# Measures where an average is the meaningful summary, not a sum — "Total
# Age: 1,380" or "Total Salary: $2.39M" tells nobody anything useful,
# whereas "Average Age" / "Average Salary" is exactly the KPI a person
# expects. Everything else (revenue, profit, deposits, transaction
# counts, ...) is a quantity worth adding up.
AVERAGE_PREFERRED_HINTS = {"age", "rate", "score", "salary", "price"}

# Columns whose values are individual real-world entities (people,
# accounts, products) rather than a handful of grouping categories —
# these suit a "Top N" ranked bar/table, never a pie (too many slices).
ENTITY_NAME_HINTS = {
    "customer", "client", "buyer", "employee", "user", "person",
    "patient", "member", "student", "vendor", "supplier", "account",
    "name",
}

MIN_NON_NULL_RATIO = 0.5


def _non_null_ok(column: dict) -> bool:
    return column["stats"].get("non_null_ratio", 1.0) >= MIN_NON_NULL_RATIO


def _measure_tier(column_name: str) -> int:
    lowered = column_name.lower()
    for tier, words in enumerate(MEASURE_HINT_TIERS):
        if any(word in lowered for word in words):
            return tier
    return len(MEASURE_HINT_TIERS)  # no hint match — lowest priority, still usable


def is_measure_hint(column_name: str) -> bool:
    return _measure_tier(column_name) < len(MEASURE_HINT_TIERS)


def preferred_agg(column_name: str) -> str:
    """'sum' or 'avg' — which aggregation actually means something for
    this measure. Ranking (which tier it's in) and aggregation (how to
    summarize it) are independent: 'salary' is a perfectly important
    headline measure, it just should never be added up across rows."""
    lowered = column_name.lower()
    return "avg" if any(hint in lowered for hint in AVERAGE_PREFERRED_HINTS) else "sum"


def primary_sum_measure(measures: list[dict]) -> dict | None:
    """The best-ranked measure that's also meaningful to add up across a
    category — used for grouping charts (bar/pie/line), where 'Salary by
    Department' summed would be a meaningless total. Falls back to None
    (grouping charts then fall back to a plain row count) when every
    available measure is average-preferred."""
    for measure in measures:
        if preferred_agg(measure["name"]) == "sum":
            return measure
    return None


def looks_like_entity_name(column_name: str) -> bool:
    lowered = column_name.lower()
    return any(hint in lowered for hint in ENTITY_NAME_HINTS)


_SUBJECT_SUFFIXES = ("_date", "_name", "_id", "date", "name", "id")


def _derive_subject(column_name: str) -> str:
    """order_date -> Order, employee_name -> Employee, hire_date -> Hire.
    Used to build a natural chart title (e.g. "Employees by Department",
    "Monthly Order Trend") when there's no numeric measure to name the
    chart after instead."""
    lowered = column_name.lower().strip("_")
    for suffix in _SUBJECT_SUFFIXES:
        if lowered.endswith(suffix) and len(lowered) > len(suffix):
            lowered = lowered[: -len(suffix)].strip("_")
            break
    return lowered.replace("_", " ").title() or column_name.title()


_NEGATIVE_FLAG_VALUES = {"no", "false", "0", "inactive", "n", "not attrited", "retained", "active"}

# Only column *names* that plausibly mean "rate of a notable event" turn
# into a rate KPI — a 2-value column alone isn't enough of a signal
# (gender, active/inactive membership, yes/no newsletter opt-in are all
# perfectly ordinary 2-value columns with no "rate" meaning; treating
# every one as a rate produced nonsense like "Gender Rate: 50%").
RATE_HINT_WORDS = {
    "attrition", "churn", "default", "fraud", "converted", "conversion",
    "repeat", "retention", "complaint", "return", "cancel", "cancelled",
    "canceled", "delinquent", "risk", "failed", "failure", "bounced",
}


def _name_suggests_rate(column_name: str) -> bool:
    lowered = column_name.lower()
    return any(hint in lowered for hint in RATE_HINT_WORDS)


def is_binary_flag_column(column: dict) -> bool:
    """A categorical column with exactly two values *and* a name that
    plausibly means a notable event (attrition, churn, default, ...) —
    these need a rate ("32% attrition in Sales"), not a headcount, when
    someone asks for them "by" some other dimension. Deliberately
    conservative: a 2-value column with an ordinary descriptive name
    (gender, active) is still just a normal dimension, not a rate."""
    return (
        column["dtype"] == "categorical"
        and column["stats"].get("unique_count") == 2
        and _name_suggests_rate(column["name"])
    )


def positive_flag_value(column: dict) -> str | None:
    """Which of the two values is 'the thing being measured' — the
    event of interest a rate should be computed over. Heuristic: an
    explicitly negative-sounding word (no/false/inactive/retained/...)
    is never the positive value; failing that, the minority value is
    almost always the one someone means by "the X rate" (attrition,
    churn, default, fraud are all rare-event columns), so lower count
    wins the tie."""
    top_values = column["stats"].get("top_values") or {}
    if not top_values or len(top_values) != 2:
        return None
    candidates = list(top_values.items())
    named_negative = [v for v, _ in candidates if str(v).strip().lower() in _NEGATIVE_FLAG_VALUES]
    if len(named_negative) == 1:
        negative = named_negative[0]
        return next(v for v, _ in candidates if v != negative)
    # No clear naming signal — assume the rarer value is the event of interest.
    return min(candidates, key=lambda item: item[1])[0]


def rank_binary_flag_columns(schema: list[dict]) -> list[dict]:
    """Categorical columns with exactly two values (attrition, churn,
    default, active/inactive, ...) — worth a rate KPI on the dashboard,
    e.g. "Attrition Rate: 12%", the way a bare headcount never would
    be."""
    return [c for c in schema if _non_null_ok(c) and is_binary_flag_column(c)]


def pluralize(word: str) -> str:
    if word.endswith(("s", "x", "ch", "sh")):
        return word + "es"
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


def entity_subject(schema: list[dict]) -> str | None:
    """A natural singular noun for 'one row' in this dataset, e.g.
    "Employee" for a column named employee_name/employee_id. Used to
    turn a bare dimension breakdown into "Employees by Department"
    instead of a generic "Department Breakdown" when there's no measure
    to name the chart after.

    Deliberately restricted to *high-cardinality* columns (>12 distinct
    values, or an ~always-unique text column) — a low-cardinality
    dimension like "account_type" (Checking/Savings/Credit) can still
    contain a hint word ("account") without being an identifier column
    at all; using it here would claim each *row* is one "Account Type"
    when actually many rows share each of the 2-3 values."""
    for col in schema:
        if not looks_like_entity_name(col["name"]):
            continue
        if col["dtype"] == "text":
            return _derive_subject(col["name"])
        if col["dtype"] == "categorical" and col["stats"].get("unique_count", 0) > 12:
            return _derive_subject(col["name"])
    return None


def date_subject(date_column_name: str) -> str:
    """order_date -> Order, hire_date -> Hire — the 'thing being dated',
    for a trend-line title when there's no measure ("Hire Trend")."""
    return _derive_subject(date_column_name)


def line_granularity(date_column: dict, long_range_days: int = 62) -> tuple[str, str]:
    """Decides whether a trend line should bucket by day or by month,
    based on how much time the date column actually spans — a few
    weeks of daily transactions reads best as "Daily Transaction
    Volume"; a couple of years of orders reads best as "Monthly
    Revenue". Returns (granularity, title_prefix)."""
    import pandas as pd

    min_raw = date_column["stats"].get("min")
    max_raw = date_column["stats"].get("max")
    if min_raw and max_raw:
        try:
            span_days = (pd.to_datetime(max_raw) - pd.to_datetime(min_raw)).days
            if span_days <= long_range_days:
                return "day", "Daily"
        except (ValueError, TypeError):
            pass
    return "month", "Monthly"


def rank_measure_columns(schema: list[dict]) -> list[dict]:
    """Numeric columns, headline-hint columns first, then by name for
    stable ordering. This is the single ranking both the dashboard and
    Ask Scimly use to decide "which number matters most here"."""
    numeric = [c for c in schema if c["dtype"] == "numeric" and _non_null_ok(c)]
    return sorted(numeric, key=lambda c: (_measure_tier(c["name"]), c["name"].lower()))


def primary_date_column(schema: list[dict]) -> dict | None:
    dates = [c for c in schema if c["dtype"] == "datetime" and _non_null_ok(c)]
    return dates[0] if dates else None


def all_date_columns(schema: list[dict]) -> list[dict]:
    return [c for c in schema if c["dtype"] == "datetime" and _non_null_ok(c)]


def rank_dimension_columns(schema: list[dict], min_unique: int = 2, max_unique: int = 12) -> list[dict]:
    """Categorical columns with few enough distinct values to suit a
    pie or a grouped-by-category bar, fewest options first (fewest
    slices reads best as a pie)."""
    dims = [
        c for c in schema
        if c["dtype"] == "categorical"
        and _non_null_ok(c)
        and min_unique <= c["stats"].get("unique_count", 0) <= max_unique
    ]
    return sorted(dims, key=lambda c: c["stats"].get("unique_count", 0))


def rank_entity_columns(schema: list[dict], min_unique: int = 13) -> list[dict]:
    """Categorical columns with too many distinct values for a pie —
    individual records (products, customers, branches) better suited
    to a ranked 'Top N' bar or table, most distinct first."""
    entities = [
        c for c in schema
        if c["dtype"] == "categorical"
        and _non_null_ok(c)
        and c["stats"].get("unique_count", 0) > min_unique
    ]
    return sorted(entities, key=lambda c: -c["stats"].get("unique_count", 0))


def find_mentioned_column(prompt: str, schema: list[dict], dtypes: set[str] | None = None) -> dict | None:
    """
    Looks for an actual column name (normalized: lowercased, `_`/`-`
    treated as spaces) appearing in the user's free-text prompt — e.g.
    "payment_method" matches "...which payment method is most used?".
    This is what lets Ask Scimly work on *any* dataset's real column
    names instead of a hardcoded list of retail/HR/banking words:
    whatever the columns are actually called, if the person's question
    names one, we find it.

    Longer column names are preferred so "product_category" wins over
    a shorter but also-present "category" when both appear.
    """
    lowered_prompt = prompt.lower()
    candidates = [c for c in schema if dtypes is None or c["dtype"] in dtypes]

    matches = []
    for col in candidates:
        normalized = col["name"].lower().replace("_", " ").replace("-", " ")
        if normalized and normalized in lowered_prompt:
            matches.append(col)
    if not matches:
        return None
    matches.sort(key=lambda c: -len(c["name"]))
    return matches[0]
