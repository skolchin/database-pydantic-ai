# Contributing to database-pydantic-ai

Thanks for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/vstorm-co/database-pydantic-ai.git
cd database-pydantic-ai
make install
```

### Local CI Testing

This project uses [act](https://github.com/nektos/act) to run GitHub Actions locally. This is highly recommended for testing CI changes before pushing.

#### Prerequisites for `act`

1.  **Docker**: Ensure Docker is installed and running.
2.  **Install `act`**:
    *   **macOS**: `brew install act`
    *   **Linux**: `curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash`

#### Configuration & First Run

The project includes a `.actrc` configuration file that sets up the environment automatically.

> [!NOTE]
> **First Run Warning**: We use the `ghcr.io/catthehacker/ubuntu:full-latest` image to closely match the GitHub Actions environment. This image is **large (~20GB)**. The first time you run `make actions`, the download may take a while.

> [!IMPORTANT]
> **Apple Silicon (M1/M2/M3) Users**: The configuration forces `linux/amd64` architecture (`--container-architecture linux/amd64`) to ensure compatibility with `testcontainers` and Python wheels. Ensure your Docker settings allow for x86_64 emulation (Rosetta for Linux is recommended on Docker Desktop).

#### Running Actions

```bash
# Run all CI checks locally (uses the configuration from .actrc)
make actions
```

## Running Tests

```bash
make test        # Run tests with coverage
make all         # Run format + lint + typecheck + typecheck-mypy + test
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
| `make all` | Run all checks (format, lint, typecheck, typecheck-mypy, test) |
| `make actions` | Run GitHub Actions locally with `act` |
| `make clear` | Clean build artifacts |
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

- We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Run `make format` to auto-format and `make lint` to check
- Follow existing patterns in the codebase and ensure strict typing

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. Make your changes and add tests for new functionality
3. Ensure `make all` passes (100% coverage is required)
4. Submit a PR with a clear description of the changes

## Questions?

Open an issue on [GitHub](https://github.com/vstorm-co/database-pydantic-ai/issues).
