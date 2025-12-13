# Changelog

Alle wichtigen Änderungen an eMMA werden hier dokumentiert.

## [1.0.0] - 2024-12-09

### 🎉 Initial Release

Erste produktionsreife Version von eMMA (Enterprise Monitoring & Management Application).

### Features

#### Authentication & Security
- JWT-basierte Authentifizierung mit Access/Refresh Token Rotation
- Passwort-Hashing mit bcrypt (12 Rounds)
- Role-Based Access Control (Admin, Operator, Viewer)
- Rate-Limiting (60 req/min API, 5 req/min Auth)
- Security Headers (HSTS, CSP, X-Frame-Options, etc.)
- Request-ID Tracing für alle Anfragen

#### Service Health Monitoring
- HTTP/HTTPS Endpoint Monitoring
- TCP Port Checks
- SSL Certificate Validation mit Ablauf-Warnung
- DNS Resolution Checks
- ICMP Ping Checks
- Automatischer Background-Scheduler
- Uptime-Berechnung (24h rolling)
- Status: Healthy → Degraded → Unhealthy

#### Docker Container Management
- Container-Liste mit Live-Status
- Ressourcen-Monitoring (CPU, Memory, Network I/O)
- Container-Actions: Start, Stop, Restart, Remove
- Log-Abruf pro Container
- Docker Daemon Info

#### User Management (Admin Panel)
- Benutzer erstellen, bearbeiten, löschen
- Rollen zuweisen (Admin/Operator/Viewer)
- Benutzer aktivieren/deaktivieren
- Passwort zurücksetzen
- Session-Management (alle Sessions beenden)

#### Audit Logging
- Automatische Protokollierung aller CRUD-Operationen
- Event-Typen: Auth, User, Service, Container, System
- Filter nach User, Aktion, Zeitraum
- Vorher/Nachher-Werte bei Updates
- 90-Tage Retention Policy

#### Real-Time Updates
- WebSocket-Verbindung für Live-Updates
- Auto-Reconnect mit exponentiellen Backoff
- Channel-basierte Subscriptions
- Toast-Notifications bei Status-Änderungen

#### Dashboard & Visualisierungen
- Service Health Donut-Chart
- Response Time Line-Chart
- Uptime Bar-Chart
- Container Resource Charts
- Activity Timeline
- System Status Banner

#### Infrastructure
- Docker Compose Setup (Dev & Prod)
- PostgreSQL mit Connection Pooling
- NGINX Reverse Proxy Konfiguration
- GitHub Actions CI/CD Pipeline
- Multi-Stage Docker Builds
- Structured JSON Logging

### Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Pydantic v2
- aiodocker

**Frontend:**
- React 18
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- Zustand
- Recharts

### Breaking Changes
- Keine (Initial Release)

### Known Issues
- Docker-Monitoring erfordert Socket-Mount
- WebSocket reconnect kann bei langen Disconnects fehlschlagen

---

## Versioning

Dieses Projekt folgt [Semantic Versioning](https://semver.org/):
- MAJOR: Inkompatible API-Änderungen
- MINOR: Neue Features (abwärtskompatibel)
- PATCH: Bugfixes (abwärtskompatibel)
