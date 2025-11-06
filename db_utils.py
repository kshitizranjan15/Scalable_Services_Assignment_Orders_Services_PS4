import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env located in the same service folder (safe and explicit)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path))


def get_connection(db_name=None):
    """Return a MySQL connection object."""
    # Ensure port is an int when provided
    port = os.getenv("DB_PORT")
    try:
        port = int(port) if port is not None else 3306
    except ValueError:
        port = 3306

    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=port,
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=db_name if db_name else None
    )
    return conn
