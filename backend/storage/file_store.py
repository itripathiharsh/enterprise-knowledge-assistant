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

def register_document(doc_id: str, doc_name: str, total_pages: int, total_chunks: int,
                       file_size_kb: float, user_id: str = "") -> str:
    manifest = load_manifest()
    manifest[doc_id] = {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "file_size_kb": round(file_size_kb, 2),
        "uploaded_at": datetime.utcnow().isoformat(),
        "version_status": "current",
        "user_id": user_id
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
    file_path = get_file_path(doc_id)
    if file_path and file_path.exists():
        file_path.unlink()

def get_file_path(doc_id: str) -> Path:
    for p in settings.UPLOAD_DIR.glob(f"{doc_id}.*"):
        return p
    return Path()
