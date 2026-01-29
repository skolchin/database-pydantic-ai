import random
import string
from datetime import datetime, timedelta

import psycopg2
from loguru import logger

# Configuration - adjust if you changed docker-compose.yaml
DB_CONFIG = "postgresql://user:password@localhost:5432/test_db"


def generate_random_string(length=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def setup_test_database():
    """Sets up a sample database for PostgreSQL example."""
    try:
        logger.info(f"Connecting to Postgres at {DB_CONFIG}...")
        conn = psycopg2.connect(DB_CONFIG)
        cursor = conn.cursor()

        # 1. Create Tables
        logger.info("Creating tables...")
        cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
            user_id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT UNIQUE
        )""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS Profiles (
            profile_id SERIAL PRIMARY KEY,
            bio TEXT,
            user_id INTEGER UNIQUE,
            CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
        )""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS Orders (
            order_id SERIAL PRIMARY KEY,
            amount DECIMAL(10, 2),
            order_date DATE,
            user_id INTEGER,
            CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
        )""")

        # 2. Generate Random Seed Data
        logger.info("Generating test data...")

        for _ in range(10):
            uname = f"user_{generate_random_string(5)}"
            email = f"{uname}@example.com"

            try:
                cursor.execute(
                    "INSERT INTO Users (username, email) VALUES (%s, %s) RETURNING user_id",
                    (uname, email),
                )
                u_id = cursor.fetchone()[0]

                # Create Profile
                bio = f"Random bio for {uname} who loves {generate_random_string(4)}."
                cursor.execute("INSERT INTO Profiles (bio, user_id) VALUES (%s, %s)", (bio, u_id))

                # Create random Orders
                for _ in range(random.randint(1, 5)):
                    amount = round(random.uniform(10.0, 500.0), 2)
                    date = datetime.now() - timedelta(days=random.randint(0, 30))

                    cursor.execute(
                        "INSERT INTO Orders (amount, order_date, user_id) VALUES (%s, %s, %s)",
                        (amount, date.date(), u_id),
                    )
            except psycopg2.IntegrityError:
                conn.rollback()
                continue

        conn.commit()
        logger.info("Database populated successfully.")

        # 3. Verification
        cursor.execute("SELECT COUNT(*) FROM Users")
        logger.info(f"Total Users: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM Orders")
        logger.info(f"Total Orders: {cursor.fetchone()[0]}")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.exception(f"Error: {e}")
        logger.warning("\nMake sure your PostgreSQL container is running:")
        logger.warning("docker-compose up -d")


if __name__ == "__main__":
    setup_test_database()
