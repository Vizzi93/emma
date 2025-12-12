# eMMA Installation Guide

Diese Anleitung führt dich Schritt für Schritt durch die Installation von eMMA auf deinem Server.

---

## Inhaltsverzeichnis

1. [Systemvoraussetzungen](#1-systemvoraussetzungen)
2. [Schnellstart mit Docker](#2-schnellstart-mit-docker)
3. [Manuelle Installation](#3-manuelle-installation)
4. [Produktions-Deployment](#4-produktions-deployment)
5. [NGINX Reverse Proxy](#5-nginx-reverse-proxy)
6. [SSL-Zertifikate](#6-ssl-zertifikate)
7. [Erster Login](#7-erster-login)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Systemvoraussetzungen

### Minimum Hardware

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| CPU | 2 Cores | 4 Cores |
| RAM | 2 GB | 4 GB |
| Disk | 20 GB | 50 GB SSD |

### Software

| Software | Version | Zweck |
|----------|---------|-------|
| Ubuntu/Debian | 22.04+ / 12+ | Betriebssystem |
| Docker | 24.0+ | Container Runtime |
| Docker Compose | 2.20+ | Container Orchestration |
| Git | 2.30+ | Versionskontrolle |

### Optionale Software (für Entwicklung)

| Software | Version |
|----------|---------|
| Node.js | 18+ |
| Python | 3.11+ |
| PostgreSQL | 15+ |

---

## 2. Schnellstart mit Docker

Die einfachste Methode für eine schnelle Installation.

### 2.1 Docker installieren

```bash
# Docker installieren (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh

# Benutzer zur Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Neu einloggen oder:
newgrp docker

# Installation prüfen
docker --version
docker compose version
```

### 2.2 Repository klonen

```bash
# Repository klonen
git clone https://github.com/dojaflow/emma.git
cd emma

# Oder als ZIP herunterladen
wget https://github.com/dojaflow/emma/archive/refs/tags/v1.0.0.zip
unzip v1.0.0.zip
cd emma-1.0.0
```

### 2.3 Konfiguration erstellen

```bash
# Beispiel-Konfiguration kopieren
cp .env.example .env

# Konfiguration bearbeiten
nano .env
```

**Wichtige Einstellungen in `.env`:**

```env
# ══════════════════════════════════════════════════════════════
# DATENBANK
# ══════════════════════════════════════════════════════════════
POSTGRES_USER=emma
POSTGRES_PASSWORD=SICHERES_PASSWORT_HIER       # ⚠️ Ändern!
POSTGRES_DB=emma
DATABASE_URL=postgresql+asyncpg://emma:SICHERES_PASSWORT_HIER@db:5432/emma

# ══════════════════════════════════════════════════════════════
# SICHERHEIT
# ══════════════════════════════════════════════════════════════
JWT_SECRET_KEY=MINDESTENS_32_ZEICHEN_LANGER_GEHEIMER_SCHLUESSEL  # ⚠️ Ändern!
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ══════════════════════════════════════════════════════════════
# CORS (erlaubte Domains)
# ══════════════════════════════════════════════════════════════
ALLOWED_ORIGINS=https://emma.deine-domain.de

# ══════════════════════════════════════════════════════════════
# ENVIRONMENT
# ══════════════════════════════════════════════════════════════
ENVIRONMENT=production
DEBUG=false
```

**JWT Secret generieren:**

```bash
# Sicheren Schlüssel generieren
openssl rand -hex 32
```

### 2.4 Starten

```bash
# Services starten
docker compose up -d

# Status prüfen
docker compose ps

# Logs ansehen
docker compose logs -f
```

### 2.5 Zugriff

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 3. Manuelle Installation

Für Entwicklung oder wenn du mehr Kontrolle brauchst.

### 3.1 System vorbereiten

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Benötigte Pakete installieren
sudo apt install -y \
  git \
  curl \
  build-essential \
  python3.11 \
  python3.11-venv \
  python3-pip \
  postgresql \
  postgresql-contrib \
  nginx
```

### 3.2 Node.js installieren

```bash
# Node.js 18 via NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Version prüfen
node --version  # v18.x.x
npm --version   # 9.x.x
```

### 3.3 PostgreSQL einrichten

```bash
# PostgreSQL starten
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Datenbank und Benutzer erstellen
sudo -u postgres psql << EOF
CREATE USER emma WITH PASSWORD 'dein_sicheres_passwort';
CREATE DATABASE emma OWNER emma;
GRANT ALL PRIVILEGES ON DATABASE emma TO emma;
EOF

# Verbindung testen
psql -h localhost -U emma -d emma -c "SELECT 1;"
```

### 3.4 Backend installieren

```bash
# In Backend-Verzeichnis wechseln
cd emma/server

# Virtual Environment erstellen
python3.11 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install --upgrade pip
pip install -e ".[dev,docker]"

# Umgebungsvariablen setzen
cp ../.env.example .env
nano .env  # Anpassen!

# Datenbank migrieren
alembic upgrade head

# Server starten (Entwicklung)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3.5 Frontend installieren

```bash
# In neuem Terminal
cd emma/client

# Dependencies installieren
npm install

# Entwicklungsserver starten
npm run dev

# Oder: Production Build
npm run build
```

### 3.6 Systemd Service (für Production)

**Backend Service erstellen:**

```bash
sudo nano /etc/systemd/system/emma-backend.service
```

```ini
[Unit]
Description=eMMA Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=emma
Group=emma
WorkingDirectory=/opt/emma/server
Environment="PATH=/opt/emma/server/venv/bin"
EnvironmentFile=/opt/emma/.env
ExecStart=/opt/emma/server/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Service aktivieren:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable emma-backend
sudo systemctl start emma-backend
sudo systemctl status emma-backend
```

---

## 4. Produktions-Deployment

### 4.1 Docker Compose Production

```bash
# Production Compose verwenden
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 4.2 Sicherheits-Checkliste

- [ ] JWT_SECRET_KEY geändert (mind. 32 Zeichen)
- [ ] Datenbank-Passwort geändert
- [ ] DEBUG=false gesetzt
- [ ] ALLOWED_ORIGINS auf deine Domain gesetzt
- [ ] Firewall konfiguriert
- [ ] SSL-Zertifikat installiert
- [ ] Backups eingerichtet

### 4.3 Firewall einrichten

```bash
# UFW installieren und konfigurieren
sudo apt install ufw

# Standard-Regeln
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH erlauben (wichtig!)
sudo ufw allow ssh

# HTTP/HTTPS erlauben
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Firewall aktivieren
sudo ufw enable
sudo ufw status
```

---

## 5. NGINX Reverse Proxy

### 5.1 NGINX installieren

```bash
sudo apt install nginx
sudo systemctl enable nginx
```

### 5.2 Konfiguration erstellen

```bash
sudo nano /etc/nginx/sites-available/emma
```

```nginx
# HTTP → HTTPS Redirect
server {
    listen 80;
    server_name emma.deine-domain.de;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name emma.deine-domain.de;

    # SSL Zertifikate (siehe Abschnitt 6)
    ssl_certificate /etc/letsencrypt/live/emma.deine-domain.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/emma.deine-domain.de/privkey.pem;

    # SSL Einstellungen
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/emma.access.log;
    error_log /var/log/nginx/emma.error.log;

    # Frontend (Static Files)
    location / {
        root /opt/emma/client/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache für Assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket
    location /v1/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Health Check
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 5.3 Konfiguration aktivieren

```bash
# Symlink erstellen
sudo ln -s /etc/nginx/sites-available/emma /etc/nginx/sites-enabled/

# Default-Config entfernen
sudo rm /etc/nginx/sites-enabled/default

# Konfiguration testen
sudo nginx -t

# NGINX neu laden
sudo systemctl reload nginx
```

---

## 6. SSL-Zertifikate

### 6.1 Let's Encrypt mit Certbot

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx

# Zertifikat anfordern
sudo certbot --nginx -d emma.deine-domain.de

# Auto-Renewal testen
sudo certbot renew --dry-run
```

### 6.2 Manuelles Zertifikat

Falls du ein eigenes Zertifikat hast:

```bash
# Zertifikate kopieren
sudo mkdir -p /etc/ssl/emma
sudo cp dein-zertifikat.crt /etc/ssl/emma/emma.crt
sudo cp dein-private-key.key /etc/ssl/emma/emma.key

# Berechtigungen setzen
sudo chmod 600 /etc/ssl/emma/emma.key
```

---

## 7. Erster Login

### 7.1 Admin-Benutzer erstellen

Nach der Installation musst du den ersten Admin-Benutzer erstellen:

**Option A: Über die Registrierung**

1. Öffne https://emma.deine-domain.de/register
2. Registriere dich mit E-Mail und Passwort
3. Der erste Benutzer wird automatisch Admin

**Option B: Über die Kommandozeile**

```bash
# In den Container/Server verbinden
docker compose exec backend bash
# oder: cd /opt/emma/server && source venv/bin/activate

# Python Shell starten
python << 'EOF'
import asyncio
from app.db.session import async_session_maker
from app.models.user import User, UserRole
from app.core.auth import password_hasher

async def create_admin():
    async with async_session_maker() as session:
        admin = User(
            email="admin@deine-domain.de",
            password_hash=password_hasher.hash("DeinSicheresPasswort123!"),
            full_name="Administrator",
            role=UserRole.ADMIN.value,
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Admin erstellt: {admin.email}")

asyncio.run(create_admin())
EOF
```

### 7.2 Erste Services einrichten

1. Login unter https://emma.deine-domain.de/login
2. Navigiere zu "Services"
3. Klicke "Service hinzufügen"
4. Füge deinen ersten Service hinzu:
   - Name: `Google DNS`
   - Typ: `HTTPS`
   - Target: `https://dns.google`
   - Interval: `60` Sekunden

---

## 8. Troubleshooting

### Container starten nicht

```bash
# Logs prüfen
docker compose logs backend
docker compose logs db

# Container neu erstellen
docker compose down
docker compose up -d --build
```

### Datenbank-Verbindung fehlgeschlagen

```bash
# PostgreSQL Status prüfen
docker compose exec db pg_isready

# Verbindung testen
docker compose exec backend python -c "
from app.db.session import engine
import asyncio
async def test():
    async with engine.connect() as conn:
        print('DB OK')
asyncio.run(test())
"
```

### WebSocket verbindet nicht

```bash
# NGINX WebSocket-Config prüfen
sudo nginx -t

# Backend WebSocket testen
wscat -c "ws://localhost:8000/v1/ws?token=DEIN_TOKEN"
```

### Permission Denied (Docker Socket)

```bash
# Berechtigungen für Docker Socket
sudo chmod 666 /var/run/docker.sock

# Oder: Benutzer zur Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER
```

### Logs einsehen

```bash
# Docker Logs
docker compose logs -f --tail=100

# Systemd Logs
sudo journalctl -u emma-backend -f

# NGINX Logs
sudo tail -f /var/log/nginx/emma.error.log
```

### Datenbank zurücksetzen

```bash
# ⚠️ ACHTUNG: Löscht alle Daten!
docker compose down -v
docker compose up -d
```

---

## Support

Bei Problemen:

1. Prüfe die [GitHub Issues](https://github.com/dojaflow/emma/issues)
2. Erstelle ein neues Issue mit:
   - Fehlermeldung
   - Logs
   - Systeminfo (`docker info`, `uname -a`)

---

## Nächste Schritte

Nach erfolgreicher Installation:

1. ✅ Ersten Admin-Benutzer erstellen
2. ✅ SSL-Zertifikat einrichten
3. ✅ Services zum Monitoring hinzufügen
4. ✅ Weitere Benutzer anlegen
5. ✅ Backups einrichten
6. ✅ Monitoring für eMMA selbst einrichten

---

*Letzte Aktualisierung: Dezember 2024 | eMMA v1.0.0*
