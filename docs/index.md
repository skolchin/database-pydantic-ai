# SQL Toolset for Pydantic AI

A powerful PydanticAI toolset designed to empower AI agents with SQL database capabilities. It provides a standardized set of tools for agents to explore schemas, query data, and understand database structures with built-in security and performance controls.

## Key Features

- **Multi-Backend Support**: Out-of-the-box support for **SQLite** (via `aiosqlite`) and **PostgreSQL** (via `asyncpg`).
- **Standardized Toolset**: Consistent interface for AI agents using **Pydantic models** for all data structures.
- **Security-First**: Built-in `read_only` mode to protect your data from accidental modifications.
- **Resource Management**: Configurable query timeouts and maximum row limits to prevent runaway queries.
- **Deep Exploration**: Tools for listing tables, fetching schemas, describing table structures, and explaining query plans.
- **PydanticAI Native**: Seamless integration with PydanticAI's `Agent` and `FunctionToolset` patterns.

## Quickstart

Connect a PydanticAI agent to a SQLite database in just a few lines of code:

> [!WARNING]
> This example assumes you have an existing database file. If you don't, you can create a sample one by running the setup script in `examples/sql/sqlite/setup_db.py`.

```python
import asyncio
from pydantic_ai import Agent
from sql_toolset_pydantic_ai.sql.backends.sqlite import SQLiteDatabase
from sql_toolset_pydantic_ai.sql.toolset import create_database_toolset, SQLDatabaseDeps, SQLITE_SYSTEM_PROMPT

async def main():
    # 1. Initialize the database backend & Setup dependencies
    # Using async context manager ensures the database connection is properly closed
    async with SQLiteDatabase("data.db") as db:
        deps = SQLDatabaseDeps(database=db, read_only=True)

        # 2. Create the toolset
        toolset = create_database_toolset()

        # 3. Initialize the Agent
        agent = Agent(
            "openai:gpt-4o",
            deps_type=SQLDatabaseDeps,
            toolsets=[toolset],
            system_prompt=SQLITE_SYSTEM_PROMPT
        )

        # 4. Run the agent
        result = await agent.run(
            "What are the top 5 most expensive products in our database?",
            deps=deps
        )
        print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- [Installation](installation.md)
- [Database Backends](backends.md)
- [Explore Examples](examples.md)
