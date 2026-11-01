"""
Database package initialization and table creation.
"""

from sqlalchemy import text
from app.core.config import settings
from app.database.connection import engine, Base, SessionLocal
from app.database.models import ValidationRule
from app.core.constants import RULE_DEFINITIONS


def init_db():
    """Create all tables and seed default validation rules if not present."""
    if settings.DATABASE_URL.startswith("sqlite") and ":memory:" not in settings.DATABASE_URL:
        try:
            with engine.connect() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL"))
                conn.commit()
        except Exception:
            pass
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for rule_id, rule_info in RULE_DEFINITIONS.items():
            existing = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
            if not existing:
                new_rule = ValidationRule(
                    id=rule_info["rule_id"],
                    name=rule_info["name"],
                    description=rule_info["description"],
                    default_severity=rule_info["default_severity"],
                    version=rule_info["version"],
                    is_active=True,
                )
                db.add(new_rule)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

