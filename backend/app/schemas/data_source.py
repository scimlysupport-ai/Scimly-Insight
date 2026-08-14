from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from typing_extensions import Literal


class SourceType(str):
    POSTGRES = "postgres"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    MONGODB = "mongodb"
    GOOGLE_SHEETS = "google_sheets"
    REST_API = "rest_api"


class CreateDataSourceRequest(BaseModel):
    name: str = Field(..., min_length=1)
    source_type: Literal[
        SourceType.POSTGRES,
        SourceType.MYSQL,
        SourceType.SQLSERVER,
        SourceType.ORACLE,
        SourceType.MONGODB,
        SourceType.GOOGLE_SHEETS,
        SourceType.REST_API,
    ]
    config: dict[str, Any]


class DataSourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    config: dict[str, Any]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
