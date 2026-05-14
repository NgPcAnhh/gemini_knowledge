import os
import logging
import psycopg2
import psycopg2.extras

logger = logging.getLogger("f88-realtime-db")

def db_conn():
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        dbname=os.getenv("PG_DB", "credit_control"),
        user=os.getenv("PG_USER", "admin"),
        password=os.getenv("PG_PASSWORD", "123456"),
        connect_timeout=5,
    )
    with conn.cursor() as cur:
        cur.execute("SET TIME ZONE 'Asia/Ho_Chi_Minh';")
    conn.commit()
    return conn

def execute_read_query(query: str, params: tuple = ()):
    conn = db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()

def execute_read_one(query: str, params: tuple = ()):
    conn = db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        return cur.fetchone()
    finally:
        conn.close()
