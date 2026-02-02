import asyncio

from dotenv import load_dotenv
from loguru import logger
from pydantic_ai import Agent

from sql_toolset_pydantic_ai.sql.backends.postgres import PostgreSQLDatabase
from sql_toolset_pydantic_ai.sql.toolset import (
    SQLITE_SYSTEM_PROMPT,
    SQLDatabaseDeps,
    create_database_toolset,
)

load_dotenv()

# Configuration - adjust to match your environment if necessary
PG_CONFIG = {"user": "user", "password": "password", "db": "test_db", "host": "localhost:5432"}


async def run_sql_agent_example():
    """
    Demonstrate how to empower a Pydantic AI agent with PostgreSQL capabilities
    using the sql-toolset-pydantic-ai package.
    """
    logger.info("--- Pydantic AI SQL Toolset Example (PostgreSQL) ---")

    # 1. Initialize the database backend
    # This backend manages the connection pool to your PostgreSQL instance
    db = PostgreSQLDatabase(**PG_CONFIG)

    # 2. Setup dependencies
    # Configures the agent's interaction with the database
    deps = SQLDatabaseDeps(database=db, read_only=True, max_rows=100, query_timeout=10.0)

    # 3. Create the toolset
    # Provides the agent with standardized tools for schema exploration and querying
    toolset = create_database_toolset()

    # 4. Define the agent
    agent = Agent(
        "openai:gpt-4o",  # or your preferred model
        deps_type=SQLDatabaseDeps,
        toolsets=[toolset],
        system_prompt=SQLITE_SYSTEM_PROMPT,
    )

    try:
        # 5. Run the agent
        # The agent will automatically use tools to understand the Postgres schema
        logger.info("\nQuestion: 'How many orders does each user have? Show me the top 3 users.'")
        result = await agent.run(
            user_prompt="How many orders does each user have? Show me the top 3 by order count.",
            deps=deps,
        )

        logger.info("\nAgent's Reasoning and Answer:")
        logger.info(result.output)

    except Exception as e:
        logger.exception(f"\nError occurred: {e}")
        logger.warning(
            "\nTip: Make sure your PostgreSQL container is running: 'docker-compose up -d'"
        )
        logger.warning("And the database is populated: 'python setup_db.py'")
    finally:
        # Ensure the connection pool is closed
        await db.close()


if __name__ == "__main__":
    # Run agent with manual cleanup
    asyncio.run(run_sql_agent_example())
