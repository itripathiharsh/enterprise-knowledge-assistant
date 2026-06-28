"""
Cross-encoder re-ranker using ms-marco-MiniLM-L-6-v2.
Takes query + top-K chunks from retrieval, returns re-ranked subset.
Model is ~70MB, downloads once on first use, runs on CPU.
"""
from sentence_transformers import CrossEncoder
from typing import List
from models.schemas import ChunkResult
import logging

logger = logging.getLogger(__name__)

_reranker_model = None

def get_reranker() -> CrossEncoder:
    global _reranker_model
    if _reranker_model is None:
        logger.info("Loading cross-encoder reranker model...")
        _reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker_model

def rerank(query: str, chunks: List[ChunkResult], top_k: int = 5) -> List[ChunkResult]:
    """
    Re-rank chunks using cross-encoder.
    Input: up to top_k*2 chunks from hybrid retrieval.
    Output: top_k chunks re-ordered by cross-encoder score.
    """
    if not chunks:
        return chunks
    
    try:
        model = get_reranker()
        pairs = [(query, chunk.text) for chunk in chunks]
        scores = model.predict(pairs)
        
        # Zip scores with chunks and sort
        scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        reranked = [chunk for _, chunk in scored[:top_k]]
        
        # Update similarity scores to reflect re-ranker scores (normalized)
        min_s, max_s = min(scores), max(scores)
        score_range = max_s - min_s if max_s != min_s else 1
        for i, (score, chunk) in enumerate(scored[:top_k]):
            reranked[i].similarity_score = round(float((score - min_s) / score_range), 4)
        
        return reranked
    except Exception as e:
        logger.warning(f"Re-ranking failed, using original order: {e}")
        return chunks[:top_k]
