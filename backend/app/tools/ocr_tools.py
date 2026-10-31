"""
OCR fallback tools for scanned documents.
"""

from typing import Any, Dict, Optional, Tuple
from app.services.ocr_service import ocr_service


def is_ocr_available() -> bool:
    """Checks if Tesseract OCR engine is installed and operational."""
    return ocr_service.is_available()


def run_ocr(image_bytes: bytes) -> Tuple[bool, str, Optional[str]]:
    """
    Executes OCR on an image slice.
    Returns (success, text, message).
    """
    return ocr_service.ocr_image_bytes(image_bytes)


def get_ocr_diagnostic() -> Dict[str, Any]:
    """Returns status and diagnostic details of the host OCR engine."""
    available = ocr_service.is_available()
    return {
        "engine": "Tesseract OCR",
        "available": available,
        "mode": "automatic fallback" if available else "manual extraction required",
    }

