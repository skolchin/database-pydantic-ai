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
    async with SQLiteDatabase(":memory:", read_only=False) as client:
        yield client


@pytest_asyncio.fixture
async def sqlite_client_read_only() -> AsyncGenerator[SQLiteDatabase, Any]:
    # Using `:memory:` to use fast and RAM
    async with SQLiteDatabase(":memory:") as client:
        yield client


### TESTS ###
## READ-ONLY ##
@pytest.mark.asyncio
async def test_read_client_without_query(sqlite_client_read_only: SQLiteDatabase) -> None:
    """
    Test that an empty query raises a ValueError.

    Verifies that the database backend properly validates queries and raises
    a ValueError when an empty query is provided.
    """
    # No Query
    with pytest.raises(ValueError) as exc_info:
        await sqlite_client_read_only.execute("")
    assert str(exc_info.value) == "Query is empty or only contains comments."


@pytest.mark.asyncio
async def test_read_client_multiple_queries(sqlite_client_read_only: SQLiteDatabase) -> None:
    """
    Test that multiple SQL statements are rejected for security.

    Verifies that the database backend properly validates queries and raises
    a PermissionError when multiple statements are provided.
    """
    # Multiple queries
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(";;;;;INSERT;;;;;")
    assert str(exc_info.value) == "Multiple statements are not allowed for security reasons."


@pytest.mark.asyncio
async def test_read_client_allows_select(sqlite_client_read_only: SQLiteDatabase) -> None:
    """
    Test that SELECT queries are allowed in read-only mode.

    Verifies that the database backend properly allows SELECT queries when
    read-only mode is enabled.
    """
    await sqlite_client_read_only.execute("SELECT 1")


@pytest.mark.asyncio
async def test_read_client_cte_select_allowed(sqlite_client_read_only: SQLiteDatabase) -> None:
    """
    Test that SELECT queries with CTEs are allowed in read-only mode.

    Verifies that the database backend properly allows SELECT queries with
    Common Table Expressions (CTEs) when read-only mode is enabled.
    """
    await sqlite_client_read_only.execute(
        """
        WITH x AS (
            SELECT 1 AS value
        )
        SELECT value FROM x
        """
    )


@pytest.mark.asyncio
async def test_read_client_with_write_query_basic(sqlite_client_read_only: SQLiteDatabase) -> None:
    """
    Test that basic INSERT queries are rejected in read-only mode.

    Verifies that the database backend properly rejects INSERT queries when
    read-only mode is enabled.
    """
    # Basic INSERT
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_start_comment(
    sqlite_client_read_only: SQLiteDatabase,
) -> None:
    """
    Test that INSERT queries with leading block comments are rejected.

    Verifies that the database backend properly detects and rejects write
    operations even when they are preceded by block comments.
    """
    # Leading block comment
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "/* comments here */ INSERT INTO users (id, name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_start_hyphen(
    sqlite_client_read_only: SQLiteDatabase,
) -> None:
    """
    Test that INSERT queries with leading line comments are rejected.

    Verifies that the database backend properly detects and rejects write
    operations even when they are preceded by line comments.
    """
    # Leading line comment
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "-- comment line\nINSERT INTO users (id, name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_mixed_case(
    sqlite_client_read_only: SQLiteDatabase,
) -> None:
    """
    Test that INSERT queries with mixed case and comments are rejected.

    Verifies that the database backend properly detects and rejects write
    operations regardless of case sensitivity or leading whitespace/comments.
    """
    # Mixed case and leading spaces/comments
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "   -- comment\nInSeRt INTO users (id, name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_start_with(
    sqlite_client_read_only: SQLiteDatabase,
) -> None:
    """
    Test that INSERT queries inside CTEs are rejected in read-only mode.

    Verifies that the database backend properly detects and rejects write
    operations even when they are hidden within Common Table Expressions (CTEs).
    """
    # CTE with forbidden keyword inside
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "WITH x AS (SELECT * FROM users) "
            "INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation detected inside CTE in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_inline_comment(
    sqlite_client_read_only: SQLiteDatabase,
) -> None:
    # Inline comment in the middle of the query
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "INSERT INTO users (id, /* comment */ name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_multiline_cte(
    sqlite_client_read_only: SQLiteDatabase,
) -> None:
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
    assert str(exc_info.value) == "Write operation detected inside CTE in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_whitespace_variants(
    sqlite_client_read_only: SQLiteDatabase,
) -> None:
    # Leading/trailing whitespace and line breaks
    with pytest.raises(PermissionError) as exc_info:
        await sqlite_client_read_only.execute(
            "  \n\tINSERT  INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


## READ & WRITE ##


@pytest.mark.asyncio
async def test_client_closure(sqlite_client: SQLiteDatabase) -> None:
    await sqlite_client.close()
    assert sqlite_client._connection is None


@pytest.mark.asyncio
async def test_execute_create_table(sqlite_client: SQLiteDatabase) -> None:
    # Act
    await sqlite_client.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);")
    res = await sqlite_client.execute("SELECT name FROM sqlite_master WHERE type='table';")

    # Assert
    assert res is not None
    assert len(res.rows) == 1
    assert res.rows[0][0] == "users"


@pytest.mark.asyncio
async def test_relationship_integrity(sqlite_client: SQLiteDatabase) -> None:
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
async def test_relationship_integrity_empty_table(sqlite_client: SQLiteDatabase) -> None:
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
async def test_get_table_info_no_data(sqlite_client: SQLiteDatabase) -> None:
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


@pytest.mark.asyncio
async def test_get_table_info_object(sqlite_client: SQLiteDatabase) -> None:
    # Act
    await sqlite_client.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await sqlite_client.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    res_users = await sqlite_client.get_table_info("users", return_md=False)
    res_orders = await sqlite_client.get_table_info("orders", return_md=False)

    # Assert
    assert res_users is not None
    assert res_orders is not None

    assert res_users == TableInfo(
        name="users",
        columns=[
            ColumnInfo(
                name="id", data_type="INTEGER", nullable=True, default=None, is_primary_key=True
            ),
            ColumnInfo(
                name="name", data_type="TEXT", nullable=True, default=None, is_primary_key=False
            ),
            ColumnInfo(
                name="city", data_type="TEXT", nullable=False, default=None, is_primary_key=False
            ),
        ],
        row_count=0,
        primary_key=["id"],
        foreign_keys=[],
    )

    assert res_orders == TableInfo(
        name="orders",
        columns=[
            ColumnInfo(
                name="id", data_type="INTEGER", nullable=True, default=None, is_primary_key=True
            ),
            ColumnInfo(
                name="user_id",
                data_type="INTEGER",
                nullable=True,
                default=None,
                is_primary_key=False,
            ),
            ColumnInfo(
                name="product", data_type="TEXT", nullable=True, default=None, is_primary_key=False
            ),
        ],
        row_count=0,
        primary_key=["id"],
        foreign_keys=[
            ForeignKeyInfo(column="user_id", references_table="users", references_column="id")
        ],
    )


@pytest.mark.asyncio
async def test_get_table_info_no_table(sqlite_client: SQLiteDatabase) -> None:
    # Act
    res = await sqlite_client.get_table_info("some_table")

    # Assert
    assert res is None


@pytest.mark.asyncio
async def test_get_tables(sqlite_client: SQLiteDatabase) -> None:
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
async def test_get_tables_no_tables(sqlite_client: SQLiteDatabase) -> None:
    # Act
    res = await sqlite_client.get_tables()

    # Assert
    assert res is not None
    assert isinstance(res, list)
    assert len(res) == 0


@pytest.mark.asyncio
async def test_get_schema_string(sqlite_client: SQLiteDatabase) -> None:
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
    assert isinstance(res, str)


@pytest.mark.asyncio
async def test_get_schema_object(sqlite_client: SQLiteDatabase) -> None:
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
    res = await sqlite_client.get_schema(return_md=False)

    # Assert
    assert res is not None
    assert res == SchemaInfo(
        tables=[
            TableInfo(
                name="users",
                columns=[
                    ColumnInfo(
                        name="id",
                        data_type="INTEGER",
                        nullable=True,
                        default=None,
                        is_primary_key=True,
                    ),
                    ColumnInfo(
                        name="name",
                        data_type="TEXT",
                        nullable=True,
                        default=None,
                        is_primary_key=False,
                    ),
                    ColumnInfo(
                        name="city",
                        data_type="TEXT",
                        nullable=False,
                        default=None,
                        is_primary_key=False,
                    ),
                ],
                row_count=1,
                primary_key=["id"],
                foreign_keys=[],
            ),
            TableInfo(
                name="orders",
                columns=[
                    ColumnInfo(
                        name="id",
                        data_type="INTEGER",
                        nullable=True,
                        default=None,
                        is_primary_key=True,
                    ),
                    ColumnInfo(
                        name="user_id",
                        data_type="INTEGER",
                        nullable=True,
                        default=None,
                        is_primary_key=False,
                    ),
                    ColumnInfo(
                        name="product",
                        data_type="TEXT",
                        nullable=True,
                        default=None,
                        is_primary_key=False,
                    ),
                ],
                row_count=0,
                primary_key=["id"],
                foreign_keys=[
                    ForeignKeyInfo(
                        column="user_id", references_table="users", references_column="id"
                    )
                ],
            ),
            TableInfo(
                name="products",
                columns=[
                    ColumnInfo(
                        name="main_key",
                        data_type="INTEGER",
                        nullable=True,
                        default=None,
                        is_primary_key=True,
                    ),
                    ColumnInfo(
                        name="name",
                        data_type="BLOB",
                        nullable=False,
                        default=None,
                        is_primary_key=False,
                    ),
                    ColumnInfo(
                        name="price",
                        data_type="REAL",
                        nullable=True,
                        default=None,
                        is_primary_key=False,
                    ),
                ],
                row_count=0,
                primary_key=["main_key"],
                foreign_keys=[
                    ForeignKeyInfo(
                        column="name", references_table="orders", references_column="product"
                    )
                ],
            ),
        ]
    )


@pytest.mark.asyncio
async def test_get_schema_no_tables_object(sqlite_client: SQLiteDatabase) -> None:
    # Act
    res = await sqlite_client.get_schema(return_md=False)

    # Assert
    assert res is not None
    assert res == SchemaInfo(tables=[])


@pytest.mark.asyncio
async def test_explain(sqlite_client: SQLiteDatabase) -> None:
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
async def test_explain_random(sqlite_client: SQLiteDatabase) -> None:
    # Act
    res = await sqlite_client.explain("random_query")

    # Assert
    assert res is not None
    assert len(res) > 0
    assert isinstance(res, str)
