"""
Database toolset for PydanticAI agents.

Provides comprehensive support for both SQL and non-SQL databases.
Works with any PydanticAI agent - no specific dependencies nor requirements.

Example:
<example_here>
"""
# TODO - update example

from importlib.metadata import version

from sql_toolset_pydantic_ai.sql.protocol import SQLDatabaseProtocol
from sql_toolset_pydantic_ai.sql.toolset import SQL_SYSTEM_PROMPT, create_database_toolset
from sql_toolset_pydantic_ai.types import (
    ColumnInfo,
    ForeignKeyInfo,
    QueryResult,
    SchemaInfo,
    TableInfo,
)

__all__ = [
    # Main factory
    "create_database_toolset",
    # Protocol
    "SQLDatabaseProtocol",
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
