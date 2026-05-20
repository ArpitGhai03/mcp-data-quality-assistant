import psycopg2
from psycopg2 import sql
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from db_config import get_prod_config, get_staging_config


# ---------- Create connection ----------
def connect(config):
    """Connect to PostgreSQL database"""
    return psycopg2.connect(**config)


# ---------- Create table ----------
def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id SERIAL PRIMARY KEY,
        customer_name VARCHAR(255),
        amount NUMERIC(10, 2),
        country VARCHAR(100),
        created_at DATE
    )
    """)

    conn.commit()


# ---------- Insert fake data ----------
def insert_data(conn, num_rows=100, missing_ratio=0.1, modify_ratio=0.1):
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] > 0:
        print("⏭️  Data already exists in database, skipping insert")
        return

    from faker import Faker
    import random
    fake = Faker()

    for i in range(1, num_rows + 1):
        name = fake.name()
        amount = round(random.uniform(100, 5000), 2)
        country = fake.country()
        date = fake.date()

        cursor.execute("""
        INSERT INTO orders (order_id, customer_name, amount, country, created_at) 
        VALUES (%s, %s, %s, %s, %s)
        """, (i, name, amount, country, date))

    conn.commit()


# ---------- Create staging with issues ----------
def insert_staging_data(prod_conn, staging_conn):
    prod_cursor = prod_conn.cursor()
    staging_cursor = staging_conn.cursor()

    prod_cursor.execute("SELECT * FROM orders")
    rows = prod_cursor.fetchall()

    import random
    for row in rows:
        order_id, name, amount, country, date = row

        # ❗ simulate missing data (skip some rows) - 20% data loss
        if random.random() < 0.2:
            continue

        # ❗ simulate modified data - 20% data corruption
        if random.random() < 0.2:
            amount = float(amount) * random.uniform(0.7, 1.3)

        staging_cursor.execute("""
        INSERT INTO orders (order_id, customer_name, amount, country, created_at) 
        VALUES (%s, %s, %s, %s, %s)
        """, (order_id, name, amount, country, date))

    staging_conn.commit()


# ---------- Main ----------
def main():
    reset = "--reset" in sys.argv
    
    if reset:
        print("🔄 Resetting databases...")
        prod_conn = connect(get_prod_config())
        staging_conn = connect(get_staging_config())
        
        prod_cursor = prod_conn.cursor()
        staging_cursor = staging_conn.cursor()
        
        prod_cursor.execute("DROP TABLE IF EXISTS orders CASCADE")
        staging_cursor.execute("DROP TABLE IF EXISTS orders CASCADE")
        
        prod_conn.commit()
        staging_conn.commit()
        print("   ✅ Dropped orders tables")
    else:
        prod_conn = connect(get_prod_config())
        staging_conn = connect(get_staging_config())
    
    create_tables(prod_conn)
    create_tables(staging_conn)

    insert_data(prod_conn, num_rows=500)
    insert_staging_data(prod_conn, staging_conn)

    prod_conn.close()
    staging_conn.close()

    print("✅ Databases ready! (prod and staging PostgreSQL databases)")


if __name__ == "__main__":
    main()