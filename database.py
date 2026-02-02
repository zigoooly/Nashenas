import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        nickname TEXT NOT NULL
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

def get_nickname(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT nickname FROM users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def set_nickname(user_id, nickname):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO users (user_id, nickname)
    VALUES (%s, %s)
    ON CONFLICT (user_id)
    DO UPDATE SET nickname=EXCLUDED.nickname
    """, (user_id, nickname))
    conn.commit()
    cur.close()
    conn.close()
