# Database Backends

`sql-toolset-pydantic-ai` supports multiple database backends through a unified `SQLDatabaseProtocol`. These backends are designed to be passed into `SQLDatabaseDeps`, providing the actual implementation for the AI tools.

## SQLite

The `SQLiteDatabase` backend uses `aiosqlite` for asynchronous database access. It's the simplest way to get started.

```python
from sql_toolset_pydantic_ai.sql.backends.sqlite import SQLiteDatabase
from sql_toolset_pydantic_ai.sql.toolset import SQLDatabaseDeps

# Initialize the backend
db = SQLiteDatabase("path/to/database.db")

# Pass it to dependencies for the agent
deps = SQLDatabaseDeps(database=db, read_only=True)
```

### Key Features
- **Zero Configuration**: Just point to a `.db` file.
- **Read-Only Mode**: Leverages SQLite URI parameters for strict read-only access at the connection level.
- **Native Exploration**: Uses `sqlite_master` and `PRAGMA` for reliable schema discovery.

---

## PostgreSQL

The `PostgreSQLDatabase` backend uses `asyncpg` for high-performance asynchronous access.

```python
from sql_toolset_pydantic_ai.sql.backends.postgres import PostgreSQLDatabase
from sql_toolset_pydantic_ai.sql.toolset import SQLDatabaseDeps

# Initialize the backend with connection details
db = PostgreSQLDatabase(
    user="myuser",
    password="mypassword",
    db="mydb",
    host="localhost:5432"
)

# Pass it to dependencies for the agent
deps = SQLDatabaseDeps(database=db, read_only=True)
```

### Key Features
- **Connection Pooling**: Built-in support for `asyncpg` pools for efficient resource usage.
- **Standard Exploration**: Uses `information_schema` for robust table and relationship discovery.
- **Enterprise Ready**: Designed for production PostgreSQL environments.

---

## Implementing Custom Backends

You can support any database by implementing the `SQLDatabaseProtocol`. This allows you to use the same toolset with any data source that can be queried via SQL.

```python
from typing import Any
from sql_toolset_pydantic_ai.sql.protocol import SQLDatabaseProtocol
from sql_toolset_pydantic_ai.types import QueryResult, SchemaInfo, TableInfo, ForeignKeyInfo

class MyCustomDB(SQLDatabaseProtocol):
    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def execute(self, query: str, params: tuple[Any, ...] | None = None) -> QueryResult: ...
    async def get_tables(self) -> list[str]: ...
    async def get_foreign_keys(self, table_name: str) -> list[ForeignKeyInfo]: ...
    async def get_table_info(self, table_name: str) -> TableInfo | None: ...
    async def get_schema(self) -> SchemaInfo: ...
    async def explain(self, query: str) -> str: ...
```
