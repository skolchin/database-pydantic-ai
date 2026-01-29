# Installation

We recommend using `uv` to manage your project's dependencies.

## Using uv

```bash
uv add sql-toolset-pydantic-ai
```

## Database Drivers

The library includes support for SQLite and PostgreSQL. The necessary drivers are installed as dependencies:

- **SQLite**: uses `aiosqlite`
- **PostgreSQL**: uses `asyncpg`

If you are using PostgreSQL, you might also need `psycopg2-binary` for setup scripts or certain advanced features, though the core library uses the asynchronous `asyncpg` driver.
