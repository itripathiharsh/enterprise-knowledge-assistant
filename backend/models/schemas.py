from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ── Document schemas ──────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    doc_id: str
    doc_name: str
    total_pages: int
    total_chunks: int
    message: str

class DocumentInfo(BaseModel):
    doc_id: str
    doc_name: str
    total_pages: int
    total_chunks: int
    uploaded_at: str
    file_size_kb: float
    version_status: Optional[str] = "current"

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int

class DocumentSummaryResponse(BaseModel):
    doc_id: str
    doc_name: str
    summary: str

# ── Query schemas ─────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(..., description="UUID for conversation session")
    doc_filter: Optional[List[str]] = Field(None, description="Filter by doc_ids")

class ChunkResult(BaseModel):
    text: str
    doc_name: str
    page_number: int
    chunk_index: int
    similarity_score: float

class Source(BaseModel):
    document: str
    doc_id: str
    page: int

class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    chunks: List[ChunkResult]
    confidence: float
    follow_up_questions: List[str]
    session_id: str

# ── Feedback schemas ───────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    feedback: str  # "helpful" | "not_helpful"

# ── Stats schemas ──────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_documents: int
    total_pages: int
    total_chunks: int
    embedding_model: str
    vector_db: str
    recent_queries: List[str]
