import os
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.skip("Set TEST_DATABASE_URL to run integration tests.", allow_module_level=True)

if "test" not in TEST_DATABASE_URL.lower():
    pytest.skip("Refusing to run tests without a test database.", allow_module_level=True)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("KAFKA_ENABLED", "0")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402

engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except OperationalError:
        pytest.skip("Test database is not reachable.")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)

def create_user(client, email=None):
    if email is None:
        email = f"user-{uuid.uuid4()}@example.com"
    response = client.post("/users", json={"email": email})
    assert response.status_code == 201
    return response.json()["id"], email


def build_order_payload(user_id):
    return {
        "user_id": user_id,
        "currency": "USD",
        "items": [
            {"product_sku": "sku-1", "quantity": 1, "unit_price": 5.0},
        ],
    }


def test_create_user(client):
    email = f"user-{uuid.uuid4()}@example.com"
    response = client.post("/users", json={"email": email})

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert "id" in data
    assert "created_at" in data


def test_create_and_get_order(client):
    user_id, _ = create_user(client)

    order_payload = {
        "user_id": user_id,
        "currency": "usd",
        "items": [
            {"product_sku": "sku-1", "quantity": 2, "unit_price": 5.0},
            {"product_sku": "sku-2", "quantity": 1, "unit_price": 15.0},
        ],
    }

    order_resp = client.post("/orders", json=order_payload)
    assert order_resp.status_code == 201
    order_data = order_resp.json()

    assert order_data["user_id"] == user_id
    assert order_data["currency"] == "USD"
    assert order_data["total_amount"] == 25.0
    assert order_data["status"] == "CREATED"

    get_resp = client.get(f"/orders/{order_data['id']}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()

    assert fetched["id"] == order_data["id"]
    assert len(fetched["items"]) == 2


def test_create_user_duplicate_email_conflict(client):
    email = f"user-{uuid.uuid4()}@example.com"
    user_id, _ = create_user(client, email=email)
    assert user_id

    response = client.post("/users", json={"email": email})
    assert response.status_code == 409


def test_create_order_user_not_found(client):
    payload = build_order_payload(str(uuid.uuid4()))
    response = client.post("/orders", json=payload)
    assert response.status_code == 404


def test_get_order_not_found(client):
    response = client.get(f"/orders/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_item_quantity_validation(client, quantity):
    user_id, _ = create_user(client)
    payload = build_order_payload(user_id)
    payload["items"][0]["quantity"] = quantity

    response = client.post("/orders", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize("unit_price", [0, -5.0])
def test_order_item_unit_price_validation(client, unit_price):
    user_id, _ = create_user(client)
    payload = build_order_payload(user_id)
    payload["items"][0]["unit_price"] = unit_price

    response = client.post("/orders", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize("product_sku", ["", "x" * 65])
def test_order_item_sku_validation(client, product_sku):
    user_id, _ = create_user(client)
    payload = build_order_payload(user_id)
    payload["items"][0]["product_sku"] = product_sku

    response = client.post("/orders", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize("currency", ["US", "USDA"])
def test_order_currency_validation(client, currency):
    user_id, _ = create_user(client)
    payload = build_order_payload(user_id)
    payload["currency"] = currency

    response = client.post("/orders", json=payload)
    assert response.status_code == 422
