# StreamStore (Kafka Orders)

Small demo that produces a single order message to a Kafka `orders` topic using Python and `confluent_kafka`.

## What’s here
- `producer.py` sends one JSON order message.
- `docker-compose.yaml` runs a single-node Kafka broker (KRaft).

## Quick start
1) Start Kafka:
```bash
docker compose up -d
```

2) Install Python deps:
```bash
python -m pip install confluent-kafka
```

3) Run the producer:
```bash
python producer.py
```

You should see a delivery report confirming the message was sent.

## Notes
- The producer connects to `localhost:9092`.
- The topic name is `orders`.
