from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio

from src.sql_toolset_pydantic_ai.sqlite import SQLiteClient
from src.sql_toolset_pydantic_ai.types import ColumnInfo, ForeignKeyInfo, SchemaInfo, TableInfo


# Setup fixture for the client
@pytest_asyncio.fixture
async def db_client() -> AsyncGenerator[SQLiteClient, Any]:
    # Using `:memory:` to use fast and RAM
    client = SQLiteClient(":memory:")
    await client.connect()
    yield client
    await client.close()


### TESTS ###
@pytest.mark.asyncio
async def test_client_closure(db_client) -> None:
    await db_client.close()
    assert db_client._connection is None


@pytest.mark.asyncio
async def test_execute_create_table(db_client) -> None:
    # Act
    await db_client.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);")
    res = await db_client.execute("SELECT name FROM sqlite_master WHERE type='table';")

    # Assert
    assert res is not None
    assert len(res.rows) == 1
    assert res.rows[0][0] == "users"


@pytest.mark.asyncio
async def test_relationship_integrity(db_client) -> None:
    # Act
    await db_client.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT)")
    await db_client.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    tables = await db_client.get_tables()
    res = await db_client.get_foreign_keys("orders")

    # Assert
    assert res is not None
    assert len(tables) == 2
    assert len(res) > 0
    assert res == [
        ForeignKeyInfo(column="user_id", references_table="users", references_column="id")
    ]


@pytest.mark.asyncio
async def test_relationship_integrity_empty_table(db_client) -> None:
    # Act
    tables = await db_client.get_tables()
    fk = await db_client.get_foreign_keys("table")

    # Assert
    assert tables is not None
    assert isinstance(tables, list)
    assert tables == []

    assert fk is not None
    assert isinstance(fk, list)
    assert fk == [ForeignKeyInfo("", "", "")]


@pytest.mark.asyncio
async def test_get_table_info(db_client) -> None:
    # Act
    await db_client.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await db_client.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    res_users = await db_client.get_table_info("users")
    res_orders = await db_client.get_table_info("orders")

    # Assert
    assert res_users is not None
    assert res_orders is not None

    assert res_users == TableInfo(
        name="users",
        columns=[
            ColumnInfo("id", "INTEGER", True, None, True),
            ColumnInfo("name", "TEXT", True, None, False),
            ColumnInfo("city", "TEXT", False, None, False),
        ],
        row_count=0,
        primary_key=["id"],
        foreign_keys=[],
    )

    assert res_orders == TableInfo(
        name="orders",
        columns=[
            ColumnInfo("id", "INTEGER", True, None, True),
            ColumnInfo("user_id", "INTEGER", True, None, False),
            ColumnInfo("product", "TEXT", True, None, False),
        ],
        row_count=0,
        primary_key=["id"],
        foreign_keys=[ForeignKeyInfo("user_id", "users", "id")],
    )


@pytest.mark.asyncio
async def test_get_table_info_no_table(db_client) -> None:
    # Act
    res = await db_client.get_table_info("some_table")

    # Assert
    assert res is not None
    assert res == TableInfo("", [ColumnInfo("", "", True, None, False)], None, [])


@pytest.mark.asyncio
async def test_get_tables(db_client) -> None:
    # Act
    await db_client.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await db_client.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    await db_client.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price INTEGER, "
        "FOREIGN KEY (name) REFERENCES orders (product));"
    )
    res = await db_client.get_tables()

    # Assert
    assert res is not None
    assert len(res) > 0
    assert res == ["users", "orders", "products"]


@pytest.mark.asyncio
async def test_get_tables_no_tables(db_client) -> None:
    # Act
    res = await db_client.get_tables()

    # Assert
    assert res is not None
    assert isinstance(res, list)
    assert len(res) == 0


@pytest.mark.asyncio
async def test_get_schema(db_client) -> None:
    # Act
    await db_client.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await db_client.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    await db_client.execute(
        "CREATE TABLE products (main_key INTEGER PRIMARY KEY, name BLOB NOT NULL, price REAL, "
        "FOREIGN KEY (name) REFERENCES orders (product));"
    )
    await db_client.execute("INSERT INTO users ('name', 'city') VALUES ('test', 'TestCity')")
    res = await db_client.get_schema()

    # Assert
    assert res is not None
    assert res == SchemaInfo(
        tables=[
            TableInfo(
                "users",
                [
                    ColumnInfo("id", "INTEGER", True, None, True),
                    ColumnInfo("name", "TEXT", True, None, False),
                    ColumnInfo("city", "TEXT", False, None, False),
                ],
                1,
                ["id"],
                [],
            ),
            TableInfo(
                "orders",
                [
                    ColumnInfo("id", "INTEGER", True, None, True),
                    ColumnInfo("user_id", "INTEGER", True, None, False),
                    ColumnInfo("product", "TEXT", True, None, False),
                ],
                0,
                ["id"],
                [ForeignKeyInfo("user_id", "users", "id")],
            ),
            TableInfo(
                "products",
                [
                    ColumnInfo("main_key", "INTEGER", True, None, True),
                    ColumnInfo("name", "BLOB", False, None, False),
                    ColumnInfo("price", "REAL", True, None, False),
                ],
                0,
                ["main_key"],
                [ForeignKeyInfo("name", "orders", "product")],
            ),
        ]
    )


@pytest.mark.asyncio
async def test_get_schema_no_tables(db_client) -> None:
    # Act
    res = await db_client.get_schema()

    # Assert
    assert res is not None
    assert res == SchemaInfo([])


@pytest.mark.asyncio
async def test_explain(db_client) -> None:
    # Act
    await db_client.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await db_client.execute("INSERT INTO users ('name', 'city') VALUES ('test', 'TestCity');")

    res = await db_client.explain("SELECT COUNT(*) FROM users;")

    # Assert
    assert res is not None
