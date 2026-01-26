import json
from confluent_kafka import Producer
from uuid import uuid4

producerConfig = {"bootstrap.servers": "localhost:9092"}

producer = Producer(producerConfig)


# Callback function to handle delivery reports
def delivery_report(err, msg):
    """Called once for each message produced to indicate delivery result.
    Triggered by poll() or flush()."""
    if err is not None:
        print(f"❌ Message delivery failed: {err}")
    else:
        print(
            f"✅ Message delivered to: {msg.topic()}, partition: [{msg.partition()}], offset: {msg.offset()}"
        )


order = {"order_id": str(uuid4()), "user": "Lois", "item": "Pizza", "quantity": 2}

# turn the order dictionary into a JSON string and then encode it to bytes
orderStr = json.dumps(order).encode("utf-8")

# SEND TO: Kafka "orders" topic
producer.produce(topic="orders", value=orderStr, callback=delivery_report)

# Ensure all messages are sent before exiting ensuring durability
producer.flush()
