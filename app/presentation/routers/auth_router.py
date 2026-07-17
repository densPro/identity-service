"""Authentication REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.commands.login_user import LoginUserCommand
from app.application.commands.refresh_token import RefreshTokenCommand
from app.application.commands.register_user import RegisterUserCommand
from app.application.dtos.token_response import (
    RefreshTokenDTO,
    TokenPayloadDTO,
    TokenResponseDTO,
    TokenValidateDTO,
)
from app.application.dtos.user_login import UserLoginDTO
from app.application.dtos.user_register import UserRegisterDTO
from app.application.dtos.user_response import UserResponseDTO
from app.application.queries.validate_token import ValidateTokenQuery
from app.core.logging import get_logger
from app.dependencies import get_unit_of_work
from app.domain.exceptions import (
    DuplicateUserError,
    InactiveUserError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
logger = get_logger(__name__)


# ------------------------------------------------------------------
# POST /api/v1/auth/register
# ------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. Email must be unique.",
)
async def register(
    dto: UserRegisterDTO,
    uow=Depends(get_unit_of_work),
) -> UserResponseDTO:
    logger.debug("register request", extra={"email": dto.email, "role": dto.role.value})
    try:
        command = RegisterUserCommand(uow)
        result = await command.execute(dto)
        logger.info("User registered", extra={"user_id": str(result.id), "email": result.email})
        return result
    except DuplicateUserError as exc:
        logger.warning("Duplicate registration attempt", extra={"email": dto.email})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)


# ------------------------------------------------------------------
# POST /api/v1/auth/login
# ------------------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenResponseDTO,
    summary="Login",
    description="Authenticate with email and password. Returns a JWT access + refresh token pair.",
)
async def login(
    dto: UserLoginDTO,
    uow=Depends(get_unit_of_work),
) -> TokenResponseDTO:
    try:
        command = LoginUserCommand(uow)
        result = await command.execute(dto)
        logger.info("User logged in", extra={"email": dto.email})
        return result
    except InvalidCredentialsError as exc:
        logger.warning("Invalid login credentials", extra={"email": dto.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    except InactiveUserError as exc:
        logger.warning("Inactive user login attempt", extra={"email": dto.email})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


# ------------------------------------------------------------------
# POST /api/v1/auth/refresh
# ------------------------------------------------------------------
@router.post(
    "/refresh",
    response_model=TokenResponseDTO,
    summary="Refresh tokens",
    description="Exchange a valid refresh token for a new access + refresh token pair (token rotation).",
)
async def refresh(
    dto: RefreshTokenDTO,
    uow=Depends(get_unit_of_work),
) -> TokenResponseDTO:
    try:
        command = RefreshTokenCommand(uow)
        return await command.execute(dto.refresh_token)
    except TokenExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    except TokenInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    except InactiveUserError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


# ------------------------------------------------------------------
# POST /api/v1/auth/validate
# ------------------------------------------------------------------
@router.post(
    "/validate",
    response_model=TokenPayloadDTO,
    summary="Validate access token",
    description=(
        "Verify an access token and return its decoded claims. "
        "Intended to be called by other microservices."
    ),
)
async def validate_token(dto: TokenValidateDTO) -> TokenPayloadDTO:
    try:
        query = ValidateTokenQuery()
        return await query.execute(dto.token)
    except TokenExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    except TokenInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
