from typing import Any, Protocol, runtime_checkable

from database_pydantic_ai.types import ForeignKeyInfo, QueryResult, SchemaInfo, TableInfo


@runtime_checkable
class SQLDatabaseProtocol(Protocol):
    """Protocol for database backends."""

    read_only: bool
    echo: bool

    async def connect(self) -> None:
        """Connect to the database"""
        ...

    async def close(self) -> None:
        """Close database connection."""
        ...

    async def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> QueryResult:
        """Execute a SQL query with optional parameters."""
        ...

    async def get_tables(self, schema_name: str | None = None) -> list[str]:
        """Get list of tables in the database"""
        ...

    async def get_foreign_keys(self, table_name: str) -> list[ForeignKeyInfo]:
        """Get information about foreign keys in given table"""
        ...

    async def get_table_info(self, table_name: str) -> TableInfo | str | None:
        """Get detailed information about a specific table."""
        ...

    async def get_schemas(self) -> list[str] | None:
        """Get list of schemas in the database or None if schemas are not supported """
        ...

    async def get_schema(self, schema_name: str | None = None, return_md: bool = True) -> SchemaInfo | str:
        """Get database schema information."""
        ...

    async def explain(self, query: str) -> str:
        """Get query execution plan."""
        ...
