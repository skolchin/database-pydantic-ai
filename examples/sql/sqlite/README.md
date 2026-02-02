# SQLite Example

This directory contains a complete example of using the `sql-toolset-pydantic-ai` with an SQLite database.

## Prerequisites

- Python 3.10+

## Setup

1. **Install dependencies:**

   ```bash
   uv add sql-toolset-pydantic-ai
   ```

2. **Configure environment variables:**
   Copy the `.env.example` from the root directory to this directory (or the root directory of your project) and add your OpenAI API key:

   ```bash
   cp ../../../.env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Populate the database with sample data:**

   ```bash
   python setup_db.py
   ```

## Running the Example

Run the usage example to see the library in action, both directly and through a Pydantic AI agent:

```bash
python usage_example.py
```

## Files

- `setup_db.py`: Script to create tables and insert sample data into `example.db`.
- `usage_example.py`: Demonstrates backend usage and integration with Pydantic AI (manual cleanup pattern).
- `usage_example_context_manager.py`: Demonstrates the recommended async context manager pattern for automatic resource cleanup.

## Resource Management Patterns

The example includes two patterns for managing database connections:

### Manual Cleanup (usage_example.py)

```python
db = SQLiteDatabase(":memory:", read_only=False)
try:
    # Use the database
    result = await agent.run(user_prompt="...", deps=deps)
finally:
    await db.close()
```

### Async Context Manager (usage_example_context_manager.py)

```python
async with SQLiteDatabase(":memory:", read_only=False) as db:
    # Use the database
    result = await agent.run(user_prompt="...", deps=deps)
# Connection is automatically closed
```

The async context manager pattern is recommended as it ensures proper cleanup even if exceptions occur.
