# Examples

You can find runnable examples in the [examples/](https://github.com/vstorm-co/sql-toolset-pydantic-ai/tree/main/examples) directory of the repository.

## SQL Examples

These examples demonstrate how to use the toolset with different SQL databases:

- **[SQLite](https://github.com/vstorm-co/sql-toolset-pydantic-ai/tree/main/examples/sql/sqlite)**: A complete example showing how to set up a local SQLite database and connect a Pydantic AI agent to it.
- **[PostgreSQL](https://github.com/vstorm-co/sql-toolset-pydantic-ai/tree/main/examples/sql/postgresql)**: A Docker-based example that sets up a PostgreSQL instance and demonstrates agent integration.

## Running Examples Locally

The project includes a `Makefile` to quickly run the examples:

```bash
# Run SQLite example
make run-example-sqlite

# Run PostgreSQL example (requires Docker)
make run-example-postgres
```
