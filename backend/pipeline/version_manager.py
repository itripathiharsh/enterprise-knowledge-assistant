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
