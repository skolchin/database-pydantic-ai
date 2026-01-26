from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic_ai import RunContext

from src.sql_toolset_pydantic_ai.protocol import DatabaseProtocol
from src.sql_toolset_pydantic_ai.toolsets.sqlite import (
    DatabaseDeps,
    create_database_toolset,
)
from src.sql_toolset_pydantic_ai.types import QueryResult


@pytest.fixture
def mock_client() -> AsyncMock:
    client = AsyncMock(spec=DatabaseProtocol)
    return client


@pytest.fixture
def deps(mock_client: AsyncMock) -> DatabaseDeps:
    # Instead of a generic AsyncMock, use a real instance or
    # link the database attribute to your mock_client
    deps = MagicMock(spec=DatabaseDeps)
    deps.database = mock_client  # <--- This is the missing link
    return deps


@pytest.fixture
def context(deps: DatabaseDeps) -> RunContext[DatabaseDeps]:
    # Mocking RunContext since it might be complex to instantiate directly
    # dependent on pydantic-ai version
    ctx = MagicMock(spec=RunContext)
    ctx.deps = deps
    ctx.deps.max_rows = 20
    return ctx


def test_toolset_creation() -> None:
    toolset = create_database_toolset()
    # toolset.tools might be a dict or list depending on version,
    # but error suggested it iterates as strings (keys).
    # If it is a dict, .values() gives the tools.
    tools_list = list(toolset.tools.values()) if isinstance(toolset.tools, dict) else toolset.tools

    assert len(tools_list) == 6
    tool_names = {t.name for t in tools_list}
    assert tool_names == {
        "list_tables",
        "get_schema",
        "describe_table",
        "explain_query",
        "query",
        "sample_query",
    }


@pytest.mark.asyncio
async def test_list_tables(context: RunContext[DatabaseDeps], mock_client: AsyncMock) -> None:
    toolset = create_database_toolset()
    # Access by key if dict, else find in list
    if isinstance(toolset.tools, dict):
        tool = toolset.tools["list_tables"]
    else:
        tool = next(t for t in toolset.tools if t.name == "list_tables")

    mock_client.get_tables.return_value = ["users", "posts"]

    # Tool likely wraps the function in .function attribute
    result = await tool.function(context)

    assert result == ["users", "posts"]
    mock_client.get_tables.assert_called_once()


@pytest.mark.asyncio
async def test_get_schema(context: RunContext[DatabaseDeps], mock_client: AsyncMock) -> None:
    toolset = create_database_toolset()
    if isinstance(toolset.tools, dict):
        tool = toolset.tools["get_schema"]
    else:
        tool = next(t for t in toolset.tools if t.name == "get_schema")

    mock_schema = MagicMock()
    mock_client.get_schema.return_value = mock_schema

    result = await tool.function(context)

    assert result == mock_schema
    mock_client.get_schema.assert_called_once()


@pytest.mark.asyncio
async def test_describe_table(context: RunContext[DatabaseDeps], mock_client: AsyncMock) -> None:
    toolset = create_database_toolset()
    if isinstance(toolset.tools, dict):
        tool = toolset.tools["describe_table"]
    else:
        tool = next(t for t in toolset.tools if t.name == "describe_table")

    mock_table_info = MagicMock()
    mock_client.get_table_info.return_value = mock_table_info

    # Tool.run takes context as first arg, and keyword args for the rest
    result = await tool.function(context, table_name="users")

    assert result == mock_table_info
    mock_client.get_table_info.assert_called_once_with("users")


@pytest.mark.asyncio
async def test_explain_query(context: RunContext[DatabaseDeps], mock_client: AsyncMock) -> None:
    toolset = create_database_toolset()
    if isinstance(toolset.tools, dict):
        tool = toolset.tools["explain_query"]
    else:
        tool = next(t for t in toolset.tools if t.name == "explain_query")

    mock_client.explain.return_value = "QUERY PLAN..."

    result = await tool.function(context, sql_query="SELECT * FROM users")

    assert result == "QUERY PLAN..."
    mock_client.explain.assert_called_once_with("SELECT * FROM users")


@pytest.mark.asyncio
async def test_run_sql_query(context: RunContext[DatabaseDeps], mock_client: AsyncMock) -> None:
    toolset = create_database_toolset()
    if isinstance(toolset.tools, dict):
        tool = toolset.tools["query"]
    else:
        tool = next(t for t in toolset.tools if t.name == "query")

    mock_result = MagicMock()
    mock_client.execute.return_value = mock_result

    result = await tool.function(context, sql_query="SELECT * FROM users;")

    assert result == mock_result
    mock_client.execute.assert_called_once_with("SELECT * FROM users;")


@pytest.mark.asyncio
async def test_run_sample_sql_query(
    context: RunContext[DatabaseDeps], mock_client: AsyncMock
) -> None:
    toolset = create_database_toolset()
    if isinstance(toolset.tools, dict):
        tool = toolset.tools["sample_query"]
    else:
        tool = next(t for t in toolset.tools if t.name == "sample_query")

    mock_result = MagicMock()
    mock_client.execute.return_value = mock_result

    result = await tool.function(context, sql_query="SELECT * FROM users;")

    assert result == mock_result
    mock_client.execute.assert_called_once_with("SELECT * FROM users;")


@pytest.mark.asyncio
async def test_query_truncation(context: RunContext[DatabaseDeps], mock_client: AsyncMock) -> None:
    toolset = create_database_toolset()
    tool = next(t for t in toolset.tools.values() if t.name == "query")

    # Create a mock QueryResult with 10 rows
    mock_result = QueryResult(
        columns=["id", "name"],
        rows=[(i, f"user{i}") for i in range(10)],
        row_count=10,
        execution_time_ms=123.4,
    )

    mock_client.execute.return_value = mock_result

    # Set max_rows to 5 via context deps
    context.deps.max_rows = 5

    result = await tool.function(context, sql_query="SELECT * FROM users;")

    # The returned result should be truncated to 5 rows
    assert len(result.rows) == 5
    assert result.row_count == 5
    assert result.columns == ["id", "name"]
    mock_client.execute.assert_called_once_with("SELECT * FROM users;")


@pytest.mark.asyncio
async def test_query_custom_limit(
    context: RunContext[DatabaseDeps], mock_client: AsyncMock
) -> None:
    toolset = create_database_toolset()
    tool = next(t for t in toolset.tools.values() if t.name == "sample_query")

    mock_result = QueryResult(
        columns=["id"], rows=[(i,) for i in range(10)], row_count=10, execution_time_ms=50.0
    )

    mock_client.execute.return_value = mock_result

    # Override max_rows to 3
    result = await tool.function(context, sql_query="SELECT id FROM users;", limit=3)

    assert len(result.rows) == 3
    assert result.row_count == 3


@pytest.mark.asyncio
async def test_sample_query_truncation(
    context: RunContext[DatabaseDeps], mock_client: AsyncMock
) -> None:
    toolset = create_database_toolset()
    tool = next(t for t in toolset.tools.values() if t.name == "sample_query")

    mock_result = QueryResult(
        columns=["id"], rows=[(i,) for i in range(10)], row_count=10, execution_time_ms=25.0
    )

    mock_client.execute.return_value = mock_result

    # sample_query has a default limit of 5
    result = await tool.function(context, sql_query="SELECT id FROM users;")

    assert len(result.rows) == 5
    assert result.row_count == 5
