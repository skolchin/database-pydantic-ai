# API Reference

This section provides detailed API documentation for the `sql-toolset-pydantic-ai` package.

## Core Toolset

::: sql_toolset_pydantic_ai.sql.toolset
    options:
      members:
        - create_database_toolset
        - SQLDatabaseDeps

### Default System Prompt

This is the prompt used to instruct the agent:

```markdown
--8<-- "src/sql_toolset_pydantic_ai/sql/toolset.py:12:30"
```

## Backends

### SQLite

::: sql_toolset_pydantic_ai.sql.backends.sqlite.SQLiteDatabase

### PostgreSQL

::: sql_toolset_pydantic_ai.sql.backends.postgres.PostgreSQLDatabase

### Protocol

::: sql_toolset_pydantic_ai.sql.protocol.SQLDatabaseProtocol

## Types

::: sql_toolset_pydantic_ai.types
