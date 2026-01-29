# SQLite Example

This directory contains a complete example of using the `sql-toolset-pydantic-ai` with an SQLite database.

## Prerequisites

- Python 3.10+

## Setup

1. **Install dependencies:**
   ```bash
   uv add sql-toolset-pydantic-ai
   ```

2. **Configure environment variables:**
   Copy the `.env.example` from the root directory to this directory (or the root directory of your project) and add your OpenAI API key:
   ```bash
   cp ../../../.env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Populate the database with sample data:**
   ```bash
   python setup_db.py
   ```

## Running the Example

Run the usage example to see the library in action, both directly and through a Pydantic AI agent:

```bash
python usage_example.py
```

## Files

- `setup_db.py`: Script to create tables and insert sample data into `example.db`.
- `usage_example.py`: Demonstrates backend usage and integration with Pydantic AI.
