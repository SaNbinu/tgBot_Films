import sqlite3
from datetime import datetime

DB_PATH = "films.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS films (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        status TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_film(user_id: int, name: str, status: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO films (user_id, name, status, date)
        VALUES (?, ?, ?, ?)
    """, (user_id, name, status, str(datetime.now())))

    conn.commit()
    conn.close()


def get_films(user_id: int, status: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, date FROM films
        WHERE user_id=? AND status=?
        ORDER BY id DESC
    """, (user_id, status))

    rows = cur.fetchall()
    conn.close()

    return rows