"""SQLite toolset for AI agents used to inference with database on given permission level"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import FunctionToolset, RunContext

from sql_toolset_pydantic_ai.protocol import DatabaseProtocol
from sql_toolset_pydantic_ai.types import QueryResult, SchemaInfo, TableInfo

SQLITE_SYSTEM_PROMPT = """
## SQLite Database Tools

### IMPORTANT
* Database may be running in READ-ONLY mode
* When in read-only mode, only SELECT queries are allowed

You have access to SQLite database tools for database operations and querying:
* `list_tables` - list all tables which are present in database
* `get_schema` - read the database schema
* `describe_table` - describe table's content
* `explain_query` - explains dependencies which given SQL query needs to run
* `sample_query` - do a small query to understand the data inside

### Best Practices
* Always try to perform sample data query before performing full query process
* Before running any query, validate it with current schema of the tables and database
* Be careful with querying the database, try to validate beforehand
"""


@dataclass
class SQLiteDeps:
    """Dependencies that will be available for all of the tools"""

    client: DatabaseProtocol


def create_sqlite_toolset() -> FunctionToolset[SQLiteDeps]:
    """
    Creates a bundle of tools that the PydanticAI Agent will use.
    The doc strings are `CRITICAL`; they are the instructions for the AI.
    """
    toolset = FunctionToolset[SQLiteDeps]()

    @toolset.tool
    async def list_tables(ctx: RunContext[SQLiteDeps]) -> list[str]:
        """Get names of all tables in the database to understand available data"""
        return await ctx.deps.client.get_tables()

    @toolset.tool
    async def get_schema(ctx: RunContext[SQLiteDeps]) -> SchemaInfo:
        """Get the database schema to understand the database better"""
        return await ctx.deps.client.get_schema()

    @toolset.tool
    async def describe_table(ctx: RunContext[SQLiteDeps], table_name: str) -> TableInfo:
        """Get detailed data about given table"""
        return await ctx.deps.client.get_table_info(table_name)

    @toolset.tool
    async def explain_query(ctx: RunContext[SQLiteDeps], sql_query: str) -> str:
        """Explain planned query in detail before performing it on the database"""
        return await ctx.deps.client.explain(sql_query)

    @toolset.tool
    async def sample_query(
        ctx: RunContext[SQLiteDeps], sql_query: str, limit: int = 5
    ) -> QueryResult:
        """Perform a sample query to explore the data stored"""
        return await ctx.deps.client.execute(sql_query)

    return toolset
