---
name: emma-deployment
description: eMMA deployment with Docker, docker-compose, and CI/CD. Use when working on deployment or infrastructure.
globs:
  - "docker-compose*.yml"
  - "Dockerfile"
  - "**/Dockerfile"
  - ".github/workflows/**"
  - "nginx/**"
---

# eMMA Deployment & Infrastructure

Docker-based deployment with GitHub Actions CI/CD.

## Docker Compose

### Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Rebuild single service
docker-compose up -d --build api

# Stop all
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Production
```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| client | 3000 | React Frontend |
| api | 8000 | FastAPI Backend |
| postgres | 5432 | PostgreSQL Database |
| redis | 6379 | Cache & Rate Limiting |
| migrations | - | One-shot DB migrations |

## Dockerfile Best Practices

### Backend (Multi-stage)
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/ready || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend (Multi-stage)
```dockerfile
# Build stage
FROM node:20-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Runtime stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:3000 || exit 1
```

## GitHub Actions CI/CD

### CI Workflow
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: |
          cd server
          uv pip install --system -e ".[dev]"

      - name: Run tests
        run: |
          cd server
          pytest tests/ --cov=app --cov-report=xml

      - name: Lint
        run: |
          cd server
          ruff check .

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: client/package-lock.json

      - name: Install dependencies
        run: |
          cd client
          npm ci

      - name: Lint
        run: |
          cd client
          npm run lint

      - name: Type check
        run: |
          cd client
          npm run type-check

      - name: Test
        run: |
          cd client
          npm run test:ci
```

### CD Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push Docker images
        run: |
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/emma
            git pull
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Environment Variables

### Required
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/emma
DB_PASSWORD=secure_password

# Security
SECRET_KEY=your-32-char-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Optional
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Health Checks

### Backend
- `/health` - Basic health check
- `/ready` - Readiness check (DB connection)

### Docker Compose Health Check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/ready"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Database Migrations

### Run migrations
```bash
# Via docker-compose (uses migrations service)
docker-compose up migrations

# Manual
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"
```

## Troubleshooting

### Container won't start
```bash
docker-compose logs api
docker-compose ps
```

### Database connection issues
```bash
docker-compose exec postgres psql -U emma -d emma
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d
```
