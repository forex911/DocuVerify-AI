"""
Application configuration for DocuVerify AI.
"""

from decimal import Decimal
from pathlib import Path
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load .env file from project root or backend directory if present
load_dotenv()


class Settings:
    APP_NAME: str = "DocuVerify AI"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/docuverify.db")

    # File Upload Limits
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))  # 10MB default
    ALLOWED_EXTENSIONS: set = {".pdf"}
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Deterministic validation tolerances
    FINANCIAL_TOLERANCE: Decimal = Decimal(os.getenv("FINANCIAL_TOLERANCE", "0.00"))
    QUANTITY_TOLERANCE: Decimal = Decimal(os.getenv("QUANTITY_TOLERANCE", "0.00"))

    # Optional Gemini
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # OCR configuration
    OCR_ENABLED: bool = os.getenv("OCR_ENABLED", "false").lower() in ("true", "1", "yes")
    TESSERACT_CMD: Optional[str] = os.getenv("TESSERACT_CMD", None)

    def init_app(self):
        """Ensure necessary directories exist."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_app()

