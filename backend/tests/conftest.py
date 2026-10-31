"""
Pytest fixtures and configuration for DocuVerify AI test suite.
Uses temporary isolated SQLite databases and isolated file directories.
"""

import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.database import Base
from app.database.connection import get_db
from app.database.models import ValidationRule
from app.core.constants import RULE_DEFINITIONS
from app.main import app

os.environ["OCR_ENABLED"] = "false"


@pytest.fixture(scope="session")
def test_temp_dir():
    """Provides a temporary directory for test uploads."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="function")
def db_session(test_temp_dir):
    """Provides an isolated SQLite database session for each test."""
    db_file = test_temp_dir / f"test_{tempfile.mktemp(dir='')}.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
    Base.metadata.create_all(bind=engine)

    # Seed rules
    db = TestingSessionLocal()
    for rule_id, rule_info in RULE_DEFINITIONS.items():
        r = ValidationRule(
            id=rule_info["rule_id"],
            name=rule_info["name"],
            description=rule_info["description"],
            default_severity=rule_info["default_severity"],
            version=rule_info["version"],
            is_active=True,
        )
        db.add(r)
    db.commit()

    try:
        yield db
    finally:
        db.close()
        # Dispose engine connections on Windows before file cleanup
        engine.dispose()
        if db_file.exists():
            try:
                db_file.unlink()
            except Exception:
                pass


@pytest.fixture(scope="function")
def client(db_session, test_temp_dir, monkeypatch):
    """Provides a FastAPI TestClient wired to the temporary DB and upload directory."""
    monkeypatch.setattr(settings, "UPLOAD_DIR", test_temp_dir)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
