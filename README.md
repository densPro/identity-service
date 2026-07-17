# 🔐 Identity Service

The **Identity Service** is the centralized authentication and authorization microservice for the **Chirimoya** healthcare platform. It is responsible for user registration, login, JWT token issuance, token rotation, and token validation for all other services in the platform.

- **Base URL:** `http://localhost:8002`
- **Interactive Docs:** `http://localhost:8002/docs`
- **ReDoc:** `http://localhost:8002/redoc`

---

## Table of Contents

1. [Architecture](#architecture)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Environment Variables](#environment-variables)
5. [Running the Service](#running-the-service)
6. [Database Migrations](#database-migrations)
7. [API Reference](#api-reference)
   - [Health](#health)
   - [Authentication](#authentication)
   - [Users](#users)
8. [Authentication Flow](#authentication-flow)
9. [Error Reference](#error-reference)
10. [Roles & Statuses](#roles--statuses)
11. [Inter-Service Integration](#inter-service-integration)
12. [Docker & Docker Compose](#docker--docker-compose)

---

## Architecture

This service follows **Domain-Driven Design (DDD)** with a clean layered architecture:

```
Presentation Layer   →  REST API routers (FastAPI)
Application Layer    →  Commands, Queries, DTOs
Domain Layer         →  Entities, Enums, Domain Exceptions
Infrastructure Layer →  SQLAlchemy ORM, DB session, Repositories
Core                 →  Security (bcrypt + JWT), Logging
```

The `User` entity is a pure Python aggregate root with no framework dependencies. All database concerns live in the infrastructure layer, keeping the domain model clean.

---

## Tech Stack

| Component        | Technology                          |
|-----------------|-------------------------------------|
| Framework       | FastAPI 0.115+                      |
| Server          | Uvicorn (ASGI)                      |
| Database        | PostgreSQL (via asyncpg)            |
| ORM             | SQLAlchemy 2.0 (async)             |
| Migrations      | Alembic                             |
| Auth            | JWT (PyJWT) + bcrypt                |
| Validation      | Pydantic v2 + pydantic-settings     |
| Python          | 3.12+                               |

---

## Project Structure

```
identity-service/
├── app/
│   ├── main.py                  # Application factory (FastAPI app)
│   ├── config.py                # Settings via pydantic-settings (.env)
│   ├── dependencies.py          # FastAPI dependency injection (UoW)
│   ├── application/
│   │   ├── commands/            # Write operations (register, login, refresh)
│   │   ├── queries/             # Read operations (get user, validate token)
│   │   └── dtos/                # Request/Response data shapes
│   ├── core/
│   │   ├── security.py          # bcrypt hashing + JWT create/decode
│   │   └── logging.py           # Structured logging setup
│   ├── domain/
│   │   ├── entities/user.py     # User aggregate root
│   │   ├── enums/               # UserRole, UserStatus
│   │   └── exceptions.py        # Domain-specific exceptions
│   ├── infrastructure/
│   │   └── database/            # SQLAlchemy engine, session, models
│   ├── middleware/
│   │   └── logging_middleware.py # Request/response logging
│   └── presentation/
│       └── routers/             # auth_router, users_router, health_router
├── migrations/                  # Alembic migration files
├── Dockerfile                   # Multi-stage production image
├── requirements.txt
├── alembic.ini
└── .env                         # Local environment configuration
```

---

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed.

| Variable                      | Default                          | Description                                    |
|-------------------------------|----------------------------------|------------------------------------------------|
| `APP_NAME`                    | `"Identity Service"`             | Application name shown in logs and docs        |
| `DEBUG`                       | `False`                          | Enables SQLAlchemy query echo and debug mode   |
| `API_V1_PREFIX`               | `"/api/v1"`                      | API prefix (informational, routers use it directly) |
| `DATABASE_URL`                | `postgresql+asyncpg://...`       | Async PostgreSQL connection string             |
| `JWT_SECRET_KEY`              | —                                | Secret for signing **access** tokens (**required**) |
| `JWT_REFRESH_SECRET_KEY`      | —                                | Secret for signing **refresh** tokens (**required**) |
| `JWT_ALGORITHM`               | `"HS256"`                        | JWT signing algorithm                          |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15`                             | Access token lifetime in minutes               |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                              | Refresh token lifetime in days                 |
| `LOG_LEVEL`                   | `"INFO"`                         | `DEBUG`, `INFO`, `WARNING`, `ERROR`            |
| `LOG_FORMAT`                  | `"text"`                         | `text` (human-readable) or `json` (structured) |
| `CORS_ORIGINS`                | `["*"]`                          | JSON array of allowed origins                  |

> ⚠️ **Never commit real `JWT_SECRET_KEY` or `JWT_REFRESH_SECRET_KEY` values to version control.**

---

## Running the Service

### Option 1: Docker Compose (recommended)

The service ships with a `docker-compose.yml` that starts **both** the application and its dedicated PostgreSQL database as a single Compose stack — identical in structure to the `patient-management-service`.

```powershell
# 1. Navigate to service root
cd api/identity-service

# 2. Build and start all services in the background
docker compose up -d --build

# 3. Apply database migrations (once the stack is healthy)
docker exec -it identity-service alembic upgrade head
```

To stop the stack:
```powershell
docker compose down
# To also remove the database volume:
docker compose down -v
```

**Port mapping:**

| Container        | Host port → Container port |
|------------------|----------------------------|
| `identity-service` | `8002 → 8002`            |
| `identity-db`      | `5435 → 5432`            |

### Option 2: Local Development

**Prerequisites:** Python 3.12+, PostgreSQL running on port `5435`, virtual environment.

```powershell
# 1. Navigate to service root
cd api/identity-service

# 2. Activate the virtual environment
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. Apply database migrations
alembic upgrade head

# 4. Start the development server (with auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

> Ensure `DATABASE_URL` in `.env` points to `localhost:5435` for local runs.

---

## Database Migrations

Migrations are managed with **Alembic** and run against the `DATABASE_URL` defined in `.env`.

```powershell
# Apply all pending migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# Generate a new migration (after changing ORM models)
alembic revision --autogenerate -m "describe your change"

# View current migration state
alembic current

# View migration history
alembic history
```

The first migration (`e25a7f8dec4a`) creates the `users` table with the following columns:

| Column            | Type                     | Notes                      |
|-------------------|--------------------------|----------------------------|
| `id`              | `UUID`                   | Primary key, auto-generated |
| `email`           | `VARCHAR(255)` UNIQUE    | Used for login             |
| `hashed_password` | `TEXT`                   | bcrypt hash                |
| `first_name`      | `VARCHAR(100)`           |                            |
| `last_name`       | `VARCHAR(100)`           |                            |
| `role`            | `ENUM`                   | `admin`, `doctor`, `patient`, `staff` |
| `status`          | `ENUM`                   | `active`, `inactive`, `suspended` |
| `created_at`      | `TIMESTAMP`              | UTC, auto-set on insert    |
| `updated_at`      | `TIMESTAMP`              | UTC, auto-updated          |

---

## API Reference

### Health

#### `GET /api/v1/health`

Returns the operational status of the service and its database connection.

**Response `200 OK`**
```json
{
  "service": "identity-service",
  "status": "ok",
  "database": "ok"
}
```

If the database is unreachable, `"database"` returns `"unavailable"` but the HTTP status is still `200`.

---

### Authentication

All auth endpoints live under `/api/v1/auth` and do **not** require a token.

---

#### `POST /api/v1/auth/register`

Register a new user account.

**Request Body**
```json
{
  "email": "john.doe@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "patient"
}
```

| Field        | Type   | Required | Constraints              |
|--------------|--------|----------|--------------------------|
| `email`      | string | ✅       | Valid email format        |
| `password`   | string | ✅       | 8–128 characters          |
| `first_name` | string | ✅       | 1–100 characters          |
| `last_name`  | string | ✅       | 1–100 characters          |
| `role`       | string | ❌       | `admin`, `doctor`, `patient`, `staff` — defaults to `patient` |

**Response `201 Created`**
```json
{
  "id": "a3f1c2d4-1234-5678-abcd-ef0123456789",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "patient",
  "status": "active",
  "created_at": "2026-07-16T14:00:00Z",
  "updated_at": "2026-07-16T14:00:00Z"
}
```

**Error Responses**

| Status | When |
|--------|------|
| `409 Conflict` | Email is already registered |
| `422 Unprocessable Entity` | Validation failure (bad email, short password, etc.) |

---

#### `POST /api/v1/auth/login`

Authenticate with email and password. Returns a JWT access + refresh token pair.

**Request Body**
```json
{
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```

**Response `200 OK`**
```json
{
  "access_token": "<jwt_access_token>",
  "refresh_token": "<jwt_refresh_token>",
  "token_type": "bearer",
  "expires_in": 900
}
```

> `expires_in` is in **seconds** (900 = 15 minutes by default).

**Error Responses**

| Status | When |
|--------|------|
| `401 Unauthorized` | Wrong email or password |
| `403 Forbidden` | Account is suspended or inactive |

---

#### `POST /api/v1/auth/refresh`

Exchange a valid refresh token for a **new** access + refresh token pair (token rotation — the old refresh token is invalidated conceptually on the next refresh cycle).

**Request Body**
```json
{
  "refresh_token": "<jwt_refresh_token>"
}
```

**Response `200 OK`** — same shape as `/login`:
```json
{
  "access_token": "<new_jwt_access_token>",
  "refresh_token": "<new_jwt_refresh_token>",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses**

| Status | When |
|--------|------|
| `401 Unauthorized` | Refresh token is expired or invalid |
| `403 Forbidden` | User account is suspended |

---

#### `POST /api/v1/auth/validate`

Verify an access token and return its decoded claims. **Designed to be called by other microservices** to validate incoming requests without needing direct DB access.

**Request Body**
```json
{
  "token": "<jwt_access_token>"
}
```

**Response `200 OK`**
```json
{
  "sub": "a3f1c2d4-1234-5678-abcd-ef0123456789",
  "email": "john.doe@example.com",
  "role": "patient"
}
```

| Field   | Description                       |
|---------|-----------------------------------|
| `sub`   | User UUID (subject claim)         |
| `email` | User's email address              |
| `role`  | User's role string                |

**Error Responses**

| Status | When |
|--------|------|
| `401 Unauthorized` | Token is expired or has an invalid signature |

---

### Users

All user endpoints require a valid **Bearer access token** in the `Authorization` header.

```
Authorization: Bearer <jwt_access_token>
```

---

#### `GET /api/v1/users/me`

Return the profile of the currently authenticated user.

**Headers**
```
Authorization: Bearer <jwt_access_token>
```

**Response `200 OK`**
```json
{
  "id": "a3f1c2d4-1234-5678-abcd-ef0123456789",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "patient",
  "status": "active",
  "created_at": "2026-07-16T14:00:00Z",
  "updated_at": "2026-07-16T14:00:00Z"
}
```

**Error Responses**

| Status | When |
|--------|------|
| `401 Unauthorized` | Token missing, expired, or invalid |
| `404 Not Found` | User ID from token no longer exists in DB |

---

#### `GET /api/v1/users/{user_id}`

Return the profile of any user by UUID. Requires a valid access token.

**Path Parameter**

| Parameter | Type   | Description         |
|-----------|--------|---------------------|
| `user_id` | `UUID` | Target user's UUID  |

**Headers**
```
Authorization: Bearer <jwt_access_token>
```

**Response `200 OK`** — same shape as `/me`.

**Error Responses**

| Status | When |
|--------|------|
| `401 Unauthorized` | Token missing, expired, or invalid |
| `404 Not Found` | No user with that UUID exists |

---

## Authentication Flow

```
┌─────────┐           ┌──────────────────┐          ┌──────────────┐
│  Client │           │ Identity Service  │          │  PostgreSQL  │
└────┬────┘           └────────┬─────────┘          └──────┬───────┘
     │                         │                           │
     │  POST /auth/register    │                           │
     │────────────────────────►│  Hash password (bcrypt)   │
     │                         │──── INSERT user ─────────►│
     │◄────────────────────────│                           │
     │  201 UserResponse       │                           │
     │                         │                           │
     │  POST /auth/login       │                           │
     │────────────────────────►│  Verify password          │
     │                         │──── SELECT user ─────────►│
     │                         │◄──────────────────────────│
     │                         │  Issue access + refresh   │
     │◄────────────────────────│  tokens (JWT HS256)       │
     │  200 TokenResponse      │                           │
     │                         │                           │
     │  GET /users/me          │                           │
     │  Authorization: Bearer  │                           │
     │────────────────────────►│  Decode + validate JWT    │
     │                         │──── SELECT user ─────────►│
     │◄────────────────────────│                           │
     │  200 UserResponse       │                           │
     │                         │                           │
     │  POST /auth/refresh     │                           │
     │  { refresh_token }      │                           │
     │────────────────────────►│  Decode refresh token     │
     │                         │──── SELECT user ─────────►│
     │                         │  Issue new token pair     │
     │◄────────────────────────│                           │
     │  200 TokenResponse      │                           │
```

### Token Details

| Token Type    | Lifetime       | Secret Used              | Claims |
|---------------|----------------|--------------------------|--------|
| Access token  | 15 min (default) | `JWT_SECRET_KEY`       | `sub`, `email`, `role`, `type=access`, `exp`, `iat` |
| Refresh token | 7 days (default) | `JWT_REFRESH_SECRET_KEY` | `sub`, `type=refresh`, `exp`, `iat` |

---

## Error Reference

All error responses follow this shape:

```json
{
  "detail": "Human-readable error message."
}
```

| HTTP Status | Domain Exception       | Meaning                                      |
|-------------|------------------------|----------------------------------------------|
| `401`       | `InvalidCredentialsError` | Wrong email or password                   |
| `401`       | `TokenExpiredError`    | JWT has passed its `exp` claim               |
| `401`       | `TokenInvalidError`    | JWT signature is wrong or token is malformed |
| `403`       | `InactiveUserError`    | Account is suspended or inactive             |
| `404`       | `UserNotFoundError`    | No user found for given ID or email          |
| `409`       | `DuplicateUserError`   | Email already registered                     |
| `422`       | Pydantic validation    | Request body fails schema validation         |

---

## Roles & Statuses

### User Roles (`UserRole`)

| Value     | Description                          |
|-----------|--------------------------------------|
| `patient` | Default role for new registrations   |
| `doctor`  | Medical professional                 |
| `admin`   | Platform administrator               |
| `staff`   | Administrative / support staff       |

### User Statuses (`UserStatus`)

| Value       | Description                                       |
|-------------|---------------------------------------------------|
| `active`    | Account is fully operational (default on creation) |
| `inactive`  | Account has been deactivated                      |
| `suspended` | Account is temporarily suspended; login is blocked |

Suspended and inactive users receive `403 Forbidden` on login attempts.

---

## Inter-Service Integration

Other microservices in the Chirimoya platform should **never** re-implement JWT decoding. Instead, call the validate endpoint:

```http
POST http://identity-service:8002/api/v1/auth/validate
Content-Type: application/json

{
  "token": "<access_token_from_client>"
}
```

On success (`200`), the response gives you `sub` (user UUID), `email`, and `role` — all you need to authorize a request. On `401`, reject the client's request.

**Example with `httpx` in another Python service:**
```python
import httpx

async def validate_token(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/api/v1/auth/validate",
            json={"token": token},
        )
        response.raise_for_status()  # raises on 401
        return response.json()       # {"sub": "...", "email": "...", "role": "..."}
```

---

## Docker & Docker Compose

The service uses a **multi-stage Dockerfile** for a lean production image and a `docker-compose.yml` that groups the application and its database into a single Compose stack.

### Compose services

| Service            | Image                          | Host port |
|--------------------|--------------------------------|-----------|
| `identity-service` | Built from local `Dockerfile`  | `8002`    |
| `identity-db`      | `postgres:16-alpine`           | `5435`    |

### Common commands

```powershell
# Start full stack (build on first run)
docker compose up -d --build

# View running services
docker compose ps

# Tail logs
docker compose logs -f

# Run migrations inside the running container
docker exec -it identity-service alembic upgrade head

# Stop stack (preserves DB volume)
docker compose down

# Stop stack and delete the DB volume
docker compose down -v

# Rebuild image after code changes
docker compose up -d --build identity-service
```

### Dockerfile details

- **Stage 1 (builder):** Installs Python dependencies into a prefix directory.
- **Stage 2 (runtime):** Copies only installed packages and app code; runs as a **non-root user** (`appuser`) for security.

**Health Check** (built into image):
```
GET http://localhost:8002/api/v1/health
Interval: 30s | Timeout: 5s | Start period: 10s | Retries: 3
```

> **Note:** When running via Compose, the app container connects to the database using the internal Docker network hostname `postgres` (not `localhost`). The `docker-compose.yml` injects the correct `DATABASE_URL` automatically via the `environment:` override, so your `.env` file can keep `localhost:5435` for local development.
