"""
SQLite-backed conversation session storage.
Replaces the in-memory dict in rag/memory.py.
Database: data/sessions.db (created automatically on first run).
"""
import sqlite3
import json
from pathlib import Path
from core.config import settings
from typing import List, Dict

DB_PATH = settings.BASE_DIR / "data" / "sessions.db"

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist. Called on app startup."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON sessions(session_id)")
        conn.commit()

def add_turn(session_id: str, question: str, answer: str, max_turns: int = 6):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, "user", question)
        )
        conn.execute(
            "INSERT INTO sessions (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, "assistant", answer)
        )
        conn.commit()
        
        # Prune: keep only last max_turns*2 rows for this session
        conn.execute("""
            DELETE FROM sessions WHERE session_id = ? AND rowid NOT IN (
                SELECT rowid FROM sessions WHERE session_id = ?
                ORDER BY created_at DESC LIMIT ?
            )
        """, (session_id, session_id, max_turns * 2))
        conn.commit()

def get_history(session_id: str) -> List[Dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM sessions WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,)
        ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in rows]

def clear_session(session_id: str):
    with _get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
