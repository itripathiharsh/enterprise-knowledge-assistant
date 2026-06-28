# Enterprise Knowledge Assistant — V2 Features Specification

> **Purpose of this document:** Defines every V2 enhancement — what it is, exactly which file(s) it touches in the V1 codebase, what code gets added/modified, and what new files get created.
> 
> This document is a **diff layer on top of `TECHNICAL_SPEC.md`**. Read that first. Everything here assumes V1 is already built and working.

---

## Table of Contents

1. [V2 Feature Map — Quick Reference](#1-v2-feature-map--quick-reference)
2. [Fix 1 — OCR for Scanned PDFs](#2-fix-1--ocr-for-scanned-pdfs)
3. [Fix 2 — Persistent Session Storage (SQLite)](#3-fix-2--persistent-session-storage-sqlite)
4. [Fix 3 — JWT Authentication](#4-fix-3--jwt-authentication)
5. [Fix 4 — Gemini Rate Limit Queue](#5-fix-4--gemini-rate-limit-queue)
6. [Fix 5 — Multi-file Upload with Progress](#6-fix-5--multi-file-upload-with-progress)
7. [Fix 6 — Table Extraction (camelot)](#7-fix-6--table-extraction-camelot)
8. [Enhancement 1 — Hybrid Search (BM25 + Semantic)](#8-enhancement-1--hybrid-search-bm25--semantic)
9. [Enhancement 2 — Query Rewriting](#9-enhancement-2--query-rewriting)
10. [Enhancement 3 — Cross-Encoder Re-ranking](#10-enhancement-3--cross-encoder-re-ranking)
11. [Enhancement 4 — Multi-document Reasoning Prompt](#11-enhancement-4--multi-document-reasoning-prompt)
12. [Enhancement 5 — Deployment (Railway + Vercel)](#12-enhancement-5--deployment-railway--vercel)
13. [Enhancement 6 — Document Versioning](#13-enhancement-6--document-versioning)
14. [Enhancement 7 — Evaluation Dashboard UI](#14-enhancement-7--evaluation-dashboard-ui)
15. [Updated Requirements & Dependencies](#15-updated-requirements--dependencies)
16. [Updated Environment Variables](#16-updated-environment-variables)
17. [Updated Repository Structure (V2 diff)](#17-updated-repository-structure-v2-diff)

---

## 1. V2 Feature Map — Quick Reference

| # | Feature | Type | Touches |
|---|---------|------|---------|
| F1 | OCR for scanned PDFs | Fix | `pipeline/ingestion.py`, new `pipeline/ocr.py` |
| F2 | SQLite session storage | Fix | new `storage/session_store.py`, `rag/memory.py` |
| F3 | JWT auth | Fix | new `api/auth.py`, `api/middleware.py`, all routes, FE `hooks/useAuth.ts`, `components/auth/LoginModal.tsx` |
| F4 | Gemini rate limit queue | Fix | new `rag/rate_limiter.py`, `rag/gemini_client.py` |
| F5 | Multi-file upload + progress | Fix | `api/routes/documents.py`, FE `components/documents/DocumentUpload.tsx` |
| F6 | Table extraction | Fix | new `pipeline/table_extractor.py`, `pipeline/ingestion.py` |
| E1 | Hybrid search (BM25 + semantic) | Enhancement | new `pipeline/bm25_index.py`, `pipeline/retriever.py`, `storage/bm25_store.py` |
| E2 | Query rewriting | Enhancement | new `rag/query_rewriter.py`, `rag/engine.py`, `rag/prompts.py` |
| E3 | Cross-encoder re-ranking | Enhancement | new `pipeline/reranker.py`, `pipeline/retriever.py` |
| E4 | Multi-doc reasoning prompt | Enhancement | `rag/prompts.py`, `rag/engine.py` |
| E5 | Deployment | Enhancement | new `railway.json`, `vercel.json`, `Procfile`, `frontend/next.config.js` |
| E6 | Document versioning | Enhancement | `storage/file_store.py`, `api/routes/documents.py`, new `pipeline/version_manager.py` |
| E7 | Evaluation dashboard UI | Enhancement | new `frontend/components/dashboard/EvalDashboard.tsx`, `api/routes/stats.py` |

---

## 2. Fix 1 — OCR for Scanned PDFs

### What & Why
PyMuPDF returns empty or near-empty text for image-based PDFs (scanned documents). We detect this and fall back to `pytesseract` OCR to extract text from page images.

### Files Modified

**`backend/pipeline/ingestion.py`** — change the `extract_pages` function:

```python
# ADD THIS IMPORT at top
from pipeline.ocr import ocr_page

# REPLACE extract_pages function:
def extract_pages(pdf_path: Path) -> List[Dict]:
    """
    Extract text from each page.
    If a page has < 50 chars of extractable text (likely scanned),
    fall back to OCR via pytesseract.
    """
    pages = []
    doc = fitz.open(str(pdf_path))
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        
        # Threshold: < 50 chars means page is likely an image
        if len(text) < 50:
            logger.info(f"Page {page_num+1} has sparse text ({len(text)} chars), attempting OCR...")
            text = ocr_page(page)  # returns OCR'd text string
        
        pages.append({
            "page_number": page_num + 1,
            "text": text
        })
    doc.close()
    return pages
```

### New File: `backend/pipeline/ocr.py`

```python
"""
OCR fallback for scanned PDF pages using pytesseract + PIL.
Only called when a page has insufficient extractable text.
"""
import fitz
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def ocr_page(fitz_page) -> str:
    """
    Render a PyMuPDF page to image and run tesseract OCR on it.
    Returns extracted text string.
    """
    try:
        # Render at 2x scale for better OCR accuracy (300 DPI equivalent)
        mat = fitz.Matrix(2.0, 2.0)
        pix = fitz_page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        
        image = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(image, lang="eng")
        
        logger.info(f"OCR extracted {len(text)} chars")
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return ""
```

### New Dependencies (add to `requirements.txt`)

```
pytesseract==0.3.10
Pillow==10.3.0
```

### System Requirement
Tesseract binary must be installed on the OS.

```bash
# Ubuntu/Debian
apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Frontend Impact
None. Fully backend-transparent. The upload response will now include correct chunk counts even for scanned PDFs.

---

## 3. Fix 2 — Persistent Session Storage (SQLite)

### What & Why
V1 stores conversation memory in a Python dict — lost on every server restart. Replace with SQLite via Python's built-in `sqlite3` module (zero new dependencies).

### New File: `backend/storage/session_store.py`

```python
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
```

### Modified File: `backend/rag/memory.py`

Replace the entire file:

```python
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
```

### Modified File: `backend/main.py`

Add to startup:

```python
from storage.session_store import init_db

@app.on_event("startup")
async def startup():
    ChromaStore.initialize()
    init_db()  # ADD THIS LINE
```

### Frontend Impact
None. Sessions now persist across server restarts transparently.

---

## 4. Fix 3 — JWT Authentication

### What & Why
Without auth, any user can delete documents uploaded by others. V2 adds simple email+password auth with JWT tokens. Each user's documents are namespaced by `user_id` in ChromaDB metadata and the file manifest.

### Scope
Simple self-contained auth — no external service. Passwords hashed with `bcrypt`. Tokens are JWT (HS256). No email verification for simplicity.

### New Dependencies

```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### New File: `backend/storage/user_store.py`

```python
"""
SQLite user store. Table: users(id, email, hashed_password, created_at)
"""
import sqlite3
import uuid
from pathlib import Path
from core.config import settings

DB_PATH = settings.BASE_DIR / "data" / "users.db"

def _conn():
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c

def init_users_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def create_user(email: str, hashed_password: str) -> dict:
    user_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO users (id, email, hashed_password) VALUES (?, ?, ?)",
            (user_id, email, hashed_password)
        )
        conn.commit()
    return {"id": user_id, "email": email}

def get_user_by_email(email: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None

def get_user_by_id(user_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None
```

### New File: `backend/api/auth.py`

```python
"""
Auth utilities: password hashing, JWT creation/verification.
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from core.config import settings
from storage.user_store import get_user_by_id

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency. Returns user dict or raises 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(user_id)
    if not user:
        raise credentials_exception
    return user
```

### New File: `backend/api/routes/auth_routes.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from storage.user_store import create_user, get_user_by_email
from api.auth import hash_password, verify_password, create_access_token

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str  # min 8 chars enforced on FE

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    if get_user_by_email(req.email):
        raise HTTPException(400, "Email already registered.")
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")
    
    hashed = hash_password(req.password)
    user = create_user(req.email, hashed)
    token = create_access_token(user["id"])
    return TokenResponse(access_token=token, user_id=user["id"], email=user["email"])

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid email or password.")
    token = create_access_token(user["id"])
    return TokenResponse(access_token=token, user_id=user["id"], email=user["email"])
```

### Modified: All Protected Routes

Add `current_user: dict = Depends(get_current_user)` to every route handler that reads/writes documents or queries. Pass `user_id = current_user["id"]` to ingestion and retrieval functions so data is scoped per user.

**`api/routes/documents.py` — upload endpoint example:**

```python
from api.auth import get_current_user

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)  # ADD
):
    user_id = current_user["id"]
    # Pass user_id to ingest_pdf so metadata and manifest are scoped
    result = ingest_pdf(content, file.filename, user_id=user_id)
    ...
```

**`pipeline/ingestion.py` — add `user_id` to metadata:**

```python
def ingest_pdf(file_bytes: bytes, original_filename: str, user_id: str) -> Dict:
    ...
    metadatas = [
        {
            "doc_id": doc_id,
            "doc_name": original_filename,
            "page_number": c["page_number"],
            "chunk_index": c["chunk_index"],
            "user_id": user_id  # ADD
        }
        for c in chunks
    ]
```

**`pipeline/retriever.py` — always filter by user_id:**

```python
def retrieve(self, question: str, user_id: str, doc_filter=None):
    where = {"user_id": {"$eq": user_id}}
    if doc_filter:
        where = {"$and": [{"user_id": {"$eq": user_id}}, {"doc_id": {"$in": doc_filter}}]}
    ...
```

### Modified: `backend/core/config.py`

Add:

```python
JWT_SECRET: str = "change-this-in-production-use-long-random-string"
JWT_EXPIRE_HOURS: int = 24
```

### Modified: `backend/main.py`

```python
from api.routes import auth_routes
from storage.user_store import init_users_db

@app.on_event("startup")
async def startup():
    ChromaStore.initialize()
    init_db()
    init_users_db()  # ADD

app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
```

### Frontend — New Files

**`frontend/hooks/useAuth.ts`**

```typescript
"use client";
import { useState, useCallback } from "react";
import axios from "axios";
import { API_BASE_URL } from "@/lib/constants";

interface AuthState {
  token: string | null;
  userId: string | null;
  email: string | null;
}

export function useAuth() {
  const [auth, setAuth] = useState<AuthState>(() => {
    // Hydrate from localStorage on mount
    if (typeof window === "undefined") return { token: null, userId: null, email: null };
    return {
      token: localStorage.getItem("auth_token"),
      userId: localStorage.getItem("auth_user_id"),
      email: localStorage.getItem("auth_email"),
    };
  });

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await axios.post(`${API_BASE_URL}/auth/login`, { email, password });
    localStorage.setItem("auth_token", data.access_token);
    localStorage.setItem("auth_user_id", data.user_id);
    localStorage.setItem("auth_email", data.email);
    setAuth({ token: data.access_token, userId: data.user_id, email: data.email });
    return data;
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const { data } = await axios.post(`${API_BASE_URL}/auth/register`, { email, password });
    localStorage.setItem("auth_token", data.access_token);
    localStorage.setItem("auth_user_id", data.user_id);
    localStorage.setItem("auth_email", data.email);
    setAuth({ token: data.access_token, userId: data.user_id, email: data.email });
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user_id");
    localStorage.removeItem("auth_email");
    setAuth({ token: null, userId: null, email: null });
  }, []);

  return { ...auth, isAuthenticated: !!auth.token, login, register, logout };
}
```

Add `Authorization: Bearer {token}` header to all axios calls in `frontend/lib/api.ts`:

```typescript
// Modify the axios instance
const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

**`frontend/components/auth/LoginModal.tsx`** — standard email/password form with register/login toggle. Shows on app load if no token present. On success sets token and dismisses modal.

### Where it sits in the UI
- App load → check `localStorage` for token → if missing, show `LoginModal` as a centered overlay
- Header shows logged-in email + logout button
- All API calls automatically include the Bearer token via axios interceptor

---

## 5. Fix 4 — Gemini Rate Limit Queue

### What & Why
Gemini free tier: 15 RPM. Under concurrent usage, raw API calls fail with 429. Fix: a token bucket / async queue that serializes Gemini calls and retries with backoff.

### New File: `backend/rag/rate_limiter.py`

```python
"""
Async rate limiter for Gemini API — 15 RPM token bucket.
Wraps all Gemini calls. Thread-safe via asyncio.Lock.
"""
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class GeminiRateLimiter:
    """
    Token bucket: 15 requests per 60 seconds.
    Each request consumes 1 token. Tokens refill over time.
    """
    def __init__(self, rpm: int = 14):  # Use 14 to stay safely under 15
        self.rpm = rpm
        self.min_interval = 60.0 / rpm  # seconds between requests
        self._lock = asyncio.Lock()
        self._last_request_time = 0.0

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            wait = self._last_request_time + self.min_interval - now
            if wait > 0:
                logger.debug(f"Rate limiter: waiting {wait:.2f}s")
                await asyncio.sleep(wait)
            self._last_request_time = time.monotonic()

_limiter = GeminiRateLimiter(rpm=14)

async def with_rate_limit(coro):
    """Wrap any async coroutine with rate limiting + exponential backoff retry."""
    max_retries = 3
    for attempt in range(max_retries):
        await _limiter.acquire()
        try:
            return await coro
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 2 ** attempt * 5  # 5s, 10s, 20s
                logger.warning(f"Gemini 429. Retry {attempt+1}/{max_retries} in {wait}s")
                await asyncio.sleep(wait)
            else:
                raise
    raise RuntimeError("Gemini API rate limit exceeded after retries.")
```

### Modified: `backend/rag/gemini_client.py`

Convert synchronous Gemini calls to async and wrap with rate limiter:

```python
import asyncio
import google.generativeai as genai
from rag.rate_limiter import with_rate_limit
from core.config import settings
from typing import AsyncGenerator

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = genai.GenerativeModel(settings.GEMINI_MODEL)

async def generate_async(prompt: str, system: str = "") -> str:
    """Async non-streaming generation with rate limiting."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    
    async def _call():
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: _model.generate_content(full_prompt)
        )
        return response.text
    
    return await with_rate_limit(_call())

async def generate_stream_async(prompt: str, system: str = "") -> AsyncGenerator[str, None]:
    """Async streaming generation with rate limiting."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    await _limiter.acquire()  # acquire once before streaming starts
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: _model.generate_content(full_prompt, stream=True)
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text

# Keep sync versions as thin wrappers for non-route code (e.g., evaluation)
def generate(prompt: str, system: str = "") -> str:
    return asyncio.run(generate_async(prompt, system))
```

### Modified: `backend/rag/engine.py`

Change `answer` and `answer_stream` to use `generate_async` / `generate_stream_async`. Make route handlers `async def`.

### Modified: `backend/api/routes/query.py`

Change `ask` endpoint from `def` to `async def`:

```python
@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    ...
    return await engine.answer(...)
```

### Frontend Impact
None. The queue is fully server-side. Users may notice slightly longer waits under concurrent load — acceptable for free tier.

---

## 6. Fix 5 — Multi-file Upload with Progress

### What & Why
V1 UI accepts one file at a time. V2 supports dragging multiple PDFs at once with a per-file progress indicator.

### Modified: `backend/api/routes/documents.py`

Add a batch upload endpoint:

```python
from typing import List as PyList

@router.post("/upload-batch")
async def upload_batch(
    files: PyList[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload multiple PDFs. Returns array of results, one per file.
    Failed files are included with error field set, not a 500.
    """
    results = []
    for file in files:
        try:
            content = await file.read()
            result = ingest_pdf(content, file.filename, user_id=current_user["id"])
            results.append({"success": True, **result})
        except Exception as e:
            results.append({
                "success": False,
                "doc_name": file.filename,
                "error": str(e)
            })
    return {"results": results, "total": len(files),
            "succeeded": sum(1 for r in results if r["success"])}
```

### Modified: `frontend/components/documents/DocumentUpload.tsx`

Replace single-file input with:

```tsx
"use client";
import { useState, useCallback } from "react";
import { Upload, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { API_BASE_URL } from "@/lib/constants";
import axios from "axios";

interface FileProgress {
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  message?: string;
}

interface Props {
  onUploadComplete: () => void;
}

export function DocumentUpload({ onUploadComplete }: Props) {
  const [files, setFiles] = useState<FileProgress[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const pdfs = Array.from(newFiles).filter(f => f.type === "application/pdf");
    setFiles(prev => [
      ...prev,
      ...pdfs.map(f => ({ file: f, status: "pending" as const }))
    ]);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(e.dataTransfer.files);
  }, [addFiles]);

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadAll = async () => {
    if (files.length === 0 || isUploading) return;
    setIsUploading(true);

    // Upload one at a time to show per-file progress
    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== "pending") continue;
      
      setFiles(prev => prev.map((f, idx) =>
        idx === i ? { ...f, status: "uploading" } : f
      ));
      
      try {
        const form = new FormData();
        form.append("file", files[i].file);
        const token = localStorage.getItem("auth_token");
        
        const { data } = await axios.post(`${API_BASE_URL}/documents/upload`, form, {
          headers: {
            "Content-Type": "multipart/form-data",
            "Authorization": `Bearer ${token}`
          }
        });
        
        setFiles(prev => prev.map((f, idx) =>
          idx === i ? { ...f, status: "done", message: `${data.total_chunks} chunks indexed` } : f
        ));
      } catch (err: any) {
        setFiles(prev => prev.map((f, idx) =>
          idx === i ? { ...f, status: "error", message: err.response?.data?.detail || "Failed" } : f
        ));
      }
    }

    setIsUploading(false);
    onUploadComplete();
    // Clear done files after 3 seconds
    setTimeout(() => setFiles(prev => prev.filter(f => f.status !== "done")), 3000);
  };

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-input")?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors
          ${isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}
      >
        <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          Drop PDFs here or <span className="text-primary">browse</span>
        </p>
        <p className="text-xs text-muted-foreground/60 mt-1">Multiple files supported</p>
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
      </div>

      {/* File list with per-file status */}
      {files.length > 0 && (
        <div className="space-y-1.5">
          {files.map((fp, i) => (
            <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 text-sm">
              {fp.status === "pending" && <div className="w-4 h-4 rounded-full border-2 border-border flex-shrink-0" />}
              {fp.status === "uploading" && <Loader2 className="w-4 h-4 animate-spin text-primary flex-shrink-0" />}
              {fp.status === "done" && <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />}
              {fp.status === "error" && <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0" />}
              
              <div className="flex-1 min-w-0">
                <p className="truncate font-medium">{fp.file.name}</p>
                {fp.message && (
                  <p className={`text-xs ${fp.status === "error" ? "text-destructive" : "text-muted-foreground"}`}>
                    {fp.message}
                  </p>
                )}
              </div>
              
              {fp.status === "pending" && (
                <button onClick={() => removeFile(i)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}

          {files.some(f => f.status === "pending") && (
            <button
              onClick={uploadAll}
              disabled={isUploading}
              className="w-full py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium
                         hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {isUploading ? "Uploading..." : `Upload ${files.filter(f => f.status === "pending").length} file(s)`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 7. Fix 6 — Table Extraction (camelot)

### What & Why
Tables in PDFs are extracted as garbled plain text by default. `camelot-py` extracts tables as structured data which we then convert to markdown before chunking — preserving row/column relationships.

### New Dependency

```
camelot-py[cv]==0.11.0
ghostscript  # system dependency
opencv-python-headless==4.9.0.80
```

### System Requirement

```bash
# Ubuntu
apt-get install ghostscript

# macOS
brew install ghostscript
```

### New File: `backend/pipeline/table_extractor.py`

```python
"""
Extract tables from PDFs using camelot and convert to markdown.
Called from ingestion.py after standard text extraction.
Tables are appended to the text of the page they appear on.
"""
import camelot
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

def extract_tables_from_page(pdf_path: Path, page_number: int) -> str:
    """
    Extract all tables from a specific page.
    Returns markdown string of all tables found (empty string if none).
    page_number is 1-indexed.
    """
    try:
        tables = camelot.read_pdf(
            str(pdf_path),
            pages=str(page_number),
            flavor="lattice"  # For bordered tables; fall back to "stream" if 0 found
        )
        
        if len(tables) == 0:
            # Try stream flavor (for tables without visible borders)
            tables = camelot.read_pdf(
                str(pdf_path),
                pages=str(page_number),
                flavor="stream"
            )
        
        if len(tables) == 0:
            return ""
        
        markdown_tables = []
        for table in tables:
            df = table.df
            if df.empty:
                continue
            # Convert DataFrame to markdown
            md = df.to_markdown(index=False)
            markdown_tables.append(md)
        
        return "\n\n".join(markdown_tables)
    
    except Exception as e:
        logger.warning(f"Table extraction failed for page {page_number}: {e}")
        return ""
```

### Modified: `backend/pipeline/ingestion.py`

In `extract_pages`, append table markdown to page text:

```python
from pipeline.table_extractor import extract_tables_from_page

def extract_pages(pdf_path: Path) -> List[Dict]:
    pages = []
    doc = fitz.open(str(pdf_path))
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        
        if len(text) < 50:
            text = ocr_page(page)
        
        # Extract tables and append as structured markdown
        table_md = extract_tables_from_page(pdf_path, page_num + 1)
        if table_md:
            text = text + "\n\n[TABLES ON THIS PAGE]\n" + table_md
        
        pages.append({"page_number": page_num + 1, "text": text})
    doc.close()
    return pages
```

### Also add to `requirements.txt`

```
tabulate==0.9.0  # required by df.to_markdown()
pandas==2.2.2    # required by camelot DataFrame output
```

---

## 8. Enhancement 1 — Hybrid Search (BM25 + Semantic)

### What & Why
Pure semantic search misses exact keyword matches (e.g., "Policy GDPR-2024-v3", employee IDs, product codes). BM25 is a classical keyword search algorithm. Combining both with Reciprocal Rank Fusion (RRF) gives best of both worlds.

### New File: `backend/pipeline/bm25_index.py`

```python
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
```

### New Dependency

```
rank-bm25==0.2.2
```

### Modified: `backend/pipeline/ingestion.py`

Add at end of `ingest_pdf`:

```python
from pipeline.bm25_index import rebuild_index

def ingest_pdf(...) -> Dict:
    ...
    ChromaStore.add_chunks(...)
    rebuild_index()  # Rebuild BM25 after every new document
    ...
```

### Modified: `backend/pipeline/retriever.py`

Replace the `retrieve` method with hybrid search + Reciprocal Rank Fusion:

```python
from pipeline.bm25_index import get_bm25_index

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
        results = []
        for chunk_id in fused_ids[:self.top_k]:
            if chunk_id in sem_map:
                s = sem_map[chunk_id]
                similarity = 1.0 - s["distance"]
                results.append(ChunkResult(
                    text=s["text"],
                    doc_name=s["metadata"].get("doc_name", "Unknown"),
                    page_number=s["metadata"].get("page_number", 0),
                    chunk_index=s["metadata"].get("chunk_index", 0),
                    similarity_score=round(similarity, 4)
                ))
        
        return results
```

---

## 9. Enhancement 2 — Query Rewriting

### What & Why
Users often ask ambiguous or context-dependent questions like "What about sick leave?" as a follow-up. Query rewriting uses the conversation history to produce a standalone, specific question before retrieval — improving search recall.

### New File: `backend/rag/query_rewriter.py`

```python
"""
Query rewriter: takes conversation history + current question,
returns a clearer, standalone search query.
Only activates when there is prior conversation history.
"""
from rag.gemini_client import generate
import logging

logger = logging.getLogger(__name__)

REWRITE_PROMPT = """You are a search query optimizer for a document retrieval system.

Given the conversation history and the user's latest question, rewrite the question as a clear, specific, standalone search query that includes all necessary context from the history.

Rules:
- Return ONLY the rewritten query. No explanation, no quotes, no preamble.
- If the question is already clear and standalone, return it unchanged.
- Keep it under 50 words.
- Make it specific enough to retrieve the right document sections.

Conversation history:
{history}

Latest question: {question}

Rewritten search query:"""

def rewrite_query(question: str, history: list) -> str:
    """
    Returns rewritten query string.
    Falls back to original question on any error.
    Only rewrites if there is history (no point rewriting the first question).
    """
    if not history:
        return question
    
    try:
        history_str = "\n".join(
            f"{'User' if t['role'] == 'user' else 'Assistant'}: {t['content']}"
            for t in history[-4:]  # Last 2 turns is enough context
        )
        prompt = REWRITE_PROMPT.format(history=history_str, question=question)
        rewritten = generate(prompt).strip()
        
        if rewritten and len(rewritten) < 500:  # Sanity check
            logger.info(f"Query rewritten: '{question}' → '{rewritten}'")
            return rewritten
    except Exception as e:
        logger.warning(f"Query rewrite failed: {e}")
    
    return question
```

### Modified: `backend/rag/engine.py`

```python
from rag.query_rewriter import rewrite_query

class RAGEngine:
    def answer(self, question: str, session_id: str, ...):
        history = MemoryManager.get_history(session_id)
        
        # Rewrite query for better retrieval
        search_query = rewrite_query(question, history)
        
        # Use rewritten query for retrieval, original question for generation
        chunks = self.retriever.retrieve(search_query, ...)
        
        # Build prompt with ORIGINAL question (not rewritten)
        prompt = RAG_USER_TEMPLATE.format(
            history=...,
            context=...,
            question=question  # Always use original for the final answer
        )
        ...
```

---

## 10. Enhancement 3 — Cross-Encoder Re-ranking

### What & Why
After BM25+semantic retrieval gives us top-10 candidates, a cross-encoder re-ranker scores each (query, chunk) pair together — far more accurate than embedding similarity alone because it processes both query and chunk jointly.

### New Dependency

```
sentence-transformers==3.0.1  # already in requirements; cross-encoders included
```

### New File: `backend/pipeline/reranker.py`

```python
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
```

### Modified: `backend/pipeline/retriever.py`

```python
from pipeline.reranker import rerank

class Retriever:
    def retrieve(self, question: str, ...) -> List[ChunkResult]:
        # ... existing hybrid retrieval that returns top_k*2 candidates ...
        candidates = [...]  # 10 candidates from hybrid search
        
        # Re-rank candidates to get final top_k
        return rerank(question, candidates, top_k=self.top_k)
```

### Config note
Re-ranking adds ~200-500ms per query on CPU. Acceptable for this use case. To disable, set `ENABLE_RERANKING=false` in `.env` and skip the `rerank()` call.

---

## 11. Enhancement 4 — Multi-document Reasoning Prompt

### What & Why
When retrieved chunks come from multiple documents, the model should explicitly synthesize across them rather than just answering from the top chunk. A targeted prompt instruction handles this.

### Modified: `backend/rag/prompts.py`

Replace `RAG_SYSTEM_PROMPT` with:

```python
RAG_SYSTEM_PROMPT = """You are an Enterprise Knowledge Assistant. Answer employee questions accurately using ONLY the provided document excerpts.

Rules:
1. Answer ONLY based on the provided context. Do not use external knowledge.
2. If the answer is not found in the context, respond with exactly: "I could not find information about this in the available documents. Please check the relevant source documents directly or contact the relevant team."
3. If information comes from MULTIPLE documents, explicitly synthesize and reconcile them. Mention if documents agree or if there are differences.
4. Be concise and direct. No filler text.
5. Always maintain a professional, helpful tone.
6. When referencing specific information, naturally indicate which document it came from using the source labels in the excerpts.
7. Do not fabricate page numbers or document names not present in the excerpts."""

# Multi-source synthesis instruction (appended to user prompt when chunks span >1 doc)
MULTI_DOC_NOTE = """
Note: The excerpts above come from {num_docs} different documents ({doc_names}). 
Synthesize information across all sources in your answer. If sources conflict, note the discrepancy."""
```

### Modified: `backend/rag/engine.py`

In `_build_context` or just before building the prompt:

```python
def _get_multi_doc_note(self, chunks: List[ChunkResult]) -> str:
    from rag.prompts import MULTI_DOC_NOTE
    unique_docs = list({c.doc_name for c in chunks})
    if len(unique_docs) <= 1:
        return ""
    return MULTI_DOC_NOTE.format(
        num_docs=len(unique_docs),
        doc_names=", ".join(unique_docs)
    )

# In answer() and answer_stream():
context = self._build_context(chunks)
multi_doc_note = self._get_multi_doc_note(chunks)

prompt = RAG_USER_TEMPLATE.format(
    history=history_str,
    context=context + multi_doc_note,  # Append note
    question=question
)
```

---

## 12. Enhancement 5 — Deployment (Railway + Vercel)

### Backend: Railway

Railway provides a free tier with persistent storage and environment variable management.

#### New File: `backend/Procfile`

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### New File: `railway.json` (in `backend/`)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### Railway Setup Steps (document in README)

```
1. Push backend/ to a GitHub repo
2. Go to railway.app → New Project → Deploy from GitHub
3. Select the backend/ directory
4. Add environment variables:
   GEMINI_API_KEY = your_key
   JWT_SECRET = long_random_string
5. Add a Volume at /app/data (for ChromaDB and uploads persistence)
6. Deploy. Copy the Railway public URL.
```

#### Railway Note on Persistent Storage
Railway Volumes are required for ChromaDB and file uploads to persist across deployments. Without a volume, data resets on redeploy. Volume path: `/app/data`.

### Frontend: Vercel

#### New File: `frontend/vercel.json`

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "env": {
    "NEXT_PUBLIC_API_URL": "@next_public_api_url"
  }
}
```

#### New/Modified: `frontend/next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In production, NEXT_PUBLIC_API_URL points to Railway
    return [];
  },
  // Allow images from any domain (for future avatar/doc preview)
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }]
  }
};

module.exports = nextConfig;
```

#### Vercel Setup Steps (document in README)

```
1. Push frontend/ to GitHub
2. Go to vercel.com → New Project → Import from GitHub
3. Set root directory to frontend/
4. Add environment variable:
   NEXT_PUBLIC_API_URL = https://your-railway-backend-url.railway.app/api
5. Deploy.
```

#### CORS update for production

In `backend/core/config.py`:

```python
ALLOWED_ORIGINS: list = [
    "http://localhost:3000",
    "https://your-vercel-app.vercel.app"  # Add after Vercel deploy
]
```

Or set dynamically via env:

```python
ALLOWED_ORIGINS_STR: str = "http://localhost:3000"

@property
def ALLOWED_ORIGINS(self) -> list:
    return [o.strip() for o in self.ALLOWED_ORIGINS_STR.split(",")]
```

Then in `.env`: `ALLOWED_ORIGINS_STR=http://localhost:3000,https://yourapp.vercel.app`

---

## 13. Enhancement 6 — Document Versioning

### What & Why
When a user re-uploads a document with the same name (e.g., updated HR policy), V1 creates a duplicate. V2 detects the name match, keeps the old version accessible, and marks the new one as current — without re-ingesting everything.

### New File: `backend/pipeline/version_manager.py`

```python
"""
Document versioning.
When a document with the same name as an existing one is uploaded,
the existing entry is archived (version_status = "archived")
and the new one is marked as "current".
"""
from storage.file_store import load_manifest, save_manifest
from storage.chroma_store import ChromaStore
from typing import Optional

def get_current_version(doc_name: str) -> Optional[dict]:
    """Find the current (non-archived) document entry with the given name."""
    manifest = load_manifest()
    for doc in manifest.values():
        if doc.get("doc_name") == doc_name and doc.get("version_status") != "archived":
            return doc
    return None

def archive_document(doc_id: str):
    """
    Mark an existing document as archived.
    ChromaDB chunks remain for reference but are excluded from search by default.
    """
    manifest = load_manifest()
    if doc_id in manifest:
        manifest[doc_id]["version_status"] = "archived"
        manifest[doc_id]["archived_at"] = __import__("datetime").datetime.utcnow().isoformat()
        save_manifest(manifest)
        # Tag ChromaDB records so retriever can optionally exclude them
        # Note: ChromaDB doesn't support update metadata directly on filtered docs
        # We use the version_status field in the manifest; retriever checks it.

def handle_version_on_upload(doc_name: str) -> Optional[str]:
    """
    Call before ingestion.
    If a current version exists with the same name, archive it.
    Returns the archived doc_id (or None if no previous version).
    """
    existing = get_current_version(doc_name)
    if existing:
        archive_document(existing["doc_id"])
        return existing["doc_id"]
    return None
```

### Modified: `backend/pipeline/ingestion.py`

```python
from pipeline.version_manager import handle_version_on_upload

def ingest_pdf(file_bytes: bytes, original_filename: str, user_id: str = "") -> Dict:
    # Check for existing version with same name
    archived_id = handle_version_on_upload(original_filename)
    if archived_id:
        logger.info(f"Archived previous version of {original_filename} (id={archived_id})")
    
    # ... rest of ingestion unchanged ...
```

### Modified: `backend/storage/file_store.py`

Update `register_document` to include `version_status`:

```python
def register_document(doc_id: str, doc_name: str, total_pages: int,
                       total_chunks: int, file_size_kb: float):
    manifest = load_manifest()
    manifest[doc_id] = {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "file_size_kb": round(file_size_kb, 2),
        "uploaded_at": datetime.utcnow().isoformat(),
        "version_status": "current"  # ADD
    }
    save_manifest(manifest)
```

### Modified: `backend/api/routes/documents.py`

Update list endpoint to show version info:

```python
@router.get("/")
def list_documents(include_archived: bool = False):
    docs = get_all_documents()
    if not include_archived:
        docs = [d for d in docs if d.get("version_status") != "archived"]
    return {"documents": docs, "total": len(docs)}
```

### Frontend: `DocumentCard.tsx`

Show version badge if a document is the current version and has archived predecessors (check via `version_status` field). Add a "Version History" tooltip showing previous upload dates.

---

## 14. Enhancement 7 — Evaluation Dashboard UI

### What & Why
The V1 evaluation framework runs as a CLI script. V2 exposes evaluation results through an API and displays them in a dedicated dashboard tab in the UI.

### Modified: `backend/api/routes/stats.py`

Add eval endpoint:

```python
import json
from pathlib import Path
from evaluation.evaluator import evaluate

@router.post("/evaluate")
async def run_evaluation():
    """
    Run evaluation against test cases.
    Returns per-question results + aggregate metrics.
    Only runs if documents are already ingested.
    """
    from storage.chroma_store import ChromaStore
    if ChromaStore.get_collection().count() == 0:
        raise HTTPException(400, "No documents ingested. Upload documents first.")
    
    try:
        results = evaluate()  # From evaluation/evaluator.py
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
def get_last_evaluation():
    """Return cached last evaluation result from disk."""
    cache_path = Path("data/last_eval.json")
    if not cache_path.exists():
        raise HTTPException(404, "No evaluation has been run yet.")
    return json.loads(cache_path.read_text())
```

Update `evaluation/evaluator.py` to save results to disk:

```python
def evaluate():
    ...
    # Save to disk for dashboard
    cache_path = Path(__file__).parent.parent / "data" / "last_eval.json"
    cache_path.write_text(json.dumps({
        "run_at": datetime.utcnow().isoformat(),
        "summary": {
            "avg_semantic_similarity": round(avg_sim, 4),
            "source_attribution_accuracy": round(source_accuracy, 4)
        },
        "results": results
    }, indent=2))
    
    return results
```

### New Frontend: `frontend/components/dashboard/EvalDashboard.tsx`

```tsx
"use client";
import { useState } from "react";
import { Play, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "@/lib/constants";

interface EvalResult {
  id: string;
  question: string;
  expected: string;
  actual: string;
  semantic_similarity: number;
  source_found: boolean;
  confidence: number;
}

interface EvalSummary {
  total_cases: number;
  avg_semantic_similarity: number;
  source_attribution_accuracy: number;
  avg_confidence: number;
}

export function EvalDashboard() {
  const [isRunning, setIsRunning] = useState(false);
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [results, setResults] = useState<EvalResult[]>([]);
  const [error, setError] = useState("");

  const runEval = async () => {
    setIsRunning(true);
    setError("");
    try {
      const token = localStorage.getItem("auth_token");
      const { data } = await axios.post(`${API_BASE_URL}/stats/evaluate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSummary(data.summary);
      setResults(data.results);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Evaluation failed.");
    }
    setIsRunning(false);
  };

  const simColor = (sim: number) =>
    sim >= 0.7 ? "text-green-500" : sim >= 0.4 ? "text-amber-500" : "text-red-500";

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-sm">Evaluation Dashboard</h2>
        <button
          onClick={runEval}
          disabled={isRunning}
          className="flex items-center gap-1.5 text-xs bg-primary text-primary-foreground
                     px-3 py-1.5 rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          <Play className="w-3 h-3" />
          {isRunning ? "Running..." : "Run Eval"}
        </button>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      {summary && (
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: "Avg Similarity", value: `${(summary.avg_semantic_similarity * 100).toFixed(1)}%` },
            { label: "Source Accuracy", value: `${(summary.source_attribution_accuracy * 100).toFixed(1)}%` },
            { label: "Avg Confidence", value: `${(summary.avg_confidence * 100).toFixed(1)}%` },
            { label: "Test Cases", value: summary.total_cases }
          ].map(({ label, value }) => (
            <div key={label} className="bg-muted/50 rounded-lg p-2.5 text-center">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-lg font-semibold">{value}</p>
            </div>
          ))}
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {results.map((r) => (
            <div key={r.id} className="border border-border rounded-lg p-2.5 text-xs space-y-1">
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium">{r.question}</p>
                {r.source_found
                  ? <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                  : <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />}
              </div>
              <p className={`font-mono ${simColor(r.semantic_similarity)}`}>
                Similarity: {(r.semantic_similarity * 100).toFixed(1)}%
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

Place this component in the sidebar below `StatsPanel`, visible in a "Evaluation" tab.

---

## 15. Updated Requirements & Dependencies

Full `backend/requirements.txt` for V2:

```
# Web framework
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9

# Data validation
pydantic==2.7.1
pydantic-settings==2.3.1
pydantic[email]==2.7.1

# PDF processing
PyMuPDF==1.24.5
pytesseract==0.3.10
Pillow==10.3.0
camelot-py[cv]==0.11.0
opencv-python-headless==4.9.0.80
pandas==2.2.2
tabulate==0.9.0

# AI / ML
sentence-transformers==3.0.1
chromadb==0.5.3
rank-bm25==0.2.2

# LLM
google-generativeai==0.7.2

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Utils
numpy==1.26.4
python-dotenv==1.0.1
```

---

## 16. Updated Environment Variables

Full `backend/.env` for V2:

```env
# LLM
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Auth
JWT_SECRET=replace-with-a-64-char-random-string-in-production
JWT_EXPIRE_HOURS=24

# RAG config
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K=5
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_MEMORY_TURNS=6
ENABLE_RERANKING=true
BM25_WEIGHT=0.3
SEMANTIC_WEIGHT=0.7

# CORS (comma-separated for production)
ALLOWED_ORIGINS_STR=http://localhost:3000

# Rate limiter
GEMINI_RPM_LIMIT=14
```

---

## 17. Updated Repository Structure (V2 diff)

Changes from V1 structure. `+` = new file, `~` = modified file.

```
backend/
├── main.py                        ~ startup: init_db, init_users_db, auth router
├── api/
│   ├── auth.py                    + JWT utilities, get_current_user dependency
│   ├── routes/
│   │   ├── auth_routes.py         + /register, /login
│   │   ├── documents.py           ~ upload: user_id scoping, multi-file batch endpoint
│   │   ├── query.py               ~ async def, user_id from token
│   │   └── stats.py               ~ /evaluate and /evaluate/last endpoints
├── core/
│   └── config.py                  ~ JWT_SECRET, JWT_EXPIRE_HOURS, ENABLE_RERANKING,
│                                    BM25_WEIGHT, ALLOWED_ORIGINS_STR
├── pipeline/
│   ├── ingestion.py               ~ OCR fallback, table extraction, version check, rebuild BM25
│   ├── retriever.py               ~ hybrid search (BM25+semantic), re-ranking
│   ├── ocr.py                     + pytesseract OCR fallback
│   ├── table_extractor.py         + camelot table → markdown
│   ├── bm25_index.py              + BM25 index with pickle persistence
│   ├── reranker.py                + cross-encoder re-ranker
│   └── version_manager.py         + document versioning logic
├── rag/
│   ├── engine.py                  ~ async, query rewriting, multi-doc note
│   ├── gemini_client.py           ~ async + rate-limited
│   ├── memory.py                  ~ delegates to SQLite session_store
│   ├── prompts.py                 ~ MULTI_DOC_NOTE, updated system prompt
│   ├── query_rewriter.py          + LLM-based query rewriting
│   └── rate_limiter.py            + async token bucket for Gemini
├── storage/
│   ├── chroma_store.py            (unchanged)
│   ├── file_store.py              ~ register_document: doc_id param, version_status
│   ├── session_store.py           + SQLite conversation sessions
│   └── user_store.py              + SQLite users table
├── evaluation/
│   └── evaluator.py               ~ saves results to data/last_eval.json
└── data/
    ├── uploads/                   (unchanged)
    ├── chroma_db/                 (unchanged)
    ├── sessions.db                + auto-created on startup
    ├── users.db                   + auto-created on startup
    ├── bm25_index.pkl             + auto-created on first ingestion
    └── last_eval.json             + auto-created on first eval run

frontend/
├── components/
│   ├── auth/
│   │   └── LoginModal.tsx         + email/password login + register form
│   ├── documents/
│   │   └── DocumentUpload.tsx     ~ multi-file drag & drop with per-file progress
│   └── dashboard/
│       └── EvalDashboard.tsx      + evaluation results panel
├── hooks/
│   └── useAuth.ts                 + JWT auth state management
└── lib/
    └── api.ts                     ~ axios interceptor for Bearer token
```
