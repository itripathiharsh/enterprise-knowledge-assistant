from sentence_transformers import SentenceTransformer
from typing import List
from core.config import settings
import numpy as np

class Embedder:
    _model = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return cls._model

    @classmethod
    def embed(cls, texts: List[str]) -> List[List[float]]:
        model = cls.get_model()
        embeddings = model.encode(texts, show_progress_bar=False, batch_size=64)
        return embeddings.tolist()

    @classmethod
    def embed_single(cls, text: str) -> List[float]:
        return cls.embed([text])[0]

    @classmethod
    def cosine_similarity(cls, a: List[float], b: List[float]) -> float:
        a_np = np.array(a)
        b_np = np.array(b)
        denom = np.linalg.norm(a_np) * np.linalg.norm(b_np)
        if denom == 0:
            return 0.0
        return float(np.dot(a_np, b_np) / denom)
