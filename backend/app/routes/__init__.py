"""
Routes package exports.
"""

from app.routes.health import router as health_router
from app.routes.orders import router as orders_router
from app.routes.documents import router as documents_router
from app.routes.verification import router as verification_router
from app.routes.workflows import router as workflows_router
from app.routes.reviews import router as reviews_router
from app.routes.audit import router as audit_router
from app.routes.dashboard import router as dashboard_router

__all__ = [
    "health_router",
    "orders_router",
    "documents_router",
    "verification_router",
    "workflows_router",
    "reviews_router",
    "audit_router",
    "dashboard_router",
]

