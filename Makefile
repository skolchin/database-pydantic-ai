.DEFAULT_GOAL := all

.PHONY: install install-all-python sync test test-fast testcov test-all-python \
        lint format typecheck typecheck-mypy typecheck-both all docs docs-serve \
        run-example-sqlite run-example-postgres postgres-down actions clear help

# Install dependencies
install:
	uv sync --all-extras --group dev --group lint --group docs
	uv run pre-commit install --install-hooks

# Install all supported Python versions for multi-version testing
install-all-python:
	UV_PROJECT_ENVIRONMENT=.venv310 uv sync --python 3.10 --all-extras --group dev
	UV_PROJECT_ENVIRONMENT=.venv311 uv sync --python 3.11 --all-extras --group dev
	UV_PROJECT_ENVIRONMENT=.venv312 uv sync --python 3.12 --all-extras --group dev
	UV_PROJECT_ENVIRONMENT=.venv313 uv sync --python 3.13 --all-extras --group dev

# Sync dependencies
sync:
	uv sync --all-extras --group dev --group lint --group docs

# Run tests with coverage
test:
	COLUMNS=150 uv run coverage run -m pytest --durations=20
	@uv run coverage report
	@$(MAKE) postgres-down

# Run tests without coverage
test-fast:
	uv run pytest -v
	@$(MAKE) postgres-down

# Generate HTML coverage report
testcov:
	COLUMNS=150 uv run coverage run -m pytest --durations=20
	@uv run coverage html
	@echo "HTML coverage report generated in htmlcov/"
	@$(MAKE) postgres-down

# Run tests on all Python versions
test-all-python:
	UV_PROJECT_ENVIRONMENT=.venv310 uv run --python 3.10 coverage run -m pytest
	UV_PROJECT_ENVIRONMENT=.venv311 uv run --python 3.11 coverage run -m pytest
	UV_PROJECT_ENVIRONMENT=.venv312 uv run --python 3.12 coverage run -m pytest
	UV_PROJECT_ENVIRONMENT=.venv313 uv run --python 3.13 coverage run -m pytest

# Run linter
lint:
	uv run ruff format --check src tests
	uv run ruff check src tests

# Format code
format:
	uv run ruff format src tests
	uv run ruff check --fix --fix-only src tests

# Type checking
typecheck:
	PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright

typecheck-mypy:
	uv run mypy src tests

typecheck-both: typecheck typecheck-mypy

# Run all checks
all: format lint typecheck typecheck-mypy test

# Documentation
docs:
	uv run mkdocs build

docs-serve:
	uv run mkdocs serve

# Run examples
run-example-sqlite:
	@echo "Setting up SQLite example database..."
	uv run python examples/sql/sqlite/setup_db.py
	@echo "Running SQLite example (manual cleanup pattern)..."
	uv run python examples/sql/sqlite/usage_example.py
	@echo "Running SQLite example (context manager pattern)..."
	uv run python examples/sql/sqlite/usage_example_context_manager.py

run-example-postgres:
	@echo "Ensuring PostgreSQL is running (requires docker-compose)..."
	docker-compose -f examples/sql/postgresql/docker-compose.yaml up -d
	@echo "Waiting for Postgres to be ready..."
	@sleep 3
	@echo "Setting up PostgreSQL example database..."
	uv run python examples/sql/postgresql/setup_db.py
	@echo "Running PostgreSQL example (manual cleanup pattern)..."
	uv run python examples/sql/postgresql/usage_example.py
	@echo "Running PostgreSQL example (context manager pattern)..."
	uv run python examples/sql/postgresql/usage_example_context_manager.py
	@$(MAKE) postgres-down

postgres-down:
	@echo "Stopping PostgreSQL (docker-compose)..."
	-docker-compose -f examples/sql/postgresql/docker-compose.yaml down

actions:
	act push

# Clean build artifacts
clear: postgres-down
	rm -rf build dist *.egg-info
	rm -rf .coverage htmlcov .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

# Show help
help:
	@echo "Available targets:"
	@echo "  install            Install dependencies and pre-commit hooks"
	@echo "  install-all-python Install for Python 3.10-3.13"
	@echo "  sync               Sync dependencies"
	@echo "  test               Run tests with coverage (100% required)"
	@echo "  test-fast          Run tests without coverage"
	@echo "  testcov            Run tests and generate HTML coverage report"
	@echo "  test-all-python    Run tests on all Python versions"
	@echo "  lint               Check linting (ruff format + check)"
	@echo "  format             Format code (ruff format + fix)"
	@echo "  typecheck          Run Pyright type checker"
	@echo "  typecheck-mypy     Run MyPy type checker"
	@echo "  typecheck-both     Run both Pyright and MyPy"
	@echo "  all                Run format, lint, typecheck, and test"
	@echo "  docs               Build documentation"
	@echo "  docs-serve         Serve documentation locally"
	@echo "  run-example-sqlite Run SQLite examples"
	@echo "  run-example-postgres Run PostgreSQL examples"
	@echo "  actions            Run GitHub Actions locally with act"
	@echo "  clear              Clean build artifacts and caches"
	@echo "  help               Show this help message"
