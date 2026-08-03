"""
Global dashboard filters (Phase 9).

Filters are schema-driven, not hardcoded to specific field names — any
categorical column with a workable number of distinct values becomes a
multi-select filter, and any datetime column becomes a date-range filter.
This is deliberately more general than the roadmap's original "Date /
Country / Product / Department" filters: those were written before there
was real data to build against, and a dataset like an access-review
export (role / status / department / mfa / last_login) has none of the
roadmap's named fields but exactly the same *shape* of need — narrow the
rows, then recompute every chart from the narrowed set.

Special case — "tag" columns: a column like
    "Stale Admin; Admin No Mfa; Missing Department"
is categorical by dtype, but each row is really a bundle of independent
flags packed into one string, not one atomic category. Treating the whole
compound string as a single filterable value produces a useless dropdown
(every row is close to unique). Instead this module detects
delimiter-separated columns and filters/lists them by individual tag —
"show rows tagged Stale Admin", matching any row whose tag bundle
contains it — rather than by exact compound-string equality.
"""
import re
import pandas as pd

# A categorical column with too many distinct values makes an unusable
# filter dropdown (nobody wants to scroll 300 checkboxes) — same spirit
# as the pie chart's 2-12 sweet spot in the recommendation engine, just a
# looser cap since a filter list tolerates more options than a pie slice.
MAX_FILTER_OPTIONS = 50

# Checked in priority order; a delimiter only "counts" if it shows up in
# at least TAG_DELIMITER_MIN_RATIO of the column's non-null values, so a
# column that just happens to have a stray comma somewhere doesn't get
# mistaken for a tag list.
TAG_DELIMITERS = [";", "|", ","]
TAG_DELIMITER_MIN_RATIO = 0.4


def _detect_tag_delimiter(series: pd.Series) -> str | None:
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return None
    for delimiter in TAG_DELIMITERS:
        ratio = non_null.str.contains(re.escape(delimiter), regex=True).mean()
        if ratio >= TAG_DELIMITER_MIN_RATIO:
            return delimiter
    return None


def _split_tags(value, delimiter: str) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(delimiter) if part.strip()]


def get_filter_options(df: pd.DataFrame, schema: list[dict]) -> dict:
    """
    Returns the filterable columns and their available options/range,
    computed from the actual (deduplicated, coerced, normalized) data —
    not from the schema's cached top-10 `top_values`, so the filter
    dropdown always lists every real option, not just the most common ones.
    """
    categorical = []
    date_ranges = []

    for col in schema:
        name = col["name"]
        if name not in df.columns:
            continue

        if col["dtype"] == "categorical":
            column_series = df[name].dropna()
            delimiter = _detect_tag_delimiter(column_series)

            if delimiter:
                tags: set[str] = set()
                for value in column_series:
                    tags.update(_split_tags(value, delimiter))
                if 2 <= len(tags) <= MAX_FILTER_OPTIONS:
                    categorical.append({
                        "column": name,
                        "options": sorted(tags),
                        "type": "tags",
                    })
                continue

            unique_count = col["stats"].get("unique_count", 0)
            if 2 <= unique_count <= MAX_FILTER_OPTIONS:
                options = sorted(str(v) for v in column_series.unique().tolist())
                categorical.append({
                    "column": name,
                    "options": options,
                    "type": "categorical",
                })

        elif col["dtype"] == "datetime":
            parsed = pd.to_datetime(df[name], errors="coerce", format="mixed")
            if parsed.notna().any():
                date_ranges.append({
                    "column": name,
                    "min": str(parsed.min().date()),
                    "max": str(parsed.max().date()),
                })

    return {"categorical": categorical, "date_ranges": date_ranges}


def apply_filters(df: pd.DataFrame, filters: dict, schema: list[dict]) -> pd.DataFrame:
    """
    Narrows the (already coerced/normalized) dataframe to rows matching
    every active filter. Every chart the dashboard builds afterward is
    computed from this narrowed frame, so one filter change updates every
    widget at once instead of each chart filtering independently.

    For a tag-style column, a row matches if it contains ANY of the
    selected tags (the same OR semantics as a normal multi-select filter,
    just checked against the split tag bundle instead of the whole string).

    `filters` is the plain-dict form of DashboardFilters
    ({"categorical": {...}, "date_ranges": {...}}).
    """
    known_columns = {c["name"] for c in schema}
    df = df.copy()

    for column, values in (filters.get("categorical") or {}).items():
        if column not in known_columns or column not in df.columns or not values:
            continue

        delimiter = _detect_tag_delimiter(df[column].dropna())
        if delimiter:
            selected = set(values)
            mask = df[column].apply(
                lambda v: bool(selected & set(_split_tags(v, delimiter)))
            )
            df = df[mask]
        else:
            df = df[df[column].isin(values)]

    for column, date_range in (filters.get("date_ranges") or {}).items():
        if column not in known_columns or column not in df.columns:
            continue
        start = (date_range or {}).get("start")
        end = (date_range or {}).get("end")
        if not start and not end:
            continue

        series = pd.to_datetime(df[column], errors="coerce", format="mixed")
        mask = pd.Series(True, index=df.index)
        if start:
            mask &= series >= pd.to_datetime(start)
        if end:
            # Inclusive of the whole end day, not just midnight of it.
            mask &= series < pd.to_datetime(end) + pd.Timedelta(days=1)
        df = df[mask]

    return df
