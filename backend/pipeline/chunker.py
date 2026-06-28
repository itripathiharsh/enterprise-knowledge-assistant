from typing import List, Dict
import re

class RecursiveChunker:
    """
    Recursive character-based text splitter.
    Splits on paragraphs → sentences → words to preserve semantic boundaries.
    """
    
    SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        if not separators:
            return [text]
        
        separator = separators[0]
        remaining = separators[1:]
        
        if separator == "":
            splits = list(text)
        else:
            splits = text.split(separator)
        
        good_splits = []
        current = ""
        
        for split in splits:
            split_with_sep = split + (separator if separator != "" else "")
            if len(current) + len(split_with_sep) <= self.chunk_size:
                current += split_with_sep
            else:
                if current:
                    good_splits.append(current.strip())
                if len(split_with_sep) > self.chunk_size and remaining:
                    sub_splits = self._split_text(split_with_sep, remaining)
                    good_splits.extend(sub_splits)
                    current = ""
                else:
                    current = split_with_sep
        
        if current.strip():
            good_splits.append(current.strip())
        
        return good_splits

    def chunk(self, text: str) -> List[str]:
        raw_chunks = self._split_text(text, self.SEPARATORS)
        
        # Apply overlap: each chunk includes tail of previous chunk
        if self.chunk_overlap == 0 or len(raw_chunks) <= 1:
            return [c for c in raw_chunks if c.strip()]
        
        chunks_with_overlap = []
        for i, chunk in enumerate(raw_chunks):
            if i == 0:
                chunks_with_overlap.append(chunk)
            else:
                overlap_text = raw_chunks[i-1][-self.chunk_overlap:]
                chunks_with_overlap.append(overlap_text + " " + chunk)
        
        return [c for c in chunks_with_overlap if len(c.strip()) > 20]

    def chunk_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        Input: [{"page_number": 1, "text": "..."}]
        Output: [{"page_number": 1, "text": "...", "chunk_index": 0}]
        """
        result = []
        chunk_index = 0
        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"].strip()
            if not page_text:
                continue
            chunks = self.chunk(page_text)
            for chunk in chunks:
                result.append({
                    "page_number": page_num,
                    "text": chunk,
                    "chunk_index": chunk_index
                })
                chunk_index += 1
        return result
