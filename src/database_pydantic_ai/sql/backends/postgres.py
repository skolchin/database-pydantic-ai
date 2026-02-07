import asyncio
import time
from types import TracebackType
from typing import Any

import asyncpg

from database_pydantic_ai.sql.base import BaseSQLDatabase
from database_pydantic_ai.sql.protocol import SQLDatabaseProtocol
from database_pydantic_ai.types import (
    ColumnInfo,
    ForeignKeyInfo,
    QueryResult,
    SchemaInfo,
    TableInfo,
)


class PostgreSQLDatabase(BaseSQLDatabase, SQLDatabaseProtocol):
    def __init__(
        self, user: str, password: str, db: str, host: str, read_only: bool = True
    ) -> None:
        super().__init__(read_only=read_only)
        self.user = user
        self.password = password
        self.db = db
        self.host = host
        self._pool: asyncpg.Pool | None = None

        self.dsn = f"postgresql://{self.user}:{self.password}@{self.host}/{self.db}"

    async def __aenter__(self) -> "PostgreSQLDatabase":
        """Support for `async with` context manager"""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Ensure the pool is closed when exiting the context."""
        await self.close()

    async def connect(
        self,
        min_size: int = 1,
        max_size: int = 10,
        command_timeout: float = 60.0,
        timeout: float = 120.0,
    ) -> asyncpg.Pool:
        """
        Connect to the database.

        Args:
            min_size: Minimum size of the connection pool.
            max_size: Maximum size of the connection pool.
            command_timeout: Timeout for individual queries in seconds.
            timeout: Timeout for establishing the connection in seconds.
        """
        if not self._pool:
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=min_size,
                max_size=max_size,
                command_timeout=command_timeout,  # Timeout for individual queries
                timeout=timeout,  # Timeout for establishing connection
            )
        return self._pool

    async def close(self) -> None:
        """Close database connection."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def execute(self, query: str, params: tuple[Any, ...] | None = None) -> QueryResult:
        """Execute a SQL query with optional parameters."""
        safe_query = self.check_query_safety(query)

        pool = await self.connect()
        # Check if connection pool was successfully established
        if pool is None:
            raise RuntimeError("Failed to establish database connection")

        start_time = time.perf_counter()

        # Make the query w/ params
        if params:
            args = params if isinstance(params, (list, tuple)) else (params,)

            # Use `fetch` if you want rows back, or `execute` if you just want the status
            records = await pool.fetch(safe_query, *args)
        else:
            records = await pool.fetch(safe_query)

        # Transform data to fit schema
        processed_rows = [tuple(row) for row in records]
        columns = list(records[0].keys()) if records else []

        return QueryResult(
            columns=columns,
            rows=processed_rows,
            row_count=len(processed_rows),
            execution_time_ms=(time.perf_counter() - start_time),
        )

    async def get_tables(self) -> list[str]:
        """Get list of tables in the public schema."""
        pool = await self.connect()
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        result = await pool.fetch(query)
        table_list = [r["table_name"] for r in result]

        return table_list

    async def get_foreign_keys(self, table_name: str) -> list[ForeignKeyInfo]:
        """Get information about foreign keys in given table"""
        pool = await self.connect()
        # Use $1 instead of f-string
        query = """
        SELECT DISTINCT
            kcu.column_name AS local_column,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = $1;
        """

        # Pass table_name as an argument to fetch
        records = await pool.fetch(query, table_name)

        return [
            ForeignKeyInfo(
                column=r["local_column"],
                references_table=r["foreign_table"],
                references_column=r["foreign_column"],
            )
            for r in records
        ]

    async def get_table_info(
        self, table_name: str, return_md: bool = True
    ) -> TableInfo | str | None:
        """Get detailed information about a specific table."""
        tables = await self.get_tables()
        if table_name not in tables:
            return None

        query = """
            SELECT DISTINCT ON (c.ordinal_position)
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN TRUE ELSE FALSE END AS is_primary
            FROM information_schema.columns c
            LEFT JOIN information_schema.key_column_usage kcu
                ON c.table_name = kcu.table_name
                AND c.column_name = kcu.column_name
            LEFT JOIN information_schema.table_constraints tc
                ON kcu.constraint_name = tc.constraint_name
                AND tc.constraint_type = 'PRIMARY KEY'
            WHERE c.table_name = $1
            AND c.table_schema = 'public'
            ORDER BY c.ordinal_position, is_primary DESC;
        """
        pool = await self.connect()
        records = await pool.fetch(query, table_name)

        columns = []
        primary_keys = []
        foreign_keys = []

        for r in records:
            col = ColumnInfo(
                name=r["column_name"],
                data_type=r["data_type"],
                nullable=(r["is_nullable"] == "YES"),
                default=r["column_default"],
                is_primary_key=r["is_primary"],
            )

            if col.is_primary_key:
                primary_keys.append(col.name)
            columns.append(col)

        # Get foreign keys using your existing method
        foreign_keys = await self.get_foreign_keys(table_name)

        # Get real row count
        count_res = await self.execute(f"SELECT COUNT(*) FROM {table_name};")
        actual_row_count = count_res.rows[0][0] if count_res.rows else 0

        table = TableInfo(
            name=table_name,
            columns=columns,
            row_count=actual_row_count,
            foreign_keys=foreign_keys,
            primary_key=primary_keys,
        )

        if return_md:
            table_md = self.render_table_as_markdown(table)
            return table_md

        return table

    async def get_schema(self, return_md: bool = True) -> SchemaInfo | str:
        """Get database schema information."""
        table_names = await self.get_tables()

        tasks = [self.get_table_info(table_name, return_md=return_md) for table_name in table_names]
        tables = await asyncio.gather(*tasks)

        if return_md:
            str_tables = [str(t) for t in tables if t]
            return "\n".join(str_tables)

        # Filter out empty responses in the output
        return SchemaInfo(tables=[t for t in tables if t])

    async def explain(self, query: str) -> str:
        """Get query execution plan."""
        pool = await self.connect()
        query = f"EXPLAIN {query}"

        explanation = ""

        try:
            result = await pool.fetch(query)

            for r in result:
                explanation += f"{r['QUERY PLAN']}"

            return explanation

        except asyncpg.exceptions.PostgresSyntaxError:
            return "Invalid query, please try again"
