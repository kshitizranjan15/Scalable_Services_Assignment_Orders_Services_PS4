# ECI Orders Service

A single-purpose Orders microservice (FastAPI) extracted from the monorepo. It stores orders and order items in a MySQL database named `order_db` and can bootstrap its schema and data from CSV files.

## Repository layout

- `main.py` — FastAPI application exposing `/orders` endpoints
- `db_utils.py` — helper to read `.env` and create MySQL connections
- `db_setup.py` — creates `order_db`, tables, and loads CSV data
- `requirements.txt` — Python dependencies
- `.env` — service environment (excluded from git)
- `csv_files/` — included sample CSVs (`Orders.csv`, `Order_Items.csv`)
- `.gitignore` — ignores `.env`, pycache, etc.
- `README.md` — this file

## Overview

- Purpose: manage Orders and Order Items (create, list, fetch-by-id).
- DB: MySQL database `order_db` (created by `db_setup.py` if missing).
- CSV loader: `db_setup.py` will read CSVs and insert rows into tables.

## Requirements

- Python 3.10+
- MySQL server accessible with credentials in `.env`
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Edit the service-local `.env` file (already present in this folder). Typical variables:

- `DB_HOST` (default: 127.0.0.1)
- `DB_PORT` (default: 3306)
- `DB_USER` (default: root)
- `DB_PASSWORD` (change from the placeholder)
- `CSV_DIR` (optional: defaults to `./csv_files` in this folder)

db_utils.py loads the `.env` automatically from this service folder.

## Load CSVs into MySQL (bootstrap)

1. Ensure MySQL is running and `.env` contains valid credentials.
2. From this folder run:

```bash
python db_setup.py
```

This will:
- create `order_db` (if missing)
- create tables `Orders` and `Order_Items` (if missing)
- bulk-insert the CSVs from the directory referenced by `CSV_DIR` (defaults to `./csv_files`)

If you want to use a different CSV location, set `CSV_DIR` in the `.env` or the environment before running.

## Run the API (development)

Start the app with uvicorn (default port 8000):

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI docs: `http://127.0.0.1:8000/docs`

## API Endpoints


Orders

- `GET /orders?limit={n}` — list orders (default `limit=10`)
- `GET /orders/{order_id}` — get order header and its items
- `POST /orders` — insert a new order (payload matches `Order` Pydantic model in `main.py`)
- `PUT /orders/{order_id}` — update order header fields (customer_id, order_status, payment_status, order_total). The endpoint expects the same `Order` model but will update header columns for the specified order.
- `DELETE /orders/{order_id}` — delete an order and its associated order items.

Request examples are included in the `csv_files/` and can be tested with curl/Postman.

## Examples

Minimal `POST /orders` payload:

```json
{
	"order_id": 123,
	"customer_id": 456,
	"order_total": 99.99,
	"order_status": "PENDING",
	"payment_status": "UNPAID",
	"items": [
		{ "product_id": 1, "sku": "SKU-001", "quantity": 2, "unit_price": 19.99 }
	]
}
```


Endpoint examples (curl)

1) List orders (GET /orders)

```bash
curl "http://127.0.0.1:8000/orders?limit=5"
```

Sample response (array):

```json
[
	{ "order_id": 1, "customer_id": 44, "order_status": "CREATED", "payment_status": "FAILED", "order_total": 966.29, "created_at": "2024-09-18 14:40:32" },
	{ "order_id": 2, "customer_id": 98, "order_status": "CANCELLED", "payment_status": "FAILED", "order_total": 786.94, "created_at": "2023-02-06 02:26:38" }
]
```

2) Get order by id (GET /orders/{order_id})

```bash
curl "http://127.0.0.1:8000/orders/123"
```

Sample response (object with items):

```json
{
	"order_id": 123,
	"customer_id": 456,
	"order_status": "PENDING",
	"payment_status": "UNPAID",
	"order_total": 99.99,
	"created_at": "2025-01-01 12:00:00",
	"items": [
		{ "order_item_id": 1, "order_id": 123, "product_id": 1, "sku": "SKU-001", "quantity": 2, "unit_price": 19.99 }
	]
}
```

3) Create a new order (POST /orders)

```bash
curl -X POST "http://127.0.0.1:8000/orders" \
	-H "Content-Type: application/json" \
	-d '{"order_id": 123, "customer_id": 456, "order_total": 99.99, "order_status": "PENDING", "payment_status": "UNPAID", "items": [{"product_id":1,"sku":"SKU-001","quantity":2,"unit_price":19.99}] }'
```

Successful response:

```json
{ "message": "✅ Order inserted successfully" }
```

4) Update order header (PUT /orders/{order_id})

```bash
curl -X PUT "http://127.0.0.1:8000/orders/123" \
	-H "Content-Type: application/json" \
	-d '{"order_id":123, "customer_id":999, "order_total":149.99, "order_status":"PROCESSING", "payment_status":"PAID", "items":[] }'
```

Successful response:

```json
{ "message": "✅ Order updated successfully" }
```

5) Delete order (DELETE /orders/{order_id})

```bash
curl -X DELETE "http://127.0.0.1:8000/orders/123"
```

Successful response:

```json
{ "message": "🗑️ Order 123 deleted successfully" }
```

## Notes & Caveats

- CSV loading uses pandas and inserts rows directly; very large CSVs may take time.
- Primary keys (`order_id`) must be unique. Duplicate keys will produce DB errors.
- The service reads `.env` from the service folder — do not commit real secrets. `.gitignore` already excludes `.env`.
- Error responses include DB error messages to help debugging in development; avoid exposing such details in production.

## Teardown (drop) SQL

If you need to drop tables or the database during development, the SQL snippets are included as commented code inside `db_setup.py` under the comment "OPTIONAL: teardown SQL". Use them only when you intentionally want to remove data.

## Useful files

- `main.py` — API implementation
- `db_utils.py` — connection helper (loads `.env` in the service folder)
- `db_setup.py` — create/load schema and data; contains commented drop SQL
- `csv_files/` — Orders and Order_Items sample CSVs

## License

No license specified. Add a `LICENSE` file if you want to make this open source.
