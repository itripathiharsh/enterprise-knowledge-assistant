from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # Auth
    JWT_SECRET: str
    JWT_EXPIRE_HOURS: int = 24

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
    ENABLE_RERANKING: bool = True
    BM25_WEIGHT: float = 0.3
    SEMANTIC_WEIGHT: float = 0.7
    GEMINI_RPM_LIMIT: int = 14
    
    # CORS
    ALLOWED_ORIGINS_STR: str = "http://localhost:3000"
    
    @property
    def ALLOWED_ORIGINS(self) -> list:
        return [o.strip() for o in self.ALLOWED_ORIGINS_STR.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
