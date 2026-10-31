"""
PDF Text Extraction Service utilizing PyMuPDF (fitz) with graceful OCR fallback.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pymupdf
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Raised when PDF extraction cannot proceed due to format, encryption, or corruption."""
    pass


class PDFExtractor:
    """Extracts text page-by-page from PDF files with provenance tracking and fallback detection."""

    MIN_TEXT_THRESHOLD_CHARS = 30  # Pages with fewer characters may be scanned/image-based

    @classmethod
    def extract_document(cls, file_path: Path) -> Dict[str, Any]:
        """
        Extracts structured page-by-page text from a PDF document.

        Returns:
            Dict containing:
                - page_count: int
                - full_text: str
                - pages: List[Dict[str, Any]]
                - requires_manual_extraction: bool
                - extraction_method: str
                - extraction_metadata: Dict[str, Any]
        """
        if not file_path.exists():
            raise PDFExtractionError(f"File not found at path: {file_path}")

        try:
            doc = pymupdf.open(str(file_path))
        except Exception as e:
            logger.error("Failed to open PDF %s: %s", file_path, str(e))
            raise PDFExtractionError(f"Corrupted or invalid PDF format: {str(e)}")

        try:
            if doc.is_encrypted:
                raise PDFExtractionError("PDF is password-encrypted and cannot be processed.")

            page_count = len(doc)
            if page_count == 0:
                raise PDFExtractionError("PDF file is empty (contains 0 pages).")

            pages_data: List[Dict[str, Any]] = []
            full_text_parts: List[str] = []
            any_requires_manual = False
            total_ocr_pages = 0

            for page_idx in range(page_count):
                page_num = page_idx + 1
                page = doc[page_idx]

                # Extract digital vector text
                page_text = page.get_text("text").strip()
                char_count = len(page_text)
                method = "pymupdf"
                ocr_used = False
                limitation_note = None

                # Detect scanned/empty page
                if char_count < cls.MIN_TEXT_THRESHOLD_CHARS:
                    # Attempt OCR if available
                    if ocr_service.is_available():
                        try:
                            pix = page.get_pixmap()
                            img_bytes = pix.tobytes("png")
                            ocr_success, ocr_text, ocr_msg = ocr_service.ocr_image_bytes(img_bytes)
                            if ocr_success and len(ocr_text) > char_count:
                                page_text = ocr_text
                                char_count = len(page_text)
                                method = "tesseract_ocr"
                                ocr_used = True
                                total_ocr_pages += 1
                            else:
                                any_requires_manual = True
                                limitation_note = ocr_msg or "Page text could not be extracted via OCR."
                        except Exception as ocr_err:
                            logger.warning("OCR attempt failed for page %d: %s", page_num, str(ocr_err))
                            any_requires_manual = True
                            limitation_note = f"OCR failed: {str(ocr_err)}"
                    else:
                        any_requires_manual = True
                        limitation_note = "Scanned/image-based page detected. OCR is unavailable on this host; manual review required."

                pages_data.append({
                    "page_number": page_num,
                    "text": page_text,
                    "char_count": char_count,
                    "method": method,
                    "ocr_used": ocr_used,
                    "limitation_note": limitation_note,
                })

                if page_text:
                    full_text_parts.append(f"--- PAGE {page_num} ---\n{page_text}")

            full_text = "\n\n".join(full_text_parts)
            primary_method = "tesseract_ocr" if (total_ocr_pages == page_count and page_count > 0) else "pymupdf"
            if total_ocr_pages > 0 and total_ocr_pages < page_count:
                primary_method = "hybrid_pymupdf_ocr"

            return {
                "page_count": page_count,
                "full_text": full_text,
                "pages": pages_data,
                "requires_manual_extraction": any_requires_manual,
                "extraction_method": primary_method,
                "extraction_metadata": {
                    "total_pages": page_count,
                    "ocr_pages_count": total_ocr_pages,
                    "is_pdf_encrypted": False,
                },
            }
        finally:
            doc.close()

