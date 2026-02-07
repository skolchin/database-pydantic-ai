# Examples

You can find runnable examples in the [examples/](https://github.com/vstorm-co/database-pydantic-ai/tree/main/examples) directory of the repository.

## SQL Examples

These examples demonstrate how to use the toolset with different SQL databases:

- **[SQLite](https://github.com/vstorm-co/database-pydantic-ai/tree/main/examples/sql/sqlite)**: A complete example showing how to set up a local SQLite database and connect a Pydantic AI agent to it. Includes both manual cleanup and async context manager patterns.
- **[PostgreSQL](https://github.com/vstorm-co/database-pydantic-ai/tree/main/examples/sql/postgresql)**: A Docker-based example that sets up a PostgreSQL instance and demonstrates agent integration. Includes both manual cleanup and async context manager patterns.

## Running Examples Locally

The project includes a `Makefile` to quickly run the examples:

```bash
# Run SQLite example
make run-example-sqlite

# Run PostgreSQL example (requires Docker)
make run-example-postgres
```

## Resource Management

The library supports two patterns for managing database connections:

### Manual Cleanup

```python
db = SQLiteDatabase(":memory:", read_only=False)
try:
    # Use the database
    result = await agent.run(user_prompt="...", deps=deps)
finally:
    await db.close()
```

### Async Context Manager (Recommended)

```python
async with SQLiteDatabase(":memory:", read_only=False) as db:
    # Use the database
    result = await agent.run(user_prompt="...", deps=deps)
# Connection is automatically closed
```

The async context manager pattern is recommended as it ensures proper cleanup even if exceptions occur.
