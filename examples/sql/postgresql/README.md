# PostgreSQL Example

This directory contains a complete example of using the `sql-toolset-pydantic-ai` with a PostgreSQL database.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose (for running the PostgreSQL instance)

## Setup

1. **Start the PostgreSQL database:**

   ```bash
   docker-compose up -d
   ```

2. **Install dependencies:**

   ```bash
   uv add sql-toolset-pydantic-ai psycopg2-binary
   ```

3. **Configure environment variables:**
   Copy the `.env.example` from the root directory to this directory (or the root directory of your project) and add your OpenAI API key:

   ```bash
   cp ../../../.env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

4. **Populate the database with sample data:**

   ```bash
   python setup_db.py
   ```

## Running the Example

Run the usage example to see the library in action, both directly and through a Pydantic AI agent:

```bash
python usage_example.py
```

## Files

- `setup_db.py`: Script to create tables and insert sample data into the PostgreSQL database.
- `usage_example.py`: Demonstrates backend usage and integration with Pydantic AI (manual cleanup pattern).
- `usage_example_context_manager.py`: Demonstrates the recommended async context manager pattern for automatic resource cleanup.

## Resource Management Patterns

The example includes two patterns for managing database connections:

### Manual Cleanup (usage_example.py)

```python
db = PostgreSQLDatabase(user="user", password="password", db="test_db", host="localhost:5432")
try:
    # Use the database
    result = await agent.run(user_prompt="...", deps=deps)
finally:
    await db.close()
```

### Async Context Manager (usage_example_context_manager.py)

```python
async with PostgreSQLDatabase(user="user", password="password", db="test_db", host="localhost:5432") as db:
    # Use the database
    result = await agent.run(user_prompt="...", deps=deps)
# Connection is automatically closed
```

The async context manager pattern is recommended as it ensures proper cleanup even if exceptions occur.

## Files

- `docker-compose.yaml`: PostgreSQL container configuration.
- `setup_db.py`: Script to create tables and insert sample data.
- `usage_example.py`: Demonstrates backend usage and integration with Pydantic AI (manual cleanup pattern).
- `usage_example_context_manager.py`: Demonstrates the recommended async context manager pattern for automatic resource cleanup.
