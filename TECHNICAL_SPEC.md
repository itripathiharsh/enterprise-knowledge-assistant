# Enterprise Knowledge Assistant — Complete Technical Specification

> **This document is the single source of truth for building the entire project end-to-end.**
> Every component, file, API contract, data model, prompt, and config is defined here.
> An AI coding agent should be able to build the full system from this document alone with zero clarifying questions.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Repository Structure](#3-repository-structure)
4. [Architecture Overview](#4-architecture-overview)
5. [Data Flow](#5-data-flow)
6. [Backend — FastAPI](#6-backend--fastapi)
7. [AI Pipeline — RAG Engine](#7-ai-pipeline--rag-engine)
8. [Frontend — Next.js](#8-frontend--nextjs)
9. [API Contract](#9-api-contract)
10. [Database & Storage Schemas](#10-database--storage-schemas)
11. [Prompts](#11-prompts)
12. [Environment Variables](#12-environment-variables)
13. [Configuration Files](#13-configuration-files)
14. [Setup & Run Instructions](#14-setup--run-instructions)
15. [Evaluation Framework](#15-evaluation-framework)
16. [README Content](#16-readme-content)
17. [Design Decisions & Assumptions](#17-design-decisions--assumptions)
18. [Limitations & Future Work](#18-limitations--future-work)

---

## 1. Project Overview

**Name:** Enterprise Knowledge Assistant  
**Purpose:** Allow employees to ask natural language questions and get accurate, cited answers from a company's internal PDF document library.  
**Core Pattern:** Retrieval-Augmented Generation (RAG)

### Feature Set

**Core (Required)**
- PDF upload and ingestion pipeline
- Text extraction, chunking, embedding, vector storage
- Semantic search + RAG answer generation
- Source citations (document name + page number)
- Chat UI with question input and answer display

**Bonus (Implemented)**
- Conversation memory (multi-turn context)
- Confidence score (cosine similarity of top chunk)
- Show retrieved chunks (expandable)
- Suggested follow-up questions
- Copy answer button
- Answer streaming (SSE)
- Document statistics dashboard
- Thumbs up/down feedback
- Claude-like thinking status indicators
- Dark/Light mode
- Recent queries
- Document summary button
- Upload additional documents anytime

---

## 2. Tech Stack

### Backend
| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.11 | Assignment preference |
| Web Framework | FastAPI | Async, fast, auto-docs |
| PDF Parsing | PyMuPDF (fitz) | Fast, accurate, free |
| Text Chunking | Custom (recursive) | Full control, no framework lock-in |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Free, runs locally, 384-dim |
| Vector DB | ChromaDB (persistent local) | Free, no server needed, persistent |
| LLM | Google Gemini 1.5 Flash via `google-generativeai` | Free tier: 15 RPM / 1M TPM |
| Streaming | FastAPI StreamingResponse + SSE | Native async support |
| Storage | Local filesystem + SQLite (via ChromaDB) | Zero cost |

### Frontend
| Component | Choice | Reason |
|-----------|--------|--------|
| Framework | Next.js 14 (App Router) | React, SSR, free on Vercel |
| Styling | Tailwind CSS | Utility-first, no cost |
| UI Components | shadcn/ui | Free, beautiful, accessible |
| Icons | Lucide React | Free |
| HTTP Client | Axios + native fetch for SSE | Simple |
| State | React useState/useReducer | No extra libs needed |
| Theme | next-themes | Dark/light mode |

### DevOps
| Component | Choice |
|-----------|--------|
| Local Dev | `uvicorn` + `npm run dev` |
| CORS | FastAPI CORSMiddleware |
| Env Vars | `.env` files |

> **Cost = $0.** Gemini free tier is sufficient. All other tools are open source and run locally.

---

## 3. Repository Structure

```
enterprise-knowledge-assistant/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py       # Upload, list, delete, summarize
│   │   │   ├── query.py           # Ask, stream, feedback
│   │   │   └── stats.py           # Dashboard stats
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Settings, env vars
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── logging.py             # Logger setup
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── ingestion.py           # PDF load → chunk → embed → store
│   │   ├── chunker.py             # Text chunking logic
│   │   ├── embedder.py            # Sentence transformer wrapper
│   │   └── retriever.py           # ChromaDB search wrapper
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── engine.py              # RAG orchestrator
│   │   ├── prompts.py             # All prompt templates
│   │   ├── gemini_client.py       # Gemini API wrapper
│   │   └── memory.py              # Conversation memory manager
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models
│   ├── storage/
│   │   ├── chroma_store.py        # ChromaDB client singleton
│   │   └── file_store.py          # Uploaded file management
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── evaluator.py           # Evaluation runner
│   │   └── test_cases.json        # Test Q&A pairs
│   ├── data/
│   │   ├── uploads/               # Raw uploaded PDFs
│   │   └── chroma_db/             # ChromaDB persistent storage
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx             # Root layout, theme provider
│   │   ├── page.tsx               # Main chat page
│   │   ├── globals.css
│   │   └── providers.tsx          # Context providers
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx     # Message list
│   │   │   ├── ChatInput.tsx      # Input bar + send
│   │   │   ├── MessageBubble.tsx  # Single message
│   │   │   ├── ThinkingIndicator.tsx  # Animated status steps
│   │   │   ├── SourceCard.tsx     # Citation card
│   │   │   ├── ChunkViewer.tsx    # Retrieved chunks expandable
│   │   │   ├── FollowUpSuggestions.tsx
│   │   │   └── FeedbackButtons.tsx
│   │   ├── documents/
│   │   │   ├── DocumentUpload.tsx # Drag & drop upload
│   │   │   ├── DocumentList.tsx   # Uploaded docs list
│   │   │   └── DocumentCard.tsx   # Single doc with summary btn
│   │   ├── dashboard/
│   │   │   └── StatsPanel.tsx     # Document statistics
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx        # Left sidebar
│   │   │   ├── Header.tsx         # Top bar with theme toggle
│   │   │   └── RecentQueries.tsx
│   │   └── ui/                    # shadcn/ui components
│   ├── lib/
│   │   ├── api.ts                 # API client functions
│   │   ├── types.ts               # TypeScript interfaces
│   │   ├── utils.ts               # Helpers
│   │   └── constants.ts           # API base URL etc
│   ├── hooks/
│   │   ├── useChat.ts             # Chat state management
│   │   ├── useDocuments.ts        # Document state
│   │   └── useStream.ts           # SSE streaming hook
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── .env.local.example
│
├── docs/
│   └── architecture.png           # Architecture diagram (generate separately)
│
├── docker-compose.yml             # Optional local orchestration
├── README.md
└── TECHNICAL_SPEC.md              # This file
```

---

## 4. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────┐  │
│  │ ChatUI   │  │ DocumentMgmt │  │ Dashboard │  │ Sidebar  │  │
│  └────┬─────┘  └──────┬───────┘  └─────┬─────┘  └──────────┘  │
└───────┼───────────────┼────────────────┼────────────────────────┘
        │ REST/SSE      │ multipart/form │ REST
        ▼               ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  /query      │  │  /documents  │  │  /stats               │ │
│  │  /ask        │  │  /upload     │  │                       │ │
│  │  /stream     │  │  /summarize  │  │                       │ │
│  │  /feedback   │  │  /delete     │  │                       │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────────────────┘ │
│         │                 │                                      │
│  ┌──────▼──────────────────▼──────────────────────────────────┐ │
│  │                    RAG Engine                               │ │
│  │  ┌───────────┐  ┌──────────────┐  ┌───────────────────┐   │ │
│  │  │ Retriever │  │ Gemini Client│  │ Memory Manager    │   │ │
│  │  └─────┬─────┘  └──────┬───────┘  └───────────────────┘   │ │
│  └────────┼───────────────┼─────────────────────────────────┘  │
│           │               │                                      │
│  ┌────────▼───────┐  ┌────▼───────────────────────────────┐    │
│  │  ChromaDB      │  │  Google Gemini 1.5 Flash API        │    │
│  │  (local disk)  │  │  (free tier, external)              │    │
│  └────────────────┘  └─────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Ingestion Pipeline                          │   │
│  │  PDF Upload → PyMuPDF → Chunker → Embedder → ChromaDB   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow

### 5.1 Document Ingestion Flow

```
User uploads PDF
       ↓
FastAPI receives multipart file
       ↓
Save raw PDF to data/uploads/{doc_id}.pdf
       ↓
PyMuPDF extracts text per page (preserves page numbers)
       ↓
Chunker splits text into overlapping chunks
  - chunk_size: 512 tokens (~400 words)
  - chunk_overlap: 64 tokens
  - strategy: recursive character split
       ↓
Each chunk gets metadata:
  { doc_id, doc_name, page_number, chunk_index, total_chunks }
       ↓
SentenceTransformer embeds each chunk → 384-dim vector
       ↓
ChromaDB stores: vector + text + metadata
       ↓
Return { doc_id, doc_name, total_pages, total_chunks }
```

### 5.2 Query / Answer Flow

```
User sends question + session_id
       ↓
Memory Manager fetches last N turns for session_id
       ↓
Query is embedded → 384-dim vector
       ↓
ChromaDB semantic search → Top 5 chunks
  (optional: filter by doc_id if user selected specific doc)
       ↓
Confidence score = cosine similarity of top chunk
       ↓
Build prompt:
  [System] + [Conversation History] + [Retrieved Chunks] + [Question]
       ↓
Gemini 1.5 Flash generates answer (streaming via SSE)
       ↓
Post-process: extract sources, generate follow-up suggestions
       ↓
Store turn in memory
       ↓
Return: { answer, sources, chunks, confidence, follow_ups }
```

---

## 6. Backend — FastAPI

### 6.1 `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import documents, query, stats
from core.config import settings
from storage.chroma_store import ChromaStore

app = FastAPI(
    title="Enterprise Knowledge Assistant API",
    version="1.0.0",
    description="RAG-based document Q&A system"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ChromaDB on startup
@app.on_event("startup")
async def startup():
    ChromaStore.initialize()

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

### 6.2 `backend/core/config.py`

```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma_db"
    
    # RAG
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    TOP_K: int = 5
    
    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Memory
    MAX_MEMORY_TURNS: int = 6  # last 6 turns = 3 exchanges
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
```

### 6.3 `backend/models/schemas.py`

```python
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
```

### 6.4 `backend/storage/chroma_store.py`

```python
import chromadb
from chromadb.config import Settings as ChromaSettings
from core.config import settings
from typing import List, Dict, Any, Optional

class ChromaStore:
    _client = None
    _collection = None
    COLLECTION_NAME = "documents"

    @classmethod
    def initialize(cls):
        cls._client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        cls._collection = cls._client.get_or_create_collection(
            name=cls.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    @classmethod
    def get_collection(cls):
        if cls._collection is None:
            cls.initialize()
        return cls._collection

    @classmethod
    def add_chunks(cls, ids: List[str], embeddings: List[List[float]],
                   documents: List[str], metadatas: List[Dict]):
        col = cls.get_collection()
        # ChromaDB add in batches of 500 to avoid memory issues
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            col.add(
                ids=ids[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )

    @classmethod
    def query(cls, query_embedding: List[float], n_results: int = 5,
              where: Optional[Dict] = None) -> Dict:
        col = cls.get_collection()
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances", "embeddings"]
        }
        if where:
            kwargs["where"] = where
        return col.query(**kwargs)

    @classmethod
    def delete_by_doc_id(cls, doc_id: str):
        col = cls.get_collection()
        col.delete(where={"doc_id": {"$eq": doc_id}})

    @classmethod
    def get_stats(cls) -> Dict:
        col = cls.get_collection()
        count = col.count()
        # Get unique doc metadata
        if count == 0:
            return {"total_chunks": 0, "total_pages": 0, "total_documents": 0, "documents": []}
        
        results = col.get(include=["metadatas"], limit=count)
        metadatas = results["metadatas"]
        
        docs = {}
        for m in metadatas:
            doc_id = m.get("doc_id")
            if doc_id not in docs:
                docs[doc_id] = {
                    "doc_id": doc_id,
                    "doc_name": m.get("doc_name"),
                    "pages": set()
                }
            docs[doc_id]["pages"].add(m.get("page_number", 0))
        
        total_pages = sum(len(d["pages"]) for d in docs.values())
        return {
            "total_chunks": count,
            "total_pages": total_pages,
            "total_documents": len(docs),
            "documents": list(docs.values())
        }
```

### 6.5 `backend/storage/file_store.py`

```python
import json
import uuid
from pathlib import Path
from datetime import datetime
from core.config import settings

MANIFEST_PATH = settings.UPLOAD_DIR / "manifest.json"

def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text())

def save_manifest(manifest: dict):
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

def register_document(doc_name: str, total_pages: int, total_chunks: int,
                       file_size_kb: float) -> str:
    doc_id = str(uuid.uuid4())
    manifest = load_manifest()
    manifest[doc_id] = {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "file_size_kb": file_size_kb,
        "uploaded_at": datetime.utcnow().isoformat()
    }
    save_manifest(manifest)
    return doc_id

def get_all_documents() -> list:
    return list(load_manifest().values())

def get_document(doc_id: str) -> dict | None:
    return load_manifest().get(doc_id)

def delete_document(doc_id: str):
    manifest = load_manifest()
    if doc_id in manifest:
        del manifest[doc_id]
        save_manifest(manifest)
    pdf_path = settings.UPLOAD_DIR / f"{doc_id}.pdf"
    if pdf_path.exists():
        pdf_path.unlink()

def get_pdf_path(doc_id: str) -> Path:
    return settings.UPLOAD_DIR / f"{doc_id}.pdf"
```

### 6.6 `backend/pipeline/chunker.py`

```python
from typing import List, Dict
import re

class RecursiveChunker:
    """
    Recursive character-based text splitter.
    Splits on paragraphs → sentences → words to preserve semantic boundaries.
    """
    
    SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        if not separators:
            return [text]
        
        separator = separators[0]
        remaining = separators[1:]
        
        if separator == "":
            splits = list(text)
        else:
            splits = text.split(separator)
        
        good_splits = []
        current = ""
        
        for split in splits:
            split_with_sep = split + (separator if separator != "" else "")
            if len(current) + len(split_with_sep) <= self.chunk_size:
                current += split_with_sep
            else:
                if current:
                    good_splits.append(current.strip())
                if len(split_with_sep) > self.chunk_size and remaining:
                    sub_splits = self._split_text(split_with_sep, remaining)
                    good_splits.extend(sub_splits)
                    current = ""
                else:
                    current = split_with_sep
        
        if current.strip():
            good_splits.append(current.strip())
        
        return good_splits

    def chunk(self, text: str) -> List[str]:
        raw_chunks = self._split_text(text, self.SEPARATORS)
        
        # Apply overlap: each chunk includes tail of previous chunk
        if self.chunk_overlap == 0 or len(raw_chunks) <= 1:
            return [c for c in raw_chunks if c.strip()]
        
        chunks_with_overlap = []
        for i, chunk in enumerate(raw_chunks):
            if i == 0:
                chunks_with_overlap.append(chunk)
            else:
                overlap_text = raw_chunks[i-1][-self.chunk_overlap:]
                chunks_with_overlap.append(overlap_text + " " + chunk)
        
        return [c for c in chunks_with_overlap if len(c.strip()) > 20]

    def chunk_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        Input: [{"page_number": 1, "text": "..."}]
        Output: [{"page_number": 1, "text": "...", "chunk_index": 0}]
        """
        result = []
        chunk_index = 0
        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"].strip()
            if not page_text:
                continue
            chunks = self.chunk(page_text)
            for chunk in chunks:
                result.append({
                    "page_number": page_num,
                    "text": chunk,
                    "chunk_index": chunk_index
                })
                chunk_index += 1
        return result
```

### 6.7 `backend/pipeline/embedder.py`

```python
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
```

### 6.8 `backend/pipeline/ingestion.py`

```python
import fitz  # PyMuPDF
import uuid
from pathlib import Path
from typing import List, Dict
from pipeline.chunker import RecursiveChunker
from pipeline.embedder import Embedder
from storage.chroma_store import ChromaStore
from storage.file_store import register_document
from core.config import settings
import logging

logger = logging.getLogger(__name__)

def extract_pages(pdf_path: Path) -> List[Dict]:
    """Extract text from each page of a PDF."""
    pages = []
    doc = fitz.open(str(pdf_path))
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        pages.append({
            "page_number": page_num + 1,  # 1-indexed
            "text": text
        })
    doc.close()
    return pages

def ingest_pdf(file_bytes: bytes, original_filename: str) -> Dict:
    """
    Full ingestion pipeline:
    1. Save PDF
    2. Extract pages
    3. Chunk
    4. Embed
    5. Store in ChromaDB
    6. Register in manifest
    Returns document info dict.
    """
    # Generate doc_id and save file
    doc_id = str(uuid.uuid4())
    pdf_path = settings.UPLOAD_DIR / f"{doc_id}.pdf"
    pdf_path.write_bytes(file_bytes)
    
    file_size_kb = len(file_bytes) / 1024
    
    logger.info(f"Ingesting {original_filename} ({file_size_kb:.1f} KB)")
    
    # Extract
    pages = extract_pages(pdf_path)
    total_pages = len(pages)
    
    # Chunk
    chunker = RecursiveChunker(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    chunks = chunker.chunk_pages(pages)
    
    if not chunks:
        raise ValueError(f"No text could be extracted from {original_filename}")
    
    # Embed
    texts = [c["text"] for c in chunks]
    embeddings = Embedder.embed(texts)
    
    # Prepare ChromaDB records
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "doc_id": doc_id,
            "doc_name": original_filename,
            "page_number": c["page_number"],
            "chunk_index": c["chunk_index"]
        }
        for c in chunks
    ]
    
    # Store
    ChromaStore.add_chunks(ids=ids, embeddings=embeddings,
                           documents=texts, metadatas=metadatas)
    
    # Register in manifest
    register_document(
        doc_name=original_filename,
        total_pages=total_pages,
        total_chunks=len(chunks),
        file_size_kb=round(file_size_kb, 2)
    )
    
    # Update manifest with correct doc_id
    from storage.file_store import load_manifest, save_manifest
    manifest = load_manifest()
    # Find the newly added entry (last added)
    for k, v in manifest.items():
        if v["doc_name"] == original_filename and "doc_id" not in v:
            manifest[k]["doc_id"] = doc_id
            break
    # Actually: fix register_document to accept doc_id
    # See corrected version below
    
    logger.info(f"Ingested {len(chunks)} chunks from {total_pages} pages")
    
    return {
        "doc_id": doc_id,
        "doc_name": original_filename,
        "total_pages": total_pages,
        "total_chunks": len(chunks)
    }
```

> **Note for agent:** Update `storage/file_store.py::register_document` to accept `doc_id` as parameter instead of generating it internally, since `ingestion.py` generates the doc_id to use as both the PDF filename and ChromaDB metadata key. Pass `doc_id` from `ingest_pdf` to `register_document`.

### 6.9 `backend/pipeline/retriever.py`

```python
from typing import List, Optional, Dict
from pipeline.embedder import Embedder
from storage.chroma_store import ChromaStore
from models.schemas import ChunkResult
import numpy as np

class Retriever:
    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def retrieve(self, question: str,
                 doc_filter: Optional[List[str]] = None) -> List[ChunkResult]:
        query_embedding = Embedder.embed_single(question)
        
        where = None
        if doc_filter:
            if len(doc_filter) == 1:
                where = {"doc_id": {"$eq": doc_filter[0]}}
            else:
                where = {"doc_id": {"$in": doc_filter}}
        
        results = ChromaStore.query(
            query_embedding=query_embedding,
            n_results=self.top_k,
            where=where
        )
        
        chunks = []
        if not results["documents"] or not results["documents"][0]:
            return chunks
        
        for i, (text, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            # ChromaDB cosine distance = 1 - cosine_similarity
            similarity = 1.0 - distance
            chunks.append(ChunkResult(
                text=text,
                doc_name=metadata.get("doc_name", "Unknown"),
                page_number=metadata.get("page_number", 0),
                chunk_index=metadata.get("chunk_index", 0),
                similarity_score=round(similarity, 4)
            ))
        
        # Sort by similarity descending
        chunks.sort(key=lambda x: x.similarity_score, reverse=True)
        return chunks

    def get_confidence(self, chunks: List[ChunkResult]) -> float:
        if not chunks:
            return 0.0
        return round(chunks[0].similarity_score, 4)
```

### 6.10 `backend/rag/memory.py`

```python
from typing import List, Dict
from collections import defaultdict
from core.config import settings

class MemoryManager:
    """
    In-memory conversation store keyed by session_id.
    Each session stores a list of {role, content} dicts.
    Persists only for the lifetime of the server process.
    """
    _store: Dict[str, List[Dict]] = defaultdict(list)

    @classmethod
    def add_turn(cls, session_id: str, question: str, answer: str):
        cls._store[session_id].append({"role": "user", "content": question})
        cls._store[session_id].append({"role": "assistant", "content": answer})
        # Keep only last MAX_MEMORY_TURNS messages
        max_msgs = settings.MAX_MEMORY_TURNS * 2
        if len(cls._store[session_id]) > max_msgs:
            cls._store[session_id] = cls._store[session_id][-max_msgs:]

    @classmethod
    def get_history(cls, session_id: str) -> List[Dict]:
        return cls._store.get(session_id, [])

    @classmethod
    def clear(cls, session_id: str):
        if session_id in cls._store:
            del cls._store[session_id]
```

### 6.11 `backend/rag/gemini_client.py`

```python
import google.generativeai as genai
from core.config import settings
from typing import Generator

genai.configure(api_key=settings.GEMINI_API_KEY)

_model = genai.GenerativeModel(settings.GEMINI_MODEL)

def generate(prompt: str, system: str = "") -> str:
    """Non-streaming generation."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    response = _model.generate_content(full_prompt)
    return response.text

def generate_stream(prompt: str, system: str = "") -> Generator[str, None, None]:
    """Streaming generation — yields text chunks."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    response = _model.generate_content(full_prompt, stream=True)
    for chunk in response:
        if chunk.text:
            yield chunk.text
```

### 6.12 `backend/rag/prompts.py`

```python
# All prompts are defined here. Do not inline prompts elsewhere.

RAG_SYSTEM_PROMPT = """You are an Enterprise Knowledge Assistant. Your job is to answer employee questions accurately using ONLY the provided document excerpts.

Rules:
1. Answer ONLY based on the provided context. Do not use external knowledge.
2. If the answer is not found in the context, respond with exactly: "I could not find information about this in the available documents. Please check the relevant source documents directly or contact HR/the relevant team."
3. Be concise and direct. No filler text.
4. Always maintain a professional, helpful tone.
5. When you reference specific information, naturally indicate which document it came from.
6. Do not make up page numbers or document names. Use only what is provided."""

RAG_USER_TEMPLATE = """Conversation History:
{history}

Retrieved Document Excerpts:
{context}

Employee Question: {question}

Answer:"""

FOLLOW_UP_PROMPT = """Given this Q&A exchange about enterprise documents:

Question: {question}
Answer: {answer}

Generate exactly 3 natural follow-up questions an employee might ask next. 
Return ONLY a JSON array of 3 strings, nothing else.
Example: ["What is the appeal process?", "How many days notice is required?", "Does this apply to contractors?"]"""

SUMMARY_PROMPT = """You are summarizing an internal enterprise document for employees.

Document name: {doc_name}
Document content (excerpts from all pages):
{content}

Provide a concise summary (150-200 words) covering:
1. What this document is about
2. Key policies, procedures, or information it contains  
3. Who it applies to

Be factual and direct."""
```

### 6.13 `backend/rag/engine.py`

```python
import json
import logging
from typing import List, Optional, AsyncGenerator
from pipeline.retriever import Retriever
from rag.gemini_client import generate, generate_stream
from rag.prompts import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE, FOLLOW_UP_PROMPT
from rag.memory import MemoryManager
from models.schemas import AskResponse, Source, ChunkResult

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        self.retriever = Retriever()

    def _build_context(self, chunks: List[ChunkResult]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(
                f"[Excerpt {i} | Source: {chunk.doc_name}, Page {chunk.page_number}]\n{chunk.text}"
            )
        return "\n\n---\n\n".join(parts)

    def _build_history_str(self, history: List[dict]) -> str:
        if not history:
            return "None"
        parts = []
        for turn in history:
            role = "Employee" if turn["role"] == "user" else "Assistant"
            parts.append(f"{role}: {turn['content']}")
        return "\n".join(parts)

    def _extract_sources(self, chunks: List[ChunkResult]) -> List[Source]:
        seen = set()
        sources = []
        for chunk in chunks:
            key = (chunk.doc_name, chunk.page_number)
            if key not in seen:
                seen.add(key)
                sources.append(Source(
                    document=chunk.doc_name,
                    doc_id="",  # populated if needed
                    page=chunk.page_number
                ))
        return sources

    def _get_follow_ups(self, question: str, answer: str) -> List[str]:
        try:
            prompt = FOLLOW_UP_PROMPT.format(question=question, answer=answer)
            raw = generate(prompt)
            # Strip markdown if present
            raw = raw.strip().lstrip("```json").rstrip("```").strip()
            return json.loads(raw)[:3]
        except Exception:
            return []

    def answer(self, question: str, session_id: str,
               doc_filter: Optional[List[str]] = None) -> AskResponse:
        """Non-streaming answer generation."""
        chunks = self.retriever.retrieve(question, doc_filter=doc_filter)
        confidence = self.retriever.get_confidence(chunks)
        
        history = MemoryManager.get_history(session_id)
        context = self._build_context(chunks)
        history_str = self._build_history_str(history)
        
        prompt = RAG_USER_TEMPLATE.format(
            history=history_str,
            context=context if context else "No relevant documents found.",
            question=question
        )
        
        answer_text = generate(prompt, system=RAG_SYSTEM_PROMPT)
        
        # Store turn in memory
        MemoryManager.add_turn(session_id, question, answer_text)
        
        sources = self._extract_sources(chunks)
        follow_ups = self._get_follow_ups(question, answer_text)
        
        return AskResponse(
            answer=answer_text,
            sources=sources,
            chunks=chunks,
            confidence=confidence,
            follow_up_questions=follow_ups,
            session_id=session_id
        )

    def answer_stream(self, question: str, session_id: str,
                      doc_filter: Optional[List[str]] = None):
        """
        Generator that yields SSE-formatted strings.
        First yields metadata chunk, then text chunks, then done.
        """
        chunks = self.retriever.retrieve(question, doc_filter=doc_filter)
        confidence = self.retriever.get_confidence(chunks)
        
        history = MemoryManager.get_history(session_id)
        context = self._build_context(chunks)
        history_str = self._build_history_str(history)
        
        prompt = RAG_USER_TEMPLATE.format(
            history=history_str,
            context=context if context else "No relevant documents found.",
            question=question
        )
        
        # Yield metadata first
        sources = self._extract_sources(chunks)
        meta = {
            "type": "metadata",
            "sources": [s.dict() for s in sources],
            "chunks": [c.dict() for c in chunks],
            "confidence": confidence,
            "session_id": session_id
        }
        yield f"data: {json.dumps(meta)}\n\n"
        
        # Stream answer text
        full_answer = ""
        for text_chunk in generate_stream(prompt, system=RAG_SYSTEM_PROMPT):
            full_answer += text_chunk
            yield f"data: {json.dumps({'type': 'text', 'content': text_chunk})}\n\n"
        
        # Store in memory
        MemoryManager.add_turn(session_id, question, full_answer)
        
        # Yield follow-ups
        follow_ups = self._get_follow_ups(question, full_answer)
        yield f"data: {json.dumps({'type': 'follow_ups', 'questions': follow_ups})}\n\n"
        
        # Done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

### 6.14 `backend/api/routes/documents.py`

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from models.schemas import (DocumentUploadResponse, DocumentListResponse,
                             DocumentSummaryResponse, DocumentInfo)
from pipeline.ingestion import ingest_pdf
from storage.file_store import get_all_documents, get_document, delete_document, get_pdf_path
from storage.chroma_store import ChromaStore
from rag.gemini_client import generate
from rag.prompts import SUMMARY_PROMPT
import fitz
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {"application/pdf"}
MAX_FILE_SIZE_MB = 50

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only PDF files are supported.")
    
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max size is {MAX_FILE_SIZE_MB}MB.")
    
    try:
        result = ingest_pdf(content, file.filename)
        return DocumentUploadResponse(
            **result,
            message=f"Successfully ingested {result['total_chunks']} chunks from {result['total_pages']} pages."
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(500, "Failed to process document.")

@router.get("/", response_model=DocumentListResponse)
def list_documents():
    docs = get_all_documents()
    return DocumentListResponse(
        documents=[DocumentInfo(**d) for d in docs],
        total=len(docs)
    )

@router.delete("/{doc_id}")
def delete_doc(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    ChromaStore.delete_by_doc_id(doc_id)
    delete_document(doc_id)
    return {"message": f"Deleted {doc['doc_name']}"}

@router.get("/{doc_id}/summary", response_model=DocumentSummaryResponse)
def summarize_document(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    
    pdf_path = get_pdf_path(doc_id)
    if not pdf_path.exists():
        raise HTTPException(404, "PDF file not found.")
    
    # Extract first 5 pages for summary
    pdf_doc = fitz.open(str(pdf_path))
    pages_text = []
    for i in range(min(5, len(pdf_doc))):
        pages_text.append(pdf_doc[i].get_text("text"))
    pdf_doc.close()
    
    content = "\n\n".join(pages_text)[:4000]  # Limit context
    
    prompt = SUMMARY_PROMPT.format(doc_name=doc["doc_name"], content=content)
    summary = generate(prompt)
    
    return DocumentSummaryResponse(
        doc_id=doc_id,
        doc_name=doc["doc_name"],
        summary=summary
    )
```

### 6.15 `backend/api/routes/query.py`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import AskRequest, AskResponse, FeedbackRequest
from rag.engine import RAGEngine
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
def ask(request: AskRequest):
    try:
        _recent_queries.append(request.question)
        if len(_recent_queries) > 20:
            _recent_queries.pop(0)
        return engine.answer(
            question=request.question,
            session_id=request.session_id,
            doc_filter=request.doc_filter
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(500, "Failed to generate answer.")

@router.post("/ask/stream")
def ask_stream(request: AskRequest):
    """Server-Sent Events streaming endpoint."""
    try:
        _recent_queries.append(request.question)
        if len(_recent_queries) > 20:
            _recent_queries.pop(0)
        
        return StreamingResponse(
            engine.answer_stream(
                question=request.question,
                session_id=request.session_id,
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
```

### 6.16 `backend/api/routes/stats.py`

```python
from fastapi import APIRouter
from models.schemas import StatsResponse
from storage.chroma_store import ChromaStore
from core.config import settings
from api.routes.query import _recent_queries

router = APIRouter()

@router.get("/", response_model=StatsResponse)
def get_stats():
    chroma_stats = ChromaStore.get_stats()
    return StatsResponse(
        total_documents=chroma_stats["total_documents"],
        total_pages=chroma_stats["total_pages"],
        total_chunks=chroma_stats["total_chunks"],
        embedding_model=settings.EMBEDDING_MODEL,
        vector_db="ChromaDB (local persistent)",
        recent_queries=list(reversed(_recent_queries[-5:]))
    )
```

### 6.17 `backend/requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
pydantic==2.7.1
pydantic-settings==2.3.1
PyMuPDF==1.24.5
sentence-transformers==3.0.1
chromadb==0.5.3
google-generativeai==0.7.2
numpy==1.26.4
python-dotenv==1.0.1
```

---

## 7. AI Pipeline — RAG Engine

### 7.1 Chunking Strategy

- **Method:** Recursive character split
- **Chunk size:** 512 characters (~100-130 words)
- **Overlap:** 64 characters
- **Separator priority:** `\n\n` → `\n` → `. ` → `,` → ` ` → character
- **Rationale:** Sentence Transformers perform best on sub-512-token inputs. Overlap preserves context across chunk boundaries. Recursive splitting respects natural semantic boundaries (paragraphs → sentences).

### 7.2 Embedding Model

- **Model:** `all-MiniLM-L6-v2`
- **Dimensions:** 384
- **Why:** Fastest free model with excellent quality for retrieval. Runs on CPU. No API key needed. ~80MB download.

### 7.3 Vector Store

- **Database:** ChromaDB with cosine similarity
- **Persistence:** Local disk at `data/chroma_db/`
- **Metadata per chunk:** doc_id, doc_name, page_number, chunk_index

### 7.4 Retrieval

- **Top-K:** 5 chunks
- **Similarity measure:** Cosine (via ChromaDB HNSW index)
- **Confidence score:** `1 - distance` of top chunk (range 0-1)
- **Filtering:** Optional filter by one or more doc_ids

### 7.5 LLM

- **Model:** Gemini 1.5 Flash
- **Free tier:** 15 requests/minute, 1 million tokens/minute, 1500 requests/day
- **Context window:** 1M tokens (more than enough)
- **Why:** Best free model available with streaming support

### 7.6 Hallucination Prevention

- System prompt explicitly instructs the model to answer ONLY from context
- System prompt provides exact fallback text when information is not found
- Retrieved chunks are clearly labeled with source and page number
- Confidence score < 0.3 triggers a low-confidence UI warning on the frontend

---

## 8. Frontend — Next.js

### 8.1 `frontend/lib/types.ts`

```typescript
export interface Source {
  document: string;
  doc_id: string;
  page: number;
}

export interface ChunkResult {
  text: string;
  doc_name: string;
  page_number: number;
  chunk_index: number;
  similarity_score: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  chunks?: ChunkResult[];
  confidence?: number;
  followUpQuestions?: string[];
  isStreaming?: boolean;
  timestamp: Date;
}

export interface DocumentInfo {
  doc_id: string;
  doc_name: string;
  total_pages: number;
  total_chunks: number;
  uploaded_at: string;
  file_size_kb: number;
}

export interface StatsData {
  total_documents: number;
  total_pages: number;
  total_chunks: number;
  embedding_model: string;
  vector_db: string;
  recent_queries: string[];
}

export type ThinkingStep =
  | "understanding"
  | "planning"
  | "searching"
  | "reading"
  | "gathering"
  | "synthesizing"
  | "validating"
  | "generating"
  | "done";
```

### 8.2 `frontend/lib/constants.ts`

```typescript
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const THINKING_STEPS: { key: string; label: string; duration: number }[] = [
  { key: "understanding", label: "Understanding your request...", duration: 600 },
  { key: "planning", label: "Planning execution...", duration: 500 },
  { key: "searching", label: "Searching knowledge base...", duration: 800 },
  { key: "reading", label: "Reading documents...", duration: 700 },
  { key: "gathering", label: "Gathering relevant context...", duration: 600 },
  { key: "synthesizing", label: "Synthesizing information...", duration: 500 },
  { key: "validating", label: "Validating answer...", duration: 400 },
  { key: "generating", label: "Generating final response...", duration: 0 },
];

export const LOW_CONFIDENCE_THRESHOLD = 0.3;
```

### 8.3 `frontend/lib/api.ts`

```typescript
import axios from "axios";
import { API_BASE_URL } from "./constants";
import { DocumentInfo, StatsData, Source, ChunkResult } from "./types";

const api = axios.create({ baseURL: API_BASE_URL });

// ── Documents ─────────────────────────────────────────────────────

export async function uploadDocument(file: File): Promise<{
  doc_id: string; doc_name: string; total_pages: number;
  total_chunks: number; message: string;
}> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const { data } = await api.get("/documents/");
  return data.documents;
}

export async function deleteDocument(docId: string): Promise<void> {
  await api.delete(`/documents/${docId}`);
}

export async function summarizeDocument(docId: string): Promise<string> {
  const { data } = await api.get(`/documents/${docId}/summary`);
  return data.summary;
}

// ── Query ─────────────────────────────────────────────────────────

export async function askQuestion(params: {
  question: string; session_id: string; doc_filter?: string[];
}): Promise<{
  answer: string; sources: Source[]; chunks: ChunkResult[];
  confidence: number; follow_up_questions: string[];
}> {
  const { data } = await api.post("/ask", params);
  return data;
}

export async function submitFeedback(params: {
  session_id: string; question: string; answer: string; feedback: string;
}): Promise<void> {
  await api.post("/feedback", params);
}

export async function getRecentQueries(): Promise<string[]> {
  const { data } = await api.get("/recent-queries");
  return data.queries;
}

// ── Stats ─────────────────────────────────────────────────────────

export async function getStats(): Promise<StatsData> {
  const { data } = await api.get("/stats/");
  return data;
}
```

### 8.4 `frontend/hooks/useStream.ts`

```typescript
import { useCallback, useRef } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { Source, ChunkResult } from "@/lib/types";

interface StreamCallbacks {
  onMetadata: (meta: { sources: Source[]; chunks: ChunkResult[]; confidence: number }) => void;
  onText: (text: string) => void;
  onFollowUps: (questions: string[]) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export function useStream() {
  const abortRef = useRef<AbortController | null>(null);

  const stream = useCallback(async (
    question: string,
    session_id: string,
    callbacks: StreamCallbacks,
    doc_filter?: string[]
  ) => {
    abortRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE_URL}/ask/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id, doc_filter }),
        signal: abortRef.current.signal
      });

      if (!response.ok) throw new Error("Stream request failed");
      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "metadata") callbacks.onMetadata(data);
              else if (data.type === "text") callbacks.onText(data.content);
              else if (data.type === "follow_ups") callbacks.onFollowUps(data.questions);
              else if (data.type === "done") callbacks.onDone();
            } catch {}
          }
        }
      }
    } catch (error: any) {
      if (error.name !== "AbortError") {
        callbacks.onError(error.message);
      }
    }
  }, []);

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { stream, abort };
}
```

### 8.5 `frontend/hooks/useChat.ts`

```typescript
"use client";
import { useState, useCallback, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { Message, Source, ChunkResult } from "@/lib/types";
import { useStream } from "./useStream";
import { THINKING_STEPS } from "@/lib/constants";

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [thinkingStep, setThinkingStep] = useState<number>(-1);
  const sessionId = useRef(uuidv4());
  const { stream, abort } = useStream();
  const thinkingInterval = useRef<NodeJS.Timeout>();

  const startThinkingAnimation = useCallback(() => {
    let step = 0;
    setThinkingStep(0);
    const advance = () => {
      step++;
      if (step < THINKING_STEPS.length - 1) {
        setThinkingStep(step);
        const duration = THINKING_STEPS[step].duration;
        if (duration > 0) {
          thinkingInterval.current = setTimeout(advance, duration);
        }
        // Last thinking step stays until stream starts
      }
    };
    thinkingInterval.current = setTimeout(advance, THINKING_STEPS[0].duration);
  }, []);

  const stopThinkingAnimation = useCallback(() => {
    if (thinkingInterval.current) clearTimeout(thinkingInterval.current);
    setThinkingStep(-1);
  }, []);

  const sendMessage = useCallback(async (
    question: string,
    docFilter?: string[]
  ) => {
    if (!question.trim() || isLoading) return;

    const userMsg: Message = {
      id: uuidv4(),
      role: "user",
      content: question,
      timestamp: new Date()
    };

    const assistantMsgId = uuidv4();
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      isStreaming: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);
    startThinkingAnimation();

    let metaReceived = false;

    await stream(question, sessionId.current, {
      onMetadata: (meta) => {
        metaReceived = true;
        stopThinkingAnimation();
        setThinkingStep(THINKING_STEPS.length - 1); // "Generating..."
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, sources: meta.sources, chunks: meta.chunks, confidence: meta.confidence }
            : m
        ));
      },
      onText: (text) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: m.content + text }
            : m
        ));
      },
      onFollowUps: (questions) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, followUpQuestions: questions }
            : m
        ));
      },
      onDone: () => {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, isStreaming: false }
            : m
        ));
        stopThinkingAnimation();
        setIsLoading(false);
      },
      onError: (error) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: "Sorry, something went wrong. Please try again.", isStreaming: false }
            : m
        ));
        stopThinkingAnimation();
        setIsLoading(false);
      }
    }, docFilter);
  }, [isLoading, stream, startThinkingAnimation, stopThinkingAnimation]);

  const clearChat = useCallback(() => {
    setMessages([]);
    sessionId.current = uuidv4();
  }, []);

  return {
    messages,
    isLoading,
    thinkingStep,
    sendMessage,
    clearChat,
    sessionId: sessionId.current
  };
}
```

### 8.6 Key UI Components

#### `frontend/components/chat/ThinkingIndicator.tsx`

```tsx
import { THINKING_STEPS } from "@/lib/constants";
import { Check, Loader2 } from "lucide-react";

interface Props {
  currentStep: number;
}

export function ThinkingIndicator({ currentStep }: Props) {
  if (currentStep < 0) return null;

  return (
    <div className="flex flex-col gap-1.5 p-4 rounded-xl bg-muted/50 border border-border max-w-sm">
      {THINKING_STEPS.map((step, index) => {
        const isCompleted = index < currentStep;
        const isCurrent = index === currentStep;

        return (
          <div key={step.key} className={`flex items-center gap-2 text-sm transition-all duration-300 ${
            isCompleted ? "text-muted-foreground" :
            isCurrent ? "text-foreground font-medium" :
            "text-muted-foreground/40"
          }`}>
            <span className="w-4 h-4 flex items-center justify-center flex-shrink-0">
              {isCompleted ? (
                <Check className="w-3.5 h-3.5 text-green-500" />
              ) : isCurrent ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
              ) : (
                <span className="w-1.5 h-1.5 rounded-full bg-current" />
              )}
            </span>
            {step.label}
          </div>
        );
      })}
    </div>
  );
}
```

#### `frontend/components/chat/MessageBubble.tsx`

```tsx
"use client";
import { Message } from "@/lib/types";
import { SourceCard } from "./SourceCard";
import { ChunkViewer } from "./ChunkViewer";
import { FeedbackButtons } from "./FeedbackButtons";
import { FollowUpSuggestions } from "./FollowUpSuggestions";
import { Copy, Check } from "lucide-react";
import { useState } from "react";
import { LOW_CONFIDENCE_THRESHOLD } from "@/lib/constants";

interface Props {
  message: Message;
  onFollowUp: (question: string) => void;
  sessionId: string;
}

export function MessageBubble({ message, onFollowUp, sessionId }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-3">
          <p className="text-sm">{message.content}</p>
        </div>
      </div>
    );
  }

  const isLowConfidence = message.confidence !== undefined && message.confidence < LOW_CONFIDENCE_THRESHOLD;

  return (
    <div className="flex flex-col gap-3 max-w-[85%]">
      {/* Answer */}
      <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
        {isLowConfidence && (
          <div className="mb-2 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950 rounded-lg px-3 py-1.5">
            ⚠️ Low confidence ({(message.confidence! * 100).toFixed(0)}%) — verify with source documents.
          </div>
        )}
        <p className="text-sm whitespace-pre-wrap leading-relaxed">
          {message.content}
          {message.isStreaming && <span className="inline-block w-0.5 h-4 bg-current ml-0.5 animate-pulse" />}
        </p>
      </div>

      {/* Sources */}
      {message.sources && message.sources.length > 0 && !message.isStreaming && (
        <div className="flex flex-col gap-1.5">
          <p className="text-xs text-muted-foreground font-medium px-1">Sources</p>
          <div className="flex flex-wrap gap-2">
            {message.sources.map((source, i) => (
              <SourceCard key={i} source={source} />
            ))}
          </div>
        </div>
      )}

      {/* Confidence */}
      {message.confidence !== undefined && !message.isStreaming && (
        <div className="flex items-center gap-2 px-1">
          <div className="flex-1 h-1 bg-border rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 rounded-full transition-all"
              style={{ width: `${message.confidence * 100}%`,
                backgroundColor: message.confidence > 0.6 ? '#22c55e' :
                                  message.confidence > 0.3 ? '#f59e0b' : '#ef4444' }}
            />
          </div>
          <span className="text-xs text-muted-foreground">
            {(message.confidence * 100).toFixed(0)}% match
          </span>
        </div>
      )}

      {/* Retrieved Chunks */}
      {message.chunks && message.chunks.length > 0 && !message.isStreaming && (
        <ChunkViewer chunks={message.chunks} />
      )}

      {/* Actions */}
      {!message.isStreaming && (
        <div className="flex items-center gap-2 px-1">
          <button onClick={handleCopy}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
            {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied!" : "Copy"}
          </button>
          <FeedbackButtons
            sessionId={sessionId}
            question=""
            answer={message.content}
          />
        </div>
      )}

      {/* Follow-up suggestions */}
      {message.followUpQuestions && message.followUpQuestions.length > 0 && !message.isStreaming && (
        <FollowUpSuggestions questions={message.followUpQuestions} onSelect={onFollowUp} />
      )}
    </div>
  );
}
```

#### `frontend/components/chat/ChunkViewer.tsx`

```tsx
"use client";
import { ChunkResult } from "@/lib/types";
import { useState } from "react";
import { ChevronDown, ChevronRight, FileText } from "lucide-react";

interface Props { chunks: ChunkResult[] }

export function ChunkViewer({ chunks }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground hover:bg-muted/50 transition-colors"
      >
        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        <FileText className="w-3.5 h-3.5" />
        View {chunks.length} retrieved chunks
      </button>
      {open && (
        <div className="border-t border-border divide-y divide-border">
          {chunks.map((chunk, i) => (
            <div key={i} className="px-3 py-2.5">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-medium text-primary">
                  {chunk.doc_name} — Page {chunk.page_number}
                </span>
                <span className="text-xs text-muted-foreground">
                  {(chunk.similarity_score * 100).toFixed(0)}% match
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-4">
                {chunk.text}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 8.7 `frontend/app/page.tsx`

```tsx
"use client";
import { useState } from "react";
import { useChat } from "@/hooks/useChat";
import { useDocuments } from "@/hooks/useDocuments";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { ChatInput } from "@/components/chat/ChatInput";
import { ThinkingIndicator } from "@/components/chat/ThinkingIndicator";

export default function Home() {
  const { messages, isLoading, thinkingStep, sendMessage, clearChat, sessionId } = useChat();
  const { documents, uploadDocument, deleteDocument, isUploading } = useDocuments();
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleSend = (question: string) => {
    sendMessage(question, selectedDocs.length > 0 ? selectedDocs : undefined);
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar
        open={sidebarOpen}
        documents={documents}
        selectedDocs={selectedDocs}
        onSelectDoc={(id) => setSelectedDocs(prev =>
          prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
        )}
        onUpload={uploadDocument}
        onDelete={deleteDocument}
        isUploading={isUploading}
      />

      <main className="flex flex-col flex-1 min-w-0">
        <Header
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onClearChat={clearChat}
        />

        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md px-4">
                <h2 className="text-2xl font-semibold mb-2">Enterprise Knowledge Assistant</h2>
                <p className="text-muted-foreground text-sm">
                  Upload internal documents and ask questions in natural language.
                  I'll find the answers and cite my sources.
                </p>
              </div>
            </div>
          ) : (
            <ChatWindow
              messages={messages}
              thinkingStep={thinkingStep}
              onFollowUp={handleSend}
              sessionId={sessionId}
            />
          )}
        </div>

        <div className="border-t border-border p-4">
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            disabled={documents.length === 0}
            placeholder={documents.length === 0
              ? "Upload documents to start asking questions..."
              : "Ask a question about your documents..."}
          />
          {selectedDocs.length > 0 && (
            <p className="text-xs text-muted-foreground mt-1.5 text-center">
              Searching in {selectedDocs.length} selected document(s)
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
```

### 8.8 `frontend/package.json`

```json
{
  "name": "enterprise-knowledge-assistant",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.2.4",
    "react": "^18",
    "react-dom": "^18",
    "axios": "^1.7.2",
    "uuid": "^10.0.0",
    "lucide-react": "^0.383.0",
    "next-themes": "^0.3.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.3.0",
    "@radix-ui/react-dialog": "^1.1.1",
    "@radix-ui/react-tooltip": "^1.1.1",
    "@radix-ui/react-scroll-area": "^1.1.0"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "@types/uuid": "^10",
    "tailwindcss": "^3.4.1",
    "postcss": "^8",
    "autoprefixer": "^10"
  }
}
```

### 8.9 `frontend/tailwind.config.ts`

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        border: "hsl(var(--border))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        }
      },
    },
  },
  plugins: [],
};

export default config;
```

### 8.10 `frontend/app/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 224 71.4% 4.1%;
    --card: 0 0% 100%;
    --card-foreground: 224 71.4% 4.1%;
    --primary: 262.1 83.3% 57.8%;
    --primary-foreground: 210 20% 98%;
    --muted: 220 14.3% 95.9%;
    --muted-foreground: 220 8.9% 46.1%;
    --border: 220 13% 91%;
  }

  .dark {
    --background: 224 71.4% 4.1%;
    --foreground: 210 20% 98%;
    --card: 224 71.4% 4.1%;
    --card-foreground: 210 20% 98%;
    --primary: 263.4 70% 50.4%;
    --primary-foreground: 210 20% 98%;
    --muted: 215 27.9% 16.9%;
    --muted-foreground: 217.9 10.6% 64.9%;
    --border: 215 27.9% 16.9%;
  }
}

* {
  border-color: hsl(var(--border));
}

body {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
}
```

---

## 9. API Contract

### Full API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload a PDF |
| GET | `/api/documents/` | List all documents |
| DELETE | `/api/documents/{doc_id}` | Delete a document |
| GET | `/api/documents/{doc_id}/summary` | Summarize a document |
| POST | `/api/ask` | Ask a question (non-streaming) |
| POST | `/api/ask/stream` | Ask a question (SSE streaming) |
| POST | `/api/feedback` | Submit thumbs up/down |
| GET | `/api/recent-queries` | Get last 10 queries |
| GET | `/api/stats/` | Get dashboard statistics |
| GET | `/health` | Health check |

### POST `/api/ask` — Request

```json
{
  "question": "What is the employee leave policy?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "doc_filter": ["doc-id-1", "doc-id-2"]
}
```

### POST `/api/ask` — Response

```json
{
  "answer": "Employees are eligible for 24 paid leaves annually...",
  "sources": [
    { "document": "HR_Policy.pdf", "doc_id": "abc-123", "page": 12 }
  ],
  "chunks": [
    {
      "text": "Section 4.2 Leave Policy: All full-time employees...",
      "doc_name": "HR_Policy.pdf",
      "page_number": 12,
      "chunk_index": 47,
      "similarity_score": 0.8921
    }
  ],
  "confidence": 0.8921,
  "follow_up_questions": [
    "How do I apply for leave?",
    "Are sick leaves counted separately?",
    "What is the carry-forward policy?"
  ],
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### POST `/api/ask/stream` — SSE Event Sequence

```
data: {"type": "metadata", "sources": [...], "chunks": [...], "confidence": 0.89, "session_id": "..."}

data: {"type": "text", "content": "Employees are "}

data: {"type": "text", "content": "eligible for 24 "}

data: {"type": "text", "content": "paid leaves annually."}

data: {"type": "follow_ups", "questions": ["How do I apply?", "..."]}

data: {"type": "done"}
```

---

## 10. Database & Storage Schemas

### ChromaDB Collection: `documents`

```
Collection metadata: {"hnsw:space": "cosine"}

Per record:
  id:        "{doc_id}_{chunk_index}"  (string)
  embedding: [float x 384]
  document:  "chunk text content"
  metadata: {
    "doc_id":       "uuid-string",
    "doc_name":     "HR_Policy.pdf",
    "page_number":  12,
    "chunk_index":  47
  }
```

### File Manifest: `data/uploads/manifest.json`

```json
{
  "uuid-doc-id": {
    "doc_id": "uuid-doc-id",
    "doc_name": "HR_Policy.pdf",
    "total_pages": 24,
    "total_chunks": 87,
    "file_size_kb": 412.3,
    "uploaded_at": "2024-01-15T10:30:00"
  }
}
```

### Filesystem Layout

```
backend/data/
├── uploads/
│   ├── manifest.json
│   ├── {doc_id_1}.pdf
│   └── {doc_id_2}.pdf
└── chroma_db/
    ├── chroma.sqlite3
    └── {collection-uuid}/
```

---

## 11. Prompts

All prompts are in `backend/rag/prompts.py`. Reproduced here for reference.

### System Prompt (RAG)

The system prompt instructs the model to:
1. Answer ONLY from provided context
2. Use the exact fallback phrase when information is not found
3. Be concise and professional
4. Not fabricate document names or page numbers

Full text is in `backend/rag/prompts.py::RAG_SYSTEM_PROMPT`.

### User Prompt Template

Injects three variables: `{history}`, `{context}`, `{question}`.

Context format per chunk:
```
[Excerpt N | Source: {doc_name}, Page {page_number}]
{chunk_text}
```

### Follow-up Prompt

Asks Gemini to return a JSON array of exactly 3 follow-up questions. Parsed with `json.loads()` after stripping markdown fences.

### Summary Prompt

Uses first 5 pages (~4000 chars) of the document. Returns 150-200 word factual summary.

---

## 12. Environment Variables

### `backend/.env`

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K=5
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_MEMORY_TURNS=6
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### How to get Gemini API Key (FREE)
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy key into `backend/.env`

---

## 13. Configuration Files

### `backend/.env.example`

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K=5
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_MEMORY_TURNS=6
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### `frontend/.env.local.example`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### `docker-compose.yml` (optional)

```yaml
version: "3.9"
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend/data:/app/data

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    env_file:
      - ./frontend/.env.local
    depends_on:
      - backend
```

### `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data/uploads data/chroma_db
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

---

## 14. Setup & Run Instructions

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git
- Google account (for free Gemini API key)

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/enterprise-knowledge-assistant
cd enterprise-knowledge-assistant

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Start backend
uvicorn main:app --reload --port 8000

# 4. Frontend setup (new terminal)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### Verify Installation

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# API docs
open http://localhost:8000/docs
```

### Access the App

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

---

## 15. Evaluation Framework

### `backend/evaluation/evaluator.py`

```python
"""
RAG Evaluation script.
Run: python -m evaluation.evaluator
Requires documents to be already ingested.
"""
import json
from pathlib import Path
from rag.engine import RAGEngine
from pipeline.embedder import Embedder
import numpy as np

engine = RAGEngine()

def semantic_similarity(a: str, b: str) -> float:
    """Measure answer relevance via embedding similarity."""
    emb_a = Embedder.embed_single(a)
    emb_b = Embedder.embed_single(b)
    a_np, b_np = np.array(emb_a), np.array(emb_b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))

def evaluate():
    test_file = Path(__file__).parent / "test_cases.json"
    test_cases = json.loads(test_file.read_text())
    
    results = []
    for tc in test_cases:
        session_id = f"eval-{tc['id']}"
        response = engine.answer(tc["question"], session_id=session_id)
        
        sim = semantic_similarity(response.answer, tc["expected_answer"])
        has_source = any(
            tc["expected_source"].lower() in s.document.lower()
            for s in response.sources
        )
        
        result = {
            "id": tc["id"],
            "question": tc["question"],
            "expected": tc["expected_answer"],
            "actual": response.answer,
            "semantic_similarity": round(sim, 4),
            "source_found": has_source,
            "confidence": response.confidence,
            "num_sources": len(response.sources)
        }
        results.append(result)
        print(f"[{tc['id']}] sim={sim:.3f} source={'✓' if has_source else '✗'} conf={response.confidence:.3f}")
    
    avg_sim = sum(r["semantic_similarity"] for r in results) / len(results)
    source_accuracy = sum(r["source_found"] for r in results) / len(results)
    
    print(f"\n=== EVALUATION RESULTS ===")
    print(f"Average Semantic Similarity: {avg_sim:.4f}")
    print(f"Source Attribution Accuracy: {source_accuracy:.2%}")
    print(f"Cases evaluated: {len(results)}")
    
    return results
```

### `backend/evaluation/test_cases.json`

```json
[
  {
    "id": "TC001",
    "question": "What is the employee leave policy?",
    "expected_answer": "Employees are eligible for 24 paid leaves annually.",
    "expected_source": "HR_Policy"
  },
  {
    "id": "TC002",
    "question": "What is the refund policy for customers?",
    "expected_answer": "Refunds are allowed within 30 days of purchase.",
    "expected_source": "Customer_Policy"
  },
  {
    "id": "TC003",
    "question": "What is the notice period for resignation?",
    "expected_answer": "The standard notice period is 30 days.",
    "expected_source": "HR_Policy"
  },
  {
    "id": "TC004",
    "question": "What information is not in any document?",
    "expected_answer": "I could not find information about this",
    "expected_source": ""
  },
  {
    "id": "TC005",
    "question": "What are the data privacy requirements?",
    "expected_answer": "All customer data must be handled per GDPR guidelines.",
    "expected_source": "Compliance"
  }
]
```

### Evaluation Metrics Explanation

| Metric | Method | Target |
|--------|--------|--------|
| Semantic Similarity | Cosine similarity between expected and actual answer embeddings | > 0.7 |
| Source Attribution | Check if expected source document appears in returned sources | > 80% |
| Confidence Score | Average cosine similarity of top retrieved chunk | > 0.5 on valid questions |
| Hallucination Test | TC004 should return the "not found" fallback phrase | 100% |

---

## 16. README Content

> Create this as `README.md` in the project root.

```markdown
# Enterprise Knowledge Assistant

An AI-powered document Q&A system built with RAG (Retrieval-Augmented Generation).
Upload internal documents and ask questions in natural language — get accurate, cited answers.

## Features

- 📄 PDF upload and intelligent processing
- 🔍 Semantic search with vector embeddings
- 🤖 AI answers grounded in your documents
- 📎 Source citations with page numbers
- 💬 Conversation memory for follow-up questions
- 📊 Confidence scores and retrieved chunk viewer
- 💡 Suggested follow-up questions
- 🌙 Dark/Light mode
- ⚡ Real-time streaming responses

## Tech Stack

- **Backend:** Python, FastAPI, PyMuPDF, ChromaDB, Sentence Transformers
- **LLM:** Google Gemini 1.5 Flash (free tier)
- **Frontend:** Next.js 14, Tailwind CSS, shadcn/ui
- **Embeddings:** all-MiniLM-L6-v2 (local, free)
- **Vector DB:** ChromaDB (local persistent)

## Quick Start

See [Setup & Run Instructions](#setup) in TECHNICAL_SPEC.md.

## Architecture

See TECHNICAL_SPEC.md for full architecture, API contract, and design decisions.

## Evaluation

Run `python -m evaluation.evaluator` from the backend directory after ingesting documents.
```

---

## 17. Design Decisions & Assumptions

### Why Gemini 1.5 Flash over GPT?
OpenAI has no truly free tier (requires credit card). Gemini provides 15 RPM and 1M TPM free with just a Google account. Quality is comparable for RAG use cases.

### Why ChromaDB over FAISS?
ChromaDB is persistent by default (data survives restarts), has metadata filtering built in, and requires no index serialization code. FAISS requires manual save/load and offers no metadata filtering.

### Why `all-MiniLM-L6-v2` over OpenAI embeddings?
OpenAI embeddings require paid API. `all-MiniLM-L6-v2` runs locally on CPU, is 80MB, and delivers excellent retrieval quality. Chosen for cost ($0) and latency (no API round-trip for embedding).

### Why chunk_size=512?
`all-MiniLM-L6-v2` has a 512-token max. Chunks at this boundary prevent truncation. Overlap of 64 chars preserves context at boundaries.

### Why per-page text extraction?
PyMuPDF extracts text per page natively. Preserving page numbers in metadata enables accurate source citations (assignment requirement).

### Why in-memory conversation store?
For a 72-hour assignment scope, in-memory is sufficient and avoids DB setup. Production would use Redis or a sessions table.

### Assumptions
1. Documents are PDFs with extractable text (not scanned images).
2. Single deployment instance (no load balancing concerns for in-memory state).
3. Users have a Google account to obtain a free Gemini API key.
4. The frontend and backend run on the same machine (CORS set to localhost).

---

## 18. Limitations & Future Work

### Current Limitations

1. **No OCR:** Scanned PDFs (image-based) will return empty text. Fix: integrate `pytesseract`.
2. **In-memory session storage:** Conversation history is lost on server restart. Fix: Redis or SQLite session store.
3. **No authentication:** Any user can see/delete all documents. Fix: JWT auth + per-user document namespacing in ChromaDB.
4. **Gemini rate limits:** Free tier is 15 RPM. Under heavy load, requests may queue. Fix: upgrade plan or add request queue.
5. **Single file per upload:** The UI accepts one file at a time. Fix: multi-file upload with progress.
6. **No table/image extraction:** Tables in PDFs are extracted as plain text. Fix: `camelot-py` for tables, `fitz` image extraction.

### Future Improvements

1. **Hybrid search:** Combine BM25 keyword search with semantic search for better recall on exact terms (product codes, names).
2. **Query rewriting:** Rephrase ambiguous questions using LLM before retrieval.
3. **Re-ranking:** Add a cross-encoder re-ranker (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) to re-score top-K chunks.
4. **Multi-document reasoning:** Explicitly prompt the model to synthesize across multiple sources.
5. **Persistent feedback DB:** Store thumbs up/down in SQLite for analysis and fine-tuning signal.
6. **Deployment:** Backend on Railway/Render (free tier), Frontend on Vercel (free tier).
7. **Document versioning:** Handle updated documents without full re-ingestion.
8. **Evaluation dashboard:** Visualize retrieval quality metrics in the UI.
```
