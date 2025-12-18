---
name: emma-development
description: Use this skill when working on the eMMA (Enterprise Monitoring & Management Application) project. Provides project context, coding standards, architecture knowledge, and best practices for FastAPI backend and React frontend development.
---

# eMMA Development Skill

## Project Overview

eMMA is an enterprise IT infrastructure monitoring solution with:
- **Backend:** FastAPI (Python 3.11+), PostgreSQL, SQLAlchemy async, Alembic, JWT auth
- **Frontend:** React 18, TypeScript, Vite, TailwindCSS, Zustand, React Query
- **Real-time:** WebSocket for live updates
- **Infrastructure:** Docker Compose, GitHub Actions CI/CD

## Project Structure

```
emma-improvements/
├── server/              # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/routers/  # API endpoints
│   │   ├── core/            # Config, Auth, Middleware
│   │   ├── models/          # SQLAlchemy Models
│   │   ├── schemas/         # Pydantic Schemas
│   │   └── services/        # Business Logic
│   └── alembic/             # DB Migrations
├── client/              # React Frontend
│   ├── src/
│   │   ├── components/      # UI Components
│   │   ├── pages/           # Page Components
│   │   ├── hooks/           # Custom Hooks (React Query)
│   │   ├── stores/          # Zustand Stores
│   │   └── types/           # TypeScript Types
└── docker-compose.yml
```

## Coding Standards

### Python (Backend)

```python
# Always use type hints
async def get_service(service_id: int, db: AsyncSession) -> Service:
    ...

# Use Pydantic for validation
class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl

# Proper error handling
try:
    result = await operation()
except SpecificError as e:
    logger.error("operation_failed", error=str(e), exc_info=True)
    raise HTTPException(status_code=500, detail="Operation failed")

# Async/await for all I/O
async def check_health(url: str) -> HealthResult:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        return HealthResult(status=response.status_code)
```

### TypeScript (Frontend)

```typescript
// Functional components with hooks
const ServiceCard: React.FC<ServiceCardProps> = ({ service }) => {
  const { data, isLoading, error } = useService(service.id);

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorDisplay error={error} />;

  return <Card>{data.name}</Card>;
};

// Custom hooks for API calls
export function useServices() {
  return useQuery({
    queryKey: ['services'],
    queryFn: () => api.get('/v1/services').then(r => r.data),
    refetchInterval: 30000,
  });
}

// Zustand for client state
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      login: async (credentials) => { ... },
      logout: () => set({ user: null }),
    }),
    { name: 'emma-auth' }
  )
);
```

## Key Patterns

### API Endpoints
- All routes under `/v1/` prefix
- JWT Bearer token authentication
- Role-based access: Admin, Operator, Viewer
- Pydantic schemas for request/response validation

### Database
- SQLAlchemy async sessions
- Alembic for migrations: `alembic revision --autogenerate -m "description"`
- Always use transactions via context manager

### WebSocket
- Real-time service status updates
- Channel-based subscriptions
- Keepalive pings every 30 seconds

### Error Handling
- Backend: HTTPException with proper status codes
- Frontend: React Query error states + toast notifications
- Always log errors with context

## Commands

```bash
# Backend
cd server
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
pytest tests/ -v --cov=app

# Frontend
cd client
npm install
npm run dev
npm test
npm run build

# Docker
docker-compose up -d
docker-compose logs -f api
```

## Security Checklist

- [ ] JWT tokens with expiry (30 min access, 7 day refresh)
- [ ] Password hashing with bcrypt (12 rounds)
- [ ] CORS properly configured
- [ ] Rate limiting on auth endpoints
- [ ] Input validation via Pydantic
- [ ] No secrets in code (use .env)
- [ ] SQL injection prevention (SQLAlchemy ORM)

## When Making Changes

1. **New API Endpoint:** Create route in `routers/`, schema in `schemas/`, service logic in `services/`
2. **New Component:** Add to `components/`, create hook in `hooks/` if API needed
3. **DB Schema Change:** Create Alembic migration, update model and schema
4. **New Feature:** Update both backend API and frontend, add tests
