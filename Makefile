.PHONY: install sync test lint format typecheck all clean postgres-down

# Install dependencies
install:
	uv sync --all-extras
	uv run pre-commit install

# Sync dependencies
sync:
	uv sync --all-extras

# Run tests with coverage
test:
	uv run coverage run -m pytest -v
	uv run coverage report
	@$(MAKE) postgres-down

# Run tests without coverage
test-fast:
	uv run pytest -v
	@$(MAKE) postgres-down

# Run linter
lint:
	uv run ruff check src tests

# Format code
format:
	uv run ruff format src tests
	uv run ruff check --fix src tests
	uv run ruff check src tests --select I --fix

# Type checking
typecheck:
	uv run pyright

typecheck-mypy:
	uv run mypy src tests

# Run all checks
all: format lint typecheck typecheck-mypy typecheck test

# Run examples
run-example-sqlite:
	@echo "Setting up SQLite example database..."
	uv run python examples/sql/sqlite/setup_db.py
	@echo "Running SQLite example..."
	uv run python examples/sql/sqlite/usage_example.py

run-example-postgres:
	@echo "Ensuring PostgreSQL is running (requires docker-compose)..."
	docker-compose -f examples/sql/postgresql/docker-compose.yaml up -d
	@echo "Waiting for Postgres to be ready..."
	@sleep 3
	@echo "Setting up PostgreSQL example database..."
	uv run python examples/sql/postgresql/setup_db.py
	@echo "Running PostgreSQL example..."
	uv run python examples/sql/postgresql/usage_example.py
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
