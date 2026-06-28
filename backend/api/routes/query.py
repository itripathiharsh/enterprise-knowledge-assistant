from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from models.schemas import AskRequest, AskResponse, FeedbackRequest
from rag.engine import RAGEngine
from api.auth import get_current_user
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()
engine = RAGEngine()

# In-memory feedback store (replace with DB in production)
_feedback_log = []
# In-memory recent queries store
_recent_queries = []

@router.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        _recent_queries.append(request.question)
        if len(_recent_queries) > 20:
            _recent_queries.pop(0)
            
        return await engine.answer(
            question=request.question,
            session_id=request.session_id,
            user_id=current_user["id"],
            doc_filter=request.doc_filter
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(500, "Failed to generate answer.")

@router.post("/ask/stream")
async def ask_stream(
    request: AskRequest,
    current_user: dict = Depends(get_current_user)
):
    """Server-Sent Events streaming endpoint."""
    try:
        _recent_queries.append(request.question)
        if len(_recent_queries) > 20:
            _recent_queries.pop(0)
        
        return StreamingResponse(
            engine.answer_stream(
                question=request.question,
                session_id=request.session_id,
                user_id=current_user["id"],
                doc_filter=request.doc_filter
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Stream failed: {e}")
        raise HTTPException(500, "Failed to stream answer.")

@router.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    _feedback_log.append(request.dict())
    logger.info(f"Feedback: {request.feedback} for session {request.session_id}")
    return {"message": "Feedback recorded."}

@router.get("/recent-queries")
def get_recent_queries():
    return {"queries": list(reversed(_recent_queries[-10:]))}

@router.get("/history")
def get_history(current_user: dict = Depends(get_current_user)):
    from rag.memory import MemoryManager
    history = MemoryManager.get_history(current_user["id"])
    return {"history": history}

@router.delete("/history")
def clear_history(current_user: dict = Depends(get_current_user)):
    from rag.memory import MemoryManager
    MemoryManager.clear(current_user["id"])
    return {"status": "cleared"}
