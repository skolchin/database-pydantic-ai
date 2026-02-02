from typing import Any

from pydantic import BaseModel, ConfigDict


class CustomTypes(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class QueryResult(CustomTypes):
    """Result of a database query."""

    columns: list[str]
    rows: list[tuple[Any, ...]]
    row_count: int
    execution_time_ms: float

    def __len__(self) -> int:
        return len(self.rows)


class ColumnInfo(CustomTypes):
    """Information about a table column."""

    name: str
    data_type: str
    nullable: bool = True
    default: str | None = None
    is_primary_key: bool = False


class ForeignKeyInfo(CustomTypes):
    """Foreign key relationship."""

    column: str
    references_table: str
    references_column: str


class TableInfo(CustomTypes):
    """Information about a database table."""

    name: str
    columns: list[ColumnInfo]
    row_count: int | None = None
    primary_key: list[str] | None = None
    foreign_keys: list[ForeignKeyInfo] | None = None


class SchemaInfo(CustomTypes):
    """Database schema information."""

    tables: list[TableInfo | str]
    views: list[str] | None = None
