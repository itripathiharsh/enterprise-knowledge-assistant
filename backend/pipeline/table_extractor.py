"""
Extract tables from PDFs using camelot and convert to markdown.
Called from ingestion.py after standard text extraction.
Tables are appended to the text of the page they appear on.
"""
import camelot
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

def extract_tables_from_page(pdf_path: Path, page_number: int) -> str:
    """
    Extract all tables from a specific page.
    Returns markdown string of all tables found (empty string if none).
    page_number is 1-indexed.
    """
    try:
        tables = camelot.read_pdf(
            str(pdf_path),
            pages=str(page_number),
            flavor="lattice"  # For bordered tables; fall back to "stream" if 0 found
        )
        
        if len(tables) == 0:
            # Try stream flavor (for tables without visible borders)
            tables = camelot.read_pdf(
                str(pdf_path),
                pages=str(page_number),
                flavor="stream"
            )
        
        if len(tables) == 0:
            return ""
        
        markdown_tables = []
        for table in tables:
            df = table.df
            if df.empty:
                continue
            # Convert DataFrame to markdown
            md = df.to_markdown(index=False)
            markdown_tables.append(md)
        
        return "\n\n".join(markdown_tables)
    
    except Exception as e:
        logger.warning(f"Table extraction failed for page {page_number}: {e}")
        return ""
