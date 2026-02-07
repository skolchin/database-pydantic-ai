# API Reference

This section provides detailed API documentation for the `database-pydantic-ai` package.

## Core Toolset

::: database_pydantic_ai.sql.toolset
    options:
      members:
        - create_database_toolset
        - SQLDatabaseDeps

### Default System Prompt

This is the prompt used to instruct the agent:

```markdown
--8<-- "src/database_pydantic_ai/sql/toolset.py:12:30"
```

## Backends

### SQLite

::: database_pydantic_ai.sql.backends.sqlite.SQLiteDatabase

### PostgreSQL

::: database_pydantic_ai.sql.backends.postgres.PostgreSQLDatabase

### Protocol

::: database_pydantic_ai.sql.protocol.SQLDatabaseProtocol

## Types

::: database_pydantic_ai.types
