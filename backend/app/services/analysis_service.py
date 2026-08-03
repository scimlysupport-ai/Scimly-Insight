"""
The Dataset Analysis Engine (Phase 3).

Pipeline: Read -> Clean -> Detect types -> Generate stats -> Generate metadata

This module has no knowledge of charts or dashboards — it only describes
the shape and quality of the data. Phase 4 builds chart recommendations
on top of what this module returns.
"""
import math
import pandas as pd


def _sanitize_for_json(value):
    """Convert pandas/NumPy NaN/Inf values to JSON-safe Python values."""
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if pd.isna(value):
        return None
    return value


def read_dataframe(path: str, extension: str) -> pd.DataFrame:
    """
    Reads an uploaded file into a DataFrame. CSVs exported from real-world
    tools (spreadsheets, other SaaS exports, hand-edited files) often have
    a handful of ragged rows — an extra stray comma, a quote left open —
    that make pandas' default C parser refuse the whole file with a
    ParserError. A single bad row shouldn't take down analysis of the
    other 499 good ones, so on a tokenizing failure we retry once,
    skipping only the rows that don't parse, and surface how many were
    dropped via `attrs` so the caller can report it instead of pretending
    the file was pristine.
    """
    if extension != ".csv":
        return pd.read_excel(path)

    try:
        df = pd.read_csv(path)
        df.attrs["skipped_rows"] = 0
        return df
    except pd.errors.ParserError:
        skipped = 0

        def _count_bad_line(bad_line: list[str]) -> None:
            nonlocal skipped
            skipped += 1

        df = pd.read_csv(
            path,
            engine="python",
            on_bad_lines=_count_bad_line,
        )
        df.attrs["skipped_rows"] = skipped
        return df


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows only — no imputation. This is the frame
    that column stats (null_count, unique_count, etc.) should be computed
    from, so missingness is measured against real gaps, not against values
    a later imputation step invented."""
    return df.drop_duplicates().copy()


def impute(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing values sensibly per column type. This is purely a
    rendering convenience for charts (a line/bar chart needs a real number
    to plot) — it must run *after* stats are computed, never before, or
    every fabricated fill value gets counted as if it were real data."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = df[col].fillna("Unknown")
    return df


def _normalize_categorical_series(series: pd.Series) -> pd.Series:
    """
    Collapses whitespace/case noise so the same real-world category doesn't
    get counted as several ("Admin" / "Admin " / "ADMIN" / "viewer" all
    become one group). Deliberately conservative: only trims, collapses
    internal whitespace, and title-cases — it does not fuzzy-match spelling
    variants ("Ad min" stays distinct from "Admin"). Nulls untouched.
    """
    def clean(value):
        if pd.isna(value):
            return value
        return " ".join(str(value).split()).title()

    return series.map(clean)


def coerce_dataframe(df: pd.DataFrame, schema: list[dict]) -> pd.DataFrame:
    """
    Applies the types decided by analyze_dataframe()'s schema to the actual
    dataframe, so chart-building and filtering code operates on real
    numeric/datetime dtypes and normalized category labels — not on the
    raw strings pandas happened to infer from the file.
    """
    df = df.copy()
    for col in schema:
        name = col["name"]
        if name not in df.columns:
            continue
        dtype = col["dtype"]
        if dtype == "numeric":
            df[name] = pd.to_numeric(df[name], errors="coerce")
        elif dtype == "datetime":
            df[name] = pd.to_datetime(df[name], errors="coerce", format="mixed")
        elif dtype == "categorical":
            df[name] = _normalize_categorical_series(df[name])
    return df


def clean_dataframe(df: pd.DataFrame, schema: list[dict] | None = None) -> pd.DataFrame:
    """Dedup + impute in one step. Kept for chart-rendering call sites that
    just need a fully-populated frame to plot — analysis/stats should use
    deduplicate() alone instead so imputation doesn't mask missingness.

    Pass `schema` whenever available — it coerces dtypes and normalizes
    categorical text *before* deduping/imputing, fixing charts built on
    dirty numeric-as-string columns and letting rows differing only by
    whitespace/case correctly collapse as duplicates.
    """
    if schema is not None:
        df = coerce_dataframe(df, schema)
    return impute(deduplicate(df))


def _detect_column_type(series: pd.Series) -> str:
    """
    Classifies a column as one of: empty, datetime, numeric, boolean, categorical, text.
    Categorical vs text is decided by cardinality relative to row count.
    """
    if series.notna().sum() == 0:
        # A column with zero real values (every row blank) isn't "numeric" just
        # because pandas defaults an all-NaN column to float64 — it has no
        # data to be numeric *about*. This schema is shown directly to the
        # user (Upload page), so labeling it honestly matters.
        return "empty"

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    # NOTE: don't gate the checks below on `series.dtype == object`. Some
    # pandas versions store text in a dedicated string dtype (not plain
    # `object`), so that check silently evaluates to False and skips both
    # the datetime parsing and the free-text heuristic below — every text
    # column then falls straight through to the categorical/identifier
    # logic, regardless of what it actually contains. is_string_dtype()
    # covers both cases.
    is_stringy = pd.api.types.is_string_dtype(series) or series.dtype == object

    # Try parsing as datetime — only classify as datetime if it mostly succeeds
    if is_stringy:
        sample = series.dropna().head(50)
        if len(sample) > 0:
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                return "datetime"

    unique_ratio = series.nunique() / max(len(series), 1)

    # A numeric-looking column doesn't always arrive as a numeric dtype —
    # a stray non-numeric entry (a typo, a word like "forty-nine" instead
    # of "49") is enough to make pandas read the whole column as strings.
    # If the overwhelming majority still parse as numbers, treat it as
    # numeric (the bad entries become missing values) instead of writing
    # off the entire column as categorical.
    if is_stringy:
        coerced = pd.to_numeric(series, errors="coerce")
        if coerced.notna().sum() / series.notna().sum() >= 0.8:
            return "numeric"

    # Long free-text values (sentences, notes, descriptions) should never be
    # treated as categorical, even if every value happens to be unique in a
    # small sample — a pie chart of full sentences is never useful.
    if is_stringy:
        non_null = series.dropna().astype(str)
        avg_length = non_null.str.len().mean() if len(non_null) > 0 else 0
        if avg_length > 30:
            return "text"

    # Identifier-like columns (name, email, id, sku, ...) are effectively
    # unique per row. Even in a small dataset where the raw count of
    # distinct values happens to be <= 50, a column where almost every
    # value is different isn't a "category" — it's per-record detail
    # (the same kind of column a table, not a pie chart, should show).
    if unique_ratio >= 0.9 and series.nunique() > 1:
        return "text"

    if unique_ratio < 0.5 or series.nunique() <= 50:
        return "categorical"

    return "text"


def _column_stats(series: pd.Series, col_type: str) -> dict:
    null_count = int(series.isna().sum())
    non_null_ratio = round(1 - (null_count / len(series)), 3) if len(series) else 0.0

    if col_type == "empty":
        return {
            "null_count": null_count,
            "non_null_ratio": non_null_ratio,
        }

    if col_type == "numeric":
        real = pd.to_numeric(series, errors="coerce").dropna()
        return {
            "min": float(real.min()) if not real.empty else None,
            "max": float(real.max()) if not real.empty else None,
            "mean": round(float(real.mean()), 2) if not real.empty else None,
            "median": float(real.median()) if not real.empty else None,
            "sum": float(real.sum()) if not real.empty else None,
            "std": round(float(real.std()), 2) if len(real) > 1 and real.std() == real.std() else 0,
            "null_count": null_count,
            "non_null_ratio": non_null_ratio,
        }

    if col_type == "datetime":
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")
        return {
            "min": str(parsed.min()) if parsed.notna().any() else None,
            "max": str(parsed.max()) if parsed.notna().any() else None,
            "null_count": null_count,
            "non_null_ratio": non_null_ratio,
        }

    if col_type == "categorical":
        real = series.dropna()
        value_counts = real.value_counts().head(10)
        return {
            "unique_count": int(real.nunique()),
            "top_values": {str(k): int(v) for k, v in value_counts.items()},
            "null_count": null_count,
            "non_null_ratio": non_null_ratio,
        }

    if col_type == "boolean":
        return {
            "true_count": int(series.sum()),
            "false_count": int((~series.astype(bool)).sum()),
            "null_count": null_count,
            "non_null_ratio": non_null_ratio,
        }

    # text
    real = series.dropna()
    return {
        "unique_count": int(real.nunique()),
        "null_count": null_count,
        "non_null_ratio": non_null_ratio,
    }


def analyze_dataframe(df: pd.DataFrame) -> dict:
    """
    Runs the full pipeline and returns metadata in the shape:
    { rows, columns, schema: [{ name, dtype, stats }] }

    Stats are computed from the deduplicated-but-NOT-imputed frame, so
    null_count/unique_count/non_null_ratio reflect the data as uploaded.
    Imputation (clean_dataframe / impute) is a chart-rendering concern for
    Phase 5, not an analysis concern — it must never run before stats are
    taken, or fabricated fill values get silently counted as real data.
    """
    deduped = deduplicate(df)

    schema = []
    for col in deduped.columns:
        raw_series = deduped[col]
        col_type = _detect_column_type(raw_series)
        stats = _column_stats(raw_series, col_type)
        schema.append({
            "name": str(col),
            "dtype": col_type,
            "stats": stats,
        })

    return {
        "rows": int(deduped.shape[0]),
        "columns": int(deduped.shape[1]),
        "schema": _sanitize_for_json(schema),
        "skipped_rows": int(df.attrs.get("skipped_rows", 0)),
    }