# StreamStore (Kafka Orders + FastAPI)

Demo project that combines a small Orders API with Kafka. The API writes orders to Postgres and publishes an OrderCreated event to Kafka.

## What's here
- FastAPI Orders API (users, orders)
- SQLAlchemy models + Alembic config
- Docker Compose: Kafka, Kafka UI, Postgres, Orders API
- Kafka scripts:
  - producer.py sends a sample order message to the orders topic
  - consumer.py listens for order status updates on the order-status topic

## Quick start (Docker)
1) Start services:
```bash
docker compose up -d
```

2) Initialize schema (first run only):
```bash
alembic revision --autogenerate -m "init schema"
alembic upgrade head
```

3) API is available at:
```text
http://localhost:8000
```

## API usage
Create a user:
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

Create an order:
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<UUID>","currency":"USD","items":[{"product_sku":"sku-1","quantity":2,"unit_price":5.0}]}'
```

Fetch an order:
```bash
curl http://localhost:8000/orders/<UUID>
```

## Kafka events
On order creation, the API publishes an OrderCreated event to the orders topic.
Example payload:
```json
{
  "event_type": "OrderCreated",
  "schema_version": 1,
  "order_id": "...",
  "user_id": "...",
  "status": "CREATED",
  "total_amount": 25.0,
  "currency": "USD",
  "created_at": "2026-01-29T11:17:00.000000",
  "items": [
    {"product_sku": "sku-1", "quantity": 2, "unit_price": 5.0}
  ]
}
```

## Status consumer (optional)
The consumer listens to the order-status topic and applies updates to the database. Message format:
```json
{"order_id": "<UUID>", "status": "CANCELLED"}
```

## Environment variables
- DATABASE_URL: SQLAlchemy database URL (required)
- KAFKA_BOOTSTRAP_SERVERS: Kafka bootstrap servers (default: localhost:9092)
- KAFKA_ORDERS_TOPIC: topic for OrderCreated events (default: orders)
- KAFKA_STATUS_TOPIC: topic for status updates (default: order-status)
- KAFKA_ENABLED: set to 0 to disable publishing

## Tests
Integration tests require a test database.
```bash
set TEST_DATABASE_URL=postgresql+psycopg://orders:orderspass@localhost:5432/ordersdb_test
pip install -r requirements-dev.txt
pytest
```
