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
