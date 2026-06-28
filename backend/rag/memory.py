"""
Conversation memory manager — SQLite backed (V2).
Drop-in replacement for the V1 in-memory store.
All callers use the same interface: add_turn(), get_history().
"""
from storage.session_store import add_turn, get_history, clear_session
from core.config import settings

class MemoryManager:
    @classmethod
    def add_turn(cls, session_id: str, question: str, answer: str):
        add_turn(session_id, question, answer, max_turns=settings.MAX_MEMORY_TURNS)

    @classmethod
    def get_history(cls, session_id: str):
        return get_history(session_id)

    @classmethod
    def clear(cls, session_id: str):
        clear_session(session_id)
