# eMMA - Enterprise Monitoring & Management Application

<p align="center">
  <img src="docs/logo.png" alt="eMMA Logo" width="200">
</p>

<p align="center">
  <strong>Ein modernes Monitoring- und Management-Dashboard für IT-Infrastruktur</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#konfiguration">Konfiguration</a> •
  <a href="#api">API</a> •
  <a href="#entwicklung">Entwicklung</a>
</p>

---

## Features

### 🔍 Service Monitoring
- HTTP/HTTPS Endpoint Checks
- TCP Port Monitoring
- SSL Certificate Validation
- DNS Resolution Checks
- ICMP Ping Checks
- Automatische Checks im Hintergrund
- Uptime-Tracking (24h)

### 🐳 Docker Management
- Container-Übersicht mit Live-Status
- CPU, Memory, Network Metriken
- Start, Stop, Restart, Remove Actions
- Container-Logs

### 👥 Benutzerverwaltung
- Role-Based Access Control
- Admin, Operator, Viewer Rollen
- Session-Management
- Audit-Logging

### 📊 Dashboard
- Echtzeit-Visualisierungen
- Service Health Charts
- Response Time Trends
- Container Resource Monitoring
- Activity Timeline

### 🔒 Security
- JWT Authentication
- Rate Limiting
- Security Headers
- Audit Trail

---

## Installation

### Voraussetzungen

- Docker & Docker Compose
- Node.js 18+ (für Entwicklung)
- Python 3.11+ (für Entwicklung)
- PostgreSQL 15+

### Quick Start

```bash
# Repository klonen
git clone https://github.com/dojaflow/emma.git
cd emma

# Setup ausführen
chmod +x setup.sh
./setup.sh dev

# Services starten
docker-compose up -d
```

### Manuelle Installation

**Backend:**
```bash
cd server
python -m venv venv
source venv/bin/activate
pip install -e ".[dev,docker]"

# Datenbank migrieren
alembic upgrade head

# Server starten
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd client
npm install
npm run dev
```

---

## Konfiguration

### Umgebungsvariablen

Erstelle eine `.env` Datei basierend auf `.env.example`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://emma:secret@localhost:5432/emma

# Security
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:5173,https://emma.dojaflow.ai

# Docker (optional)
DOCKER_URL=unix:///var/run/docker.sock

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Docker Socket

Für Docker-Monitoring muss der Socket gemountet werden:

```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
```

---

## API

### Authentifizierung

```bash
# Login
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "secret"}'

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Endpoints

| Endpoint | Beschreibung |
|----------|--------------|
| `POST /v1/auth/login` | Login |
| `POST /v1/auth/register` | Registrierung |
| `GET /v1/services` | Service-Liste |
| `POST /v1/services/{id}/check` | Manueller Check |
| `GET /v1/docker/containers` | Container-Liste |
| `GET /v1/users` | Benutzer-Liste (Admin) |
| `GET /v1/audit` | Audit-Logs (Admin) |

Vollständige API-Dokumentation: `http://localhost:8000/docs`

---

## Entwicklung

### Projektstruktur

```
emma/
├── server/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/           # API Routes
│   │   ├── core/          # Config, Auth, Middleware
│   │   ├── models/        # SQLAlchemy Models
│   │   ├── schemas/       # Pydantic Schemas
│   │   └── services/      # Business Logic
│   ├── alembic/           # DB Migrations
│   └── tests/
│
├── client/                 # React Frontend
│   ├── src/
│   │   ├── components/    # UI Components
│   │   ├── pages/         # Page Components
│   │   ├── hooks/         # React Query Hooks
│   │   ├── stores/        # Zustand Stores
│   │   └── types/         # TypeScript Types
│   └── public/
│
├── nginx/                  # Reverse Proxy Config
├── .github/workflows/      # CI/CD
└── docker-compose.yml
```

### Commands

```bash
# Backend Tests
cd server && pytest

# Frontend Tests
cd client && npm test

# Linting
cd server && ruff check .
cd client && npm run lint

# Type Checking
cd server && mypy app
cd client && npm run typecheck
```

---

## Deployment

### Production Build

```bash
# Frontend Build
cd client && npm run build

# Docker Images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### CI/CD

GitHub Actions Workflow:
- **CI**: Lint, Test, Security Scan bei jedem Push
- **CD**: Auto-Deploy zu Staging (develop) und Production (main)

---

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

---

## Support

- 📧 Email: support@dojaflow.ai
- 📖 Docs: https://docs.dojaflow.ai/emma
- 🐛 Issues: https://github.com/dojaflow/emma/issues

---

<p align="center">
  Made with ❤️ by <a href="https://dojaflow.ai">DojaFlow AI</a>
</p>
