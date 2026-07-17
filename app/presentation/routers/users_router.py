"""Users REST API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dtos.token_response import TokenPayloadDTO
from app.application.dtos.user_response import UserResponseDTO
from app.application.queries.get_user import GetUserQuery
from app.application.queries.validate_token import ValidateTokenQuery
from app.core.logging import get_logger
from app.dependencies import get_unit_of_work
from app.domain.exceptions import TokenExpiredError, TokenInvalidError, UserNotFoundError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/api/v1/users", tags=["Users"])
logger = get_logger(__name__)

_bearer = HTTPBearer()


async def _get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TokenPayloadDTO:
    """Decode the Bearer token from the Authorization header."""
    try:
        query = ValidateTokenQuery()
        return await query.execute(credentials.credentials)
    except (TokenExpiredError, TokenInvalidError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=getattr(exc, "message", str(exc)),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ------------------------------------------------------------------
# GET /api/v1/users/me
# ------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserResponseDTO,
    summary="Get current user",
    description="Return the profile of the authenticated user.",
)
async def get_me(
    payload: TokenPayloadDTO = Depends(_get_current_user_payload),
    uow=Depends(get_unit_of_work),
) -> UserResponseDTO:
    try:
        query = GetUserQuery(uow)
        return await query.by_id(uuid.UUID(payload.sub))
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


# ------------------------------------------------------------------
# GET /api/v1/users/{user_id}
# ------------------------------------------------------------------
@router.get(
    "/{user_id}",
    response_model=UserResponseDTO,
    summary="Get user by ID",
    description="Return a user profile by UUID. Requires a valid access token.",
)
async def get_user_by_id(
    user_id: uuid.UUID,
    _payload: TokenPayloadDTO = Depends(_get_current_user_payload),
    uow=Depends(get_unit_of_work),
) -> UserResponseDTO:
    try:
        query = GetUserQuery(uow)
        return await query.by_id(user_id)
    except UserNotFoundError as exc:
        logger.info("User not found", extra={"user_id": str(user_id)})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
