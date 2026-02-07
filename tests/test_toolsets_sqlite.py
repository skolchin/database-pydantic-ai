import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from pydantic_ai import RunContext, RunUsage

from database_pydantic_ai.sql.backends.sqlite import SQLiteDatabase
from database_pydantic_ai.sql.toolset import (
    SQLDatabaseDeps,
    create_database_toolset,
)
from database_pydantic_ai.types import QueryResult
from tests.conftest import MODEL, get_tool


### FIXTURES ###
@pytest_asyncio.fixture
async def sqlite_client() -> AsyncGenerator[SQLiteDatabase, Any]:
    # Using `:memory:` to use fast and RAM
    client = SQLiteDatabase(":memory:", read_only=False)
    await client.connect()

    # Seed some data for testing
    await client.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
    await client.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob');")

    yield client
    await client.close()


@pytest_asyncio.fixture
async def sqlite_client_read_only() -> AsyncGenerator[SQLiteDatabase, Any]:
    # Using `:memory:` to use fast and RAM
    client = SQLiteDatabase(":memory:", read_only=True)
    await client.connect()
    yield client
    await client.close()


@pytest.fixture
def deps(sqlite_client: SQLiteDatabase) -> SQLDatabaseDeps:
    # Instead of a generic SQLiteDatabase, use a real instance or
    # link the database attribute to your sqlite_client
    return SQLDatabaseDeps(database=sqlite_client, max_rows=20, query_timeout=10.0)


@pytest.fixture
def context(deps: SQLDatabaseDeps) -> RunContext[SQLDatabaseDeps]:
    # Using the real RunContext is safer than MagicMock for E2E
    return RunContext(model=MODEL, usage=RunUsage(), deps=deps)


### TESTS ###
def test_toolset_creation() -> None:
    toolset = create_database_toolset()
    # toolset.tools might be a dict or list depending on version,
    # but error suggested it iterates as strings (keys).
    # If it is a dict, .values() gives the tools.
    tools_list = list(toolset.tools.values()) if isinstance(toolset.tools, dict) else toolset.tools

    assert len(tools_list) == 5
    tool_names = {t.name for t in tools_list}
    assert tool_names == {
        "list_tables",
        "get_schema",
        "describe_table",
        "explain_query",
        "query",
    }


@pytest.mark.asyncio
async def test_list_tables(
    context: RunContext[SQLDatabaseDeps], sqlite_client: SQLiteDatabase
) -> None:
    toolset = create_database_toolset()
    tool = get_tool(toolset, "list_tables")

    # Make the call manually
    response = await sqlite_client.get_tables()

    # Tool call manually
    result = await tool.function(context)

    # Assert
    assert isinstance(response, list)
    assert response == result


@pytest.mark.asyncio
async def test_get_schema_object(
    context: RunContext[SQLDatabaseDeps], sqlite_client: SQLiteDatabase
) -> None:
    toolset = create_database_toolset()
    tool = get_tool(toolset, "get_schema")

    # Make the call manually
    response = await sqlite_client.get_schema(return_md=False)

    # Tool call manually
    result = await tool.function(context, return_md=False)

    # Assert
    assert response == result


@pytest.mark.asyncio
async def test_describe_table(
    context: RunContext[SQLDatabaseDeps], sqlite_client: SQLiteDatabase
) -> None:
    toolset = create_database_toolset()
    tool = get_tool(toolset, "describe_table")

    # Make the call manually
    response = await sqlite_client.get_table_info("users")

    # Tool call manually
    result = await tool.function(context, table_name="users")

    # Assert
    assert response == result


@pytest.mark.asyncio
async def test_explain_query(
    context: RunContext[SQLDatabaseDeps], sqlite_client: SQLiteDatabase
) -> None:
    toolset = create_database_toolset()
    tool = get_tool(toolset, "explain_query")

    # Make the call manually
    response = await sqlite_client.explain("SELECT COUNT(*) FROM users")

    # Tool call manually
    result = await tool.function(context, sql_query="SELECT COUNT(*) FROM users")

    # Assert
    assert response == result


@pytest.mark.asyncio
async def test_run_sql_query(
    context: RunContext[SQLDatabaseDeps], sqlite_client: SQLiteDatabase
) -> None:
    toolset = create_database_toolset()
    tool = get_tool(toolset, "query")

    # Make the call manually
    response = await sqlite_client.execute("SELECT COUNT(*) FROM users")

    # Tool call manually
    result = await tool.function(context, sql_query="SELECT COUNT(*) FROM users")

    # Assert individually due to execution time being present
    assert response.columns == result.columns
    assert response.rows == result.rows
    assert response.row_count == result.row_count


@pytest.mark.asyncio
async def test_run_sql_query_max_rows(
    context: RunContext[SQLDatabaseDeps], sqlite_client: SQLiteDatabase
) -> None:
    toolset = create_database_toolset()
    tool = get_tool(toolset, "query")

    # Make the calls manually
    response = await sqlite_client.execute("SELECT * FROM users")
    result = await tool.function(context, sql_query="SELECT * FROM users", max_rows=1)

    # Assert individually due to execution time being present
    assert response.columns == result.columns
    assert response.rows != result.rows
    assert response.row_count != result.row_count
    assert len(result) == 1
    assert len(result) != len(response)


@pytest.mark.asyncio
async def test_query_timeout(
    context: RunContext[SQLDatabaseDeps], sqlite_client: SQLiteDatabase
) -> None:
    toolset = create_database_toolset()
    tool = get_tool(toolset, "query")

    async def slow_execute(*args, **kwargs):
        await asyncio.sleep(0.5)
        return QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=0)

    # Patch the actual execute method on the client instance
    with patch.object(sqlite_client, "execute", side_effect=slow_execute):
        context.deps.query_timeout = 0.01  # Set timeout much lower than sleep
        result = await tool.function(context, sql_query="SELECT * FROM users;")

    assert isinstance(result, QueryResult)
    assert result.columns == []
    assert result.rows == []
    assert result.row_count == 0
    assert result.execution_time_ms == 0


@pytest.mark.asyncio
async def test_query_read_only_violation(sqlite_client_read_only: SQLiteDatabase) -> None:
    # Setup Deps with read_only=True
    deps = SQLDatabaseDeps(database=sqlite_client_read_only, read_only=True)
    ctx = RunContext(model=MODEL, usage=RunUsage(), deps=deps)

    toolset = create_database_toolset()
    tool = get_tool(toolset, "query")

    # Try to run a write operation
    # Your tool should catch the PermissionError or the backend should raise it
    with pytest.raises(PermissionError, match="read-only"):
        await tool.function(ctx, sql_query="DELETE FROM users")
