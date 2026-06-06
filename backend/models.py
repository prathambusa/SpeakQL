from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    db_alias: str = "default"

    @field_validator("question")
    @classmethod
    def strip_question(cls, v: str) -> str:
        return v.strip()


class QueryResponse(BaseModel):
    question: str
    sql: Optional[str] = None
    execution_time_ms: Optional[float] = None
    row_count: Optional[int] = None
    columns: Optional[list[str]] = None
    rows: Optional[list[list[Any]]] = None
    clarify: bool = False
    clarify_message: Optional[str] = None
    error: Optional[str] = None
    reasoning_trace: Optional[str] = None


class ColumnMeta(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None  # "referenced_table.column"


class TableMeta(BaseModel):
    name: str
    columns: list[ColumnMeta]
    row_count: Optional[int] = None
    sample_values: Optional[dict[str, list[Any]]] = None


class SchemaResponse(BaseModel):
    db_alias: str
    tables: list[TableMeta]


class RefreshResponse(BaseModel):
    db_alias: str
    tables_indexed: int
    message: str


class HealthResponse(BaseModel):
    status: str = "ok"


class DatabaseInfo(BaseModel):
    alias: str
    dialect: str
    table_count: int
    tables: list[str]
    source: str  # "env" | "dynamic" | "upload"


class DatabaseListResponse(BaseModel):
    databases: list[DatabaseInfo]


class ConnectRequest(BaseModel):
    alias: str
    url: str


class ConnectResponse(BaseModel):
    alias: str
    tables_indexed: int
    message: str
