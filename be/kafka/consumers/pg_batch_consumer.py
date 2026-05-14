"""
consumers/pg_batch_consumer.py

Kafka Consumer chính:
Kafka topics -> Raw_Staging_Events -> Dim/Fact -> Redis pub/sub for FastAPI.

Lưu ý:
- Consumer publish raw business event sang Redis channel `f88_realtime`.
- Không publish cash_recorded mặc định để tránh dashboard hiện tại double count.
"""

import argparse
import json
import logging
import os
import time
import random
import redis
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from kafka import KafkaConsumer

from consumers.db import get_connection, execute_query
from consumers.dim_handler import handle_customer, handle_asset
from consumers.fact_handler import (
    handle_loan_application,
    handle_loan_approved,
    handle_loan_rejected,
    handle_loan_disbursed,
    handle_repayment,
    handle_status_changed,
    handle_cash_recorded,
    handle_weather,
    handle_opex,
    handle_payroll,
)
from simulator.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPICS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("pg_consumer")

REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "f88_realtime")
PUBLISH_CASH_TO_REDIS = os.getenv("PUBLISH_CASH_TO_REDIS", "0") == "1"

REALTIME_EVENT_TYPES = {
    "customer_created",
    "loan_application_created",
    "loan_approved",
    "loan_rejected",
    "loan_disbursed",
    "repayment_paid",
    "loan_status_changed",
    "weather_updated",
}
if PUBLISH_CASH_TO_REDIS:
    REALTIME_EVENT_TYPES.add("cash_recorded")


STAGING_DDL = """
CREATE TABLE IF NOT EXISTS Raw_Staging_Events (
    staging_id      BIGSERIAL PRIMARY KEY,
    event_id        VARCHAR(100) UNIQUE NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    event_time      TIMESTAMP,
    ingestion_time  TIMESTAMP DEFAULT NOW(),
    source_topic    VARCHAR(100),
    partition_key   VARCHAR(200),
    business_key    VARCHAR(200),
    payload         JSONB NOT NULL,
    process_status  VARCHAR(20) DEFAULT 'new',
    scheduled_time  TIMESTAMP,
    error_reason    TEXT
);
CREATE INDEX IF NOT EXISTS idx_staging_status ON Raw_Staging_Events(process_status);
CREATE INDEX IF NOT EXISTS idx_staging_event_type ON Raw_Staging_Events(event_type);
CREATE INDEX IF NOT EXISTS idx_staging_event_time ON Raw_Staging_Events(event_time);
CREATE INDEX IF NOT EXISTS idx_staging_scheduled ON Raw_Staging_Events(scheduled_time);
"""


def ensure_staging_table(conn):
    cur = conn.cursor()
    cur.execute(STAGING_DDL)
    conn.commit()
    logger.info("Raw_Staging_Events ensured")


def insert_staging(conn, event: dict, topic: str, partition_key: str | None = None) -> bool:
    event_id = event.get("event_id")
    payload = event.get("payload", {})
    business_key = payload.get("SoHopDong") or payload.get("CMND_CCCD") or payload.get("MaCuaHang") or ""
    
    # Calculate random delay (5-15 minutes)
    delay_mins = random.randint(5, 15)
    scheduled_time = datetime.now() + timedelta(minutes=delay_mins)

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Raw_Staging_Events
        (event_id, event_type, event_time, source_topic, partition_key, business_key, payload, scheduled_time)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (event_id) DO NOTHING
        """,
        (
            event_id,
            event.get("event_type"),
            event.get("event_time"),
            topic,
            partition_key,
            business_key,
            json.dumps(payload, ensure_ascii=False),
            scheduled_time,
        ),
    )
    return cur.rowcount > 0


def update_staging_status(conn, event_id: str, status: str, error: str | None = None):
    execute_query(
        conn,
        "UPDATE Raw_Staging_Events SET process_status = %s, error_reason = %s WHERE event_id = %s",
        (status, error, event_id),
    )


def process_event(conn, event: dict, topic: str) -> bool:
    event_type = event.get("event_type")
    payload = event.get("payload", {})
    event_time = event.get("event_time") or datetime.now().isoformat()
    payload["_event_time"] = event_time

    try:
        if event_type == "customer_created":
            handle_customer(conn, payload)

        elif event_type == "asset_appraised":
            handle_asset(conn, payload)

        elif event_type == "loan_application_created":
            cur = execute_query(
                conn,
                """
                SELECT KhachHang_Key
                FROM Dim_KhachHang
                WHERE CMND_CCCD = %s AND IsCurrent = TRUE
                ORDER BY KhachHang_Key DESC
                LIMIT 1
                """,
                (payload.get("CMND_CCCD"),),
            )
            kh = cur.fetchone()
            kh_key = kh.get("khachhang_key") if kh else None
            if kh and "KhachHang_Key" in kh:
                kh_key = kh["KhachHang_Key"]

            ts_key = None
            cmnd = payload.get("CMND_CCCD")
            if cmnd:
                cur = execute_query(
                    conn,
                    """
                    SELECT payload->>'DuongDanAnh' AS duong_dan_anh
                    FROM Raw_Staging_Events
                    WHERE event_type = 'asset_appraised'
                      AND payload->>'CMND_CCCD' = %s
                    ORDER BY COALESCE(event_time, ingestion_time) DESC, staging_id DESC
                    LIMIT 1
                    """,
                    (cmnd,),
                )
                asset_raw = cur.fetchone()
                duong_dan_anh = (asset_raw or {}).get("duong_dan_anh") if asset_raw else None
                if duong_dan_anh:
                    cur = execute_query(
                        conn,
                        """
                        SELECT TaiSan_Key
                        FROM Dim_TaiSan
                        WHERE DuongDanAnh = %s
                        ORDER BY TaiSan_Key DESC
                        LIMIT 1
                        """,
                        (duong_dan_anh,),
                    )
                    ts = cur.fetchone()
                    if ts:
                        ts_key = ts.get("TaiSan_Key") or ts.get("taisan_key")

            handle_loan_application(conn, payload, kh_key, ts_key)

        elif event_type == "loan_approved":
            handle_loan_approved(conn, payload, event_time)

        elif event_type == "loan_rejected":
            handle_loan_rejected(conn, payload, event_time)

        elif event_type == "loan_disbursed":
            handle_loan_disbursed(conn, payload, event_time)

        elif event_type == "repayment_paid":
            handle_repayment(conn, payload, event_time)

        elif event_type == "loan_status_changed":
            handle_status_changed(conn, payload, event_time)

        elif event_type == "cash_recorded":
            handle_cash_recorded(conn, payload, event_time)

        elif event_type == "weather_updated":
            # Weather is best-effort. Failure should not block other event types.
            handle_weather(conn, payload, event_time)

        elif event_type == "opex_recorded":
            handle_opex(conn, payload, event_time)

        elif event_type == "payroll_calculated":
            handle_payroll(conn, payload, event_time)

        else:
            logger.warning("Unknown event_type: %s", event_type)
            return False

        return True

    except Exception as exc:
        logger.error("Error processing %s: %s", event_type, exc, exc_info=True)
        conn.rollback()
        return False


def run_consumer(batch_size: int = 200, batch_timeout_ms: int = 5000, kafka_servers: str | None = None):
    servers = kafka_servers or KAFKA_BOOTSTRAP_SERVERS
    topics = list(KAFKA_TOPICS.values())

    logger.info("Subscribing topics: %s", topics)

    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=servers,
        group_id=os.getenv("KAFKA_GROUP_ID", "pg-sink-consumer"),
        auto_offset_reset=os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        key_deserializer=lambda m: m.decode("utf-8") if m else None,
        max_poll_records=batch_size,
        consumer_timeout_ms=1000,
    )

    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
    )

    conn = get_connection()
    ensure_staging_table(conn)

    processed_total = 0
    error_total = 0
    duplicate_total = 0

    try:
        while True:
            message_batch = consumer.poll(timeout_ms=batch_timeout_ms, max_records=batch_size)
            if not message_batch:
                time.sleep(0.5)
                continue

            batch_count = sum(len(msgs) for msgs in message_batch.values())
            logger.info("Received batch: %s messages", batch_count)

            for tp, messages in message_batch.items():
                for msg in messages:
                    event = msg.value
                    topic = msg.topic
                    event_id = event.get("event_id", "unknown")
                    partition_key = msg.key

                    try:
                        # Step 1: Insert to staging with scheduled_time
                        is_new = insert_staging(conn, event, topic, partition_key)
                    except Exception as exc:
                        logger.error("Staging failed %s: %s", event_id, exc, exc_info=True)
                        conn.rollback()
                        error_total += 1
                        continue

                    if not is_new:
                        duplicate_total += 1
                        continue

                    # Step 2: Immediate Redis publish for real-time dashboard
                    if event.get("event_type") in REALTIME_EVENT_TYPES:
                        try:
                            r.publish(REDIS_CHANNEL, json.dumps(event, ensure_ascii=False))
                        except Exception as exc:
                            logger.error("Redis publish failed: %s", exc)
                    
                    processed_total += 1

            conn.commit()
            consumer.commit()

            # Step 3: Process events that have waited long enough
            process_scheduled_events(conn)
            
            logger.info("Batch committed. Staged=%s Errors=%s Duplicates=%s", processed_total, error_total, duplicate_total)

    except KeyboardInterrupt:
        logger.info("Consumer stopping...")
    except Exception as e:
        logger.error(f"Fatal consumer error: {e}")
    finally:
        consumer.close()
        conn.close()
        try:
            r.close()
        except Exception:
            pass
        logger.info("Final stats: processed=%s errors=%s duplicates=%s", processed_total, error_total, duplicate_total)


def process_scheduled_events(conn):
    """
    Finds events in Raw_Staging_Events that are ready to be processed 
    (scheduled_time <= NOW) and syncs them to Dim/Fact tables.
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT staging_id, event_id, event_type, event_time, source_topic, payload
        FROM Raw_Staging_Events
        WHERE process_status = 'new' AND scheduled_time <= NOW()
        ORDER BY scheduled_time ASC
        LIMIT 100
        """
    )
    ready_events = cur.fetchall()
    
    if not ready_events:
        return

    logger.info("Processing %s scheduled events...", len(ready_events))
    
    for row in ready_events:
        event = {
            "event_id": row["event_id"],
            "event_type": row["event_type"],
            "event_time": row["event_time"].isoformat() if row["event_time"] else None,
            "payload": row["payload"]
        }
        
        success = process_event(conn, event, row["source_topic"])
        
        if success:
            update_staging_status(conn, row["event_id"], "processed")
        else:
            update_staging_status(conn, row["event_id"], "failed", f"Delayed processing error")
    
    conn.commit()
    
    # After committing to DB, notify FastAPI to refresh its baseline snapshot
    try:
        import redis
        r_temp = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
        )
        r_temp.publish(os.getenv("REDIS_CHANNEL", "f88_realtime"), json.dumps({"event_type": "system_reset", "payload": {}}, ensure_ascii=False))
        r_temp.close()
        logger.info("Sent system_reset to Redis to refresh dashboard baseline.")
    except Exception as e:
        logger.error(f"Failed to send system_reset: {e}")


def main():
    parser = argparse.ArgumentParser(description="Kafka -> PostgreSQL batch consumer")
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--timeout", type=int, default=5000)
    parser.add_argument("--kafka", type=str, default=None)
    args = parser.parse_args()

    run_consumer(args.batch_size, args.timeout, args.kafka)


if __name__ == "__main__":
    main()
