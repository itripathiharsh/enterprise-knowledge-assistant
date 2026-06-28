# AGENT INSTRUCTIONS — Enterprise Knowledge Assistant
# Build Order: Complete Project, End to End

---

## CRITICAL: READ THIS FIRST

You are an AI coding agent. You have been given three specification documents:

1. `TECHNICAL_SPEC.md` — V1 complete system spec (backend + frontend + AI pipeline)
2. `V2_FEATURES_SPEC.md` — V2 enhancements and fixes layered on top of V1
3. This file (`AGENT_INSTRUCTIONS.md`) — your step-by-step build order

**Your job:** Read all three documents fully before writing a single line of code. Then execute the steps below in exact order. Do not skip steps. Do not combine steps. Complete and verify each step before moving to the next.

**Rules:**
- Never assume. If a spec says to create a file, create the exact file at the exact path.
- If a spec provides full code for a file, use it exactly. Do not paraphrase or simplify.
- After every phase, run the verification command listed. Only proceed when it passes.
- If something fails, fix it before moving forward. Do not paper over errors.
- All paths are relative to the project root `enterprise-knowledge-assistant/`.

---

## API KEYS — Inject These Exactly

Before starting, register these values. Use them wherever the spec says `your_key_here`.

```
GROQ_API_KEY = [USER WILL PROVIDE — do not hardcode, leave placeholder in .env]
GEMINI_API_KEY = [USER WILL PROVIDE — do not hardcode, leave placeholder in .env]
JWT_SECRET = generate a 64-character random alphanumeric string and use it
```

> The user will fill in API keys manually after you create the `.env` file. Your job is to create the correct `.env` with the right key names and placeholders.

---

## PHASE 0 — Project Scaffold

**Goal:** Create the root folder and git repo.

### Step 0.1 — Create root directory and git init

```bash
mkdir enterprise-knowledge-assistant
cd enterprise-knowledge-assistant
git init
```

### Step 0.2 — Create root `.gitignore`

Create file at `.gitignore`:

```
# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/
dist/
build/

# Env files
.env
.env.local
*.env

# Data (never commit uploaded files or vector DB)
backend/data/

# Node
node_modules/
.next/
*.log

# OS
.DS_Store
Thumbs.db

# Models cache (sentence-transformers downloads here)
backend/.cache/
```

### Step 0.3 — Copy spec documents into repo

Place all three spec files at the root level:
- `TECHNICAL_SPEC.md`
- `V2_FEATURES_SPEC.md`
- `AGENT_INSTRUCTIONS.md`

### ✅ Phase 0 Verification

```bash
ls enterprise-knowledge-assistant/
# Expected: .git  .gitignore  TECHNICAL_SPEC.md  V2_FEATURES_SPEC.md  AGENT_INSTRUCTIONS.md
```

---

## PHASE 1 — Backend Scaffold

**Goal:** Create the full backend folder structure with all `__init__.py` files and config before writing any logic.

### Step 1.1 — Create directory tree

```bash
mkdir -p backend/api/routes
mkdir -p backend/core
mkdir -p backend/pipeline
mkdir -p backend/rag
mkdir -p backend/models
mkdir -p backend/storage
mkdir -p backend/evaluation
mkdir -p backend/data/uploads
mkdir -p backend/data/chroma_db
```

### Step 1.2 — Create all `__init__.py` files

Create empty `__init__.py` in:
- `backend/api/__init__.py`
- `backend/api/routes/__init__.py`
- `backend/core/__init__.py`
- `backend/pipeline/__init__.py`
- `backend/rag/__init__.py`
- `backend/models/__init__.py`
- `backend/storage/__init__.py`
- `backend/evaluation/__init__.py`

### Step 1.3 — Create `backend/requirements.txt`

Use the **V2 full requirements** from `V2_FEATURES_SPEC.md` Section 15. This is the final combined list — do not use the V1 list from `TECHNICAL_SPEC.md`.

### Step 1.4 — Create `backend/.env.example`

```env
# LLM — Primary (Groq)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# LLM — Fallback (Gemini)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Auth
JWT_SECRET=replace-with-64-char-random-string
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

# CORS
ALLOWED_ORIGINS_STR=http://localhost:3000

# Rate limiter
GEMINI_RPM_LIMIT=14
```

### Step 1.5 — Create `backend/.env`

Copy `.env.example` to `.env`. Leave API key placeholders as-is — user will fill them.

Generate `JWT_SECRET` value now: create a 64-char random alphanumeric string and insert it.

### ✅ Phase 1 Verification

```bash
find backend -type f -name "*.py" | sort
# Expected: all __init__.py files listed

cat backend/requirements.txt | wc -l
# Expected: > 15 lines
```

---

## PHASE 2 — Backend Core & Config

**Goal:** Write config, exceptions, logging. No business logic yet.

### Step 2.1 — Create `backend/core/config.py`

Use the code from `TECHNICAL_SPEC.md` Section 6.2, then apply the V2 additions from `V2_FEATURES_SPEC.md`:
- Add `GROQ_API_KEY: str`
- Add `GROQ_MODEL: str = "llama-3.3-70b-versatile"`
- Add `JWT_SECRET: str`
- Add `JWT_EXPIRE_HOURS: int = 24`
- Add `ENABLE_RERANKING: bool = True`
- Add `BM25_WEIGHT: float = 0.3`
- Add `SEMANTIC_WEIGHT: float = 0.7`
- Add `GEMINI_RPM_LIMIT: int = 14`
- Replace `ALLOWED_ORIGINS: list` with `ALLOWED_ORIGINS_STR: str` + property

Final `Settings` class must have ALL fields from both specs combined.

### Step 2.2 — Create `backend/core/exceptions.py`

```python
class DocumentNotFoundError(Exception):
    pass

class IngestionError(Exception):
    pass

class RetrievalError(Exception):
    pass

class AuthError(Exception):
    pass
```

### Step 2.3 — Create `backend/core/logging.py`

```python
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
```

### ✅ Phase 2 Verification

```bash
cd backend
python -c "from core.config import settings; print(settings.GROQ_MODEL)"
# Expected: llama-3.3-70b-versatile
```

---

## PHASE 3 — Data Models

**Goal:** Create all Pydantic schemas.

### Step 3.1 — Create `backend/models/schemas.py`

Use the full code from `TECHNICAL_SPEC.md` Section 6.3 exactly as written.

### ✅ Phase 3 Verification

```bash
python -c "from models.schemas import AskRequest, AskResponse, DocumentInfo; print('OK')"
# Expected: OK
```

---

## PHASE 4 — Storage Layer

**Goal:** Build all storage modules. No AI code yet.

### Step 4.1 — Create `backend/storage/chroma_store.py`

Use code from `TECHNICAL_SPEC.md` Section 6.4 exactly.

### Step 4.2 — Create `backend/storage/file_store.py`

Use code from `TECHNICAL_SPEC.md` Section 6.5, then apply V2 modification from `V2_FEATURES_SPEC.md` Section 13:
- `register_document` must accept `doc_id` as a parameter (not generate it internally)
- Add `"version_status": "current"` field to every new manifest entry

### Step 4.3 — Create `backend/storage/session_store.py`

Use the full code from `V2_FEATURES_SPEC.md` Section 3 (Fix 2). This replaces the in-memory approach entirely — do not implement the V1 in-memory version.

### Step 4.4 — Create `backend/storage/user_store.py`

Use the full code from `V2_FEATURES_SPEC.md` Section 4 (Fix 3 — `user_store.py`).

### ✅ Phase 4 Verification

```bash
python -c "
from storage.chroma_store import ChromaStore
from storage.session_store import init_db
from storage.user_store import init_users_db
init_db()
init_users_db()
print('Storage OK')
"
# Expected: Storage OK
# Also check: backend/data/sessions.db and backend/data/users.db exist
```

---

## PHASE 5 — AI Pipeline (Ingestion)

**Goal:** Build the full ingestion pipeline including all V2 enhancements.

### Step 5.1 — Create `backend/pipeline/chunker.py`

Use full code from `TECHNICAL_SPEC.md` Section 6.6 exactly.

### Step 5.2 — Create `backend/pipeline/embedder.py`

Use full code from `TECHNICAL_SPEC.md` Section 6.7 exactly.

### Step 5.3 — Create `backend/pipeline/ocr.py`

Use full code from `V2_FEATURES_SPEC.md` Section 2 (Fix 1 — `ocr.py`).

### Step 5.4 — Create `backend/pipeline/table_extractor.py`

Use full code from `V2_FEATURES_SPEC.md` Section 7 (Fix 6 — `table_extractor.py`).

### Step 5.5 — Create `backend/pipeline/bm25_index.py`

Use full code from `V2_FEATURES_SPEC.md` Section 8 (Enhancement 1 — `bm25_index.py`).

### Step 5.6 — Create `backend/pipeline/version_manager.py`

Use full code from `V2_FEATURES_SPEC.md` Section 13 (Enhancement 6 — `version_manager.py`).

### Step 5.7 — Create `backend/pipeline/ingestion.py`

Start with the V1 code from `TECHNICAL_SPEC.md` Section 6.8, then apply ALL of these V2 modifications in order:

1. **OCR fallback** — from `V2_FEATURES_SPEC.md` Section 2: update `extract_pages` to call `ocr_page` when text < 50 chars
2. **Table extraction** — from `V2_FEATURES_SPEC.md` Section 7: call `extract_tables_from_page` and append markdown to page text
3. **Version check** — from `V2_FEATURES_SPEC.md` Section 13: call `handle_version_on_upload` at top of `ingest_pdf`
4. **user_id parameter** — add `user_id: str = ""` to `ingest_pdf` signature; include in chunk metadata
5. **BM25 rebuild** — call `rebuild_index()` after `ChromaStore.add_chunks()`
6. **Fix register_document call** — pass `doc_id` as first argument (V2 signature)

Final `ingest_pdf` signature must be:
```python
def ingest_pdf(file_bytes: bytes, original_filename: str, user_id: str = "") -> Dict:
```

### Step 5.8 — Create `backend/pipeline/reranker.py`

Use full code from `V2_FEATURES_SPEC.md` Section 10 (Enhancement 3 — `reranker.py`).

### Step 5.9 — Create `backend/pipeline/retriever.py`

Start with V1 code from `TECHNICAL_SPEC.md` Section 6.9, then fully replace the `retrieve` method with the hybrid search version from `V2_FEATURES_SPEC.md` Section 8 (Enhancement 1 — modified `retriever.py`).

Also add the re-ranking call from `V2_FEATURES_SPEC.md` Section 10 at the end of `retrieve`:
```python
# After building candidates list:
if settings.ENABLE_RERANKING:
    return rerank(question, candidates, top_k=self.top_k)
return candidates[:self.top_k]
```

### ✅ Phase 5 Verification

```bash
python -c "
from pipeline.chunker import RecursiveChunker
from pipeline.embedder import Embedder
c = RecursiveChunker()
chunks = c.chunk('This is a test sentence. ' * 30)
print(f'Chunker OK: {len(chunks)} chunks')
emb = Embedder.embed_single('test')
print(f'Embedder OK: {len(emb)} dims')
"
# Expected:
# Chunker OK: 2+ chunks
# Embedder OK: 384 dims
# (First run will download ~80MB model — expected)
```

---

## PHASE 6 — LLM Client (Groq + Gemini Fallback)

**Goal:** Build the unified LLM client with Groq primary and Gemini fallback.

### Step 6.1 — Create `backend/rag/llm_client.py`

> **Important:** This file is called `llm_client.py`, NOT `gemini_client.py`. The V1 spec uses `gemini_client.py` — ignore that name. Every import elsewhere that references `gemini_client` must instead import from `llm_client`.

Use this implementation:

```python
"""
Unified LLM client.
Primary: Groq (llama-3.3-70b-versatile) — fast, free
Fallback: Google Gemini 1.5 Flash — kicks in if Groq fails or rate-limits
"""
from groq import Groq
import google.generativeai as genai
from core.config import settings
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Initialize clients
groq_client = Groq(api_key=settings.GROQ_API_KEY)
genai.configure(api_key=settings.GEMINI_API_KEY)
_gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)


def generate(prompt: str, system: str = "") -> str:
    """
    Non-streaming generation.
    Tries Groq first. On any exception, falls back to Gemini.
    """
    try:
        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.warning(f"Groq failed: {e} — falling back to Gemini")
        try:
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            response = _gemini_model.generate_content(full_prompt)
            return response.text
        except Exception as e2:
            logger.error(f"Gemini also failed: {e2}")
            raise RuntimeError(f"Both LLMs failed. Groq: {e} | Gemini: {e2}")


def generate_stream(prompt: str, system: str = "") -> Generator[str, None, None]:
    """
    Streaming generation.
    Tries Groq streaming first. On any exception, falls back to Gemini streaming.
    """
    try:
        stream = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2,
            stream=True
        )
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                yield text

    except Exception as e:
        logger.warning(f"Groq stream failed: {e} — falling back to Gemini stream")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = _gemini_model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
```

### Step 6.2 — Create `backend/rag/rate_limiter.py`

Use full code from `V2_FEATURES_SPEC.md` Section 5 (Fix 4 — `rate_limiter.py`).

> Note: The rate limiter primarily protects the Gemini fallback path. Groq has its own internal rate handling.

### ✅ Phase 6 Verification

```
# SKIP running this step until user provides API keys in .env
# Mark as: PENDING KEY INJECTION
# The user must fill GROQ_API_KEY and GEMINI_API_KEY in backend/.env before this can be tested
```

---

## PHASE 7 — RAG Engine

**Goal:** Build prompts, memory, query rewriter, and the main RAG orchestrator.

### Step 7.1 — Create `backend/rag/prompts.py`

Use the V1 prompts from `TECHNICAL_SPEC.md` Section 11, then apply V2 modifications from `V2_FEATURES_SPEC.md` Section 11 (Enhancement 4):
- Replace `RAG_SYSTEM_PROMPT` with the updated multi-doc version
- Add `MULTI_DOC_NOTE` constant

Final file must contain: `RAG_SYSTEM_PROMPT`, `RAG_USER_TEMPLATE`, `FOLLOW_UP_PROMPT`, `SUMMARY_PROMPT`, `MULTI_DOC_NOTE`.

### Step 7.2 — Create `backend/rag/memory.py`

Use the **V2 version only** from `V2_FEATURES_SPEC.md` Section 3 (Fix 2 — `memory.py`). Do not implement the V1 in-memory version at all.

### Step 7.3 — Create `backend/rag/query_rewriter.py`

Use full code from `V2_FEATURES_SPEC.md` Section 9 (Enhancement 2).

Change the import at the top to use `llm_client` not `gemini_client`:
```python
from rag.llm_client import generate  # NOT gemini_client
```

### Step 7.4 — Create `backend/rag/engine.py`

Start with V1 code from `TECHNICAL_SPEC.md` Section 6.13, then apply these V2 modifications:

1. **Import fix** — change `from rag.gemini_client import generate, generate_stream` to `from rag.llm_client import generate, generate_stream`
2. **Query rewriting** — from `V2_FEATURES_SPEC.md` Section 9: add `rewrite_query` call at start of `answer()` and `answer_stream()`; use rewritten query for retrieval, original question for generation
3. **Multi-doc note** — from `V2_FEATURES_SPEC.md` Section 11: add `_get_multi_doc_note()` method; append result to context in prompt
4. **user_id threading** — `answer()` and `answer_stream()` must accept `user_id: str = ""` and pass it to `self.retriever.retrieve()`

Final `answer` signature:
```python
def answer(self, question: str, session_id: str,
           user_id: str = "", doc_filter: Optional[List[str]] = None) -> AskResponse:
```

### ✅ Phase 7 Verification

```bash
python -c "
from rag.prompts import RAG_SYSTEM_PROMPT, MULTI_DOC_NOTE
from rag.memory import MemoryManager
from rag.query_rewriter import rewrite_query
print('RAG modules OK')
print(f'System prompt length: {len(RAG_SYSTEM_PROMPT)} chars')
"
# Expected: RAG modules OK + length > 200 chars
```

---

## PHASE 8 — Auth Layer

**Goal:** Build JWT auth utilities and routes.

### Step 8.1 — Create `backend/api/auth.py`

Use full code from `V2_FEATURES_SPEC.md` Section 4 (Fix 3 — `api/auth.py`).

### Step 8.2 — Create `backend/api/routes/auth_routes.py`

Use full code from `V2_FEATURES_SPEC.md` Section 4 (Fix 3 — `auth_routes.py`).

### ✅ Phase 8 Verification

```bash
python -c "
from api.auth import hash_password, verify_password, create_access_token
hashed = hash_password('testpassword123')
assert verify_password('testpassword123', hashed)
token = create_access_token('test-user-id')
assert len(token) > 20
print('Auth OK')
"
# Expected: Auth OK
```

---

## PHASE 9 — API Routes

**Goal:** Build all FastAPI route handlers.

### Step 9.1 — Create `backend/api/routes/documents.py`

Start with V1 code from `TECHNICAL_SPEC.md` Section 6.14, then apply these V2 modifications:

1. **Auth guard** — add `current_user: dict = Depends(get_current_user)` to `upload_document`, `list_documents`, `delete_doc`, `summarize_document`
2. **user_id** — extract `user_id = current_user["id"]` and pass to `ingest_pdf(content, file.filename, user_id=user_id)`
3. **Versioning-aware list** — update `list_documents` to accept `include_archived: bool = False` query param; filter accordingly (from `V2_FEATURES_SPEC.md` Section 13)
4. **Multi-file batch endpoint** — add `POST /upload-batch` from `V2_FEATURES_SPEC.md` Section 6 (Fix 5)

### Step 9.2 — Create `backend/api/routes/query.py`

Start with V1 code from `TECHNICAL_SPEC.md` Section 6.15, then apply:

1. **Auth guard** — add `current_user: dict = Depends(get_current_user)` to `ask` and `ask_stream`
2. **user_id threading** — pass `user_id=current_user["id"]` to `engine.answer(...)` and `engine.answer_stream(...)`
3. **Async** — change `def ask` to `async def ask`; call `await engine.answer(...)` (engine methods must be async-compatible)

### Step 9.3 — Create `backend/api/routes/stats.py`

Start with V1 code from `TECHNICAL_SPEC.md` Section 6.16, then add:
- `POST /evaluate` endpoint from `V2_FEATURES_SPEC.md` Section 14
- `GET /evaluate/last` endpoint from `V2_FEATURES_SPEC.md` Section 14

### ✅ Phase 9 Verification

```bash
python -c "
from api.routes import documents, query, stats
from api.routes import auth_routes
print('All route modules import OK')
"
# Expected: All route modules import OK
```

---

## PHASE 10 — Evaluation Module

**Goal:** Build the evaluation framework.

### Step 10.1 — Create `backend/evaluation/evaluator.py`

Use code from `TECHNICAL_SPEC.md` Section 15, then add the disk-save logic from `V2_FEATURES_SPEC.md` Section 14:

```python
# At end of evaluate(), before return:
from pathlib import Path
import json
from datetime import datetime
cache_path = Path(__file__).parent.parent / "data" / "last_eval.json"
cache_path.write_text(json.dumps({
    "run_at": datetime.utcnow().isoformat(),
    "summary": {
        "avg_semantic_similarity": round(avg_sim, 4),
        "source_attribution_accuracy": round(source_accuracy, 4)
    },
    "results": results
}, indent=2))
```

### Step 10.2 — Create `backend/evaluation/test_cases.json`

Use the exact JSON from `TECHNICAL_SPEC.md` Section 15.

> Note: These test cases use placeholder expected answers. They will only produce meaningful results once the user has ingested documents that contain matching content. The structure is correct — content is illustrative.

### ✅ Phase 10 Verification

```bash
python -c "
import json
from pathlib import Path
tc = json.loads(Path('evaluation/test_cases.json').read_text())
assert len(tc) == 5
print(f'Evaluation module OK: {len(tc)} test cases')
"
# Expected: Evaluation module OK: 5 test cases
```

---

## PHASE 11 — FastAPI App Entry Point

**Goal:** Wire everything together in `main.py`.

### Step 11.1 — Create `backend/main.py`

Use V1 code from `TECHNICAL_SPEC.md` Section 6.1, then apply ALL V2 modifications:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import documents, query, stats
from api.routes import auth_routes
from core.config import settings
from core.logging import setup_logging
from storage.chroma_store import ChromaStore
from storage.session_store import init_db
from storage.user_store import init_users_db

setup_logging()

app = FastAPI(
    title="Enterprise Knowledge Assistant API",
    version="2.0.0",
    description="RAG-based document Q&A system with hybrid search, re-ranking, and JWT auth"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    ChromaStore.initialize()
    init_db()
    init_users_db()

app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
```

### ✅ Phase 11 Verification

```bash
cd backend
python -m uvicorn main:app --port 8000 &
sleep 4
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"2.0.0"}
curl http://localhost:8000/docs
# Expected: 200 OK (Swagger UI loads)
kill %1
```

---

## PHASE 12 — Frontend Scaffold

**Goal:** Create Next.js app with all config files.

### Step 12.1 — Initialize Next.js project

```bash
cd enterprise-knowledge-assistant
npx create-next-app@14.2.4 frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
cd frontend
```

### Step 12.2 — Install additional dependencies

```bash
npm install axios uuid lucide-react next-themes \
  class-variance-authority clsx tailwind-merge \
  @radix-ui/react-dialog @radix-ui/react-tooltip @radix-ui/react-scroll-area

npm install -D @types/uuid
```

### Step 12.3 — Install shadcn/ui

```bash
npx shadcn-ui@latest init
# When prompted:
# Style: Default
# Base color: Slate
# CSS variables: Yes
```

Install required shadcn components:

```bash
npx shadcn-ui@latest add button input dialog tooltip scroll-area badge separator
```

### Step 12.4 — Replace `frontend/tailwind.config.ts`

Use exact code from `TECHNICAL_SPEC.md` Section 8.9.

### Step 12.5 — Replace `frontend/app/globals.css`

Use exact code from `TECHNICAL_SPEC.md` Section 8.10.

### Step 12.6 — Create `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Step 12.7 — Create `frontend/next.config.js`

Use code from `V2_FEATURES_SPEC.md` Section 12 (Enhancement 5 — `next.config.js`).

### ✅ Phase 12 Verification

```bash
cd frontend
npm run build 2>&1 | tail -5
# Expected: Build completes with no errors (warnings OK)
```

---

## PHASE 13 — Frontend Library Layer

**Goal:** Create all types, constants, API client, and hooks.

### Step 13.1 — Create `frontend/lib/types.ts`

Use exact code from `TECHNICAL_SPEC.md` Section 8.1.

### Step 13.2 — Create `frontend/lib/constants.ts`

Use exact code from `TECHNICAL_SPEC.md` Section 8.2.

### Step 13.3 — Create `frontend/lib/utils.ts`

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### Step 13.4 — Create `frontend/lib/api.ts`

Start with `TECHNICAL_SPEC.md` Section 8.3, then apply the V2 axios interceptor from `V2_FEATURES_SPEC.md` Section 4 (Frontend — `api.ts` modification):

```typescript
// Add this after creating the axios instance:
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("auth_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Clear stale token and reload to show login
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user_id");
      localStorage.removeItem("auth_email");
      window.location.reload();
    }
    return Promise.reject(err);
  }
);
```

### Step 13.5 — Create `frontend/hooks/useAuth.ts`

Use full code from `V2_FEATURES_SPEC.md` Section 4 (Frontend — `useAuth.ts`).

### Step 13.6 — Create `frontend/hooks/useStream.ts`

Use exact code from `TECHNICAL_SPEC.md` Section 8.4.

### Step 13.7 — Create `frontend/hooks/useChat.ts`

Use exact code from `TECHNICAL_SPEC.md` Section 8.5.

### Step 13.8 — Create `frontend/hooks/useDocuments.ts`

```typescript
"use client";
import { useState, useCallback, useEffect } from "react";
import { DocumentInfo } from "@/lib/types";
import { listDocuments, uploadDocument, deleteDocument } from "@/lib/api";

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (e) {
      console.error("Failed to fetch documents:", e);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  const handleUpload = useCallback(async (file: File) => {
    setIsUploading(true);
    try {
      await uploadDocument(file);
      await fetchDocuments();
    } finally {
      setIsUploading(false);
    }
  }, [fetchDocuments]);

  const handleDelete = useCallback(async (docId: string) => {
    await deleteDocument(docId);
    setDocuments(prev => prev.filter(d => d.doc_id !== docId));
  }, []);

  return {
    documents,
    isLoading,
    isUploading,
    uploadDocument: handleUpload,
    deleteDocument: handleDelete,
    refetch: fetchDocuments
  };
}
```

### ✅ Phase 13 Verification

```bash
cd frontend
npx tsc --noEmit 2>&1 | head -20
# Expected: No errors (warnings about unused imports are OK)
```

---

## PHASE 14 — Frontend Components

**Goal:** Build all UI components. Build in dependency order (primitives first, then composites).

### Step 14.1 — Create `frontend/components/auth/LoginModal.tsx`

Build an email/password modal with register/login tab toggle. Use the `useAuth` hook. Show on app load if no token in localStorage. On success, dismiss modal and refresh document list.

```tsx
"use client";
import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";

interface Props { onSuccess: () => void; }

export function LoginModal({ onSuccess }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async () => {
    if (!email || password.length < 8) {
      setError("Enter a valid email and password (min 8 chars).");
      return;
    }
    setLoading(true);
    setError("");
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password);
      onSuccess();
    } catch (e: any) {
      setError(e.response?.data?.detail || "Something went wrong.");
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-card border border-border rounded-2xl p-8 w-full max-w-sm shadow-xl">
        <h1 className="text-xl font-semibold mb-1">Knowledge Assistant</h1>
        <p className="text-sm text-muted-foreground mb-6">
          {mode === "login" ? "Sign in to continue." : "Create your account."}
        </p>

        <div className="flex gap-2 mb-4">
          {(["login", "register"] as const).map((m) => (
            <button key={m} onClick={() => setMode(m)}
              className={`flex-1 py-1.5 rounded-lg text-sm transition-colors
                ${mode === m ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"}`}>
              {m === "login" ? "Sign In" : "Register"}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <input type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm outline-none focus:ring-2 focus:ring-primary/30" />
          <input type="password" placeholder="Password (min 8 chars)" value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm outline-none focus:ring-2 focus:ring-primary/30" />
        </div>

        {error && <p className="text-xs text-red-500 mt-2">{error}</p>}

        <button onClick={handleSubmit} disabled={loading}
          className="w-full mt-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium
                     hover:bg-primary/90 disabled:opacity-50 transition-colors">
          {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
        </button>
      </div>
    </div>
  );
}
```

### Step 14.2 — Create `frontend/components/chat/ThinkingIndicator.tsx`

Use exact code from `TECHNICAL_SPEC.md` Section 8.6.

### Step 14.3 — Create `frontend/components/chat/SourceCard.tsx`

```tsx
import { Source } from "@/lib/types";
import { FileText } from "lucide-react";

interface Props { source: Source }

export function SourceCard({ source }: Props) {
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-border bg-muted/30 text-xs">
      <FileText className="w-3 h-3 text-muted-foreground flex-shrink-0" />
      <span className="text-muted-foreground truncate max-w-[150px]">{source.document}</span>
      <span className="text-muted-foreground/60 flex-shrink-0">p.{source.page}</span>
    </div>
  );
}
```

### Step 14.4 — Create `frontend/components/chat/ChunkViewer.tsx`

Use exact code from `TECHNICAL_SPEC.md` Section 8.6 (`ChunkViewer.tsx`).

### Step 14.5 — Create `frontend/components/chat/FeedbackButtons.tsx`

```tsx
"use client";
import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { submitFeedback } from "@/lib/api";

interface Props { sessionId: string; question: string; answer: string; }

export function FeedbackButtons({ sessionId, question, answer }: Props) {
  const [sent, setSent] = useState<"helpful" | "not_helpful" | null>(null);

  const handleFeedback = async (type: "helpful" | "not_helpful") => {
    if (sent) return;
    setSent(type);
    try {
      await submitFeedback({ session_id: sessionId, question, answer, feedback: type });
    } catch {}
  };

  return (
    <div className="flex items-center gap-1">
      <button onClick={() => handleFeedback("helpful")}
        className={`p-1 rounded transition-colors ${sent === "helpful" ? "text-green-500" : "text-muted-foreground hover:text-foreground"}`}>
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button onClick={() => handleFeedback("not_helpful")}
        className={`p-1 rounded transition-colors ${sent === "not_helpful" ? "text-red-500" : "text-muted-foreground hover:text-foreground"}`}>
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
```

### Step 14.6 — Create `frontend/components/chat/FollowUpSuggestions.tsx`

```tsx
interface Props { questions: string[]; onSelect: (q: string) => void; }

export function FollowUpSuggestions({ questions, onSelect }: Props) {
  return (
    <div className="flex flex-col gap-1.5">
      <p className="text-xs text-muted-foreground px-1">Suggested follow-ups</p>
      {questions.map((q, i) => (
        <button key={i} onClick={() => onSelect(q)}
          className="text-left text-xs px-3 py-2 rounded-lg border border-border
                     hover:border-primary/50 hover:bg-muted/50 transition-colors text-muted-foreground hover:text-foreground">
          {q}
        </button>
      ))}
    </div>
  );
}
```

### Step 14.7 — Create `frontend/components/chat/MessageBubble.tsx`

Use exact code from `TECHNICAL_SPEC.md` Section 8.6 (`MessageBubble.tsx`).

### Step 14.8 — Create `frontend/components/chat/ChatWindow.tsx`

```tsx
"use client";
import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { ThinkingIndicator } from "./ThinkingIndicator";

interface Props {
  messages: Message[];
  thinkingStep: number;
  onFollowUp: (q: string) => void;
  sessionId: string;
}

export function ChatWindow({ messages, thinkingStep, onFollowUp, sessionId }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinkingStep]);

  return (
    <div className="flex flex-col gap-6 p-4 pb-2">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} onFollowUp={onFollowUp} sessionId={sessionId} />
      ))}
      {thinkingStep >= 0 && (
        <div className="flex">
          <ThinkingIndicator currentStep={thinkingStep} />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
```

### Step 14.9 — Create `frontend/components/chat/ChatInput.tsx`

```tsx
"use client";
import { useState } from "react";
import { Send } from "lucide-react";

interface Props {
  onSend: (q: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, isLoading, disabled, placeholder }: Props) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="flex gap-2 items-end">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        placeholder={placeholder || "Ask a question..."}
        disabled={disabled || isLoading}
        rows={1}
        className="flex-1 resize-none px-4 py-3 rounded-xl border border-border bg-background text-sm
                   outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50
                   min-h-[48px] max-h-[160px] overflow-y-auto"
        style={{ height: "48px" }}
        onInput={(e) => {
          const t = e.target as HTMLTextAreaElement;
          t.style.height = "48px";
          t.style.height = Math.min(t.scrollHeight, 160) + "px";
        }}
      />
      <button onClick={handleSend} disabled={disabled || isLoading || !value.trim()}
        className="p-3 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90
                   disabled:opacity-40 transition-colors flex-shrink-0">
        <Send className="w-4 h-4" />
      </button>
    </div>
  );
}
```

### Step 14.10 — Create `frontend/components/documents/DocumentUpload.tsx`

Use the **V2 multi-file version** from `V2_FEATURES_SPEC.md` Section 6 (Fix 5 — `DocumentUpload.tsx`). Do not use the V1 single-file version.

### Step 14.11 — Create `frontend/components/documents/DocumentCard.tsx`

```tsx
"use client";
import { useState } from "react";
import { DocumentInfo } from "@/lib/types";
import { FileText, Trash2, Sparkles, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import { summarizeDocument } from "@/lib/api";

interface Props {
  doc: DocumentInfo;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

export function DocumentCard({ doc, isSelected, onSelect, onDelete }: Props) {
  const [summary, setSummary] = useState("");
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [showSummary, setShowSummary] = useState(false);

  const handleSummarize = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (summary) { setShowSummary(!showSummary); return; }
    setLoadingSummary(true);
    try {
      const s = await summarizeDocument(doc.doc_id);
      setSummary(s);
      setShowSummary(true);
    } catch {}
    setLoadingSummary(false);
  };

  return (
    <div className={`rounded-xl border transition-colors cursor-pointer
      ${isSelected ? "border-primary bg-primary/5" : "border-border hover:border-primary/30"}`}
      onClick={onSelect}>
      <div className="flex items-start gap-2.5 p-2.5">
        <FileText className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium truncate">{doc.doc_name}</p>
          <p className="text-xs text-muted-foreground">
            {doc.total_pages}p · {doc.total_chunks} chunks · {doc.file_size_kb.toFixed(0)}KB
          </p>
        </div>
        <div className="flex gap-1 flex-shrink-0">
          <button onClick={handleSummarize} title="Summarize"
            className="p-1 text-muted-foreground hover:text-primary transition-colors">
            {loadingSummary ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          </button>
          <button onClick={(e) => { e.stopPropagation(); onDelete(); }} title="Delete"
            className="p-1 text-muted-foreground hover:text-destructive transition-colors">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      {showSummary && summary && (
        <div className="px-2.5 pb-2.5 text-xs text-muted-foreground border-t border-border pt-2">
          {summary}
        </div>
      )}
    </div>
  );
}
```

### Step 14.12 — Create `frontend/components/documents/DocumentList.tsx`

```tsx
import { DocumentInfo } from "@/lib/types";
import { DocumentCard } from "./DocumentCard";

interface Props {
  documents: DocumentInfo[];
  selectedDocs: string[];
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function DocumentList({ documents, selectedDocs, onSelect, onDelete }: Props) {
  if (documents.length === 0) {
    return <p className="text-xs text-muted-foreground text-center py-4">No documents yet. Upload a PDF to get started.</p>;
  }
  return (
    <div className="flex flex-col gap-1.5">
      {documents.map((doc) => (
        <DocumentCard key={doc.doc_id} doc={doc}
          isSelected={selectedDocs.includes(doc.doc_id)}
          onSelect={() => onSelect(doc.doc_id)}
          onDelete={() => onDelete(doc.doc_id)} />
      ))}
    </div>
  );
}
```

### Step 14.13 — Create `frontend/components/dashboard/StatsPanel.tsx`

```tsx
"use client";
import { useEffect, useState } from "react";
import { StatsData } from "@/lib/types";
import { getStats } from "@/lib/api";
import { Database, FileText, Layers, Cpu } from "lucide-react";

export function StatsPanel() {
  const [stats, setStats] = useState<StatsData | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
  }, []);

  if (!stats) return null;

  return (
    <div className="p-3 space-y-3">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Statistics</p>
      <div className="grid grid-cols-2 gap-1.5">
        {[
          { icon: FileText, label: "Documents", value: stats.total_documents },
          { icon: Layers, label: "Pages", value: stats.total_pages },
          { icon: Database, label: "Chunks", value: stats.total_chunks },
          { icon: Cpu, label: "Model", value: "MiniLM" },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="bg-muted/50 rounded-lg p-2 text-center">
            <Icon className="w-3.5 h-3.5 mx-auto mb-0.5 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-sm font-semibold">{value}</p>
          </div>
        ))}
      </div>
      <div className="text-xs text-muted-foreground space-y-0.5">
        <p>Vector DB: {stats.vector_db}</p>
        <p>Embed: {stats.embedding_model}</p>
      </div>
      {stats.recent_queries.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">Recent queries</p>
          {stats.recent_queries.slice(0, 3).map((q, i) => (
            <p key={i} className="text-xs text-muted-foreground truncate py-0.5 border-b border-border last:border-0">{q}</p>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Step 14.14 — Create `frontend/components/dashboard/EvalDashboard.tsx`

Use exact code from `V2_FEATURES_SPEC.md` Section 14 (`EvalDashboard.tsx`).

### Step 14.15 — Create `frontend/components/layout/Header.tsx`

```tsx
"use client";
import { Menu, Moon, Sun, Trash2, LogOut } from "lucide-react";
import { useTheme } from "next-themes";
import { useAuth } from "@/hooks/useAuth";

interface Props {
  onToggleSidebar: () => void;
  onClearChat: () => void;
}

export function Header({ onToggleSidebar, onClearChat }: Props) {
  const { theme, setTheme } = useTheme();
  const { email, logout } = useAuth();

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-border">
      <div className="flex items-center gap-3">
        <button onClick={onToggleSidebar} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
          <Menu className="w-4 h-4" />
        </button>
        <h1 className="text-sm font-semibold">Knowledge Assistant</h1>
      </div>
      <div className="flex items-center gap-2">
        {email && <span className="text-xs text-muted-foreground hidden sm:block">{email}</span>}
        <button onClick={onClearChat} title="Clear chat"
          className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground">
          <Trash2 className="w-4 h-4" />
        </button>
        <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground">
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
        <button onClick={logout} title="Sign out"
          className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground">
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
```

### Step 14.16 — Create `frontend/components/layout/Sidebar.tsx`

```tsx
"use client";
import { DocumentInfo } from "@/lib/types";
import { DocumentUpload } from "@/components/documents/DocumentUpload";
import { DocumentList } from "@/components/documents/DocumentList";
import { StatsPanel } from "@/components/dashboard/StatsPanel";
import { EvalDashboard } from "@/components/dashboard/EvalDashboard";
import { useState } from "react";

interface Props {
  open: boolean;
  documents: DocumentInfo[];
  selectedDocs: string[];
  onSelectDoc: (id: string) => void;
  onUpload: (file: File) => Promise<void>;
  onDelete: (id: string) => void;
  isUploading: boolean;
}

export function Sidebar({ open, documents, selectedDocs, onSelectDoc, onUpload, onDelete, isUploading }: Props) {
  const [tab, setTab] = useState<"docs" | "stats" | "eval">("docs");

  if (!open) return null;

  return (
    <aside className="w-72 flex-shrink-0 border-r border-border flex flex-col h-full overflow-hidden">
      {/* Tab bar */}
      <div className="flex border-b border-border">
        {(["docs", "stats", "eval"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-2.5 text-xs font-medium transition-colors
              ${tab === t ? "border-b-2 border-primary text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
            {t === "docs" ? "Documents" : t === "stats" ? "Stats" : "Eval"}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        {tab === "docs" && (
          <div className="p-3 space-y-3">
            <DocumentUpload onUploadComplete={() => {}} />
            {selectedDocs.length > 0 && (
              <p className="text-xs text-primary">
                {selectedDocs.length} doc(s) selected — searches filtered
              </p>
            )}
            <DocumentList
              documents={documents}
              selectedDocs={selectedDocs}
              onSelect={onSelectDoc}
              onDelete={onDelete}
            />
          </div>
        )}
        {tab === "stats" && <StatsPanel />}
        {tab === "eval" && <EvalDashboard />}
      </div>
    </aside>
  );
}
```

### ✅ Phase 14 Verification

```bash
cd frontend
npx tsc --noEmit 2>&1 | grep -c "error TS"
# Expected: 0
```

---

## PHASE 15 — Frontend App Shell

**Goal:** Wire all components into the app router.

### Step 15.1 — Create `frontend/app/providers.tsx`

```tsx
"use client";
import { ThemeProvider } from "next-themes";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      {children}
    </ThemeProvider>
  );
}
```

### Step 15.2 — Replace `frontend/app/layout.tsx`

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Enterprise Knowledge Assistant",
  description: "AI-powered document Q&A system",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

### Step 15.3 — Replace `frontend/app/page.tsx`

Use exact code from `TECHNICAL_SPEC.md` Section 8.7, then add:

1. Import `LoginModal` and `useAuth`
2. Add auth gate — show `LoginModal` if not authenticated:

```tsx
// Add near the top of the component:
const { isAuthenticated } = useAuth();
const [authReady, setAuthReady] = useState(false);

// Show login modal if not authenticated
if (!authReady && !isAuthenticated) {
  return <LoginModal onSuccess={() => setAuthReady(true)} />;
}
```

### ✅ Phase 15 Verification

```bash
cd frontend
npm run dev &
sleep 8
curl -s http://localhost:3000 | grep -c "Knowledge"
# Expected: 1 or more (page title found)
kill %1
```

---

## PHASE 16 — Integration Test (Full Stack)

**Goal:** Run backend and frontend together and verify the full request flow works.

### Step 16.1 — Start backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

> ⚠️ API keys must be in `backend/.env` before this step. If not, stop and ask the user to provide them.

### Step 16.2 — Start frontend (new terminal)

```bash
cd frontend
npm run dev
```

### Step 16.3 — Manual smoke test checklist

Execute each item and confirm it works:

```
[ ] 1. Open http://localhost:3000
        → LoginModal appears

[ ] 2. Register with email + password
        → POST /api/auth/register returns 200
        → Modal closes, app loads

[ ] 3. Open sidebar → Documents tab
        → Upload a PDF (any PDF)
        → Progress indicator appears per file
        → On completion: doc appears in document list with page/chunk counts

[ ] 4. Stats tab
        → Shows total documents, pages, chunks > 0

[ ] 5. Type a question in the chat input → send
        → Thinking indicator animates through steps
        → Answer streams in with typing effect
        → Sources appear below answer
        → Confidence bar appears
        → Follow-up suggestions appear

[ ] 6. Click a follow-up suggestion
        → Question auto-sends, uses conversation context

[ ] 7. Click "View N retrieved chunks"
        → Expandable section shows chunk text + doc name + page

[ ] 8. Click thumbs up/down
        → POST /api/feedback returns 200

[ ] 9. Click copy button on an answer
        → "Copied!" confirmation appears

[ ] 10. Dark mode toggle in header
         → Theme switches

[ ] 11. Check backend logs
         → "Groq" appears for successful LLM calls
         → No uncaught exceptions

[ ] 12. Eval tab → Run Eval button
         → Returns results (scores will be low if test_cases.json doesn't match uploaded docs — that's OK)
```

### ✅ Phase 16 Verification

All 12 checklist items pass before proceeding.

---

## PHASE 17 — Deployment

**Goal:** Deploy backend to Railway, frontend to Vercel.

### Step 17.1 — Prepare backend for Railway

Create `backend/Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Create `backend/railway.json` using code from `V2_FEATURES_SPEC.md` Section 12.

Create `backend/runtime.txt`:
```
python-3.11
```

### Step 17.2 — Push backend to GitHub

```bash
# From project root
git add backend/
git commit -m "feat: enterprise knowledge assistant backend v2"
git push origin main
```

### Step 17.3 — Deploy backend on Railway

Follow steps from `V2_FEATURES_SPEC.md` Section 12 (Railway Setup Steps):

1. Go to railway.app → New Project → Deploy from GitHub repo
2. Set root directory to `backend/`
3. Add environment variables from `backend/.env` (all of them)
4. **Critical:** Add a Volume mounted at `/app/data` for ChromaDB + uploads persistence
5. Deploy
6. Copy the public Railway URL (e.g., `https://your-app.railway.app`)

### Step 17.4 — Update CORS for production

In `backend/.env` on Railway, set:
```
ALLOWED_ORIGINS_STR=http://localhost:3000,https://your-vercel-app.vercel.app
```

(Fill in actual Vercel URL after Step 17.6.)

### Step 17.5 — Prepare frontend for Vercel

Create `frontend/vercel.json` using code from `V2_FEATURES_SPEC.md` Section 12.

### Step 17.6 — Deploy frontend on Vercel

Follow steps from `V2_FEATURES_SPEC.md` Section 12 (Vercel Setup Steps):

1. Push `frontend/` to GitHub
2. vercel.com → New Project → Import
3. Set root to `frontend/`
4. Set env var: `NEXT_PUBLIC_API_URL = https://your-railway-url.railway.app/api`
5. Deploy

### Step 17.7 — Final production smoke test

```
[ ] 1. Visit Vercel URL → LoginModal appears
[ ] 2. Register → app loads
[ ] 3. Upload a PDF → ingestion works
[ ] 4. Ask a question → answer streams from Railway backend
[ ] 5. Check Railway logs → no errors
```

### ✅ Phase 17 Complete

Both URLs are live and working.

---

## PHASE 18 — Documentation & Submission

**Goal:** Finalize README and system design doc for submission.

### Step 18.1 — Create `README.md` at project root

Use the README content from `TECHNICAL_SPEC.md` Section 16. Expand it to add:
- Live demo URL (Vercel link)
- Backend API URL (Railway link)
- V2 features list
- Actual setup instructions (pointing to this agent instructions flow)

### Step 18.2 — Create `SYSTEM_DESIGN.md` at project root

Write a 1-2 page system design document covering:

```markdown
# System Design — Enterprise Knowledge Assistant

## High-Level Architecture
[describe: FE → BE → RAG Engine → ChromaDB → Groq/Gemini]

## Data Flow
[ingestion flow + query flow — from TECHNICAL_SPEC.md Section 5]

## Component Explanation
[summarize each major module and its role]

## Key Design Decisions
- Groq primary / Gemini fallback — why
- all-MiniLM-L6-v2 — why (free, CPU, 384-dim)
- ChromaDB — why (persistent, no server)
- Hybrid search (BM25 + semantic) — why (recall on exact terms)
- Cross-encoder re-ranking — why (accuracy)
- SQLite for sessions/users — why (zero dependencies, persistent)

## Scalability Considerations
- ChromaDB → Pinecone or Weaviate for large-scale
- In-process rate limiter → Redis token bucket for multi-instance
- BM25 pickle → Elasticsearch for distributed keyword search
- Railway single instance → multi-instance with shared volume
```

### Step 18.3 — Final git commit

```bash
git add .
git commit -m "feat: complete enterprise knowledge assistant v2 — all features implemented"
git push origin main
```

### ✅ Project Complete

```
Submission checklist:
[ ] GitHub repo URL (public or shared)
[ ] Vercel live URL
[ ] Railway API URL
[ ] README with setup instructions
[ ] SYSTEM_DESIGN.md (1-2 pages)
[ ] Demo video (record after deployment — 5 min max)
    - Show: upload PDF, ask question, see sources, follow-ups, dark mode, eval tab
```

---

## Appendix A — Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: groq` | groq not installed | `pip install groq==0.9.0` |
| `ChromaDB collection error on startup` | Data dir missing | `mkdir -p backend/data/chroma_db` |
| `401 Unauthorized on all requests` | Token not in localStorage | Check `useAuth` hook hydration, clear localStorage and re-login |
| `CORS error in browser` | Origin not in ALLOWED_ORIGINS_STR | Add frontend URL to env var and restart backend |
| `Groq 429 Too Many Requests` | Groq free tier limit hit | Auto-falls back to Gemini — check Gemini key is set |
| `camelot ImportError` | ghostscript not installed | `apt-get install ghostscript` or `brew install ghostscript` |
| `pytesseract not found` | Tesseract binary missing | `apt-get install tesseract-ocr` |
| `BM25Index has no chunks` | First document not yet ingested | Upload at least one document before querying |
| `Next.js hydration mismatch` | localStorage accessed on server | All auth reads wrapped in `typeof window !== "undefined"` check |
| `Railway deploy fails` | Missing Procfile or runtime.txt | Create both files in `backend/` — see Phase 17.1 |

---

## Appendix B — File Count Checklist

At the end of Phase 15, your repo must have at minimum these files:

**Backend (35 files):**
```
backend/main.py
backend/core/config.py, exceptions.py, logging.py
backend/models/schemas.py
backend/pipeline/chunker.py, embedder.py, ingestion.py, ocr.py
backend/pipeline/table_extractor.py, bm25_index.py, retriever.py, reranker.py, version_manager.py
backend/rag/llm_client.py, rate_limiter.py, prompts.py, memory.py, query_rewriter.py, engine.py
backend/storage/chroma_store.py, file_store.py, session_store.py, user_store.py
backend/api/auth.py
backend/api/routes/auth_routes.py, documents.py, query.py, stats.py
backend/evaluation/evaluator.py, test_cases.json
backend/requirements.txt, .env.example, .env, Procfile, railway.json
```

**Frontend (30+ files):**
```
frontend/app/layout.tsx, page.tsx, globals.css, providers.tsx
frontend/lib/types.ts, constants.ts, utils.ts, api.ts
frontend/hooks/useAuth.ts, useChat.ts, useStream.ts, useDocuments.ts
frontend/components/auth/LoginModal.tsx
frontend/components/chat/ChatWindow.tsx, ChatInput.tsx, MessageBubble.tsx
frontend/components/chat/ThinkingIndicator.tsx, SourceCard.tsx, ChunkViewer.tsx
frontend/components/chat/FeedbackButtons.tsx, FollowUpSuggestions.tsx
frontend/components/documents/DocumentUpload.tsx, DocumentList.tsx, DocumentCard.tsx
frontend/components/dashboard/StatsPanel.tsx, EvalDashboard.tsx
frontend/components/layout/Header.tsx, Sidebar.tsx
frontend/package.json, tailwind.config.ts, tsconfig.json, next.config.js
frontend/.env.local, vercel.json
```
