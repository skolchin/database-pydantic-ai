"""
Database toolset for PydanticAI agents.

Provides comprehensive support for both SQL and non-SQL databases.
Works with any PydanticAI agent - no specific dependencies nor requirements.

Example:
    from database_pydantic_ai.sql.backends.sqlite import SQLiteDatabase
    from database_pydantic_ai.sql.toolset import create_database_toolset, SQLDatabaseDeps

    async def main():
        # Create a database connection
        async with SQLiteDatabase(":memory:", read_only=False) as db:
            # Create a database toolset for PydanticAI
            toolset = create_database_toolset(id="my-database")

            # Use the toolset with PydanticAI
            from pydantic_ai import Agent

            agent = Agent(
                model="gpt-4",
                deps_type=SQLDatabaseDeps,
                deps=SQLDatabaseDeps(database=db, read_only=True),
                tools=toolset,
            )

            result = agent.run_sync("List all tables in the database")
            print(result.data)
"""
# Example usage is now documented in the docstring above

from importlib.metadata import version

# Backends
from database_pydantic_ai.sql.backends.postgres import PostgreSQLDatabase
from database_pydantic_ai.sql.backends.sqlite import SQLiteDatabase

# Toolsets
from database_pydantic_ai.sql.toolset import (
    SQLITE_SYSTEM_PROMPT,
    SQLDatabaseDeps,
    create_database_toolset,
)

# Types
from database_pydantic_ai.types import (
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
    "PostgreSQLDatabase",
    # Types
    "QueryResult",
    "TableInfo",
    "ColumnInfo",
    "ForeignKeyInfo",
    "SchemaInfo",
    # Constants (e.g. prompts)
    "SQLITE_SYSTEM_PROMPT",
]

__version__ = version("database-pydantic-ai")
