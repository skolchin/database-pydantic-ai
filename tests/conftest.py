"""Shared test fixtures and helpers for database-pydantic-ai."""

from collections.abc import Generator
from typing import Any

import pytest
from pydantic_ai import FunctionToolset, Tool
from pydantic_ai.models.test import TestModel
from testcontainers.postgres import PostgresContainer

from database_pydantic_ai.sql.toolset import SQLDatabaseDeps

MODEL = TestModel()


def get_tool(toolset: FunctionToolset[SQLDatabaseDeps], name: str) -> Tool[Any]:
    """Retrieve a specific tool from a toolset by name."""
    tools = toolset.tools if isinstance(toolset.tools, list) else toolset.tools.values()
    return next(t for t in tools if t.name == name)


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, Any, None]:
    """Start a PostgreSQL container once for the entire test session."""
    container = PostgresContainer("postgres:16-alpine")
    container.start()
    yield container
    container.stop()
