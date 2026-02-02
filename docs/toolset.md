# Toolset & Dependencies

The core of the library is the `create_database_toolset` function, which provides AI agents with a suite of tools for database interaction.

## Dependencies: `SQLDatabaseDeps`

To use the toolset, you must provide an instance of `SQLDatabaseDeps` to your agent's run method. This class controls how the agent interacts with the database.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `database` | `SQLDatabaseProtocol` | **Required** | The backend instance (SQLite or Postgres). |
| `read_only` | `bool` | `True` | If True, blocks destructive queries at the tool level. |
| `max_rows` | `int` | `100` | Maximum number of rows returned by the `query` tool. |
| `query_timeout` | `float` | `30.0` | Timeout in seconds for database queries. |

```python
from sql_toolset_pydantic_ai.sql.toolset import SQLDatabaseDeps

deps = SQLDatabaseDeps(
    database=db,
    read_only=True,
    max_rows=50,
    query_timeout=15.0
)
```

## Resource Management

The database backends support two patterns for managing connections:

### Manual Cleanup

```python
from sql_toolset_pydantic_ai.sql.backends.sqlite import SQLiteDatabase

db = SQLiteDatabase(":memory:", read_only=False)
try:
    # Use the database
    result = await agent.run(user_prompt="...", deps=deps)
finally:
    await db.close()
```

### Async Context Manager (Recommended)

```python
from sql_toolset_pydantic_ai.sql.backends.sqlite import SQLiteDatabase

async with SQLiteDatabase(":memory:", read_only=False) as db:
    # Use the database
    result = await agent.run(user_prompt="...", deps=deps)
# Connection is automatically closed
```

The async context manager pattern is recommended as it ensures proper cleanup even if exceptions occur. See the [examples](../examples.md) directory for complete working examples.

## System Prompts

The library provides pre-configured system prompts to help guide the AI agent in using the SQL tools effectively.

### `SQLITE_SYSTEM_PROMPT`

This prompt includes instructions for the agent on how to:

- Respect read-only mode.
- Use the available tools in the correct order (e.g., list tables -> get schema -> query).
- Apply best practices like using `LIMIT` and validating queries against the schema.

It is highly recommended to use this prompt when initializing your agent:

```python
from sql_toolset_pydantic_ai.sql.toolset import SQLITE_SYSTEM_PROMPT

agent = Agent(
    ...,
    system_prompt=SQLITE_SYSTEM_PROMPT
)
```

## Available Tools

When you call `create_database_toolset()`, the following tools are made available to the agent:

### `list_tables`

Returns a list of all table names in the database.

### `get_schema`

Returns a `SchemaInfo` object containing an overview of all tables, including column counts and approximate row counts.

### `describe_table`

Takes a `table_name` and returns detailed `TableInfo`, including:

- Column names and types
- Nullability and default values
- Primary keys
- Foreign key relationships

### `explain_query`

Takes a `sql_query` and returns the database's execution plan. Useful for the agent to verify it understands the query performance before execution.

### `query`

Executes a SQL query and returns a `QueryResult`. It respects the `max_rows` and `query_timeout` defined in `SQLDatabaseDeps`.
