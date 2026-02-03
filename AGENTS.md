# StreamStore - Worklog and Plans

## Project summary (so far)
- Started as a Kafka demo with a Python producer that sends a single order message to the `orders` topic and a simple consumer script.
- Added a FastAPI Orders API with SQLAlchemy models, Pydantic schemas, and Alembic configuration.
- Added Docker Compose for Kafka, Kafka UI, Postgres, and the Orders API container.

## What was done in this session
- Added Kafka publishing for `OrderCreated` events from the API.
  - New module: `app/kafka.py` (publisher + event serializer).
  - Wired into FastAPI startup/shutdown and order creation in `app/main.py`.
- Updated `consumer.py` to listen on `order-status` and update order status in Postgres.
- Updated `README.md` with:
  - API usage (create user/order, fetch order)
  - Kafka event payload example
  - Env var documentation
  - Test instructions
- Added dependencies:
  - `confluent-kafka` to `requirements.txt`
  - `pytest` and `httpx` via `requirements-dev.txt`
- Added integration tests in `tests/test_api.py`:
  - Create user, create order, fetch order.
  - Duplicate email conflict (409).
  - User not found (404).
  - Order not found (404).
  - Validation for quantity, unit_price, product_sku, currency.
- Ran tests using a Dockerized Postgres test DB:
  - `ordersdb_test` created in the postgres container.
  - Tests pass with `TEST_DATABASE_URL` set and pytest cache disabled.

## Current status
- API endpoints: `/health`, `/users`, `/orders`, `/orders/{order_id}`.
- Kafka:
  - Order creation emits `OrderCreated` to topic `orders`.
  - Optional consumer reads `order-status` and updates order status.
- Tests are green with a reachable Postgres test database.

## Notes / warnings observed
- FastAPI `@app.on_event` is deprecated; use lifespan handlers instead.
- Pydantic class-based `Config` is deprecated; use `ConfigDict` instead.
- Pytest cache permissions error on Windows; workaround used: `-p no:cacheprovider --ignore-glob=pytest-cache-files-*`.

## Recommended next steps
1) Create the initial Alembic migration:
   - `alembic revision --autogenerate -m "init schema"`
   - `alembic upgrade head`
2) Replace `@app.on_event` with FastAPI lifespan handlers.
3) Migrate Pydantic configs to `ConfigDict`.
4) Add a Kafka integration test (optional; can be skipped when Kafka not available).
5) Add a short `make` or `scripts/` helper for common dev commands (up, migrate, test).
