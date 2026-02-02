import random
import sqlite3
import string
from datetime import datetime, timedelta

from loguru import logger

DB_PATH = "./examples/sql/sqlite/example.db"


def generate_random_string(length=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def setup_test_database():
    """Sets up a sample SQLite database."""
    logger.info(f"Creating database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable Foreign Key support
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Create Tables
    logger.info("Creating tables...")
    cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Profiles (
        profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bio TEXT,
        user_id INTEGER UNIQUE,
        FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL,
        order_date TEXT,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
    )""")

    # 2. Generate Random Seed Data
    logger.info("Generating test data...")

    for _ in range(10):
        uname = f"user_{generate_random_string(5)}"
        email = f"{uname}@example.com"

        try:
            cursor.execute("INSERT INTO Users (username, email) VALUES (?, ?)", (uname, email))
            u_id = cursor.lastrowid

            # Create a Profile for the user
            bio = f"Random bio for {uname} who loves {generate_random_string(4)}."
            cursor.execute("INSERT INTO Profiles (bio, user_id) VALUES (?, ?)", (bio, u_id))

            # Create random Orders
            for _ in range(random.randint(1, 5)):
                amount = round(random.uniform(10.0, 500.0), 2)
                random_days = random.randint(0, 30)
                date = (datetime.now() - timedelta(days=random_days)).strftime("%Y-%m-%d")

                cursor.execute(
                    "INSERT INTO Orders (amount, order_date, user_id) VALUES (?, ?, ?)",
                    (amount, date, u_id),
                )
        except sqlite3.IntegrityError:
            continue

    conn.commit()
    logger.info("Database populated successfully.")

    # 3. Verification
    cursor.execute("SELECT COUNT(*) FROM Users")
    logger.info(f"Total Users: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM Orders")
    logger.info(f"Total Orders: {cursor.fetchone()[0]}")

    conn.close()


if __name__ == "__main__":
    setup_test_database()
