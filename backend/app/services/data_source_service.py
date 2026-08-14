import json
from io import StringIO
from typing import Any

import httpx
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

from app.models.dataset import Dataset
from app.models.data_source import DataSource
from app.services.analysis_service import analyze_dataframe


SUPPORTED_SOURCE_TYPES = {
    "postgres",
    "mysql",
    "sqlserver",
    "oracle",
    "mongodb",
    "google_sheets",
    "rest_api",
}


def _sanitize_config(config: dict[str, Any]) -> dict[str, Any]:
    sanitized = {**config}
    for secret in ["password", "uri", "auth_value", "token"]:
        if secret in sanitized:
            sanitized[secret] = "[redacted]"
    return sanitized


def _parse_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_sql_url(source_type: str, config: dict[str, Any]) -> URL:
    username = config.get("username")
    password = config.get("password")
    host = config.get("host")
    port = _parse_int(config.get("port"), 0)
    database = config.get("database")

    if not host or not database or not username or password is None:
        raise ValueError("SQL data sources require host, port, database, username, and password.")

    if source_type == "postgres":
        drivername = "postgresql+psycopg2"
        port = port or 5432
    elif source_type == "mysql":
        drivername = "mysql+mysqlconnector"
        port = port or 3306
    elif source_type == "sqlserver":
        drivername = "mssql+pymssql"
        port = port or 1433
    elif source_type == "oracle":
        drivername = "oracle+oracledb"
        port = port or 1521
    else:
        raise ValueError(f"Unsupported SQL source type '{source_type}'.")

    return URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def _limit_query(source_type: str, table: str) -> str:
    if source_type == "sqlserver":
        return f"SELECT TOP 10000 * FROM {table}"
    if source_type == "oracle":
        return f"SELECT * FROM {table} WHERE ROWNUM <= 10000"
    return f"SELECT * FROM {table} LIMIT 10000"


def _read_sql_source(source_type: str, config: dict[str, Any]) -> pd.DataFrame:
    try:
        url = _build_sql_url(source_type, config)
    except ValueError as exc:
        raise

    query = config.get("query")
    table = config.get("table")
    if not query and not table:
        raise ValueError("SQL sources require either a table or a query.")

    if not query:
        query = _limit_query(source_type, table)

    try:
        engine = create_engine(url, connect_args={"connect_timeout": 10})
        df = pd.read_sql_query(query, engine)
    except SQLAlchemyError as exc:
        raise ValueError(f"Could not query SQL source: {exc}") from exc
    return df


def _read_mongodb_source(config: dict[str, Any]) -> pd.DataFrame:
    try:
        import pymongo
    except ImportError as exc:
        raise RuntimeError("MongoDB support requires pymongo to be installed.") from exc

    uri = config.get("uri")
    database = config.get("database")
    collection = config.get("collection")
    filter_value = config.get("filter", "{}")
    if not uri or not database or not collection:
        raise ValueError("MongoDB sources require uri, database, and collection.")

    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client[database]
        filter_doc = json.loads(filter_value) if isinstance(filter_value, str) and filter_value.strip() else filter_value
        cursor = db[collection].find(filter_doc).limit(10000)
        data = list(cursor)
    except Exception as exc:
        raise ValueError(f"Could not read MongoDB source: {exc}") from exc

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    return df


def _read_google_sheets_source(config: dict[str, Any]) -> pd.DataFrame:
    sheet_url = config.get("sheet_url")
    gid = config.get("gid")
    if not sheet_url:
        raise ValueError("Google Sheets sources require a sheet URL.")

    sheet_id = None
    if "/d/" in sheet_url:
        parts = sheet_url.split("/d/")
        sheet_id = parts[1].split("/")[0]
    if not sheet_id:
        raise ValueError("Could not extract sheet ID from the provided Google Sheets URL.")

    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    if gid:
        export_url += f"&gid={gid}"

    try:
        response = httpx.get(export_url, timeout=20)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
    except Exception as exc:
        raise ValueError(f"Could not read Google Sheets source: {exc}") from exc
    return df


def _read_rest_api_source(config: dict[str, Any]) -> pd.DataFrame:
    url = config.get("url")
    if not url:
        raise ValueError("REST API sources require a URL.")

    method = config.get("method", "GET").upper()
    auth_type = config.get("auth_type", "none")
    auth_value = config.get("auth_value")
    headers = config.get("headers") or {}
    response_format = config.get("response_format")

    auth = None
    if auth_type == "bearer" and auth_value:
        headers["Authorization"] = f"Bearer {auth_value}"
    elif auth_type == "basic" and auth_value:
        if isinstance(auth_value, str) and ":" in auth_value:
            user, password = auth_value.split(":", 1)
            auth = (user, password)
        else:
            raise ValueError("Basic auth requires auth_value in the form username:password.")

    try:
        response = httpx.request(method, url, headers=headers, auth=auth, timeout=20)
        response.raise_for_status()
    except Exception as exc:
        raise ValueError(f"REST API request failed: {exc}") from exc

    content_type = response.headers.get("content-type", "")
    if response_format == "csv" or "csv" in content_type:
        try:
            return pd.read_csv(StringIO(response.text))
        except Exception as exc:
            raise ValueError(f"Could not parse REST response as CSV: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise ValueError("REST response is not valid JSON and could not be parsed as CSV.") from exc

    if isinstance(payload, list):
        return pd.DataFrame(payload)
    if isinstance(payload, dict):
        if "data" in payload and isinstance(payload["data"], list):
            return pd.DataFrame(payload["data"])
        return pd.DataFrame([payload])

    raise ValueError("REST response JSON must be a list of records or an object.")


def read_source_dataframe(source_type: str, config: dict[str, Any]) -> pd.DataFrame:
    if source_type == "postgres" or source_type == "mysql" or source_type == "sqlserver" or source_type == "oracle":
        return _read_sql_source(source_type, config)
    if source_type == "mongodb":
        return _read_mongodb_source(config)
    if source_type == "google_sheets":
        return _read_google_sheets_source(config)
    if source_type == "rest_api":
        return _read_rest_api_source(config)
    raise ValueError(f"Unsupported source type '{source_type}'.")


def create_data_source(db, user_id: int, name: str, source_type: str, config: dict[str, Any]) -> tuple[DataSource, Dataset]:
    if source_type not in SUPPORTED_SOURCE_TYPES:
        raise ValueError(f"Unsupported source type '{source_type}'.")

    source = DataSource(
        user_id=user_id,
        name=name,
        source_type=source_type,
        config_json=config,
        status="processing",
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        df = read_source_dataframe(source_type, config)
        result = analyze_dataframe(df)
        dataset = Dataset(
            datasource_id=source.id,
            rows=result["rows"],
            columns=result["columns"],
            schema_json=result["schema"],
        )
        db.add(dataset)
        source.status = "ready"
        db.commit()
        db.refresh(dataset)
        db.refresh(source)
        return source, dataset
    except Exception as exc:
        source.status = "failed"
        db.commit()
        raise


def get_data_source(db, source_id: int) -> DataSource | None:
    return db.query(DataSource).filter(DataSource.id == source_id).first()


def list_data_sources(db, user_id: int) -> list[DataSource]:
    return db.query(DataSource).filter(DataSource.user_id == user_id).order_by(DataSource.created_at.desc()).all()


def ensure_source_dataset(db, source: DataSource) -> Dataset:
    existing = db.query(Dataset).filter(Dataset.datasource_id == source.id).first()
    if existing:
        return existing

    if source.status == "failed":
        raise ValueError("Source analysis previously failed. Please fix the connection and try again.")

    df = read_source_dataframe(source.source_type, source.config_json)
    result = analyze_dataframe(df)
    dataset = Dataset(
        datasource_id=source.id,
        rows=result["rows"],
        columns=result["columns"],
        schema_json=result["schema"],
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def source_response(source: DataSource) -> dict[str, Any]:
    return {
        "id": source.id,
        "name": source.name,
        "source_type": source.source_type,
        "config": _sanitize_config(source.config_json),
        "status": source.status,
        "created_at": source.created_at,
    }
