"""
SQLite user store. Table: users(id, email, hashed_password, created_at)
"""
import sqlite3
import uuid
from pathlib import Path
from core.config import settings

DB_PATH = settings.BASE_DIR / "data" / "users.db"

def _conn():
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c

def init_users_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def create_user(email: str, hashed_password: str) -> dict:
    user_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO users (id, email, hashed_password) VALUES (?, ?, ?)",
            (user_id, email, hashed_password)
        )
        conn.commit()
    return {"id": user_id, "email": email}

def get_user_by_email(email: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None

def get_user_by_id(user_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None
