"""
Database toolset for PydanticAI agents.

Provides comprehensive support for both SQL and non-SQL databases.
Works with any PydanticAI agent - no specific dependencies nor requirements.

Example:
<example_here>
"""
# TODO - update example

from importlib.metadata import version

# Backends
from sql_toolset_pydantic_ai.sql.backends.sqlite import SQLiteDatabase

# Toolsets
from sql_toolset_pydantic_ai.sql.toolset import (
    SQL_SYSTEM_PROMPT,
    SQLDatabaseDeps,
    create_database_toolset,
)

# Types
from sql_toolset_pydantic_ai.types import (
    ColumnInfo,
    ForeignKeyInfo,
    QueryResult,
    SchemaInfo,
    TableInfo,
)

__all__ = [
    # SQL Main factory
    "create_database_toolset",
    # SQL Main dependencies
    "SQLDatabaseDeps",
    # SQL Main clients
    "SQLiteDatabase",
    # Types
    "QueryResult",
    "TableInfo",
    "ColumnInfo",
    "ForeignKeyInfo",
    "SchemaInfo",
    # Constants (e.g. prompts)
    "SQL_SYSTEM_PROMPT",
]

__version__ = version("sql-toolset-pydantic-ai")
