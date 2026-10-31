"""
PDF extraction and density analysis tools.
"""

from pathlib import Path
from typing import Any, Dict
from app.services.pdf_extractor import PDFExtractor, PDFExtractionError


def extract_pdf_pages(file_path: str) -> Dict[str, Any]:
    """
    Extracts text page-by-page from a PDF file using PyMuPDF.
    
    Returns structured dict with page_count, pages, and extraction metadata.
    """
    path_obj = Path(file_path)
    return PDFExtractor.extract_document(path_obj)


def check_pdf_density(page_text: str, min_chars: int = 30) -> bool:
    """
    Evaluates whether page text exceeds minimum digital density threshold.
    Returns True if digital text is sufficient, False if page appears scanned or image-based.
    """
    return len(page_text.strip()) >= min_chars

