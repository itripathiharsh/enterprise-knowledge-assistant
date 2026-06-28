"""
Query rewriter: takes conversation history + current question,
returns a clearer, standalone search query.
Only activates when there is prior conversation history.
"""
from rag.llm_client import generate
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
