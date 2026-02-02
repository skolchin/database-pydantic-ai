"""
SQL database toolset for PydanticAI agents.

Provides database backends and toolsets for working with SQL databases.
"""

from sql_toolset_pydantic_ai.sql.backends.postgres import PostgreSQLDatabase
from sql_toolset_pydantic_ai.sql.backends.sqlite import SQLiteDatabase
from sql_toolset_pydantic_ai.sql.protocol import SQLDatabaseProtocol
from sql_toolset_pydantic_ai.sql.toolset import (
    SQL_SYSTEM_PROMPT,
    SQLDatabaseDeps,
    create_database_toolset,
)

__all__ = [
    # Database backends
    "PostgreSQLDatabase",
    "SQLiteDatabase",
    # Protocol
    "SQLDatabaseProtocol",
    # Toolset
    "create_database_toolset",
    "SQLDatabaseDeps",
    "SQL_SYSTEM_PROMPT",
]
