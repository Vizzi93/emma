---
name: commit-message-generator
description: Generate conventional commit messages based on staged changes. Use when committing code changes.
globs:
  - "**/*"
---

# Commit Message Generator

Generate conventional commit messages following the project's commit convention.

## Commit Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, tooling

## Scopes for eMMA
- `api`: Backend API endpoints
- `auth`: Authentication/Authorization
- `docker`: Docker configuration
- `db`: Database/migrations
- `ui`: Frontend components
- `services`: Service monitoring
- `agents`: Monitoring agents
- `ci`: CI/CD pipelines

## Rules
1. Subject line max 50 characters
2. Use imperative mood ("add" not "added")
3. No period at end of subject
4. Body explains "what" and "why", not "how"
5. Reference issues in footer: `Closes #123`

## Examples
```
feat(api): add Docker container health endpoint

Implement health check endpoint for Docker containers
that returns CPU, memory and network statistics.

Closes #45
```

```
fix(auth): resolve JWT token refresh race condition

Prevent multiple simultaneous refresh requests from
invalidating valid tokens.
```

```
refactor(services): extract monitoring logic to service layer

Move business logic from API routes to dedicated
service classes for better testability.
```
