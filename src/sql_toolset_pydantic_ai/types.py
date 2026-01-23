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


# def create_database_toolset(
#     database: DatabaseProtocol | None = None,
#     read_only: bool = True,
#     max_rows: int = 1000,
#     query_timeout: float = 30.0,
#     id: str | None = None,
# ) -> FunctionToolset[DatabaseDeps]:
#     """
#     Create a database toolset for AI agents.

#     Args:
#         database: Database backend instance. If None, uses deps.database.
#         read_only: Enforce read-only mode (blocks INSERT, UPDATE, DELETE, etc.).
#         max_rows: Maximum rows to return from queries.
#         query_timeout: Query timeout in seconds.
#         id: Optional toolset ID.

#     Returns:
#         FunctionToolset with database tools.

#     Example:
#         from pydantic_ai_database import create_database_toolset, PostgresDatabase

#         db = PostgresDatabase("postgresql://user:pass@localhost/mydb")
#         toolset = create_database_toolset(db, read_only=True)

#         agent = Agent(
#             "openai:gpt-4.1",
#             toolsets=[toolset],
#         )
#     """

# @toolset.tool
# async def query(
#     ctx: RunContext[DatabaseDeps],
#     sql: str,
#     limit: int | None = None,
# ) -> str:
#     """
#     Execute a SQL query and return results.

#     Args:
#         sql: The SQL query to execute. Use parameterized queries for safety.
#         limit: Maximum number of rows to return (default: 100).

#     Returns:
#         Query results formatted as a markdown table.

#     Example:
#         query("SELECT id, name FROM users WHERE active = true", limit=10)
#     """


# @toolset.tool
# async def describe_schema(
#     ctx: RunContext[DatabaseDeps],
# ) -> str:
#     """
#     Get an overview of the database schema.

#     Returns:
#         List of all tables with their column counts and row counts.
#     """

# @toolset.tool
# async def describe_table(
#     ctx: RunContext[DatabaseDeps],
#     table_name: str,
# ) -> str:
#     """
#     Get detailed information about a specific table.

#     Args:
#         table_name: Name of the table to describe.

#     Returns:
#         Table structure including columns, types, constraints, and relationships.
#     """

# @toolset.tool
# async def explain_query(
#     ctx: RunContext[DatabaseDeps],
#     sql: str,
# ) -> str:
#     """
#     Get the execution plan for a SQL query without executing it.

#     Args:
#         sql: The SQL query to analyze.

#     Returns:
#         Query execution plan showing how the database would process the query.

#     Use this to:
#         - Understand query performance
#         - Identify missing indexes
#         - Optimize slow queries
#     """

# @toolset.tool
# async def sample_data(
#     ctx: RunContext[DatabaseDeps],
#     table_name: str,
#     limit: int = 5,
# ) -> str:
#     """
#     Get sample rows from a table to understand its data.

#     Args:
#         table_name: Name of the table to sample.
#         limit: Number of sample rows (default: 5, max: 20).

#     Returns:
#         Sample rows formatted as a markdown table.
#     """
