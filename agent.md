# Identity Service Implementation Plan

Build a Python FastAPI `identity-service` responsible for authorization and authentication of all microservices in the Chirimoya healthcare platform.

## Technology Stack
- **FastAPI** `>=0.115.0`
- **Uvicorn** `[standard]>=0.34.0`
- **SQLAlchemy** `[asyncio]>=2.0.36`
- **Asyncpg** `>=0.30.0`
- **Pydantic** `>=2.10.0`
- **Pydantic-settings** `>=2.7.0`
- **Alembic** `>=1.14.0`
- **Python-dotenv** `>=1.0.1`
- **PyJWT** `>=2.10.0` (for JWT token management)
- **Bcrypt** `>=4.2.0` (for secure password hashing)

## Architectural Design Rules
1. **Clean Architecture / DDD**: Separate code clearly into Domain, Application, Infrastructure, and Presentation layers.
2. **Domain Decoupling**: Keep domain entities completely pure Python. Do not inherit from SQLAlchemy's base or utilize ORM decorations inside the domain.
3. **Repository and Unit of Work Patterns**: Access database tables only via Repository interfaces. Manage transactions using a Unit of Work (UoW) implementation.
4. **Environment Configuration**: Load variables using `pydantic-settings` from a `.env` file.
5. **Security Best Practices**:
   - Hash passwords before saving them using `bcrypt`.
   - Issue JSON Web Tokens (JWT) for authentication (Access Token with short lifetime, Refresh Token with longer lifetime).
   - Use asymmetric (e.g., RS256) or symmetric (e.g., HS256) algorithms. HS256 is recommended for initial implementation simplicity, configurable via settings.

---

## Service Folder Structure

```text
identity-service/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── dependencies.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging.py           # Shared structured logger
│   │   └── security.py          # Password hashing & JWT generation/validation
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   └── user.py          # Pure Python User Entity (Aggregate Root)
│   │   ├── enums/
│   │   │   ├── __init__.py
│   │   │   ├── user_role.py     # ADMIN, DOCTOR, PATIENT, STAFF
│   │   │   └── user_status.py   # ACTIVE, INACTIVE, SUSPENDED
│   │   ├── exceptions.py        # Domain-specific errors
│   │   └── value_objects/
│   ├── application/
│   │   ├── __init__.py
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── register_user.py
│   │   │   ├── login_user.py
│   │   │   └── refresh_token.py
│   │   ├── queries/
│   │   │   ├── __init__.py
│   │   │   ├── get_user.py
│   │   │   └── validate_token.py
│   │   ├── dtos/
│   │   │   ├── __init__.py
│   │   │   ├── user_register.py
│   │   │   ├── user_login.py
│   │   │   ├── user_response.py
│   │   │   └── token_response.py
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       ├── repositories/
│   │       │   ├── __init__.py
│   │       │   └── user_repository.py
│   │       └── unit_of_work.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_model.py # SQLAlchemy model mapped to users table
│   │   │   └── session.py        # SQLAlchemy async engine & session factory
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── user_repository.py
│   │   └── unit_of_work.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── logging_middleware.py
│   └── presentation/
│       ├── __init__.py
│       └── routers/
│           ├── __init__.py
│           ├── auth_router.py    # endpoints: register, login, refresh, validate
│           ├── users_router.py   # endpoints: get me, get by id
│           └── health_router.py
├── migrations/                   # Alembic migration files
├── alembic.ini
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Detailed Component Blueprint

### 1. Domain Layer (`app/domain`)

#### Enums (`app/domain/enums/`)
- `UserRole`: Enum representing roles. Values: `admin`, `doctor`, `patient`, `staff`.
- `UserStatus`: Enum representing user account status. Values: `active`, `inactive`, `suspended`.

#### Entities (`app/domain/entities/user.py`)
Pure Python domain entity:
```python
from datetime import datetime
import uuid
from app.domain.enums.user_role import UserRole
from app.domain.enums.user_status import UserStatus

class User:
    def __init__(
        self,
        id: uuid.UUID,
        email: str,
        hashed_password: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        status: UserStatus = UserStatus.ACTIVE,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
```

#### Exceptions (`app/domain/exceptions.py`)
- `IdentityError(Exception)`: Base error.
- `UserNotFoundError(IdentityError)`: Raised when a user is not found by ID or Email.
- `DuplicateUserError(IdentityError)`: Raised when registering an email that already exists.
- `InvalidCredentialsError(IdentityError)`: Raised on password mismatch.
- `TokenExpiredError(IdentityError)`: Raised when a JWT token has expired.
- `TokenInvalidError(IdentityError)`: Raised when token signature or payload parsing fails.

---

### 2. Application Layer (`app/application`)

#### Interfaces (`app/application/interfaces/`)
- `IUserRepository`: Defines abstract async methods:
  - `get_by_id(user_id: UUID) -> User | None`
  - `get_by_email(email: str) -> User | None`
  - `add(user: User) -> User`
  - `update(user: User) -> User`
- `IUnitOfWork`: Defines access to repositories and commit/rollback protocol:
  - `users: IUserRepository`
  - `commit() -> None`
  - `rollback() -> None`

#### DTOs (`app/application/dtos/`)
- `UserRegisterDTO`: Email, Password (str, min length 8), First Name, Last Name, Role.
- `UserLoginDTO`: Email, Password.
- `TokenResponseDTO`: Access Token, Refresh Token, Token Type (bearer), Expires In (seconds).
- `UserResponseDTO`: ID, Email, First Name, Last Name, Role, Status, Created At, Updated At.
- `TokenValidationDTO`: Token string to validate.

#### Commands & Queries (`app/application/commands/` & `app/application/queries/`)
- **RegisterUserCommand**: Takes `UserRegisterDTO`. Checks if email is taken. Hashes password using security module. Constructs `User` domain entity. Saves using `uow.users.add(user)` and calls `uow.commit()`. Returns `UserResponseDTO`.
- **LoginUserCommand**: Takes `UserLoginDTO`. Fetches user by email. Validates hashed password. Generates JWT access and refresh tokens. Returns `TokenResponseDTO`.
- **RefreshTokenCommand**: Validates refresh token. Extracts user identity. Generates new access token and optional new refresh token (refresh token rotation).
- **GetUserQuery**: Queries user by ID or by email, throwing `UserNotFoundError` if missing.
- **ValidateTokenQuery**: Validates access token and extracts claims. Returns payload containing `sub` (user_id), `email`, and `role`.

---

### 3. Core Security & Logger (`app/core`)

#### Security Utilities (`app/core/security.py`)
- **Password Hasher**:
  - `hash_password(password: str) -> str` using `bcrypt`.
  - `verify_password(plain_password: str, hashed_password: str) -> bool` using `bcrypt`.
- **JWT Manager**:
  - `create_access_token(subject: str, email: str, role: str, expires_delta: timedelta | None = None) -> str`
  - `create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str`
  - `decode_token(token: str) -> dict` (decodes and raises `TokenExpiredError` or `TokenInvalidError`)

---

### 4. Infrastructure Layer (`app/infrastructure`)

#### Database Models (`app/infrastructure/database/models/user_model.py`)
SQLAlchemy mappings using modern `Mapped` and `mapped_column`:
```python
import uuid
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.infrastructure.database.session import Base

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

#### Repository & UoW Implementation (`app/infrastructure/repositories/` & `app/infrastructure/unit_of_work.py`)
- Implement mapping logic between `UserModel` and `User` entity inside `UserRepository`.
- Ensure transactions are fully handled by `SqlAlchemyUnitOfWork`.

---

### 5. Presentation Layer (`app/presentation`)

#### Endpoints
- **POST `/api/v1/auth/register`**: Registers a user. Handles `DuplicateUserError` and returns `409 Conflict`.
- **POST `/api/v1/auth/login`**: Authenticates user credentials. Handles `InvalidCredentialsError` and returns `401 Unauthorized`.
- **POST `/api/v1/auth/refresh`**: Generates new token pair using refresh token.
- **POST `/api/v1/auth/validate`**: Verifies access token. Returns decoded user details. Used by other microservices.
- **GET `/api/v1/users/me`**: Returns currently logged-in user profile.
- **GET `/api/v1/health`**: Simple database and service status check.

---

## Setup & Migration Instructions

1. **Alembic Init**: Run `alembic init migrations` inside `identity-service/`.
2. **Alembic Configuration**: Configure `alembic.ini` to use environment database url. Configure `migrations/env.py` to point to the async metadata of the `Base` class.
3. **Database Migration Script**: Generate the initial script via `alembic revision --autogenerate -m "create users table"` and execute via `alembic upgrade head`.
4. **Environment Variables**:
   Create a `.env` file containing:
   ```env
   APP_NAME="Identity Service"
   DEBUG=True
   API_V1_PREFIX="/api/v1"
   DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/identity_db"
   JWT_SECRET_KEY="replace-this-with-a-very-secure-random-key"
   JWT_REFRESH_SECRET_KEY="replace-this-with-another-secure-key"
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7
   LOG_LEVEL="DEBUG"
   LOG_FORMAT="text"
   ```
