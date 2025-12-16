# Empfohlene Claude Skills für eMMA-Projekt

## 🎯 Übersicht

Diese Skills wurden speziell für dein eMMA-Projekt ausgewählt und unterstützen dich bei Backend-Entwicklung, Testing, Git-Workflows und Code-Qualität.

---

## ⭐ Top-Priorität Skills (Sofort installieren)

### 1. **automating-api-testing**
**Quelle**: jeremylongshore auf SkillsMP  
**Link**: https://skillsmp.com/skills/jeremylongshore-claude-code-plugins-plus-backups-plugin-enhancements-plugin-backups-api-test-automation-20251019-150625-skills-skill-adapter-skill-md

**Was es kann**:
- Automatische Generierung von API-Tests für REST Endpoints
- Test-Abdeckung für CRUD-Operationen
- Authentication Flow Tests (JWT, Login, Refresh)
- Validierung gegen OpenAPI/Swagger Specs
- Error Handling Tests

**Perfekt für eMMA weil**:
- eMMA hat viele FastAPI REST Endpoints
- JWT Authentication muss getestet werden
- Service Health Checks brauchen Tests
- Agent Management APIs benötigen umfassende Tests

**Installation**:
```bash
# Als Project Skill (empfohlen für Teams)
mkdir -p .claude/skills/automating-api-testing
cd .claude/skills/automating-api-testing
# Skill von GitHub klonen und SKILL.md kopieren
```

**Beispiel-Nutzung**:
```
"Generate API tests for the agent management endpoints in backend/app/api/agents.py"
```

---

### 2. **commit-message-generator**
**Quelle**: kanopi auf SkillsMP  
**Link**: https://skillsmp.com/skills/kanopi-cms-cultivator-skills-commit-message-generator-skill-md

**Was es kann**:
- Automatische Generierung von Conventional Commit Messages
- Analysiert git diff und staged changes
- Folgt dem Conventional Commits Standard
- Erkennt Breaking Changes
- Integriert Ticket-Nummern aus Branch-Namen

**Perfekt für eMMA weil**:
- Konsistente Commit-Historie für das Team
- Automatisiert Best Practices
- Spart Zeit beim Committen
- Passt zu eurem Git-Workflow (Feature Branches)

**Beispiel Output**:
```
feat(auth): add JWT refresh token endpoint

- Implement refresh token rotation
- Add rate limiting for auth endpoints
- Update security middleware
```

**Beispiel-Nutzung**:
```
"I fixed the websocket reconnection issue, ready to commit"
```

---

### 3. **webapp-testing**
**Quelle**: Anthropic Official auf SkillsMP  
**Link**: https://skillsmp.com/skills/anthropics-skills-webapp-testing-skill-md  
**Status**: ⭐ Official Anthropic Skill (15k+ GitHub Stars)

**Was es kann**:
- Vollständige Web Application Testing
- Frontend & Backend Integration Tests
- Browser-Testing Support
- Performance Testing
- Error Handling Patterns

**Perfekt für eMMA weil**:
- eMMA hat React Frontend + FastAPI Backend
- WebSocket-Verbindungen müssen getestet werden
- Integration zwischen Frontend und Backend ist kritisch
- Real-time Updates erfordern End-to-End Tests

---

## 🔧 Wichtige Entwicklungs-Skills

### 4. **uv (Python Package Manager)**
**Quelle**: rghamilton3 auf SkillsMP  
**Link**: https://skillsmp.com/skills/rghamilton3-dotfiles-dot-claude-skills-uv-skill-md

**Was es kann**:
- Extrem schnelles Python Dependency Management (in Rust geschrieben)
- Virtual Environment Management
- Lock-File Generation
- CI/CD Optimierung
- PyPI Alternative

**Perfekt für eMMA weil**:
- Schnellere Dependency Installation (wichtig für Docker Builds)
- Besseres Dependency Management als pip
- Moderne Alternative zu Poetry/Pipenv
- CI/CD Pipeline Optimierung

**Beispiel-Nutzung**:
```
"Set up uv for our FastAPI backend with all dependencies"
```

---

### 5. **skill-creator**
**Quelle**: Anthropic Official  
**Link**: Bereits in Claude integriert

**Was es kann**:
- Interaktive Erstellung von Custom Skills
- Guided Workflow für SKILL.md Files
- Best Practices Templates
- Automatische Struktur-Generierung

**Perfekt für eMMA weil**:
- Du kannst eMMA-spezifische Skills erstellen
- Z.B. "eMMA-Deployment-Skill" für CI/CD
- "eMMA-Monitoring-Alert-Skill" für neue Features
- Custom Workflows für dein Team

**Beispiel-Nutzung**:
```
"Help me create a skill for eMMA database migrations"
```

---

## 🛡️ Sicherheit & Code-Qualität

### 6. **error-handling-patterns**
**Quelle**: Anthropic Official auf SkillsMP  
**Link**: Siehe webapp-testing Skill Collection

**Was es kann**:
- Error Handling Best Practices
- Exception Patterns über verschiedene Sprachen
- Graceful Degradation
- Resilient Application Design

**Perfekt für eMMA weil**:
- FastAPI Error Handling muss robust sein
- WebSocket Disconnects brauchen Graceful Handling
- Agent Communication Errors müssen behandelt werden
- Monitoring Service Failures

---

## 🐳 DevOps & Deployment

### 7. **Docker & CI/CD Skills**
**Empfehlung**: Custom Skill erstellen mit skill-creator

**Was es enthalten sollte**:
- Docker Compose Best Practices
- Multi-Stage Build Optimierung
- GitHub Actions Workflows
- Health Check Konfiguration
- Environment Variable Management

**Warum Custom Skill**:
- eMMA hat spezifische Docker-Struktur
- Custom CI/CD Pipeline (GitHub Actions)
- Deployment-Prozess ist projektspezifisch
- Team-spezifische Konventionen

**Vorschlag**: 
```
"Use skill-creator to create an 'emma-deployment' skill that handles:
- Docker builds with caching
- GitHub Actions CI/CD
- Alembic migrations in deployment
- Health check verification"
```

---

## 📊 Datenbank Management

### 8. **SQLAlchemy & Alembic Skills**
**Empfehlung**: Custom Skill oder suche nach "alembic migration" Skills

**Was es enthalten sollte**:
- Alembic Migration Best Practices
- SQLAlchemy Model Patterns
- Database Index Optimization
- Migration Rollback Strategien

**Perfekt für eMMA weil**:
- PostgreSQL mit Alembic Migrations
- Häufige Schema-Änderungen
- Production Database Safety
- Team muss Migration-Konventionen folgen

---

## 🔄 Git & Workflow Management

### 9. **beads-issue-tracking**
**Quelle**: shaneholloman auf SkillsMP  
**Link**: https://skillsmp.com/skills/shaneholloman-beads-examples-claude-code-skill-skill-md

**Was es kann**:
- Graph-basiertes Issue Tracking
- Multi-Session Work Management
- Dependency Graphs
- Context Persistence über Sessions hinweg

**Perfekt für eMMA weil**:
- Komplexe Features mit Dependencies (z.B. Alert-System)
- Multi-Session Development
- Team-Koordination
- Feature Planning

**Beispiel-Nutzung**:
```bash
beads create "Implement Alert System" -p 0 -t feature
beads create "Add Email Notifications" --depends issue-123
```

---

## 🚀 Installation & Setup

### Projekt-weite Installation (Empfohlen für eMMA)

```bash
# Im eMMA Root Directory
mkdir -p .claude/skills

# Skills klonen und installieren
cd .claude/skills

# Beispiel: automating-api-testing installieren
git clone [REPOSITORY_URL] automating-api-testing
# Nur SKILL.md und zugehörige Dateien behalten

# In Git committen, damit das ganze Team Zugriff hat
git add .claude/skills
git commit -m "feat(dev): add Claude Code skills for API testing and development"
```

### Persönliche Installation

```bash
# Nur für dich (nicht im Projekt-Repo)
mkdir -p ~/.claude/skills
cd ~/.claude/skills

# Skills hier installieren
```

---

## 📝 Nutzungs-Tipps

### 1. Skills werden automatisch aktiviert
- Claude erkennt automatisch, wann ein Skill relevant ist
- Keine manuelle Aktivierung nötig
- Basiert auf der `description` im SKILL.md

### 2. Multiple Skills gleichzeitig
- Skills können kombiniert werden
- Z.B.: commit-message-generator + automating-api-testing
- Claude wählt intelligente Kombinationen

### 3. Eigene Skills erstellen
```
"Use skill-creator to help me build a custom skill for eMMA's specific deployment workflow"
```

### 4. Skills testen
```
# Nach Installation testen
"Generate API tests for our authentication endpoints"
# Wenn Skill funktioniert, wird er automatisch verwendet
```

---

## 🎯 Empfohlene Reihenfolge für Installation

**Phase 1 - Essentials (Sofort)**:
1. ✅ automating-api-testing
2. ✅ commit-message-generator
3. ✅ webapp-testing

**Phase 2 - Development Quality (Diese Woche)**:
4. ✅ uv (Python Package Manager)
5. ✅ error-handling-patterns
6. ✅ skill-creator (für Custom Skills)

**Phase 3 - Advanced Workflows (Nächste Woche)**:
7. ✅ beads-issue-tracking
8. ✅ Custom eMMA Deployment Skill
9. ✅ Custom Database Migration Skill

---

## 🔍 Weitere Skill-Suche

### SkillsMP Kategorien für eMMA:
- **API & Backend**: https://skillsmp.com/categories/api-backend
- **Testing & Security**: https://skillsmp.com/categories/testing-security
- **Development**: https://skillsmp.com/categories/development

### Anthropic Official Skills:
- GitHub: https://github.com/anthropics/skills
- Dokumentation: https://code.claude.com/docs/en/skills

---

## ⚠️ Wichtige Hinweise

### Sicherheit bei Community Skills:
- ⚠️ Immer Code Review vor Installation
- ⚠️ Prüfe GitHub Repository (Stars, Updates, Issues)
- ⚠️ Official Anthropic Skills bevorzugen
- ⚠️ Keine Secrets in Skill-Dateien

### Best Practices:
- Skills im `.claude/skills/` Ordner committen (Team-Zugriff)
- Klare Naming Convention: `skill-name/SKILL.md`
- Regelmäßig Updates von GitHub ziehen
- Team über neue Skills informieren

### Troubleshooting:
```bash
# Skill wird nicht erkannt?
# 1. Prüfe YAML Frontmatter in SKILL.md
cat .claude/skills/skill-name/SKILL.md

# 2. Prüfe description (muss klar sein, wann Skill verwendet wird)

# 3. Teste mit direkter Erwähnung
"Use the automating-api-testing skill to generate tests for..."
```

---

## 🎉 Quick Start Beispiel

```bash
# 1. Skills Ordner erstellen
cd ~/path/to/emma-project
mkdir -p .claude/skills

# 2. EMMA_PROJECT_CONTEXT.md bereitstellen (bereits erstellt)
# Claude liest diese automatisch

# 3. Ersten Skill installieren (Beispiel: commit-message-generator)
cd .claude/skills
# Hier Skill Files ablegen

# 4. Claude Code starten
# Skills werden automatisch geladen

# 5. Testen
# "I've made changes to the auth module, help me commit them"
# Skill wird automatisch verwendet!
```

---

## 💡 Nächste Schritte

1. **Jetzt**: Installiere die Top 3 Priority Skills
2. **Diese Woche**: Teste Skills im Development Workflow
3. **Nächste Woche**: Erstelle Custom eMMA-Deployment Skill
4. **Fortlaufend**: Erweitere Skill Collection basierend auf Team-Bedarf

**Fragen zur Installation oder Anpassung?** Lass mich wissen, welche Skills du zuerst brauchst!
