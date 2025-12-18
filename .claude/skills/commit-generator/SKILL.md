---
name: commit-generator
description: Use this skill when the user wants to commit changes. Analyzes git diff and generates Conventional Commits format messages. Supports both English and German commit messages.
---

# Commit Message Generator Skill

## Overview

This skill generates well-structured commit messages following the Conventional Commits specification based on analyzing staged changes.

## Conventional Commits Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): add JWT refresh token endpoint` |
| `fix` | Bug fix | `fix(websocket): resolve reconnection race condition` |
| `docs` | Documentation | `docs(readme): update installation instructions` |
| `style` | Formatting, no code change | `style(api): fix indentation in routers` |
| `refactor` | Code restructuring | `refactor(services): extract health check logic` |
| `perf` | Performance improvement | `perf(db): add index on service status column` |
| `test` | Adding/updating tests | `test(auth): add login validation tests` |
| `chore` | Maintenance tasks | `chore(deps): update fastapi to 0.110.0` |
| `build` | Build system changes | `build(docker): optimize multi-stage build` |
| `ci` | CI/CD changes | `ci(github): add test coverage reporting` |

### Scopes (eMMA Project)

| Scope | Area |
|-------|------|
| `auth` | Authentication, JWT, login/logout |
| `api` | API routes, endpoints |
| `db` | Database, models, migrations |
| `ws` | WebSocket, real-time |
| `docker` | Docker integration |
| `services` | Service monitoring |
| `users` | User management |
| `audit` | Audit logging |
| `ui` | Frontend components |
| `hooks` | React hooks |
| `store` | Zustand stores |
| `tests` | Test files |
| `deps` | Dependencies |
| `config` | Configuration |

## Workflow

### 1. Analyze Changes

```bash
# View staged changes
git diff --cached --stat

# View detailed diff
git diff --cached

# View unstaged changes
git diff
```

### 2. Determine Type and Scope

Based on the changes:
- **New files in features/** → `feat`
- **Changes to existing behavior** → `fix` or `refactor`
- **Only .md files** → `docs`
- **Only test files** → `test`
- **package.json, pyproject.toml** → `chore(deps)` or `build`

### 3. Write Subject Line

Rules:
- Imperative mood: "add" not "added" or "adds"
- Lowercase first letter
- No period at end
- Max 50 characters
- Describe WHAT, not HOW

Good:
- `feat(auth): add password reset functionality`
- `fix(ws): handle disconnection gracefully`

Bad:
- `feat(auth): Added password reset` (past tense)
- `fix(ws): Fixed the bug.` (period, past tense)

### 4. Write Body (if needed)

When to include body:
- Complex changes needing explanation
- Breaking changes
- Non-obvious implementation choices

Format:
- Blank line after subject
- Wrap at 72 characters
- Explain WHY, not WHAT

### 5. Add Footer (if needed)

```
BREAKING CHANGE: description

Closes #123
Refs #456
```

## Examples

### Simple Feature

```
feat(services): add SSL certificate expiry monitoring

Add check for SSL certificate expiration dates during health checks.
Certificates expiring within 30 days trigger warning status.
```

### Bug Fix

```
fix(ws): prevent memory leak in keepalive timer

Clear setTimeout reference when WebSocket disconnects to prevent
accumulation of orphaned timers.

Closes #42
```

### Multiple Changes

```
refactor(api): restructure authentication middleware

- Extract token validation to separate module
- Add request context for user info
- Improve error messages for auth failures

BREAKING CHANGE: Auth middleware now requires explicit configuration
```

### Dependency Update

```
chore(deps): update react-query to v5

Migrate from useQuery options to new object syntax.
Update all hooks to use new API.
```

### Documentation

```
docs(api): add OpenAPI examples for service endpoints

Include request/response examples for:
- POST /v1/services
- GET /v1/services/{id}
- PUT /v1/services/{id}
```

## German Commit Messages (Optional)

If the project uses German:

```
feat(auth): Passwort-Reset Funktion hinzufuegen

fix(ws): Speicherleck bei Keepalive-Timer beheben

docs(readme): Installationsanleitung aktualisieren

refactor(api): Authentifizierungs-Middleware umstrukturieren
```

## Quick Reference

```bash
# Stage specific files
git add path/to/file

# Stage all changes
git add -A

# Commit with message
git commit -m "feat(scope): subject line"

# Commit with body
git commit -m "feat(scope): subject" -m "Body paragraph here."

# Amend last commit (careful!)
git commit --amend

# View commit history
git log --oneline -10
```

## Commit Message Template

```
# <type>(<scope>): <subject>
#
# Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci
# Scope: auth, api, db, ws, docker, services, users, audit, ui, hooks, store
#
# Subject: imperative, lowercase, no period, max 50 chars
#
# Body: explain WHY (wrap at 72 chars)
#
# Footer: BREAKING CHANGE, Closes #issue
```
