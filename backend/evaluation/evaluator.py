import json
from pathlib import Path
from rag.engine import RAGEngine
from pipeline.embedder import Embedder
from storage.chroma_store import ChromaStore
from rag.llm_client import generate
import numpy as np
import asyncio
from datetime import datetime
import random
import re

engine = RAGEngine()

def semantic_similarity(a: str, b: str) -> float:
    """Measure answer relevance via embedding similarity."""
    emb_a = Embedder.embed_single(a)
    emb_b = Embedder.embed_single(b)
    a_np, b_np = np.array(emb_a), np.array(emb_b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))

def generate_synthetic_test_cases(num_cases=5):
    """Dynamically generate QA test cases based on actual uploaded chunks."""
    collection = ChromaStore.get_collection()
    data = collection.get()
    
    if not data or not data["documents"]:
        raise ValueError("No documents in database to evaluate.")
        
    documents = data["documents"]
    metadatas = data["metadatas"]
    
    # Pick random chunks (up to num_cases)
    indices = list(range(len(documents)))
    random.shuffle(indices)
    selected_indices = indices[:num_cases]
    
    test_cases = []
    
    for i, idx in enumerate(selected_indices):
        text = documents[idx]
        meta = metadatas[idx]
        
        prompt = f"""You are an evaluator. Given this document excerpt, generate ONE specific question that can be answered using ONLY this text, and provide the exact correct answer.
        
Document Excerpt:
{text}

Respond STRICTLY in JSON format with no markdown formatting or backticks:
{{
  "question": "<your question>",
  "expected_answer": "<your answer>"
}}"""
        
        try:
            response = generate(prompt).strip()
            # Clean up potential markdown blocks
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
                
            parsed = json.loads(response.strip())
            
            test_cases.append({
                "id": f"TC-{i+1:03d}",
                "question": parsed["question"],
                "expected_answer": parsed["expected_answer"],
                "expected_source": meta.get("doc_name", "")
            })
        except Exception as e:
            print(f"Failed to generate test case for chunk {idx}: {e}")
            
    return test_cases

async def evaluate():
    try:
        test_cases = generate_synthetic_test_cases()
    except Exception as e:
        print(f"Skipping evaluation: {e}")
        return []
        
    results = []
    
    for tc in test_cases:
        session_id = f"eval-{tc['id']}"
        response = await engine.answer(tc["question"], session_id=session_id)
        
        sim = semantic_similarity(response.answer, tc["expected_answer"])
        has_source = any(
            tc["expected_source"].lower() in s.document.lower()
            for s in response.sources
        )
        
        result = {
            "id": tc["id"],
            "question": tc["question"],
            "expected": tc["expected_answer"],
            "actual": response.answer,
            "semantic_similarity": round(sim, 4),
            "source_found": has_source,
            "confidence": response.confidence,
            "num_sources": len(response.sources)
        }
        results.append(result)
        print(f"[{tc['id']}] sim={sim:.3f} source={'[OK]' if has_source else '[FAIL]'} conf={response.confidence:.3f}")
    
    if not results:
        return []
        
    avg_sim = sum(r["semantic_similarity"] for r in results) / len(results)
    source_accuracy = sum(r["source_found"] for r in results) / len(results)
    
    print(f"\n=== EVALUATION RESULTS ===")
    print(f"Average Semantic Similarity: {avg_sim:.4f}")
    print(f"Source Attribution Accuracy: {source_accuracy:.2%}")
    print(f"Cases evaluated: {len(results)}")
    
    cache_path = Path(__file__).parent.parent / "data" / "last_eval.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps({
        "run_at": datetime.utcnow().isoformat(),
        "summary": {
            "avg_semantic_similarity": round(avg_sim, 4),
            "source_attribution_accuracy": round(source_accuracy, 4)
        },
        "results": results
    }, indent=2))
    
    return results

if __name__ == "__main__":
    asyncio.run(evaluate())
