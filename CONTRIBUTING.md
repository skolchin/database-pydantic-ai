# Contributing to sql-toolset-pydantic-ai

Thanks for your interest in contributing to the SQL Toolset for Pydantic AI!

## Development Setup

```bash
git clone https://github.com/vstorm-co/sql-toolset-pydantic-ai.git
cd sql-toolset-pydantic-ai
make install
```

## Running Tests

```bash
make test        # Run tests with coverage
make all         # Run format + lint + typecheck + test
```

## Requirements

All PRs must meet these requirements:

- **100% test coverage** — no exceptions
- **Pass Pyright** — `make typecheck`
- **Pass MyPy** — `make typecheck-mypy`
- **Pass Ruff** — `make lint`

## Quick Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies and setup pre-commit hooks |
| `make sync` | Sync dependencies using `uv` |
| `make test` | Run tests with coverage reporting |
| `make test-fast` | Run tests without coverage |
| `make lint` | Run Ruff linter |
| `make format` | Format code using Ruff |
| `make typecheck` | Run Pyright |
| `make typecheck-mypy` | Run MyPy |
| `make all` | Run format, lint, typecheck, and test |
| `make run-example-sqlite` | Run the SQLite example |
| `make run-example-postgres` | Run the PostgreSQL example |

## Running Specific Tests

```bash
# Single test
uv run pytest tests/test_sqlite.py::test_list_tables -v

# Single file
uv run pytest tests/test_sqlite.py -v

# With debug output
uv run pytest tests/test_sqlite.py -v -s
```

## Code Style

- We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.
- Run `make format` to auto-format and `make lint` to check.
- We follow strict typing; ensure your code passes both Pyright and MyPy.

## Pull Request Process

1. Fork the repo and create your branch from `main`.
2. Make your changes.
3. Add tests for any new functionality.
4. Ensure `make all` passes (format, lint, typecheck, and 100% coverage).
5. Submit a PR with a clear description of the changes.

## Questions?

Open an issue on [GitHub](https://github.com/vstorm-co/sql-toolset-pydantic-ai/issues).
