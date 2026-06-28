from fastapi import APIRouter, HTTPException, Depends
from models.schemas import StatsResponse
from storage.chroma_store import ChromaStore
from core.config import settings
from api.routes.query import _recent_queries
from api.auth import get_current_user
import json
from pathlib import Path

router = APIRouter()

@router.get("/", response_model=StatsResponse)
def get_stats(current_user: dict = Depends(get_current_user)):
    chroma_stats = ChromaStore.get_stats(user_id=current_user["id"])
    return StatsResponse(
        total_documents=chroma_stats["total_documents"],
        total_pages=chroma_stats["total_pages"],
        total_chunks=chroma_stats["total_chunks"],
        embedding_model=settings.EMBEDDING_MODEL,
        vector_db="ChromaDB (local persistent)",
        recent_queries=list(reversed(_recent_queries[-5:]))
    )

@router.post("/evaluate")
async def run_evaluation(current_user: dict = Depends(get_current_user)):
    """
    Run evaluation against test cases.
    Returns per-question results + aggregate metrics.
    Only runs if documents are already ingested.
    """
    from evaluation.evaluator import evaluate
    
    if ChromaStore.get_collection().count() == 0:
        raise HTTPException(400, "No documents ingested. Upload documents first.")
    
    try:
        results = await evaluate()  # From evaluation/evaluator.py
        avg_sim = sum(r["semantic_similarity"] for r in results) / len(results)
        source_acc = sum(r["source_found"] for r in results) / len(results)
        
        return {
            "summary": {
                "total_cases": len(results),
                "avg_semantic_similarity": round(avg_sim, 4),
                "source_attribution_accuracy": round(source_acc, 4),
                "avg_confidence": round(sum(r["confidence"] for r in results) / len(results), 4)
            },
            "results": results
        }
    except Exception as e:
        raise HTTPException(500, f"Evaluation failed: {e}")

@router.get("/evaluate/last")
def get_last_evaluation(current_user: dict = Depends(get_current_user)):
    """Return cached last evaluation result from disk."""
    cache_path = Path("data/last_eval.json")
    if not cache_path.exists():
        raise HTTPException(404, "No evaluation has been run yet.")
    return json.loads(cache_path.read_text())
