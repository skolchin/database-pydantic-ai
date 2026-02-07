<h1 align="center">Database Toolset for Pydantic AI</h1>

<p align="center">
  <em>Empower AI Agents with SQL Database Capabilities</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/database-pydantic-ai/"><img src="https://img.shields.io/pypi/v/database-pydantic-ai.svg" alt="PyPI version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/vstorm-co/database-pydantic-ai/actions/workflows/ci.yaml"><img src="https://github.com/vstorm-co/database-pydantic-ai/actions/workflows/ci.yaml/badge.svg" alt="CI"></a>
  <a href="https://coveralls.io/github/vstorm-co/database-pydantic-ai?branch=main"><img src="https://coveralls.io/repos/github/vstorm-co/database-pydantic-ai/badge.svg?branch=main" alt="Coverage Status"></a>
  <a href="https://github.com/pydantic/pydantic-ai"><img src="https://img.shields.io/badge/Powered%20by-Pydantic%20AI-E92063?logo=pydantic&logoColor=white" alt="Pydantic AI"></a>
</p>

<p align="center">
  <b>Multi-Backend</b> — SQLite &amp; PostgreSQL
  &nbsp;&bull;&nbsp;
  <b>Security-First</b> — read-only mode &amp; query validation
  &nbsp;&bull;&nbsp;
  <b>Resource Control</b> — timeouts &amp; row limits
</p>

---

**Database Toolset** provides everything your [Pydantic AI](https://ai.pydantic.dev/) agent needs to explore schemas, query data, and understand database structures — with built-in security and performance controls.

> **Full framework?** Check out [Pydantic Deep Agents](https://github.com/vstorm-co/pydantic-deepagents) — complete agent framework with planning, filesystem, subagents, and skills.

## Use Cases

| What You Want to Build | How This Toolset Helps |
|------------------------|------------------------|
| **Data Analysis Agent** | Query databases, explore schemas, sample data |
| **Business Intelligence Bot** | Read-only access to production databases |
| **Database Documentation** | Auto-discover schemas, tables, relationships |
| **SQL Assistant** | Explain query plans, validate queries |
| **Multi-DB Agent** | Unified interface across SQLite & PostgreSQL |

## Installation

```bash
pip install database-pydantic-ai
```

Or with uv:

```bash
uv add database-pydantic-ai
```

## Quick Start

```python
import asyncio
from pydantic_ai import Agent
from database_pydantic_ai import (
    SQLiteDatabase,
    SQLDatabaseDeps,
    SQLITE_SYSTEM_PROMPT,
    create_database_toolset,
)

async def main():
    async with SQLiteDatabase("data.db") as db:
        deps = SQLDatabaseDeps(database=db, read_only=True)
        toolset = create_database_toolset()

        agent = Agent(
            "openai:gpt-4o",
            deps_type=SQLDatabaseDeps,
            toolsets=[toolset],
            system_prompt=SQLITE_SYSTEM_PROMPT,
        )

        result = await agent.run(
            "What are the top 5 most expensive products?",
            deps=deps,
        )
        print(result.output)

asyncio.run(main())
```

**That's it.** Your agent can now:

- List all tables in the database (`list_tables`)
- Get full schema overview (`get_schema`)
- Describe table structures and relationships (`describe_table`)
- Analyze query execution plans (`explain_query`)
- Execute SQL queries with safety controls (`query`)

## Available Backends

| Backend | Driver | Use Case |
|---------|--------|----------|
| `SQLiteDatabase` | `aiosqlite` | Local files, prototyping, lightweight apps |
| `PostgreSQLDatabase` | `asyncpg` | Production databases, connection pooling |

### SQLite

```python
from database_pydantic_ai import SQLiteDatabase

async with SQLiteDatabase("data.db", read_only=True) as db:
    # Zero configuration, file-based
    tables = await db.get_tables()
```

### PostgreSQL

```python
from database_pydantic_ai import PostgreSQLDatabase

async with PostgreSQLDatabase(
    user="postgres",
    password="secret",
    db="mydb",
    host="localhost:5432",
    read_only=True,
) as db:
    # Connection pooling with asyncpg
    schema = await db.get_schema()
```

## Available Tools

The `create_database_toolset()` provides 5 tools to the agent:

| Tool | Returns | Description |
|------|---------|-------------|
| `list_tables` | `list[str]` | List all available tables |
| `get_schema` | `SchemaInfo \| str` | Full database structure overview |
| `describe_table` | `TableInfo \| str` | Detailed table columns, types, constraints |
| `explain_query` | `str` | Query execution plan without running it |
| `query` | `QueryResult` | Execute SQL with timeout and row limits |

## Configuration

The `SQLDatabaseDeps` class controls the agent's database access:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `database` | `SQLDatabaseProtocol` | **Required** | Backend instance (SQLite or PostgreSQL) |
| `read_only` | `bool` | `True` | Block destructive queries (INSERT, UPDATE, DELETE, ...) |
| `max_rows` | `int` | `100` | Maximum rows returned per query |
| `query_timeout` | `float` | `30.0` | Query timeout in seconds |

## Security

Built-in protection against accidental or malicious data modifications:

- **Read-only mode** — blocks 15 dangerous SQL keywords (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, ...)
- **Multi-statement prevention** — rejects queries with multiple statements
- **Comment-aware parsing** — detects dangerous keywords even behind `--` and `/* */` comments
- **CTE handling** — validates Common Table Expressions for write operations
- **Query timeouts** — prevents runaway queries with `asyncio.wait_for()`
- **Row limits** — caps result sets to prevent memory exhaustion

## Examples

Runnable examples are in the `examples/` directory:

- **SQLite**: [examples/sql/sqlite](examples/sql/sqlite/README.md)
- **PostgreSQL**: [examples/sql/postgresql](examples/sql/postgresql/README.md)

```bash
make run-example-sqlite
make run-example-postgres
```

## Documentation

Full documentation: [vstorm-co.github.io/database-pydantic-ai](https://vstorm-co.github.io/database-pydantic-ai/)

## Related Projects

| Package | Description |
|---------|-------------|
| [Pydantic Deep Agents](https://github.com/vstorm-co/pydantic-deepagents) | Full agent framework (planning, filesystem, subagents, skills) |
| [pydantic-ai-backend](https://github.com/vstorm-co/pydantic-ai-backend) | File storage & sandbox backends |
| [pydantic-ai-todo](https://github.com/vstorm-co/pydantic-ai-todo) | Task planning toolset |
| [subagents-pydantic-ai](https://github.com/vstorm-co/subagents-pydantic-ai) | Multi-agent orchestration |
| [summarization-pydantic-ai](https://github.com/vstorm-co/summarization-pydantic-ai) | Context management |
| [pydantic-ai](https://github.com/pydantic/pydantic-ai) | The foundation — agent framework by Pydantic |

## Contributing

```bash
git clone https://github.com/vstorm-co/database-pydantic-ai.git
cd database-pydantic-ai
make install
make test  # 100% coverage required
make all   # format + lint + typecheck + test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

## License

MIT — see [LICENSE](LICENSE)

<p align="center">
  <sub>Built with ❤️ by <a href="https://github.com/vstorm-co">vstorm-co</a></sub>
</p>
