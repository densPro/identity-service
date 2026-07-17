"""FastAPI application factory for the Identity Service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import get_logger, setup_logging
from app.infrastructure.database.session import engine
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.presentation.routers import auth_router, health_router, users_router

# Initialize logging as early as possible.
setup_logging(level=settings.log_level, fmt=settings.log_format)

_log = get_logger("chirimoya.identity")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown hooks."""
    _log.info(
        "Starting up %s",
        settings.app_name,
        extra={
            "log_level":  settings.log_level,
            "log_format": settings.log_format,
            "debug":      settings.debug,
        },
    )
    yield
    _log.info("Shutting down %s — disposing connection pool", settings.app_name)
    await engine.dispose()
    _log.info("Shutdown complete")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Identity Service for the Chirimoya healthcare platform. "
            "Handles user registration, authentication, and JWT-based authorization."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # --- Middleware ---
    app.add_middleware(RequestLoggingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    app.include_router(health_router.router)
    app.include_router(auth_router.router)
    app.include_router(users_router.router)

    _log.debug("Application factory complete — %d routes registered", len(app.routes))
    return app


app = create_app()
