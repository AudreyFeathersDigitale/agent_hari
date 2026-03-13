import os
import sqlite3
from typing import List, Dict

DB_DIR = "db"
DB_PATH = os.path.join(DB_DIR, "memory.db")


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


def add_message(user_id: str, role: str, content: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_history (user_id, role, content)
        VALUES (?, ?, ?)
        """,
        (user_id, role, content),
    )

    conn.commit()
    conn.close()


def get_history(user_id: str, limit: int = 10) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content, created_at
        FROM chat_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    rows = list(reversed(rows))

    return [
        {
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def clear_history(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM chat_history
        WHERE user_id = ?
        """,
        (user_id,),
    )

    conn.commit()
    conn.close()
