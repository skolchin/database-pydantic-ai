"""PydanticAI toolset for AI agents used to inference with database on given permission level"""

import asyncio
from typing import Annotated

from pydantic import BaseModel, ConfigDict, SkipValidation
from pydantic_ai import FunctionToolset, RunContext

from database_pydantic_ai.sql.protocol import SQLDatabaseProtocol
from database_pydantic_ai.types import QueryResult, SchemaInfo, TableInfo

SQLITE_SYSTEM_PROMPT = """
## SQLite Database Toolset

### IMPORTANT
* Database may be running in READ-ONLY mode
* When in read-only mode, only SELECT queries are allowed

You have access to SQLite database tools for database operations and querying:
* `list_tables` - list all tables which are present in database
* `get_schema` - read the database schema
* `describe_table` - describe table's content
* `explain_query` - explains dependencies which given SQL query needs to run
* `query` - execute a SQL query on a database to retrieve data

### Best Practices
* Always try to perform sample data query before performing full query process
* Before running any query, validate it with current schema of the tables and database
* Be careful with querying the database, try to validate beforehand
* Use `LIMIT` clause when querying large tables to avoid retrieving too much data
"""


class SQLDatabaseDeps(BaseModel):
    """
    Dependencies for the SQL database toolset.

    Attributes:
        database: Database backend instance.
        read_only: Enforce read-only mode (blocks INSERT, UPDATE, DELETE etc.)
        max_rows: Maximum rows to return from queries.
        query_timeout: Query timeout in seconds.
        id: Optional dependency ID.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    database: Annotated[SQLDatabaseProtocol, SkipValidation]
    read_only: bool = True
    max_rows: int = 100
    query_timeout: float = 30.0
    id: str | None = None


def create_database_toolset(*, id: str | None = None) -> FunctionToolset[SQLDatabaseDeps]:
    """
    Create a database toolset for AI Agents.

    Args:
        id: Optional toolset ID.

    Returns:
        FunctionalToolset with database tools
    ...
    """
    toolset = FunctionToolset[SQLDatabaseDeps](id=id)

    @toolset.tool
    async def list_tables(ctx: RunContext[SQLDatabaseDeps]) -> list[str]:
        """
        Get names of all tables in the database to understand available data.

        Returns:
            List of all table's names.
        """
        return await ctx.deps.database.get_tables()

    @toolset.tool
    async def get_schema(ctx: RunContext[SQLDatabaseDeps], return_md: bool) -> SchemaInfo | str:
        """
        Get an overview of the database schema.

        Returns:
            List of all tables with their column counts and row counts.
        """
        return await ctx.deps.database.get_schema(return_md=return_md)

    @toolset.tool
    async def describe_table(
        ctx: RunContext[SQLDatabaseDeps], table_name: str
    ) -> TableInfo | str | None:
        """
        Get detailed information about a specific table.

        Args:
            table_name: Name of the table to describe.

        Returns:
            Table structure including columns, types, constraints, and relationships.
        """
        return await ctx.deps.database.get_table_info(table_name)

    @toolset.tool
    async def explain_query(ctx: RunContext[SQLDatabaseDeps], sql_query: str) -> str:
        """
        Get the execution plan for a SQL query without executing it.

        Args:
            sql_query: The SQL query to analyze.

        Returns:
            Query execution plan showing how the database would process the query.

        Use this to:
            - Understand query performance
            - Identify missing indexes
            - Optimize slow queries
        """
        return await ctx.deps.database.explain(sql_query)

    @toolset.tool
    async def query(
        ctx: RunContext[SQLDatabaseDeps], sql_query: str, max_rows: int | None = None
    ) -> QueryResult:
        """
        Execute a SQL query and return the results.

        Args:
            sql_query: SQL query to be executed.
            max_rows: Maximum number of rows to be returned (default: 100)

        Returns:
            QueryResults object with queried data.

        Example:
            query("SELECT id, name FROM users WHERE is_banned = true;", max_rows=10)
        """
        try:
            result = await asyncio.wait_for(
                ctx.deps.database.execute(sql_query), timeout=ctx.deps.query_timeout
            )

        except asyncio.TimeoutError:
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=0,  # indicate max wait with `0`
            )

        limit = max_rows or ctx.deps.max_rows

        if len(result.rows) > limit:
            result = QueryResult(
                columns=result.columns,
                rows=result.rows[:limit],
                row_count=min(result.row_count, limit),
                execution_time_ms=result.execution_time_ms,
            )

        return result

    return toolset
