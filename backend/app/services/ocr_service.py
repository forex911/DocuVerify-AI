"""
OCR Service supporting optional Tesseract fallback.
Safely detects whether Tesseract is installed and reports limitations honestly.
"""

import io
import logging
from typing import Optional, Tuple
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        self._is_available: Optional[bool] = None
        if settings.TESSERACT_CMD and pytesseract:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    def is_available(self) -> bool:
        """Checks if Tesseract binary and pytesseract library are installed and operational."""
        if not settings.OCR_ENABLED or pytesseract is None:
            return False

        if self._is_available is not None:
            return self._is_available

        try:
            version = pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR detected, version: %s", version)
            self._is_available = True
        except Exception as e:
            logger.warning("Tesseract OCR is not available on host: %s", str(e))
            self._is_available = False

        return self._is_available

    def ocr_image_bytes(self, image_bytes: bytes) -> Tuple[bool, str, Optional[str]]:
        """
        Runs OCR on raw image bytes.
        
        Returns:
            Tuple of (success: bool, extracted_text: str, message: Optional[str])
        """
        if not self.is_available():
            return (
                False,
                "",
                "OCR unavailable: Tesseract engine is not installed or configured. Scanned content requires manual extraction."
            )

        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return True, text.strip(), None
        except Exception as e:
            logger.error("OCR execution failed: %s", str(e))
            return False, "", f"OCR processing failed: {str(e)}"


ocr_service = OCRService()

