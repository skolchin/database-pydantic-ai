import sqlite3
import time
from typing import Any

import aiosqlite

from .types import ColumnInfo, ForeignKeyInfo, QueryResult, SchemaInfo, TableInfo


class SQLiteClient:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self):
        if not self._connection:
            self._connection = await aiosqlite.connect(self.db_path)

            # Return rows as a dict-like object for easier processing
            self._connection.row_factory = sqlite3.Row

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def execute(self, query: str, params: tuple[Any, ...] | None = None) -> QueryResult:
        await self.connect()
        start_time = time.perf_counter()

        # While using `aiosqlite`, executed call has to be awaited
        async with self._connection.execute(query, params or ()) as cursor:
            rows = await cursor.fetchall()

            # Convert `sqlite3.Row` object to tuples for the protocol
            processed_rows = [tuple(row) for row in rows]
            columns = (
                [description[0] for description in cursor.description] if cursor.description else []
            )

            return QueryResult(
                columns=columns,
                rows=processed_rows,
                row_count=len(processed_rows),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    async def get_tables(self) -> list[str]:
        # Fetch all table names from the database
        query = "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%';"
        res = await self.execute(query)

        tables = []
        for row in res.rows:
            tables.append(row[0])

        return tables

    async def get_foreign_keys(self, table_name: str) -> list[ForeignKeyInfo]:
        tables = await self.get_tables()
        if table_name not in tables:
            return [ForeignKeyInfo("", "", "")]

        foreign_keys = []
        query = f"PRAGMA foreign_key_list ({table_name});"
        res = await self.execute(query)

        for row in res.rows:
            foreign_keys.append(
                ForeignKeyInfo(column=row[3], references_table=row[2], references_column=row[4])
            )

        return foreign_keys

    async def get_table_info(self, table_name: str) -> TableInfo:
        tables = await self.get_tables()
        if table_name not in tables:
            return TableInfo("", [ColumnInfo("", "", True, None, False)], None, [])

        query = f"PRAGMA table_info ({table_name});"
        res = await self.execute(query)

        columns = []
        primary_keys = []
        foreign_keys = []

        for row in res.rows:
            col = ColumnInfo(
                name=row[1],
                data_type=row[2],
                nullable=row[3] == 0,
                default=row[4],
                is_primary_key=row[5] == 1,
            )

            if col.is_primary_key:
                primary_keys.append(col.name)
            columns.append(col)

        # Get foreign keys for the table
        foreign_keys = await self.get_foreign_keys(table_name)

        # Get real row count
        count_res = await self.execute(f"SELECT COUNT(*) FROM {table_name};")
        actual_row_count = count_res.rows[0][0] if count_res.rows else 0

        return TableInfo(
            name=table_name,
            columns=columns,
            row_count=actual_row_count,
            primary_key=primary_keys,
            foreign_keys=foreign_keys,
        )

    async def get_schema(self) -> SchemaInfo:
        table_names = await self.get_tables()
        tables = []
        for table_name in table_names:
            table_info = await self.get_table_info(table_name)
            tables.append(table_info)

        return SchemaInfo(tables=tables)

    async def explain(self, query: str) -> str:
        query = f"EXPLAIN QUERY PLAN {query}"
        res = await self.execute(query)

        explanation_lines = []
        for row in res.rows:
            explanation_lines.append(" | ".join(map(str, row)))

        return "\n".join(explanation_lines)
