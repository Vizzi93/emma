# eMMA Quickstart Guide

Schnellstart in 5 Minuten.

---

## Voraussetzungen

- Docker & Docker Compose installiert
- Git installiert
- Port 5173 und 8000 frei

---

## Installation

```bash
# 1. Repository klonen
git clone https://github.com/dojaflow/emma.git
cd emma

# 2. Konfiguration erstellen
cp .env.example .env

# 3. Starten
docker compose up -d

# 4. Status prüfen
docker compose ps
```

---

## Zugriff

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## Erster Login

1. Öffne http://localhost:5173/register
2. Erstelle einen Account
3. Der erste User wird automatisch Admin

---

## Ersten Service hinzufügen

1. Login → Services → "Service hinzufügen"
2. Beispiel:
   - **Name:** Google
   - **Typ:** HTTPS
   - **Target:** https://google.com
   - **Interval:** 60
3. Speichern

---

## Nützliche Befehle

```bash
# Logs ansehen
docker compose logs -f

# Stoppen
docker compose down

# Neu starten
docker compose restart

# Alles löschen (inkl. Daten!)
docker compose down -v
```

---

## Nächste Schritte

1. 📖 [Vollständige Installationsanleitung](./INSTALLATION.md)
2. 🔒 SSL-Zertifikat einrichten
3. 🖥️ Weitere Services hinzufügen
4. 👥 Team-Mitglieder einladen

---

## Hilfe

- GitHub Issues: https://github.com/dojaflow/emma/issues
- Dokumentation: https://docs.dojaflow.ai/emma
