# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

eMMA (Enterprise Monitoring & Management Application) is an IT infrastructure monitoring solution with:
- Service monitoring (HTTP/HTTPS, TCP, SSL, DNS, ICMP)
- Docker container management
- Role-based access control (Admin, Operator, Viewer)
- Real-time WebSocket updates

## Tech Stack

**Backend:** FastAPI (Python 3.11+), PostgreSQL 16 with async SQLAlchemy, Alembic migrations, JWT auth
**Frontend:** React 18, TypeScript, Vite, TailwindCSS, Zustand (state), React Query (data fetching), Vitest
**Infrastructure:** Docker Compose, Redis (rate limiting/caching)

## Project Structure

```
emma/
├── server/              # FastAPI Backend
│   ├── app/
│   │   ├── api/         # API Routes (v1)
│   │   ├── core/        # Config, Auth, Middleware
│   │   ├── models/      # SQLAlchemy Models
│   │   ├── schemas/     # Pydantic Schemas
│   │   └── services/    # Business Logic
│   ├── alembic/         # DB Migrations
│   └── tests/
├── client/              # React Frontend
│   ├── src/
│   │   ├── components/  # UI Components
│   │   ├── pages/       # Page Components
│   │   ├── hooks/       # React Query Hooks
│   │   ├── stores/      # Zustand Stores
│   │   └── types/       # TypeScript Types
└── docker-compose.yml
```

## Development Commands

### Backend (from `server/`)
```bash
pip install -e ".[dev,docker]"      # Install dependencies
alembic upgrade head                 # Run migrations
alembic revision --autogenerate -m "msg"  # Create migration
uvicorn app.main:app --reload --port 8000  # Dev server
pytest                               # Run tests
ruff check .                         # Lint
mypy app                             # Type check
```

### Frontend (from `client/`)
```bash
npm install         # Install dependencies
npm run dev         # Dev server (Vite)
npm run build       # Production build
npm test            # Run tests (Vitest)
npm run lint        # ESLint
npm run lint:fix    # ESLint with autofix
npm run type-check  # TypeScript check
npm run format      # Prettier format
```

### Docker
```bash
docker-compose up -d                 # Start all services (dev)
docker-compose logs -f api           # Follow API logs
docker-compose exec api bash         # Shell into API container

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Architecture Notes

- API is versioned under `/v1/` prefix
- All backend route handlers use `async def`
- Database operations use SQLAlchemy async sessions
- Frontend uses React Query for server state, Zustand for client state
- WebSocket for real-time monitoring updates
- Health endpoints: `/health`, `/ready`

## Key Conventions

- **Python:** PEP 8, type hints required, async/await for I/O
- **TypeScript:** Functional components with hooks, arrow functions preferred
- **Commits:** `<type>(<scope>): <subject>` (types: feat, fix, docs, refactor, test, chore)
- **API Security:** JWT tokens, CORS configured, rate limiting via Redis
- **DB Changes:** Always use Alembic migrations, never modify schema directly

## API Endpoints (partial)

- `POST /v1/auth/login` - Authentication
- `GET /v1/services` - List monitored services
- `POST /v1/services/{id}/check` - Trigger manual check
- `GET /v1/docker/containers` - List Docker containers
- `GET /v1/users` - User management (Admin only)
- `GET /v1/audit` - Audit logs (Admin only)

Full API docs available at `http://localhost:8000/docs`
