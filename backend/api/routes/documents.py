from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List as PyList
from models.schemas import (DocumentUploadResponse, DocumentListResponse,
                             DocumentSummaryResponse, DocumentInfo)
from pipeline.ingestion import ingest_document
from storage.file_store import get_all_documents, get_document, delete_document, get_file_path
from storage.chroma_store import ChromaStore
from rag.llm_client import generate
from rag.prompts import SUMMARY_PROMPT
from api.auth import get_current_user
import fitz
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document", # docx
    "application/msword", # doc
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", # xlsx
    "application/vnd.ms-excel" # xls
}
MAX_FILE_SIZE_MB = 50

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")
    
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max size is {MAX_FILE_SIZE_MB}MB.")
    
    try:
        user_id = current_user["id"]
        result = ingest_document(content, file.filename, user_id=user_id)
        return DocumentUploadResponse(
            **result,
            message=f"Successfully ingested {result['total_chunks']} chunks from {result['total_pages']} pages."
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(500, "Failed to process document.")

@router.post("/upload-batch")
async def upload_batch(
    files: PyList[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload multiple files. Returns array of results, one per file.
    Failed files are included with error field set, not a 500.
    """
    results = []
    for file in files:
        if file.content_type not in ALLOWED_TYPES:
            results.append({
                "success": False,
                "doc_name": file.filename,
                "error": f"Unsupported file type: {file.content_type}"
            })
            continue

        try:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise Exception(f"File too large. Max size is {MAX_FILE_SIZE_MB}MB.")
                
            result = ingest_document(content, file.filename, user_id=current_user["id"])
            results.append({"success": True, **result})
        except Exception as e:
            results.append({
                "success": False,
                "doc_name": file.filename,
                "error": str(e)
            })
    return {"results": results, "total": len(files),
            "succeeded": sum(1 for r in results if r["success"])}

@router.get("/", response_model=DocumentListResponse)
def list_documents(
    include_archived: bool = False,
    current_user: dict = Depends(get_current_user)
):
    docs = get_all_documents()
    filtered_docs = []
    for d in docs:
        if d.get("user_id") == current_user["id"]:
            if include_archived or d.get("version_status") != "archived":
                filtered_docs.append(DocumentInfo(**d))
                
    return DocumentListResponse(
        documents=filtered_docs,
        total=len(filtered_docs)
    )

@router.delete("/{doc_id}")
def delete_doc(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    if doc.get("user_id") and doc["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized to delete this document.")
        
    delete_document(doc_id)
    ChromaStore.delete_by_doc_id(doc_id)
    return {"message": f"Deleted {doc['doc_name']}"}

@router.get("/{doc_id}/summary", response_model=DocumentSummaryResponse)
def summarize_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    if doc.get("user_id") and doc["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized to access this document.")
    
    file_path = get_file_path(doc_id)
    if not file_path or not file_path.exists():
        raise HTTPException(404, "Document file not found.")
    
    ext = file_path.suffix.lower()
    
    # Extract text for summary based on extension
    content = ""
    if ext == ".pdf":
        pdf_doc = fitz.open(str(file_path))
        pages_text = []
        for i in range(min(5, len(pdf_doc))):
            pages_text.append(pdf_doc[i].get_text("text"))
        pdf_doc.close()
        content = "\n\n".join(pages_text)[:4000]
    else:
        # Re-use ingestion extraction for simplicity (first page equivalent)
        from pipeline.ingestion import extract_text_pages, extract_docx_pages, extract_csv_xlsx_pages
        if ext in [".md", ".txt"]:
            pages = extract_text_pages(file_path)
        elif ext in [".docx", ".doc"]:
            pages = extract_docx_pages(file_path)
        elif ext == ".csv":
            pages = extract_csv_xlsx_pages(file_path, is_csv=True)
        elif ext in [".xlsx", ".xls", ".sheet"]:
            pages = extract_csv_xlsx_pages(file_path, is_csv=False)
        else:
            pages = [{"text": ""}]
        
        content = pages[0]["text"][:4000]
    
    prompt = SUMMARY_PROMPT.format(doc_name=doc["doc_name"], content=content)
    summary = generate(prompt)
    
    return DocumentSummaryResponse(
        doc_id=doc_id,
        doc_name=doc["doc_name"],
        summary=summary
    )
