import asyncio

from dotenv import load_dotenv
from loguru import logger
from pydantic_ai import Agent

from sql_toolset_pydantic_ai.sql.backends.sqlite import SQLiteDatabase
from sql_toolset_pydantic_ai.sql.toolset import (
    SQLITE_SYSTEM_PROMPT,
    SQLDatabaseDeps,
    create_database_toolset,
)

load_dotenv()


async def run_sql_agent_example_context_manager():
    """
    Demonstrate how to empower a Pydantic AI agent with SQL capabilities
    using the sql-toolset-pydantic-ai package with async context manager.
    This is the recommended pattern for automatic resource cleanup.
    """
    logger.info("--- Pydantic AI SQL Toolset Example (SQLite) with Context Manager ---")

    # 1. Initialize the database backend
    # Using async context manager for automatic cleanup
    async with SQLiteDatabase("./examples/sql/sqlite/example.db", read_only=False) as db:
        # 2. Setup dependencies
        deps = SQLDatabaseDeps(database=db, read_only=True, max_rows=100, query_timeout=10.0)

        # 3. Create the toolset
        toolset = create_database_toolset()

        # 4. Define the agent
        agent = Agent(
            "openai:gpt-4o",  # or your preferred model
            deps_type=SQLDatabaseDeps,
            toolsets=[toolset],
            system_prompt=SQLITE_SYSTEM_PROMPT,
        )

        # 5. Run the agent
        # The agent will use the toolset to explore the schema and answer the query
        logger.info("\nQuestion: 'What is the most expensive order and who placed it?'")
        result = await agent.run(
            user_prompt="What is the most expensive order and who placed it?", deps=deps
        )

        logger.info("\nAgent's Reasoning and Answer:")
        logger.info(result.output)


if __name__ == "__main__":
    # Run the example with context manager (recommended)
    asyncio.run(run_sql_agent_example_context_manager())
