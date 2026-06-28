"""
BM25 index over all document chunks.
Stored as a pickle file alongside ChromaDB.
Rebuilt on every new document ingestion.
All text is lowercased and tokenized by whitespace for simplicity.
"""
import pickle
from pathlib import Path
from typing import List, Dict
from rank_bm25 import BM25Okapi
from core.config import settings

BM25_PATH = settings.BASE_DIR / "data" / "bm25_index.pkl"

def _tokenize(text: str) -> List[str]:
    return text.lower().split()

class BM25Index:
    def __init__(self):
        self.bm25: BM25Okapi | None = None
        self.chunk_ids: List[str] = []  # Parallel to BM25 corpus
        self.corpus: List[List[str]] = []

    def build(self, chunks: List[Dict]):
        """
        chunks: [{"id": "doc_id_0", "text": "..."}, ...]
        """
        self.chunk_ids = [c["id"] for c in chunks]
        self.corpus = [_tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(self.corpus)

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Returns [{"chunk_id": str, "score": float}] sorted desc."""
        if self.bm25 is None:
            return []
        tokens = _tokenize(query)
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [{"chunk_id": self.chunk_ids[i], "score": float(s)} for i, s in ranked if s > 0]

    def save(self):
        with open(BM25_PATH, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls) -> "BM25Index":
        if BM25_PATH.exists():
            with open(BM25_PATH, "rb") as f:
                return pickle.load(f)
        return cls()

# Global singleton
_bm25_index: BM25Index | None = None

def get_bm25_index() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index.load()
    return _bm25_index

def rebuild_index():
    """Called after every document ingestion to rebuild the BM25 index."""
    from storage.chroma_store import ChromaStore
    col = ChromaStore.get_collection()
    count = col.count()
    if count == 0:
        return
    results = col.get(include=["documents"], limit=count)
    chunks = [{"id": id_, "text": doc}
              for id_, doc in zip(results["ids"], results["documents"])]
    idx = BM25Index()
    idx.build(chunks)
    idx.save()
    global _bm25_index
    _bm25_index = idx
