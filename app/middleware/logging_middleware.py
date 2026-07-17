"""HTTP request/response logging middleware.

Emits one INFO log line per request with:
  - A unique request ID (X-Request-ID header, or auto-generated UUID4 short hash)
  - HTTP method and path
  - Response status code
  - Wall-clock duration in milliseconds
  - Client IP address
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger("chirimoya.identity.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request and response with timing and request ID."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id: str = (
            request.headers.get("X-Request-ID")
            or uuid.uuid4().hex[:12]
        )
        request.state.request_id = request_id

        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        start = time.perf_counter()

        logger.debug(
            "→ %s %s",
            request.method,
            request.url.path,
            extra={
                "request_id": request_id,
                "method":     request.method,
                "path":       request.url.path,
                "query":      str(request.url.query) or None,
                "client_ip":  client_ip,
            },
        )

        exc_to_reraise: BaseException | None = None
        try:
            response = await call_next(request)
        except Exception as exc:
            exc_to_reraise = exc
            from starlette.responses import PlainTextResponse
            response = PlainTextResponse("Internal Server Error", status_code=500)

        duration_ms = (time.perf_counter() - start) * 1_000

        log_extra = {
            "request_id":  request_id,
            "method":      request.method,
            "path":        request.url.path,
            "status_code": response.status_code,
            "duration_ms": f"{duration_ms:.1f}",
            "client_ip":   client_ip,
        }

        if response.status_code >= 500:
            logger.error(
                "← %s %s %d  %.1fms",
                request.method, request.url.path, response.status_code, duration_ms,
                exc_info=exc_to_reraise, extra=log_extra,
            )
        elif response.status_code >= 400:
            logger.warning(
                "← %s %s %d  %.1fms",
                request.method, request.url.path, response.status_code, duration_ms,
                extra=log_extra,
            )
        else:
            logger.info(
                "← %s %s %d  %.1fms",
                request.method, request.url.path, response.status_code, duration_ms,
                extra=log_extra,
            )

        response.headers["X-Request-ID"] = request_id

        if exc_to_reraise is not None:
            raise exc_to_reraise

        return response
