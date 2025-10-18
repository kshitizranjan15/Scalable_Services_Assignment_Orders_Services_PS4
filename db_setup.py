import os
import pandas as pd
from db_utils import get_connection
from pathlib import Path

# Default CSV_DIR is the service-local csv_files directory. Can be overridden by CSV_DIR env var.
SERVICE_DIR = Path(__file__).resolve().parent
CSV_DIR = Path(os.getenv("CSV_DIR", str(SERVICE_DIR / "csv_files")))

def create_database_and_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS order_db")
    conn.commit()
    cur.close()
    conn.close()

    conn = get_connection("order_db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Orders (
            order_id INT PRIMARY KEY,
            customer_id INT,
            order_status VARCHAR(50),
            payment_status VARCHAR(50),
            order_total DECIMAL(10,2),
            created_at DATETIME
        )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Order_Items (
        order_item_id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT,
        product_id INT,
        sku VARCHAR(100),
        quantity INT,
        unit_price DECIMAL(10,2)
    )
""")
    conn.commit()
    conn.close()
    print("✅ order_db and tables created")


# --- OPTIONAL: teardown SQL (commented) ---
# Use only when you intentionally want to drop data. Keep commented to avoid accidental execution.
#
# SQL to drop tables:
# DROP TABLE IF EXISTS order_db.Order_Items;
# DROP TABLE IF EXISTS order_db.Orders;
#
# SQL to drop database:
# DROP DATABASE IF EXISTS order_db;


def load_csvs():
    def load(csv_file, table_name):
        file_path = CSV_DIR / csv_file
        df = pd.read_csv(str(file_path))
        print(f"📥 Loading {csv_file} ({len(df)} rows) into order_db.{table_name}")
        conn = get_connection("order_db")
        cur = conn.cursor()
        cols = ", ".join(df.columns)
        placeholders = ", ".join(["%s"] * len(df.columns))
        for _, row in df.iterrows():
            cur.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})", tuple(row))
        conn.commit()
        conn.close()
        print(f"✅ Inserted {len(df)} rows into order_db.{table_name}")

    load("Orders.csv", "Orders")
    load("Order_Items.csv", "Order_Items")


if __name__ == "__main__":
    create_database_and_tables()
    load_csvs()
