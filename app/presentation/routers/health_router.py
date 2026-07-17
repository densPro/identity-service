"""Health check router."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.logging import get_logger
from app.infrastructure.database.session import async_session_factory

router = APIRouter(prefix="/api/v1", tags=["Health"])
logger = get_logger(__name__)


@router.get(
    "/health",
    summary="Health check",
    description="Returns service status and database connectivity.",
)
async def health_check() -> dict:
    db_status = "ok"
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Database health check failed", exc_info=exc)
        db_status = "unavailable"

    return {
        "service": "identity-service",
        "status": "ok",
        "database": db_status,
    }
