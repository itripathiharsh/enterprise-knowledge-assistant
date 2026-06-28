import json
import logging
from typing import List, Optional, AsyncGenerator
from pipeline.retriever import Retriever
from rag.llm_client import generate_async, generate_stream_async
from rag.prompts import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE, FOLLOW_UP_PROMPT, MULTI_DOC_NOTE
from rag.memory import MemoryManager
from models.schemas import AskResponse, Source, ChunkResult
from rag.query_rewriter import rewrite_query

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

    async def _get_follow_ups(self, question: str, answer: str) -> List[str]:
        try:
            prompt = FOLLOW_UP_PROMPT.format(question=question, answer=answer)
            raw = await generate_async(prompt)
            # Strip markdown if present
            raw = raw.strip().lstrip("```json").rstrip("```").strip()
            return json.loads(raw)[:3]
        except Exception:
            return []

    def _get_multi_doc_note(self, chunks: List[ChunkResult]) -> str:
        unique_docs = list({c.doc_name for c in chunks})
        if len(unique_docs) <= 1:
            return ""
        return MULTI_DOC_NOTE.format(
            num_docs=len(unique_docs),
            doc_names=", ".join(unique_docs)
        )

    async def answer(self, question: str, session_id: str,
               user_id: str = "", doc_filter: Optional[List[str]] = None) -> AskResponse:
        """Non-streaming answer generation."""
        history = MemoryManager.get_history(session_id)
        
        # Rewrite query for better retrieval
        search_query = rewrite_query(question, history)
        
        chunks = self.retriever.retrieve(search_query, user_id=user_id, doc_filter=doc_filter)
        confidence = self.retriever.get_confidence(chunks)
        
        context = self._build_context(chunks)
        multi_doc_note = self._get_multi_doc_note(chunks)
        history_str = self._build_history_str(history)
        
        prompt = RAG_USER_TEMPLATE.format(
            history=history_str,
            context=(context + multi_doc_note) if context else "No relevant documents found.",
            question=question
        )
        
        answer_text = await generate_async(prompt, system=RAG_SYSTEM_PROMPT)
        
        # Store turn in memory
        MemoryManager.add_turn(session_id, question, answer_text)
        
        sources = self._extract_sources(chunks)
        follow_ups = await self._get_follow_ups(question, answer_text)
        
        return AskResponse(
            answer=answer_text,
            sources=sources,
            chunks=chunks,
            confidence=confidence,
            follow_up_questions=follow_ups,
            session_id=session_id
        )

    async def answer_stream(self, question: str, session_id: str,
                      user_id: str = "", doc_filter: Optional[List[str]] = None):
        """
        Generator that yields SSE-formatted strings.
        First yields metadata chunk, then text chunks, then done.
        """
        history = MemoryManager.get_history(session_id)
        
        # Rewrite query for better retrieval
        search_query = rewrite_query(question, history)
        
        chunks = self.retriever.retrieve(search_query, user_id=user_id, doc_filter=doc_filter)
        confidence = self.retriever.get_confidence(chunks)
        
        context = self._build_context(chunks)
        multi_doc_note = self._get_multi_doc_note(chunks)
        history_str = self._build_history_str(history)
        
        prompt = RAG_USER_TEMPLATE.format(
            history=history_str,
            context=(context + multi_doc_note) if context else "No relevant documents found.",
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
        async for text_chunk in generate_stream_async(prompt, system=RAG_SYSTEM_PROMPT):
            full_answer += text_chunk
            yield f"data: {json.dumps({'type': 'text', 'content': text_chunk})}\n\n"
        
        # Store in memory
        MemoryManager.add_turn(session_id, question, full_answer)
        
        # Yield follow-ups
        follow_ups = await self._get_follow_ups(question, full_answer)
        yield f"data: {json.dumps({'type': 'follow_ups', 'questions': follow_ups})}\n\n"
        
        # Done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
