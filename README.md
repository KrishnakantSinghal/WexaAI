# WexaAI — Real-Time Analytics & Reporting Platform

A production-grade SaaS analytics platform built with **FastAPI** (Python 3.11+) and **Next.js 14** (TypeScript). Think a lightweight Mixpanel/Metabase.

## Architecture Overview

```
WexaAI/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── core/               # Config, security, exceptions, dependencies, logging
│   │   ├── db/                 # SQLAlchemy async session, Redis, base models
│   │   ├── models/             # SQLAlchemy ORM models (User, Org, Event, Dashboard, Alert…)
│   │   ├── schemas/            # Pydantic v2 schemas (request/response validation)
│   │   ├── repositories/       # Database access layer (Clean Architecture)
│   │   ├── services/           # Business logic layer
│   │   ├── routers/            # FastAPI route handlers
│   │   ├── tasks/              # Celery tasks (event processing, alert eval, reports)
│   │   ├── websocket/          # WebSocket connection manager
│   │   └── middleware/         # Correlation ID, structured logging
│   ├── alembic/                # Database migrations
│   └── tests/                  # pytest + pytest-asyncio tests
└── frontend/                   # Next.js 14 App Router frontend
    └── src/
        ├── app/                # Pages (auth, dashboard, events, alerts, settings)
        ├── components/         # Reusable UI components
        ├── hooks/              # useAuth, useWebSocket
        ├── store/              # Zustand state (auth, dashboard)
        ├── lib/                # Axios client, React Query config, utils
        └── types/              # TypeScript type definitions
```

## Tech Stack

### Backend

| Layer         | Technology                             |
| ------------- | -------------------------------------- |
| Framework     | FastAPI 0.115 + Uvicorn                |
| Language      | Python 3.11+ with full type hints      |
| Database      | PostgreSQL 16 + SQLAlchemy 2.0 (async) |
| Migrations    | Alembic                                |
| Cache / Queue | Redis 7                                |
| Task Queue    | Celery 5 + Celery Beat                 |
| Auth          | JWT (python-jose) + bcrypt (passlib)   |
| Validation    | Pydantic v2                            |
| Rate Limiting | slowapi                                |
| Logging       | structlog (JSON structured logs)       |
| Real-Time     | WebSockets (Starlette)                 |
| Email         | aiosmtplib                             |
| Reports       | ReportLab (PDF)                        |
| Testing       | pytest + pytest-asyncio + httpx        |

### Frontend

| Layer         | Technology                      |
| ------------- | ------------------------------- |
| Framework     | Next.js 14 (App Router)         |
| UI            | React 18 + TypeScript           |
| Styling       | Tailwind CSS                    |
| State         | Zustand                         |
| Data Fetching | TanStack Query (React Query v5) |
| Charts        | Recharts                        |
| Forms         | React Hook Form + Zod           |
| Real-Time     | Native WebSocket                |

## Features

### ✅ Must Have

- **Authentication & Multi-Tenancy** — JWT access + HTTP-only refresh token cookie, role hierarchy (Owner → Admin → Analyst → Viewer), org-level data isolation
- **Data Ingestion** — Single/batch event API, CSV upload, async Celery processing, API key management
- **Dashboards & Widgets** — Custom dashboards, 5 widget types (line/bar/pie/KPI/table), drag layout, public sharing, auto-refresh
- **Real-Time** — WebSocket live dashboard updates, alert push notifications, event stream viewer

### ✅ Should Have

- **Alerts** — Threshold-based rules, Celery Beat evaluation, email + webhook (Slack-compatible) + in-app notifications, mute/snooze
- **Scheduled Reports** — PDF generation via Celery, email delivery, report archive

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### With Docker (Recommended)

```bash
# 1. Clone and configure
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
# Edit backend/.env with your settings

# 2. Start all services
docker-compose up -d

# 3. Run migrations (first time only)
docker-compose exec api alembic upgrade head

# 4. Open the app
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/api/docs
# Flower (Celery monitor): http://localhost:5555
```

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL and Redis URLs

# Run migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery Beat (separate terminal)
celery -A app.tasks.celery_app beat --loglevel=info
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Start dev server
npm run dev
# Open http://localhost:3000
```

## Environment Variables

### Backend (`backend/.env`)

| Variable                                    | Description                       | Default                    |
| ------------------------------------------- | --------------------------------- | -------------------------- |
| `DATABASE_URL`                              | PostgreSQL async URL              | `postgresql+asyncpg://...` |
| `REDIS_URL`                                 | Redis connection URL              | `redis://localhost:6379/0` |
| `SECRET_KEY`                                | JWT signing secret (min 32 chars) | **change this!**           |
| `ACCESS_TOKEN_EXPIRE_MINUTES`               | JWT access token TTL              | `15`                       |
| `REFRESH_TOKEN_EXPIRE_DAYS`                 | Refresh token TTL                 | `7`                        |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | Email config                      | —                          |
| `ALLOWED_ORIGINS`                           | CORS origins (comma-separated)    | `http://localhost:3000`    |
| `FRONTEND_URL`                              | Frontend URL (for invite links)   | `http://localhost:3000`    |

### Frontend (`frontend/.env.local`)

| Variable              | Description          |
| --------------------- | -------------------- |
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_WS_URL`  | WebSocket base URL   |

## API Reference

Interactive API docs available at `http://localhost:8000/api/docs` (Swagger UI).

### Key Endpoints

```
POST   /api/v1/auth/signup              Sign up + create organization
POST   /api/v1/auth/signin              Sign in
POST   /api/v1/auth/refresh             Refresh access token

GET    /api/v1/users/me                 Current user profile
PATCH  /api/v1/users/me                 Update profile

GET    /api/v1/organizations/current    Current organization
POST   /api/v1/organizations/current/members/invite  Invite member
GET    /api/v1/organizations/current/api-keys  List API keys
POST   /api/v1/organizations/current/api-keys  Create API key

POST   /api/v1/events/ingest            Single event ingestion
POST   /api/v1/events/ingest/batch      Batch event ingestion (up to 1000)
POST   /api/v1/events/ingest/csv        CSV file upload
POST   /api/v1/events/query             Query/aggregate events

GET    /api/v1/dashboards               List dashboards
POST   /api/v1/dashboards               Create dashboard
GET    /api/v1/dashboards/{id}          Get dashboard with widgets
POST   /api/v1/dashboards/{id}/widgets  Add widget

GET    /api/v1/alerts                   List alerts
POST   /api/v1/alerts                   Create alert rule
POST   /api/v1/alerts/{id}/mute         Mute alert

WS     /ws/dashboard/{id}              Live dashboard updates
WS     /ws/alerts                      Real-time alert notifications
WS     /ws/events/stream               Live event stream
```

## Database Design

- **Partitioned events table** — range partitioned by `timestamp` for time-series query performance
- **Indexes** — composite indexes on `(organization_id, timestamp)` and `(organization_id, event_name)`
- **Soft deletes** — all major entities use `deleted_at` for safe deletion
- **Multi-tenancy** — all queries scoped by `organization_id` at the repository layer

## Running Tests

```bash
cd backend

# Ensure test DB exists
createdb wexaai_test

# Run tests
pytest --cov=app --cov-report=term-missing

# Run specific file
pytest tests/test_auth.py -v
```

## Architecture Decisions

1. **Clean Architecture** — Strict layer separation: Routers → Services → Repositories → Models. Each layer has a single responsibility.
2. **Async-First** — Every I/O operation uses `async/await`. SQLAlchemy 2.0 async, aioredis, aiosmtplib.
3. **Event-Driven** — Celery workers decouple ingestion from heavy processing. Celery Beat handles scheduled alert evaluation and report generation.
4. **Security** — JWT with short-lived access tokens + HTTP-only refresh cookies. Passwords hashed with bcrypt (cost factor 12). API keys stored as SHA-256 hashes. Rate limiting via slowapi + Redis.
5. **Observability** — Structured JSON logging (structlog), correlation IDs on every request, health check endpoints.

## Deployment

### Backend (Railway / Render)

1. Set all environment variables in the platform dashboard
2. Use the provided `Dockerfile` in `backend/`
3. Run `alembic upgrade head` as a release command
4. Deploy Celery worker and Beat as separate services

### Frontend (Vercel)

1. Import the `frontend/` directory
2. Set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` environment variables
3. Deploy

## License

MIT
