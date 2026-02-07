# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-02-02

### Added

- Initial release
- SQLite backend via `aiosqlite` with async context manager support
- PostgreSQL backend via `asyncpg` with connection pooling
- `SQLDatabaseProtocol` — runtime-checkable protocol for custom backends
- `BaseSQLDatabase` — shared security layer with 15 forbidden SQL keywords
- `create_database_toolset()` factory with 5 tools: `list_tables`, `get_schema`, `describe_table`, `explain_query`, `query`
- `SQLDatabaseDeps` — Pydantic-based dependency container with `read_only`, `max_rows`, `query_timeout`
- Read-only mode with comment-aware SQL parsing and CTE handling
- Multi-statement prevention for security
- Query timeout protection via `asyncio.wait_for()`
- Row limit enforcement to prevent memory exhaustion
- Markdown rendering for schema output (`return_md` parameter)
- Pydantic v2 models: `QueryResult`, `TableInfo`, `ColumnInfo`, `ForeignKeyInfo`, `SchemaInfo`
- Full documentation with MkDocs Material
- 100% test coverage with SQLite (in-memory) and PostgreSQL (testcontainers)
- Examples for both SQLite and PostgreSQL with manual and context manager patterns
