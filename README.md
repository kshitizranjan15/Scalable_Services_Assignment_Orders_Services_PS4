# Order Service — Docker build, run and push

This folder contains the Order service code and Docker assets. Follow the steps below to build images, run locally (with MySQL), and push images to a registry (Docker Hub or GHCR).

IMPORTANT: The repository's `Dockerfile` currently runs `python main.py` as the image's default command. If you'd like the container to wait for MySQL and run DB setup before starting the app, either run the provided `entrypoint.sh` (see notes) or update the `Dockerfile` CMD/ENTRYPOINT to use it.

Quick overview of new files in this folder:

- `entrypoint.sh` — waits for DB, runs `db_setup.py` and starts uvicorn
- `wait_for_db.py` — helper to wait for DB TCP readiness
- `docker-compose.yml` — optional local stack (MySQL + service)
- `.dockerignore` — files to exclude from the image build

## Environment (.env)
Create `order_service/.env` or edit existing. Example:

```
DB_HOST=mysql_db
DB_PORT=3306
DB_USER=root
DB_PASSWORD=rootpassword
DB_NAME=order_db
CSV_DIR=./csv_files
MYSQL_ROOT_PASSWORD=rootpassword
```

Keep `.env` out of git (it's already in `.dockerignore`).

## Build & run (recommended: docker-compose)
From `order_service/`:

1. Build and start stack:
```bash
cd order_service
docker-compose up --build
```

2. Run in background:
```bash
docker-compose up -d --build
```

3. Watch logs:
```bash
docker-compose logs -f order_service
```

4. Verify API:
```bash
curl http://127.0.0.1:8000/orders
# Open OpenAPI
http://127.0.0.1:8000/docs
```

Notes about `entrypoint.sh` and `Dockerfile`:
- The included `entrypoint.sh` (executable bit not set automatically) will wait for DB and run `db_setup.py` before starting `uvicorn`.
- If you want the built image to use `entrypoint.sh`, update `Dockerfile` to add:

```
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

or override the container command at runtime:

```bash
docker run --rm --network order_net --env-file .env <image> /entrypoint.sh
```

## Manual Docker build & run (no compose)
1. Build image:
```bash
cd order_service
docker build -t <your-dockerhub-username>/order_service:latest .
```

2. Create network and run MySQL:
```bash
docker network create order_net || true
docker run -d --name mysql_db --network order_net \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=order_db \
  mysql:8.0
```

3. Run service (use .env or pass env vars):
```bash
# using .env
docker run -d --name order_service_container --network order_net --env-file .env -p 8000:8000 <your-dockerhub-username>/order_service:latest

# or run the entrypoint directly (if you updated Dockerfile or override cmd):
docker run --rm --network order_net --env-file .env <your-dockerhub-username>/order_service:latest /entrypoint.sh
```

4. Initialize DB tables (if required):

Before running the commands below, wait for MySQL to be ready (check `docker-compose logs mysql` or `docker logs mysql_db`).

Option A — run `db_setup.py` inside the running service container (recommended when using `docker-compose`):

```bash
# wait for mysql to be ready, then run the setup inside the running order_service container
docker-compose exec order_service python db_setup.py
```

Option B — run `db_setup.py` in a temporary container attached to the same network (useful if you only built the image):

```bash
# find the compose network name (usually order_service_default) and run the image once to initialize DB
docker run --rm --network $(docker network ls --filter name=order_service_default -q) --env-file .env <your-dockerhub-username>/order_service:latest python db_setup.py
```

Legacy / alternative (when you started the container manually and used `--name order_service_container`):

```bash
# inside running container by name
docker exec -it order_service_container python db_setup.py
```

## Push image to Docker Hub
1. Login:
```bash
docker login
```

2. Tag and push:
```bash
docker tag order_service:latest <your-dockerhub-username>/order_service:1.0.0
docker push <your-dockerhub-username>/order_service:1.0.0
```

## Push image to GitHub Container Registry (GHCR)
1. Build and tag:
```bash
docker build -t ghcr.io/<GITHUB_USERNAME>/order_service:1.0.0 .
```
2. Login and push (use a PAT with `write:packages` scope if needed):
```bash
echo $CR_PAT | docker login ghcr.io -u <GITHUB_USERNAME> --password-stdin
docker push ghcr.io/<GITHUB_USERNAME>/order_service:1.0.0
```

Notes on using `GITHUB_TOKEN` for GHCR in GitHub Actions: you may need to enable package write permissions for `GITHUB_TOKEN` in repository settings or use a PAT stored in `secrets.CR_PAT`.

## Git steps — commit Docker assets and push to GitHub
1. Add new files and commit:
```bash
cd order_service
git add Dockerfile entrypoint.sh wait_for_db.py docker-compose.yml .dockerignore README.md
git commit -m "chore(docker): add Docker helpers, compose and README"
git push origin main
```

2. Build and test locally (optional):
```bash
docker-compose up --build --abort-on-container-exit
```

## CI: GitHub Actions (example)
This repository includes an example workflow to build and push to GHCR on push to `main` (see `.github/workflows/docker-publish.yml`).

## Troubleshooting
- If the app can't reach MySQL, ensure `DB_HOST` is set to the MySQL container name (`mysql_db` in `docker-compose.yml`) when running under Docker.
- If tables are missing, run `python db_setup.py` inside the container or locally to initialize schema and import CSVs.

---

If you'd like, I can:
- Update the `Dockerfile` to use the `entrypoint.sh` automatically (small edit), or
- Create a GitHub Actions workflow tuned for Docker Hub instead of GHCR.
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
