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
    def get_stats(cls, user_id: str = None) -> Dict:
        col = cls.get_collection()
        
        where_clause = None
        if user_id:
            where_clause = {"user_id": {"$eq": user_id}}
            
        # Get count for user (count doesn't support where, so we have to use get)
        results = col.get(where=where_clause, include=["metadatas"])
        metadatas = results.get("metadatas", [])
        count = len(metadatas)
        
        # Get unique doc metadata
        if count == 0:
            return {"total_chunks": 0, "total_pages": 0, "total_documents": 0, "documents": []}
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
