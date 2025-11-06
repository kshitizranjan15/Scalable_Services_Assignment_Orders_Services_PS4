#!/bin/sh
set -e

# Load .env if present
if [ -f .env ]; then
  # export all non-comment lines from .env
  export $(grep -v '^#' .env | xargs)
fi

echo "[entrypoint] waiting for DB..."
python wait_for_db.py

echo "[entrypoint] running DB setup (if any)"
# db_setup may create tables / import CSVs; ignore failures so container still starts
python db_setup.py || echo "db_setup.py finished or returned non-zero; continuing"

echo "[entrypoint] starting uvicorn"
exec uvicorn main:app --host 0.0.0.0 --port 8000
