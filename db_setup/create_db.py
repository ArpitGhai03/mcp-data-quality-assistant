import sqlite3
import os
from faker import Faker
import random

fake = Faker()

# ---------- Paths ----------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)
os.makedirs(DATA_DIR, exist_ok=True)

PROD_DB = os.path.join(DATA_DIR, "prod.db")
STAGING_DB = os.path.join(DATA_DIR, "staging.db")


# ---------- Create connection ----------
def connect(db_path):
    return sqlite3.connect(db_path)


# ---------- Create table ----------
def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_name TEXT,
        amount REAL,
        country TEXT,
        created_at TEXT
    )
    """)

    conn.commit()


# ---------- Insert fake data ----------
def insert_data(conn, num_rows=100, missing_ratio=0.1, modify_ratio=0.1):
    cursor = conn.cursor()

    for i in range(1, num_rows + 1):
        name = fake.name()
        amount = round(random.uniform(20, 500), 2)
        country = fake.country()
        date = fake.date()

        cursor.execute("""
        INSERT INTO orders VALUES (?, ?, ?, ?, ?)
        """, (i, name, amount, country, date))

    conn.commit()


# ---------- Create staging with issues ----------
def insert_staging_data(prod_conn, staging_conn):
    prod_cursor = prod_conn.cursor()
    staging_cursor = staging_conn.cursor()

    rows = prod_cursor.execute("SELECT * FROM orders").fetchall()

    for row in rows:
        order_id, name, amount, country, date = row

        # ❗ simulate missing data (skip some rows)
        if random.random() < 0.1:
            continue

        # ❗ simulate modified data
        if random.random() < 0.1:
            amount = amount * random.uniform(0.8, 1.2)

        staging_cursor.execute("""
        INSERT INTO orders VALUES (?, ?, ?, ?, ?)
        """, (order_id, name, amount, country, date))

    staging_conn.commit()


# ---------- Main ----------
def main():
    prod_conn = connect(PROD_DB)
    staging_conn = connect(STAGING_DB)

    create_tables(prod_conn)
    create_tables(staging_conn)

    insert_data(prod_conn, num_rows=100)

    insert_staging_data(prod_conn, staging_conn)

    prod_conn.close()
    staging_conn.close()

    print("Databases created successfully!")


if __name__ == "__main__":
    main()