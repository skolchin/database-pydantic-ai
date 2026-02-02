import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

from sql_toolset_pydantic_ai.sql.backends.postgres import PostgreSQLDatabase
from sql_toolset_pydantic_ai.types import ForeignKeyInfo, SchemaInfo, TableInfo


### FIXTURES ###
# Start the container ONCE for the whole test session
@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, Any, None]:
    container = PostgresContainer("postgres:16-alpine")
    container.start()
    yield container
    container.stop()


# Setup fixture for the client
@pytest_asyncio.fixture(scope="function")
async def pg_db(postgres_container: PostgresContainer) -> AsyncGenerator[PostgreSQLDatabase, Any]:
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)

    db = PostgreSQLDatabase(
        user=postgres_container.username,
        password=postgres_container.password,
        db=postgres_container.dbname,
        host=f"{host}:{port}",
        read_only=False,
    )

    async with db:
        await asyncio.wait_for(db.connect(max_size=5), timeout=120.0)
        await db.execute("DROP TABLE IF EXISTS users, products, orders CASCADE;")
        yield db


@pytest_asyncio.fixture
async def pg_db_read_only(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[PostgreSQLDatabase, Any]:
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)

    db = PostgreSQLDatabase(
        user=postgres_container.username,
        password=postgres_container.password,
        db=postgres_container.dbname,
        host=f"{host}:{port}",
        read_only=False,
    )

    # Create a "Setup" client that IS allowed to write
    async with db:
        await asyncio.wait_for(db.connect(max_size=5), timeout=120.0)
        await db.execute("DROP TABLE IF EXISTS users, products, orders CASCADE;")
        db.read_only = True
        yield db


### TESTS ###
## READ-ONLY ##
@pytest.mark.asyncio
async def test_read_client_without_query(pg_db_read_only: PostgreSQLDatabase) -> None:
    # No Query
    with pytest.raises(ValueError) as exc_info:
        await pg_db_read_only.execute("")
    assert str(exc_info.value) == "Query is empty or only contains comments."


@pytest.mark.asyncio
async def test_read_client_multiple_queries(pg_db_read_only: PostgreSQLDatabase) -> None:
    # Multiple queries
    with pytest.raises(PermissionError) as exc_info:
        await pg_db_read_only.execute(";;;;;INSERT;;;;;")
    assert str(exc_info.value) == "Multiple statements are not allowed for security reasons."


@pytest.mark.asyncio
async def test_read_client_allows_select(pg_db_read_only: PostgreSQLDatabase) -> None:
    await pg_db_read_only.execute("SELECT 1")


@pytest.mark.asyncio
async def test_read_client_cte_select_allowed(pg_db_read_only: PostgreSQLDatabase) -> None:
    await pg_db_read_only.execute(
        """
        WITH x AS (
            SELECT 1 AS value
        )
        SELECT value FROM x
        """
    )


@pytest.mark.asyncio
async def test_read_client_with_write_query_basic(pg_db_read_only: PostgreSQLDatabase) -> None:
    # Basic INSERT
    with pytest.raises(PermissionError) as exc_info:
        await pg_db_read_only.execute(
            "INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_start_comment(
    pg_db_read_only: PostgreSQLDatabase,
) -> None:
    # Leading block comment
    with pytest.raises(PermissionError) as exc_info:
        await pg_db_read_only.execute(
            "/* comments here */ INSERT INTO users (id, name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_start_hyphen(
    pg_db_read_only: PostgreSQLDatabase,
) -> None:
    # Leading line comment
    with pytest.raises(PermissionError) as exc_info:
        await pg_db_read_only.execute(
            "-- comment line\nINSERT INTO users (id, name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_mixed_case(pg_db_read_only: PostgreSQLDatabase) -> None:
    # Mixed case and leading spaces/comments
    with pytest.raises(PermissionError) as exc_info:
        await pg_db_read_only.execute(
            "   -- comment\nInSeRt INTO users (id, name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_start_with(pg_db_read_only: PostgreSQLDatabase) -> None:
    # CTE with forbidden keyword inside
    with pytest.raises(PermissionError) as exc_info:
        await pg_db_read_only.execute(
            "WITH x AS (SELECT * FROM users) "
            "INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation detected inside CTE in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_inline_comment(
    pg_db_read_only: PostgreSQLDatabase,
) -> None:
    # Inline comment in the middle of the query
    with pytest.raises(PermissionError) as exc_info:
        await pg_db_read_only.execute(
            "INSERT INTO users (id, /* comment */ name, email) "
            "VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


@pytest.mark.asyncio
async def test_read_client_with_write_query_multiline_cte(
    pg_db_read_only: PostgreSQLDatabase,
) -> None:
    # Multi-line CTE with INSERT after
    with pytest.raises(PermissionError) as exc_info:
        await pg_db_read_only.execute(
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
    pg_db_read_only: PostgreSQLDatabase,
) -> None:
    # Leading/trailing whitespace and line breaks
    with pytest.raises(PermissionError) as exc_info:
        await pg_db_read_only.execute(
            "  \n\tINSERT  INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com');"
        )
    assert str(exc_info.value) == "Write operation denied. Database is in read-only mode."


## READ & WRITE ##
@pytest.mark.asyncio
async def test_client_closure(pg_db: PostgreSQLDatabase) -> None:
    await pg_db.close()
    assert pg_db._pool is None


@pytest.mark.asyncio
async def test_execute_create_table(pg_db: PostgreSQLDatabase) -> None:
    # Act
    await pg_db.execute("CREATE TABLE users(id SERIAL PRIMARY KEY, name TEXT);")
    res = await pg_db.execute(
        query="""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
    )

    # Assert
    assert res is not None
    assert len(res.rows) == 1
    assert res.rows[0][0] == "users"


@pytest.mark.asyncio
async def test_relationship_integrity(pg_db: PostgreSQLDatabase) -> None:
    # Act
    await pg_db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT, city TEXT)")
    await pg_db.execute(
        "CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    tables = await pg_db.get_tables()
    res = await pg_db.get_foreign_keys("orders")

    # Assert
    assert res is not None
    assert len(tables) == 2
    assert len(res) > 0
    assert res == [
        ForeignKeyInfo(column="user_id", references_table="users", references_column="id")
    ]


@pytest.mark.asyncio
async def test_relationship_integrity_empty_table(pg_db: PostgreSQLDatabase) -> None:
    # Act
    tables = await pg_db.get_tables()
    fk = await pg_db.get_foreign_keys("table")

    # Assert
    assert tables is not None
    assert isinstance(tables, list)
    assert tables == []

    assert fk is not None
    assert isinstance(fk, list)
    assert fk == []


@pytest.mark.asyncio
async def test_get_table_info_object(pg_db: PostgreSQLDatabase) -> None:
    # Act
    await pg_db.execute(
        "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await pg_db.execute(
        "CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INTEGER,"
        "product TEXT, FOREIGN KEY (user_id) REFERENCES users (id));"
    )
    res_users = await pg_db.get_table_info("users", return_md=False)
    res_orders = await pg_db.get_table_info("orders", return_md=False)

    # Assert
    assert res_users is not None
    assert res_orders is not None

    assert isinstance(res_orders, TableInfo)
    assert isinstance(res_users, TableInfo)

    # Users
    assert res_users.name == "users"
    assert res_users.columns[0].is_primary_key
    assert res_users.row_count == 0
    assert res_users.primary_key == ["id"]
    assert res_users.foreign_keys == []

    # Orders
    assert res_orders is not None
    assert res_orders.name == "orders"
    assert not res_orders.columns[1].is_primary_key
    assert res_orders.columns[2].data_type == "text"
    assert isinstance(res_orders.foreign_keys, list)
    assert len(res_orders.foreign_keys) == 1
    assert res_orders.foreign_keys[0].column == "user_id"
    assert res_orders.foreign_keys[0].references_table == "users"


@pytest.mark.asyncio
async def test_get_table_info_no_table(pg_db: PostgreSQLDatabase) -> None:
    # Act
    res = await pg_db.get_table_info("some_table")

    # Assert
    assert res is None


@pytest.mark.asyncio
async def test_get_tables(pg_db: PostgreSQLDatabase) -> None:
    # Act
    await pg_db.execute(
        """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            city TEXT NOT NULL
        );
        """
    )
    await pg_db.execute(
        """
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users (id),
            product TEXT UNIQUE
        );
        """
    )
    await pg_db.execute(
        """
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            order_id TEXT NOT NULL REFERENCES orders (product),
            price INTEGER
        );
        """
    )
    res = await pg_db.get_tables()

    # Assert
    assert res is not None
    assert len(res) > 0
    assert res == ["orders", "products", "users"]


@pytest.mark.asyncio
async def test_get_tables_no_tables(pg_db: PostgreSQLDatabase) -> None:
    # Act
    res = await pg_db.get_tables()

    # Assert
    assert res is not None
    assert isinstance(res, list)
    assert len(res) == 0


@pytest.mark.asyncio
async def test_get_schema_str(pg_db: PostgreSQLDatabase) -> None:
    # Act
    await pg_db.execute(
        """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            city TEXT NOT NULL
        );
        """
    )
    await pg_db.execute(
        """
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users (id),
            product BYTEA UNIQUE
        );
        """
    )
    await pg_db.execute(
        """
        CREATE TABLE products (
            main_key SERIAL PRIMARY KEY,
            name BYTEA NOT NULL REFERENCES orders (product),
            price REAL
        );
        """
    )
    await pg_db.execute("INSERT INTO users (name, city) VALUES ('test', 'TestCity')")
    res = await pg_db.get_schema()

    # Assert
    assert isinstance(res, str)


@pytest.mark.asyncio
async def test_get_schema_object(pg_db: PostgreSQLDatabase) -> None:
    # Act
    await pg_db.execute(
        """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            city TEXT NOT NULL
        );
        """
    )
    await pg_db.execute(
        """
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users (id),
            product BYTEA UNIQUE
        );
        """
    )
    await pg_db.execute(
        """
        CREATE TABLE products (
            main_key SERIAL PRIMARY KEY,
            name BYTEA NOT NULL REFERENCES orders (product),
            price REAL
        );
        """
    )
    await pg_db.execute("INSERT INTO users (name, city) VALUES ('test', 'TestCity')")
    res = await pg_db.get_schema(return_md=False)

    # Assert
    assert res is not None
    assert isinstance(res, SchemaInfo)
    assert isinstance(res.tables, list)

    if len(res.tables) > 0:
        assert isinstance(res.tables[0], TableInfo)

    tables = [t for t in res.tables if isinstance(t, TableInfo)]

    # Users
    users_table = next(t for t in tables if t.name == "users")
    assert isinstance(users_table, TableInfo)
    assert users_table.row_count == 1
    assert users_table.columns[0].name == "id"
    assert users_table.columns[0].is_primary_key
    assert len(users_table.columns) == 3

    # Orders
    orders_table = next(t for t in tables if t.name == "orders")
    assert isinstance(orders_table, TableInfo)
    assert orders_table.row_count == 0
    assert orders_table.primary_key == ["id"]
    assert isinstance(orders_table.foreign_keys, list)
    assert len(orders_table.foreign_keys) == 1
    assert orders_table.foreign_keys[0].column == "user_id"
    assert orders_table.foreign_keys[0].references_table == "users"
    assert orders_table.foreign_keys[0].references_column == "id"

    # Products
    products_table = next(t for t in tables if t.name == "products")
    assert isinstance(products_table, TableInfo)
    assert products_table.row_count == 0
    assert products_table.columns[1].data_type == "bytea"
    assert products_table.columns[2].data_type == "real"
    assert products_table.primary_key == ["main_key"]


@pytest.mark.asyncio
async def test_get_schema_no_tables_object(pg_db: PostgreSQLDatabase) -> None:
    # Act
    res = await pg_db.get_schema(return_md=False)

    # Assert
    assert res is not None
    assert res == SchemaInfo(tables=[])


@pytest.mark.asyncio
async def test_explain(pg_db: PostgreSQLDatabase) -> None:
    # Act
    await pg_db.execute(
        "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT, city TEXT NOT NULL);"
    )
    await pg_db.execute("INSERT INTO users (name, city) VALUES ('test', 'TestCity');")

    res = await pg_db.explain("SELECT COUNT(*) FROM users;")

    # Assert
    assert res is not None
    assert len(res) > 0
    assert isinstance(res, str)


@pytest.mark.asyncio
async def test_explain_random(pg_db: PostgreSQLDatabase) -> None:
    # Act
    res = await pg_db.explain("random_query")

    # Assert
    assert res is not None
    assert len(res) > 0
    assert isinstance(res, str)


@pytest.mark.asyncio
async def test_context_manager(pg_db: PostgreSQLDatabase) -> None:
    async with pg_db as postgres:
        await postgres.explain("random_query")

    assert not pg_db._pool
