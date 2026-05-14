"""
simulator/kafka_producer.py

Kafka producer wrapper.
"""

import json
import logging
import time
from typing import Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

from simulator.config import KAFKA_BOOTSTRAP_SERVERS, BUSINESS_TOPIC, PUBLISH_BUSINESS_TOPIC

logger = logging.getLogger(__name__)


class EventProducer:
    def __init__(self, bootstrap_servers: Optional[str] = None, retries: int = 30, retry_sleep: float = 2.0):
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.retries = retries
        self.retry_sleep = retry_sleep
        self._producer = None

    def connect(self):
        if self._producer:
            return

        last_err = None
        for attempt in range(1, self.retries + 1):
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                    key_serializer=lambda k: str(k).encode("utf-8") if k is not None else None,
                    acks="all",
                    retries=5,
                    linger_ms=50,
                    batch_size=32768,
                    max_request_size=1048576,
                )
                logger.info("Kafka producer connected to %s", self.bootstrap_servers)
                return
            except NoBrokersAvailable as e:
                last_err = e
                logger.warning("Kafka not ready, retry %s/%s: %s", attempt, self.retries, e)
                time.sleep(self.retry_sleep)

        raise RuntimeError(f"Cannot connect to Kafka: {last_err}")

    def send_event(self, topic: str, event: dict, partition_key: Optional[str] = None, flush: bool = False):
        if not self._producer:
            self.connect()

        future = self._producer.send(topic, value=event, key=partition_key)

        # Optional mirror topic for debug/replay.
        if PUBLISH_BUSINESS_TOPIC and topic != BUSINESS_TOPIC:
            self._producer.send(BUSINESS_TOPIC, value={**event, "_source_topic": topic}, key=partition_key)

        if flush:
            self._producer.flush()
        return future

    def send_many(self, events: list[tuple[str, dict, Optional[str]]], flush: bool = True):
        futures = []
        for topic, event, key in events:
            futures.append(self.send_event(topic, event, key, flush=False))
        if flush and self._producer:
            self._producer.flush()
        return futures

    def close(self):
        if self._producer:
            self._producer.flush()
            self._producer.close()
            self._producer = None
            logger.info("Kafka producer closed")
