"""
consumers/db.py

PostgreSQL helper cho Kafka consumer.
"""

import logging
import psycopg2
import psycopg2.extras

from simulator.config import PG_CONFIG

logger = logging.getLogger(__name__)


def get_connection():
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("SET TIME ZONE 'Asia/Ho_Chi_Minh';")
    conn.commit()
    return conn


def execute_query(conn, query: str, params: tuple | list | None = None):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query, params)
    return cur


def insert_returning_id(conn, query: str, params: tuple | list):
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    return row[0] if row else None


def upsert_and_get_key(conn, check_query: str, check_params: tuple, insert_query: str, insert_params: tuple):
    cur = conn.cursor()
    cur.execute(check_query, check_params)
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(insert_query, insert_params)
    row = cur.fetchone()
    return row[0] if row else None


def table_exists(conn, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE lower(table_name) = lower(%s)
        )
        """,
        (table_name,),
    )
    return bool(cur.fetchone()[0])


def column_exists(conn, table_name: str, column_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE lower(table_name) = lower(%s)
              AND lower(column_name) = lower(%s)
        )
        """,
        (table_name, column_name),
    )
    return bool(cur.fetchone()[0])
