import json
import os
import uuid

from confluent_kafka import Consumer
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal
from app.models import Order, OrderStatus

bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
status_topic = os.environ.get("KAFKA_STATUS_TOPIC", "order-status")

consumer_config = {
    "bootstrap.servers": bootstrap_servers,
    "group.id": "order-status-updater",
    "auto.offset.reset": "earliest",
}

consumer = Consumer(consumer_config)
consumer.subscribe([status_topic])
print(f"Listening for status updates on '{status_topic}'...")


def handle_status_update(payload: dict) -> None:
    order_id = payload.get("order_id")
    status = payload.get("status")
    if not order_id or not status:
        return

    try:
        order_uuid = uuid.UUID(order_id)
        new_status = OrderStatus(status)
    except (ValueError, TypeError):
        return

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_uuid).first()
        if not order:
            return
        order.status = new_status
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Error: {msg.error()}")
            continue

        value = msg.value().decode("utf-8")
        payload = json.loads(value)
        handle_status_update(payload)
except KeyboardInterrupt:
    print("Exiting consumer...")
finally:
    consumer.close()
