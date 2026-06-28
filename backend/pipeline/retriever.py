from typing import List, Optional, Dict
from pipeline.embedder import Embedder
from storage.chroma_store import ChromaStore
from models.schemas import ChunkResult
from pipeline.bm25_index import get_bm25_index
from pipeline.reranker import rerank
from core.config import settings
import numpy as np

class Retriever:
    def __init__(self, top_k: int = 5, bm25_weight: float = 0.3, semantic_weight: float = 0.7):
        self.top_k = top_k
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.rrf_k = 60  # RRF constant

    def _reciprocal_rank_fusion(self, semantic_results: List, bm25_results: List) -> List[str]:
        """
        Merge semantic and BM25 result lists using RRF.
        Returns ordered list of chunk_ids.
        RRF score = sum(1 / (k + rank)) across all lists.
        """
        scores: Dict[str, float] = {}
        
        for rank, chunk in enumerate(semantic_results):
            cid = chunk["chunk_id"]
            scores[cid] = scores.get(cid, 0) + self.semantic_weight * (1 / (self.rrf_k + rank))
        
        for rank, result in enumerate(bm25_results):
            cid = result["chunk_id"]
            scores[cid] = scores.get(cid, 0) + self.bm25_weight * (1 / (self.rrf_k + rank))
        
        return sorted(scores, key=lambda x: scores[x], reverse=True)[:self.top_k * 2]

    def retrieve(self, question: str, user_id: str = None,
                 doc_filter: List[str] = None) -> List[ChunkResult]:
        query_embedding = Embedder.embed_single(question)
        
        # Build ChromaDB where filter
        where_clauses = []
        if user_id:
            where_clauses.append({"user_id": {"$eq": user_id}})
        if doc_filter:
            if len(doc_filter) == 1:
                where_clauses.append({"doc_id": {"$eq": doc_filter[0]}})
            else:
                where_clauses.append({"doc_id": {"$in": doc_filter}})
                
        where = {"$and": where_clauses} if len(where_clauses) > 1 else (where_clauses[0] if where_clauses else None)
        
        # Semantic search: get top_k * 2 candidates for reranking
        chroma_results = ChromaStore.query(
            query_embedding=query_embedding,
            n_results=self.top_k * 2,
            where=where
        )
        
        if not chroma_results["documents"] or not chroma_results["documents"][0]:
            return []
        
        # Format semantic results
        semantic_list = [
            {"chunk_id": id_, "text": doc, "metadata": meta, "distance": dist}
            for id_, doc, meta, dist in zip(
                chroma_results["ids"][0],
                chroma_results["documents"][0],
                chroma_results["metadatas"][0],
                chroma_results["distances"][0]
            )
        ]
        
        # BM25 search
        bm25_list = get_bm25_index().search(question, top_k=self.top_k * 2)
        
        # RRF fusion
        fused_ids = self._reciprocal_rank_fusion(
            [{"chunk_id": s["chunk_id"]} for s in semantic_list],
            bm25_list
        )
        
        # Build final results using metadata from semantic search
        sem_map = {s["chunk_id"]: s for s in semantic_list}
        candidates = []
        for chunk_id in fused_ids[:self.top_k * 2]:
            if chunk_id in sem_map:
                s = sem_map[chunk_id]
                similarity = 1.0 - s["distance"]
                candidates.append(ChunkResult(
                    text=s["text"],
                    doc_name=s["metadata"].get("doc_name", "Unknown"),
                    page_number=s["metadata"].get("page_number", 0),
                    chunk_index=s["metadata"].get("chunk_index", 0),
                    similarity_score=round(similarity, 4)
                ))
        
        if settings.ENABLE_RERANKING:
            return rerank(question, candidates, top_k=self.top_k)
        
        return candidates[:self.top_k]

    def get_confidence(self, chunks: List[ChunkResult]) -> float:
        if not chunks:
            return 0.0
        return round(chunks[0].similarity_score, 4)
