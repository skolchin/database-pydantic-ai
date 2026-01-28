from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio

from sql_toolset_pydantic_ai.sql.backends.sqlite import SQLiteDatabase
from sql_toolset_pydantic_ai.types import ColumnInfo, ForeignKeyInfo, SchemaInfo, TableInfo


# Setup fixture for the client
@pytest_asyncio.fixture
async def sqlite_client() -> AsyncGenerator[SQLiteDatabase, Any]:
    # Using `:memory:` to use fast and RAM
    client = SQLiteDatabase(":memory:", read_only=False)
    await client.connect()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def sqlite_client_read_only() -> AsyncGenerator[SQLiteDatabase, Any]:
    # Using `:memory:` to use fast and RAM
    client = SQLiteDatabase(":memory:")
    await client.connect()
    yield client
    await client.close()


### TESTS ###
## READ-ONLY ##


@pytest.mark.asyncio
async def test_read_client_with_write_query_basic(sqlite_client_read_only) -> None:
    # Basic INSERT
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Database is in read-only mode"


@pytest.mark.asyncio
async def test_read_client_with_write_query_start_comment(sqlite_client_read_only) -> None:
    # Leading block comment
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "/* comments here */ INSERT INTO users (id, name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Database is in read-only mode"


@pytest.mark.asyncio
async def test_read_client_with_write_query_start_hyphen(sqlite_client_read_only) -> None:
    # Leading line comment
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "-- comment line\nINSERT INTO users (id, name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Database is in read-only mode"


@pytest.mark.asyncio
async def test_read_client_with_write_query_mixed_case(sqlite_client_read_only) -> None:
    # Mixed case and leading spaces/comments
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "   -- comment\nInSeRt INTO users (id, name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Database is in read-only mode"


@pytest.mark.asyncio
async def test_read_client_with_write_query_start_with(sqlite_client_read_only) -> None:
    # CTE with forbidden keyword inside
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "WITH x AS (SELECT * FROM users) "
            "INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Database is in read-only mode"


@pytest.mark.asyncio
async def test_read_client_with_write_query_inline_comment(sqlite_client_read_only) -> None:
    # Inline comment in the middle of the query
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "INSERT INTO users (id, /* comment */ name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Database is in read-only mode"


@pytest.mark.asyncio
async def test_read_client_with_write_query_multiline_cte(sqlite_client_read_only) -> None:
    # Multi-line CTE with INSERT after
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            """
            WITH cte AS (
                SELECT id, name FROM users
            )
            INSERT INTO users (id, name, email)
            VALUES (1, 'Alice', 'alice@example.com');
            """
        )
    assert str(exc_info.value) == "Database is in read-only mode"


@pytest.mark.asyncio
async def test_read_client_with_write_query_whitespace_variants(sqlite_client_read_only) -> None:
    # Leading/trailing whitespace and line breaks
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "  \n\tINSERT  INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Database is in read-only mode"


## READ & WRITE ##


@pytest.mark.asyncio
async def test_client_closure(sqlite_client) -> None:
    await sqlite_client.close()
    assert sqlite_client._connection is None


@pytest.mark.asyncio
async def test_execute_create_table(sqlite_client) -> None:
    # Act
    await sqlite_client.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);")
    res = await sqlite_client.execute("SELECT name FROM sqlite_master WHERE type='table';")

    # Assert
    assert res is not None
    assert len(res.rows) == 1
    assert res.rows[0][0] == "users"


@pytest.mark.asyncio
async def test_relationship_integrity(sqlite_client) -> None:
    # Act
    await sqlite_client.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT)")
    await sqlite_client.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    tables = await sqlite_client.get_tables()
    res = await sqlite_client.get_foreign_keys("orders")

    # Assert
    assert res is not None
    assert len(tables) == 2
    assert len(res) > 0
    assert res == [
        ForeignKeyInfo(column="user_id", references_table="users", references_column="id")
    ]


@pytest.mark.asyncio
async def test_relationship_integrity_empty_table(sqlite_client) -> None:
    # Act
    tables = await sqlite_client.get_tables()
    fk = await sqlite_client.get_foreign_keys("table")

    # Assert
    assert tables is not None
    assert isinstance(tables, list)
    assert tables == []

    assert fk is not None
    assert isinstance(fk, list)
    assert fk == []


@pytest.mark.asyncio
async def test_get_table_info(sqlite_client) -> None:
    # Act
    await sqlite_client.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await sqlite_client.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    res_users = await sqlite_client.get_table_info("users")
    res_orders = await sqlite_client.get_table_info("orders")

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
async def test_get_table_info_no_table(sqlite_client) -> None:
    # Act
    res = await sqlite_client.get_table_info("some_table")

    # Assert
    assert res is None


@pytest.mark.asyncio
async def test_get_tables(sqlite_client) -> None:
    # Act
    await sqlite_client.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await sqlite_client.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    await sqlite_client.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price INTEGER, "
        "FOREIGN KEY (name) REFERENCES orders (product));"
    )
    res = await sqlite_client.get_tables()

    # Assert
    assert res is not None
    assert len(res) > 0
    assert res == ["users", "orders", "products"]


@pytest.mark.asyncio
async def test_get_tables_no_tables(sqlite_client) -> None:
    # Act
    res = await sqlite_client.get_tables()

    # Assert
    assert res is not None
    assert isinstance(res, list)
    assert len(res) == 0


@pytest.mark.asyncio
async def test_get_schema(sqlite_client) -> None:
    # Act
    await sqlite_client.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await sqlite_client.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    await sqlite_client.execute(
        "CREATE TABLE products (main_key INTEGER PRIMARY KEY, name BLOB NOT NULL, price REAL, "
        "FOREIGN KEY (name) REFERENCES orders (product));"
    )
    await sqlite_client.execute("INSERT INTO users ('name', 'city') VALUES ('test', 'TestCity')")
    res = await sqlite_client.get_schema()

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
async def test_get_schema_no_tables(sqlite_client) -> None:
    # Act
    res = await sqlite_client.get_schema()

    # Assert
    assert res is not None
    assert res == SchemaInfo([])


@pytest.mark.asyncio
async def test_explain(sqlite_client) -> None:
    # Act
    await sqlite_client.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await sqlite_client.execute("INSERT INTO users ('name', 'city') VALUES ('test', 'TestCity');")

    res = await sqlite_client.explain("SELECT COUNT(*) FROM users;")

    # Assert
    assert res is not None
    assert len(res) > 0
    assert isinstance(res, str)


@pytest.mark.asyncio
async def test_explain_random(sqlite_client) -> None:
    # Act
    res = await sqlite_client.explain("random_query")

    # Assert
    assert res is not None
    assert len(res) > 0
    assert isinstance(res, str)
