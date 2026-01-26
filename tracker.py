import json
from confluent_kafka import Consumer

cosumerConfig = {
    "bootstrap.servers": "localhost:9092",
    # a unqiue string identifying the consumer group this consumer belongs to
    "group.id": "order-tracker-group",
    "auto.offset.reset": "earliest",  # start from the beginning of the topic
}

consumer = Consumer(cosumerConfig)

consumer.subscribe(["orders"])
print("🚀 Consumer is now listening to 'orders' topic...")

try:
    while True:
        # timeout of 1 second. Every second, check for new messages
        msg = consumer.poll(1.0)
        if msg is None:
            continue  # no message received within timeout
        if msg.error():
            print(f"❌ Error: {msg.error()}")
            continue

        value = msg.value().decode("utf-8")
        order = json.loads(value)
        # Proper message received
        print(
            f"-------------------\n✅ Received message:\nOrder: {order['item']}, From: {order['user']}, Quantity: {order['quantity']}\nTopic: {msg.topic()}, Partition: [{msg.partition()}], Offset: {msg.offset()}\n-------------------"
        )
except KeyboardInterrupt:
    print("Exiting consumer...")
finally:
    consumer.close()
