import asyncio

from dotenv import load_dotenv
from loguru import logger
from pydantic_ai import Agent

from sql_toolset_pydantic_ai.sql.backends.sqlite import SQLiteDatabase
from sql_toolset_pydantic_ai.sql.toolset import (
    SQL_SYSTEM_PROMPT,
    SQLDatabaseDeps,
    create_database_toolset,
)

load_dotenv()

# Path to the example database created by setup_db.py
DB_PATH = "example.db"


async def run_sql_agent_example():
    """
    Demonstrate how to empower a Pydantic AI agent with SQL capabilities
    using the sql-toolset-pydantic-ai package.
    """
    logger.info("--- Pydantic AI SQL Toolset Example (SQLite) ---")

    # 1. Initialize the database backend
    # This backend handles the actual database communication
    db = SQLiteDatabase(DB_PATH)

    # 2. Setup dependencies
    # SQLDatabaseDeps carries the database instance and configuration (read-only, limits, etc.)
    deps = SQLDatabaseDeps(database=db, read_only=True, max_rows=100, query_timeout=10.0)

    # 3. Create the toolset
    # This automatically provides tools like list_tables, get_schema, query, etc.
    toolset = create_database_toolset()

    # 4. Define the agent
    # We pass the toolset and use the provided SQL_SYSTEM_PROMPT to guide the agent
    agent = Agent(
        "openai:gpt-4o",  # or your preferred model
        deps_type=SQLDatabaseDeps,
        toolsets=[toolset],
        system_prompt=SQL_SYSTEM_PROMPT,
    )

    try:
        # 5. Run the agent
        # The agent will use the toolset to explore the schema and answer the query
        logger.info("\nQuestion: 'What is the most expensive order and who placed it?'")
        result = await agent.run(
            user_prompt="What is the most expensive order and who placed it?", deps=deps
        )

        logger.info("\nAgent's Reasoning and Answer:")
        logger.info(result.output)

    except Exception as e:
        logger.exception(f"\nError occurred: {e}")
        logger.warning(
            "\nTip: Make sure you've run 'python setup_db.py' first to create the database."
        )
    finally:
        # Always ensure the database connection is closed
        await db.close()


if __name__ == "__main__":
    asyncio.run(run_sql_agent_example())
