import json
import logging
import os
from typing import Any, Dict

from confluent_kafka import Producer

logger = logging.getLogger("app.kafka")


class KafkaPublisher:
    def __init__(
        self,
        bootstrap_servers: str | None = None,
        topic: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        if bootstrap_servers is None:
            bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
        if topic is None:
            topic = os.environ.get("KAFKA_ORDERS_TOPIC", "orders")
        if enabled is None:
            enabled = os.environ.get("KAFKA_ENABLED", "1") not in ("0", "false", "False")

        self.topic = topic
        self.enabled = bool(bootstrap_servers) and enabled
        self.producer = (
            Producer({"bootstrap.servers": bootstrap_servers}) if self.enabled else None
        )

    def publish_order_created(self, order) -> None:
        if not self.enabled or self.producer is None:
            return

        payload = _serialize_order_created(order)

        try:
            self.producer.produce(
                self.topic,
                key=payload["order_id"],
                value=json.dumps(payload).encode("utf-8"),
            )
            self.producer.poll(0)
        except Exception:
            logger.exception("Failed to publish OrderCreated event")

    def close(self) -> None:
        if self.producer is not None:
            self.producer.flush(5)


def _serialize_order_created(order) -> Dict[str, Any]:
    return {
        "event_type": "OrderCreated",
        "schema_version": 1,
        "order_id": str(order.id),
        "user_id": str(order.user_id),
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "total_amount": float(order.total_amount),
        "currency": order.currency,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "items": [
            {
                "product_sku": item.product_sku,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            }
            for item in order.items
        ],
    }
