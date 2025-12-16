# eMMA - Enterprise Monitoring & Management Application

## 🎯 Projektübersicht

**eMMA** ist eine umfassende IT-Infrastruktur-Monitoring-Lösung für Unternehmensumgebungen.

### Kernziele
- Zentrale Überwachung von Servern, Diensten und Docker-Containern
- Echtzeit-Monitoring mit automatischen Alarmierungen
- Sichere Multi-User-Umgebung mit rollenbasierter Zugriffskontrolle
- Skalierbare und wartbare Architektur
- Automatisierte Agent-Provisionierung

### Projektstatus
- **Phase**: Produktiv-ready mit CI/CD Pipeline
- **Version**: 1.x (siehe Backend API für aktuelle Version)
- **Deployment**: Docker-basiert mit GitHub Actions Automation

---

## 🏗️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Datenbank**: PostgreSQL mit SQLAlchemy ORM
- **Migration**: Alembic
- **Authentication**: JWT (JSON Web Tokens)
- **Real-time**: WebSocket-Verbindungen
- **API-Dokumentation**: Automatisch via FastAPI (Swagger/OpenAPI)

### Frontend
- **Framework**: React mit modernen Hooks
- **State Management**: React Context / Hooks
- **HTTP Client**: Fetch API / Axios
- **Real-time**: WebSocket Client
- **Styling**: [CSS Framework ermitteln wenn nötig]

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring Agents**: Python-basierte Agents auf Zielservern
- **Protokolle**: HTTP/HTTPS, TCP, ICMP, SQL (Multi-Protocol Support)

---

## 🏛️ Architektur

### Komponenten-Übersicht

```
┌─────────────────┐
│  React Frontend │ ◄─── WebSocket + REST API
└────────┬────────┘
         │
┌────────▼────────────────────────────┐
│      FastAPI Backend                │
│  - JWT Auth & RBAC                  │
│  - Service Health Checks            │
│  - Agent Management                 │
│  - Audit Logging                    │
│  - Real-time WebSocket Updates      │
└────────┬────────────────────────────┘
         │
┌────────▼────────┐      ┌──────────────────┐
│   PostgreSQL    │      │  Monitoring      │
│   Database      │      │  Agents          │
│                 │      │  (Remote Servers)│
└─────────────────┘      └──────────────────┘
```

### Datenfluss
1. **Monitoring Agents** sammeln Daten und senden sie via REST API an Backend
2. **Backend** speichert Daten in PostgreSQL und verarbeitet Health Checks
3. **WebSocket** sendet Echtzeit-Updates an verbundene Clients
4. **Frontend** visualisiert Daten und ermöglicht Management-Operationen

---

## 📁 Projektstruktur

```
emma-project/
├── backend/
│   ├── app/
│   │   ├── api/              # API Endpoints
│   │   │   ├── auth.py       # Authentication
│   │   │   ├── agents.py     # Agent Management
│   │   │   ├── services.py   # Service Monitoring
│   │   │   └── users.py      # User Management
│   │   ├── core/             # Core Funktionalität
│   │   │   ├── config.py     # Konfiguration
│   │   │   ├── security.py   # JWT & Password Handling
│   │   │   └── database.py   # DB Connection
│   │   ├── models/           # SQLAlchemy Models
│   │   ├── schemas/          # Pydantic Schemas
│   │   ├── services/         # Business Logic
│   │   └── utils/            # Utilities
│   ├── alembic/              # DB Migrations
│   ├── tests/                # Unit & Integration Tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React Components
│   │   ├── contexts/         # Context Providers
│   │   ├── hooks/            # Custom Hooks
│   │   ├── services/         # API Services
│   │   ├── utils/            # Utilities
│   │   └── App.jsx
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── agents/                   # Monitoring Agent Code
│   ├── agent.py
│   ├── config.py
│   └── requirements.txt
├── docker-compose.yml
├── .github/
│   └── workflows/            # CI/CD Pipelines
└── docs/                     # Dokumentation
```

---

## 💻 Coding Standards

### Python (Backend & Agents)

#### Code Style
- **PEP 8** konform
- **Type Hints** für alle Funktionen
- **Docstrings** für öffentliche Funktionen und Klassen
- **Max Line Length**: 100 Zeichen

#### Namenskonventionen
```python
# Klassen: PascalCase
class ServiceMonitor:
    pass

# Funktionen/Variablen: snake_case
def check_service_health():
    user_count = 0

# Konstanten: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# Private: _leading_underscore
def _internal_helper():
    pass
```

#### Async/Await
- Konsequente Nutzung von `async`/`await` für I/O-Operationen
- FastAPI Route Handler sind `async def`
- Database Operations via SQLAlchemy async session

#### Error Handling
```python
# Spezifische Exceptions verwenden
from fastapi import HTTPException

# Immer aussagekräftige Fehlermeldungen
raise HTTPException(
    status_code=404,
    detail="Agent not found"
)

# Logging bei Fehlern
import logging
logger = logging.getLogger(__name__)

try:
    result = await operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

### JavaScript/React (Frontend)

#### Code Style
- **ESLint** Rules befolgen
- **Functional Components** mit Hooks (keine Class Components)
- **Destructuring** wo sinnvoll
- **Arrow Functions** bevorzugen

#### Namenskonventionen
```javascript
// Komponenten: PascalCase
const ServiceDashboard = () => { }

// Funktionen/Variablen: camelCase
const fetchServiceData = async () => { }

// Konstanten: UPPER_SNAKE_CASE
const API_BASE_URL = "http://..."

// Custom Hooks: use-Prefix
const useWebSocket = () => { }
```

#### Component Structure
```javascript
// 1. Imports
import React, { useState, useEffect } from 'react';

// 2. Component Definition
const MyComponent = ({ prop1, prop2 }) => {
  // 3. Hooks
  const [state, setState] = useState(null);
  
  // 4. Effects
  useEffect(() => {
    // ...
  }, []);
  
  // 5. Event Handlers
  const handleClick = () => {
    // ...
  };
  
  // 6. Render
  return (
    <div>
      {/* JSX */}
    </div>
  );
};

// 7. Export
export default MyComponent;
```

### SQL/Database

#### Migrations (Alembic)
- **Immer** Migrations für Schema-Änderungen verwenden
- Aussagekräftige Revision Messages
- Up- und Down-Migrations testen

#### Models
```python
# SQLAlchemy Models mit Type Hints
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

## 🔒 Sicherheit & Best Practices

### Authentication & Authorization
- **JWT Tokens** mit angemessener Ablaufzeit (z.B. 30 Minuten)
- **Refresh Tokens** für längere Sessions
- **RBAC**: Rolle-basierte Zugriffskontrolle
  - `admin`: Vollzugriff
  - `operator`: Monitoring & Agent-Management
  - `viewer`: Nur Lesezugriff
- **Password Hashing**: bcrypt mit Salt

### API Security
- **HTTPS** in Produktion (SSL/TLS)
- **CORS** korrekt konfigurieren
- **Rate Limiting** für kritische Endpoints
- **Input Validation** via Pydantic Schemas
- **SQL Injection Prevention** via ORM (SQLAlchemy)

### Secrets Management
- **Niemals** Secrets in Code committen
- **Environment Variables** für sensible Daten
- **.env Files** für lokale Entwicklung (in .gitignore)
- **Docker Secrets** oder externe Secret Manager in Produktion

```python
# Gut
database_url = os.getenv("DATABASE_URL")

# Schlecht
database_url = "postgresql://user:password@localhost/db"
```

### Logging & Audit
- **Strukturiertes Logging** mit Log Levels
- **Audit Logs** für kritische Operationen (User-Änderungen, Löschungen)
- **Keine sensiblen Daten** in Logs (Passwords, Tokens)
- **Correlation IDs** für Request Tracing

---

## 🔄 Development Workflow

### Git Branching Strategy

```
main (protected)
  ├── develop
  │     ├── feature/monitoring-alerts
  │     ├── feature/docker-integration
  │     └── bugfix/websocket-reconnect
  └── hotfix/critical-bug
```

- **main**: Produktiver, stabiler Code
- **develop**: Integration Branch für Features
- **feature/***: Neue Features (von develop branchen)
- **bugfix/***: Bug Fixes (von develop branchen)
- **hotfix/***: Kritische Fixes (von main branchen, in main & develop mergen)

### Commit Messages
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Beispiele**:
```
feat(api): add Docker container monitoring endpoint
fix(auth): resolve JWT token expiration issue
docs(readme): update installation instructions
```

### Pull Request Prozess
1. Branch von `develop` erstellen
2. Feature entwickeln mit Tests
3. PR öffnen mit klarer Beschreibung
4. Code Review durchführen
5. CI/CD Pipeline muss grün sein
6. Merge nach Review-Approval

### Testing
- **Unit Tests** für Business Logic
- **Integration Tests** für API Endpoints
- **Test Coverage** mindestens 70%
- Tests laufen automatisch in CI/CD

```bash
# Backend Tests
cd backend
pytest tests/ --cov=app

# Frontend Tests
cd frontend
npm test
```

---

## 🐳 Docker & Deployment

### Lokale Entwicklung
```bash
# Alle Services starten
docker-compose up -d

# Backend neu bauen
docker-compose up -d --build backend

# Logs verfolgen
docker-compose logs -f backend

# Services stoppen
docker-compose down
```

### Production Deployment
- **Multi-Stage Builds** für optimierte Images
- **Health Checks** in Dockerfiles
- **Environment-specific Configs** via .env Files
- **Volume Mounts** für persistente Daten (PostgreSQL)

### CI/CD Pipeline (GitHub Actions)
- **Automatische Tests** bei jedem Push/PR
- **Docker Image Build** bei Merge auf main
- **Deployment** auf Staging/Prod (automatisch oder manuell)

---

## 📊 Monitoring & Observability

### Application Monitoring
- **Health Check Endpoint**: `/health` (Backend)
- **Metrics**: Response Times, Error Rates
- **Logging**: Strukturierte Logs mit Timestamps

### Agent Monitoring
- **Heartbeat**: Agents senden regelmäßig Status-Updates
- **Service Checks**: HTTP, TCP, ICMP, SQL Health Checks
- **Alerts**: Bei Service-Ausfällen oder Agent-Disconnects

---

## 🚀 Entwicklungsprioritäten

### Aktueller Fokus
1. **CI/CD Optimierung**: GitHub Actions Pipeline stabilisieren
2. **Monitoring Erweiterungen**: Zusätzliche Service-Protokolle
3. **Performance**: WebSocket-Optimierung für viele Clients
4. **Documentation**: API-Dokumentation vervollständigen

### Backlog
- Alert-Management mit Benachrichtigungen (Email, Slack)
- Dashboard Customization (User-spezifische Dashboards)
- Historical Data Analysis & Reporting
- Mobile App für iOS/Android

### Tech Debt
- Legacy Code Refactoring in älteren Modulen
- Test Coverage auf 80%+ erhöhen
- Frontend Performance Optimierung
- Database Query Optimization

---

## 🎓 Wichtige Entscheidungen & Konventionen

### Warum FastAPI?
- Automatische API-Dokumentation
- Native async/await Support
- Type Safety via Pydantic
- Hohe Performance

### Warum WebSockets?
- Echtzeit-Updates ohne Polling
- Reduzierte Server-Last
- Bessere User Experience

### Warum JWT?
- Stateless Authentication
- Skalierbar (keine Session-Speicherung)
- Standardisiert und sicher

### Database Design Principles
- **Normalisierung**: 3. Normalform anstreben
- **Indexes**: Auf Foreign Keys und häufig abgefragten Feldern
- **Timestamps**: `created_at`, `updated_at` auf allen Tabellen
- **Soft Deletes**: `deleted_at` für kritische Daten statt Hard Deletes

---

## 📝 Wichtige Befehle & Shortcuts

### Backend
```bash
# Migration erstellen
alembic revision --autogenerate -m "beschreibung"

# Migration ausführen
alembic upgrade head

# Migration zurückrollen
alembic downgrade -1

# Development Server
uvicorn app.main:app --reload

# Tests
pytest tests/ -v
```

### Frontend
```bash
# Dependencies installieren
npm install

# Development Server
npm start

# Production Build
npm run build

# Tests
npm test

# Linting
npm run lint
```

### Docker
```bash
# Alle Services
docker-compose up -d

# Einzelner Service
docker-compose up -d backend

# Logs
docker-compose logs -f [service]

# Shell in Container
docker-compose exec backend bash

# Cleanup
docker-compose down -v
```

---

## 🆘 Troubleshooting

### Häufige Probleme

#### "Alembic kann Migration nicht finden"
```bash
# Lösung: Alembic Config prüfen
# alembic.ini - sqlalchemy.url muss korrekt sein
# Oder: Umgebungsvariable setzen
export DATABASE_URL="postgresql://..."
alembic upgrade head
```

#### "WebSocket Verbindung bricht ab"
- Nginx/Reverse Proxy Timeout erhöhen
- Keep-alive Konfiguration prüfen
- Client-seitige Reconnect-Logik implementieren

#### "JWT Token Invalid"
- Token-Format prüfen (Bearer + Token)
- Token Expiration prüfen
- Secret Key muss übereinstimmen (Backend + Token)

#### "Docker Container startet nicht"
- Logs prüfen: `docker-compose logs [service]`
- Environment Variables prüfen
- Port-Konflikte prüfen: `docker ps`

---

## 📚 Nützliche Ressourcen

### Dokumentation
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- Docker: https://docs.docker.com/

### Best Practices
- [12 Factor App](https://12factor.net/)
- [REST API Design](https://restfulapi.net/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## ✅ Code Review Checklist

### Vor jedem Commit
- [ ] Code folgt Projektstandards
- [ ] Type Hints vorhanden (Python)
- [ ] Keine hardcoded Secrets
- [ ] Tests geschrieben und bestanden
- [ ] Keine console.log() im Frontend (außer wichtige Logs)
- [ ] Error Handling implementiert
- [ ] Dokumentation aktualisiert

### Vor jedem PR
- [ ] Branch ist aktuell mit develop
- [ ] Alle Tests laufen durch
- [ ] CI/CD Pipeline ist grün
- [ ] Keine Merge-Konflikte
- [ ] PR-Beschreibung ist aussagekräftig

---

## 🎯 Zusammenfassung für Claude Code

**Was du immer beachten solltest:**

1. **Sicherheit First**: JWT, RBAC, Input Validation, keine Secrets in Code
2. **Code Quality**: Type Hints, Docstrings, Tests, Clean Code
3. **Architektur**: FastAPI Backend, React Frontend, PostgreSQL, Docker
4. **Standards**: PEP 8, ESLint, aussagekräftige Commits
5. **Testing**: Jede neue Funktion braucht Tests
6. **Documentation**: Code sollte selbsterklärend sein, komplexe Logik dokumentieren
7. **Performance**: Async/Await, DB-Indexing, WebSocket-Optimierung

**Bei Unsicherheiten:**
- Prüfe bestehenden Code für Patterns
- Folge den Best Practices in diesem Dokument
- Frage nach, wenn etwas unklar ist

**Ziel**: Wartbaren, sicheren, skalierbaren Code schreiben, der dem Team und zukünftigen Entwicklern hilft!
