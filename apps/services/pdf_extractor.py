import os
import re
from typing import Dict, Any, List
from pypdf import PdfReader


def clean_text(text: str) -> str:
    """Clean and normalize extracted PDF text."""
    if not text:
        return ""
    # Replace null bytes
    text = text.replace("\x00", "")
    # Normalize multiple whitespace/newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_text_from_pdf(file_path_or_buffer) -> Dict[str, Any]:
    """
    Extract text and metadata from a PDF file.
    
    Args:
        file_path_or_buffer: File path string or file-like object.
        
    Returns:
        Dict with keys:
            - page_count: Total pages
            - full_text: Aggregated and cleaned text
            - pages: List of text per page
            - error: Error message if extraction failed, else None
    """
    try:
        reader = PdfReader(file_path_or_buffer)
        
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                return {
                    "page_count": 0,
                    "full_text": "",
                    "pages": [],
                    "error": "The PDF file is password-protected and cannot be read."
                }

        page_count = len(reader.pages)
        pages_text: List[str] = []
        
        for idx, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                pages_text.append(clean_text(page_text))
            except Exception as e:
                pages_text.append(f"[Error reading page {idx + 1}: {str(e)}]")
                
        full_text = "\n\n".join(pages_text).strip()
        
        if not full_text:
            return {
                "page_count": page_count,
                "full_text": "",
                "pages": pages_text,
                "error": "No readable text could be extracted. The PDF might contain only scanned images."
            }

        return {
            "page_count": page_count,
            "full_text": full_text,
            "pages": pages_text,
            "error": None
        }

    except Exception as e:
        return {
            "page_count": 0,
            "full_text": "",
            "pages": [],
            "error": f"Failed to parse PDF: {str(e)}"
        }


def chunk_text(text: str, max_chunk_size: int = 6000, overlap: int = 500) -> List[str]:
    """
    Split long text into manageable chunks with overlap for LLM processing.
    """
    if len(text) <= max_chunk_size:
        return [text]
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (max_chunk_size - overlap)
        
    return chunks

