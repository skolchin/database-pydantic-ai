import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from pydantic_ai import RunContext, RunUsage
from testcontainers.postgres import PostgresContainer

from database_pydantic_ai.sql.backends.postgres import PostgreSQLDatabase
from database_pydantic_ai.sql.toolset import (
    SQLDatabaseDeps,
    create_database_toolset,
)
from database_pydantic_ai.types import QueryResult
from tests.conftest import MODEL, get_tool


### FIXTURES ###
# Provide a clean Database instance for each individual test
@pytest_asyncio.fixture(scope="function")
async def pg_client(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[PostgreSQLDatabase, Any]:
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)

    db = PostgreSQLDatabase(
        user=postgres_container.username,
        password=postgres_container.password,
        db=postgres_container.dbname,
        host=f"{host}:{port}",
        read_only=False,
    )

    await asyncio.wait_for(db.connect(max_size=5), timeout=120.0)

    # SETUP: Create tables needed for tests
    await db.execute("DROP TABLE IF EXISTS users CASCADE;")
    await db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);")
    await db.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob');")
    yield db

    # CLEANUP: Close connection
    await db.close()


@pytest_asyncio.fixture(scope="function")
async def pg_client_read_only(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[PostgreSQLDatabase, Any]:
    host = (
        f"{postgres_container.get_container_host_ip()}:{postgres_container.get_exposed_port(5432)}"
    )

    # Create a "Setup" client that IS allowed to write
    setup_db = PostgreSQLDatabase(
        user=postgres_container.username,
        password=postgres_container.password,
        db=postgres_container.dbname,
        host=host,
        read_only=False,  # Must be False to seed the data for tests
    )

    await asyncio.wait_for(setup_db.connect(max_size=5), timeout=120.0)

    await setup_db.execute("DROP TABLE IF EXISTS users CASCADE;")
    await setup_db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);")
    await setup_db.execute("INSERT INTO users (name) VALUES ('Alice');")

    setup_db.read_only = True

    yield setup_db
    await setup_db.close()


@pytest.fixture
def deps(pg_client: PostgreSQLDatabase) -> SQLDatabaseDeps:
    # Instead of a generic SQLiteDatabase, use a real instance or
    # link the database attribute to your sqlite_client
    return SQLDatabaseDeps(database=pg_client, max_rows=20, query_timeout=10.0)


@pytest.fixture
def context(deps: SQLDatabaseDeps) -> RunContext[SQLDatabaseDeps]:
    # Using the real RunContext is safer than MagicMock for E2E
    return RunContext(model=MODEL, usage=RunUsage(), deps=deps, max_retries=3)


### TESTS ###
def test_toolset_creation() -> None:
    """
    Test that the database toolset is created with the correct number of tools.

    Verifies that the toolset contains exactly 5 tools: list_tables, get_schema,
    describe_table, explain_query, and query.
    """
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
    context: RunContext[SQLDatabaseDeps], pg_client: PostgreSQLDatabase
) -> None:
    """
    Test the list_tables tool functionality.

    Verifies that the tool correctly retrieves all table names from the database
    and returns them in the expected format.
    """
    toolset = create_database_toolset()
    tool = get_tool(toolset, "list_tables")

    # Make the calls manually
    response = await pg_client.get_tables()
    result = await tool.function(context)

    # Assert
    assert isinstance(response, list)
    assert response == result


@pytest.mark.asyncio
async def test_get_schema_object(
    context: RunContext[SQLDatabaseDeps], pg_client: PostgreSQLDatabase
) -> None:
    """
    Test the get_schema tool functionality with object return format.

    Verifies that the tool correctly retrieves the database schema as a SchemaInfo
    object when return_md=False.
    """
    toolset = create_database_toolset()
    tool = get_tool(toolset, "get_schema")

    # Make the calls manually
    response = await pg_client.get_schema(return_md=False)
    result = await tool.function(context, return_md=False)

    # Assert
    assert response == result


@pytest.mark.asyncio
async def test_describe_table(
    context: RunContext[SQLDatabaseDeps], pg_client: PostgreSQLDatabase
) -> None:
    """
    Test the describe_table tool functionality.

    Verifies that the tool correctly retrieves detailed information about a
    specific table, including columns, types, and constraints.
    """
    toolset = create_database_toolset()
    tool = get_tool(toolset, "describe_table")

    # Make the calls manually
    response = await pg_client.get_table_info("users")
    result = await tool.function(context, table_name="users")

    # Assert
    assert response == result


@pytest.mark.asyncio
async def test_explain_query(
    context: RunContext[SQLDatabaseDeps], pg_client: PostgreSQLDatabase
) -> None:
    """
    Test the explain_query tool functionality.

    Verifies that the tool correctly retrieves the execution plan for a SQL query
    without actually executing it.
    """
    toolset = create_database_toolset()
    tool = get_tool(toolset, "explain_query")

    # Make the calls manually
    response = await pg_client.explain("SELECT COUNT(*) FROM users")
    result = await tool.function(context, sql_query="SELECT COUNT(*) FROM users")

    # Assert
    assert response == result


@pytest.mark.asyncio
async def test_run_sql_query(
    context: RunContext[SQLDatabaseDeps], pg_client: PostgreSQLDatabase
) -> None:
    """
    Test the query tool functionality.

    Verifies that the tool correctly executes a SQL query and returns the results
    in the expected format, including columns, rows, and execution metadata.
    """
    toolset = create_database_toolset()
    tool = get_tool(toolset, "query")

    # Make the calls manually
    response = await pg_client.execute("SELECT COUNT(*) FROM users")
    result = await tool.function(context, sql_query="SELECT COUNT(*) FROM users")

    # Assert individually due to execution time being present
    assert response.columns == result.columns
    assert response.rows == result.rows
    assert response.row_count == result.row_count


@pytest.mark.asyncio
async def test_run_sql_query_max_rows(
    context: RunContext[SQLDatabaseDeps], pg_client: PostgreSQLDatabase
) -> None:
    """
    Test the query tool with max_rows parameter.

    Verifies that the tool correctly limits the number of rows returned by a query
    when the max_rows parameter is specified.
    """
    toolset = create_database_toolset()
    tool = get_tool(toolset, "query")

    # Make the calls manually
    response = await pg_client.execute("SELECT * FROM users")
    result = await tool.function(context, sql_query="SELECT * FROM users", max_rows=1)

    # Assert individually due to execution time being present
    assert response.columns == result.columns
    assert response.rows != result.rows
    assert response.row_count != result.row_count
    assert len(result) == 1
    assert len(result) != len(response)


@pytest.mark.asyncio
async def test_query_timeout(
    context: RunContext[SQLDatabaseDeps], pg_client: PostgreSQLDatabase
) -> None:
    """
    Test the query tool with timeout handling.

    Verifies that the tool correctly handles query timeouts by returning an empty
    result when the query exceeds the specified timeout.
    """
    toolset = create_database_toolset()
    tool = get_tool(toolset, "query")

    async def slow_execute(*args, **kwargs):
        await asyncio.sleep(0.5)
        return QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=0)

    # Patch the actual execute method on the client instance
    with patch.object(pg_client, "execute", side_effect=slow_execute):
        context.deps.query_timeout = 0.01  # Set timeout much lower than sleep
        result = await tool.function(context, sql_query="SELECT * FROM users;")

    assert isinstance(result, QueryResult)
    assert result.columns == []
    assert result.rows == []
    assert result.row_count == 0
    assert result.execution_time_ms == 0


@pytest.mark.asyncio
async def test_query_read_only_violation(pg_client_read_only: PostgreSQLDatabase) -> None:
    # Setup Deps with read_only=True
    deps = SQLDatabaseDeps(database=pg_client_read_only, read_only=True)
    ctx = RunContext(model=MODEL, usage=RunUsage(), deps=deps)

    toolset = create_database_toolset()
    tool = get_tool(toolset, "query")

    # Try to run a write operation
    # Your tool should catch the PermissionError or the backend should raise it
    with pytest.raises(PermissionError, match="read-only"):
        await tool.function(ctx, sql_query="DELETE FROM users")
