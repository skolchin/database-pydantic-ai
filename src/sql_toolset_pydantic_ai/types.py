from dataclasses import dataclass
from typing import Any


@dataclass
class QueryResult:
    """Result of a database query."""

    columns: list[str]
    rows: list[tuple[Any, ...]]
    row_count: int
    execution_time_ms: float


@dataclass
class TableInfo:
    """Information about a database table."""

    name: str
    columns: list["ColumnInfo"]
    row_count: int | None = None
    primary_key: list[str] | None = None
    foreign_keys: list["ForeignKeyInfo"] | None = None


@dataclass
class ColumnInfo:
    """Information about a table column."""

    name: str
    data_type: str
    nullable: bool = True
    default: str | None = None
    is_primary_key: bool = False


@dataclass
class ForeignKeyInfo:
    """Foreign key relationship."""

    column: str
    references_table: str
    references_column: str


@dataclass
class SchemaInfo:
    """Database schema information."""

    tables: list[TableInfo]
    views: list[str] | None = None
