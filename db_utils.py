import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env located in the same service folder (safe and explicit)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path))


def get_connection(db_name=None):
    """Return a MySQL connection object."""
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=db_name if db_name else None
    )
    return conn
