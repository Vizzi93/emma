# eMMA auf GitHub einrichten

## Schritt 1: Dateien herunterladen

Lade das komplette Projekt hier herunter:
→ [Download Link in Claude]

Entpacke die Dateien in einen Ordner, z.B. `~/Projects/emma/`

---

## Schritt 2: GitHub Repo erstellen

1. Gehe zu: https://github.com/new
2. Repository Name: `emma`
3. Description: `Enterprise Monitoring & Management Application`
4. Visibility: Private (oder Public)
5. ❌ KEIN README, .gitignore oder License hinzufügen (haben wir schon)
6. Klicke "Create repository"

---

## Schritt 3: Lokales Git initialisieren

Öffne ein Terminal im entpackten Ordner:

```bash
# In den Projekt-Ordner wechseln
cd ~/Projects/emma

# Git initialisieren
git init

# Alle Dateien hinzufügen
git add .

# Ersten Commit erstellen
git commit -m "feat: eMMA v1.0.0 - Initial Release

🔐 Authentication (JWT, RBAC)
📊 Service Monitoring (HTTP, TCP, SSL, DNS, Ping)
🐳 Docker Container Management
👥 User Management (Admin Panel)
📝 Audit Logging
📈 Dashboard with Charts
🔄 WebSocket Real-Time Updates
🚀 CI/CD Pipeline"
```

---

## Schritt 4: Mit GitHub verbinden

```bash
# Remote hinzufügen (ersetze USERNAME mit deinem GitHub-Namen)
git remote add origin https://github.com/USERNAME/emma.git

# Oder mit SSH:
git remote add origin git@github.com:USERNAME/emma.git

# Main Branch setzen und pushen
git branch -M main
git push -u origin main
```

---

## Schritt 5: Release Tag erstellen

```bash
# Tag erstellen
git tag -a v1.0.0 -m "Release v1.0.0 - Initial Release"

# Tag pushen
git push origin v1.0.0
```

---

## Schritt 6: GitHub Release erstellen (Optional)

1. Gehe zu: https://github.com/USERNAME/emma/releases/new
2. Choose tag: `v1.0.0`
3. Release title: `eMMA v1.0.0`
4. Kopiere Inhalt aus CHANGELOG.md
5. Klicke "Publish release"

---

## Fertig! 🎉

Dein Repo ist jetzt auf GitHub unter:
`https://github.com/USERNAME/emma`

---

## Zusammenfassung der Befehle

```bash
cd ~/Projects/emma
git init
git add .
git commit -m "feat: eMMA v1.0.0 - Initial Release"
git remote add origin https://github.com/USERNAME/emma.git
git branch -M main
git push -u origin main
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```
