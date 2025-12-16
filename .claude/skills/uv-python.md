---
name: uv-python
description: Use uv for fast Python package management. Use when managing Python dependencies.
globs:
  - "server/**/*.py"
  - "server/pyproject.toml"
  - "server/requirements*.txt"
---

# UV Python Package Manager

Use uv for extremely fast Python dependency management (written in Rust).

## Installation
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

## Basic Commands

### Virtual Environment
```bash
# Create venv
uv venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### Package Management
```bash
# Install from requirements.txt
uv pip install -r requirements.txt

# Install package
uv pip install fastapi

# Install with extras
uv pip install -e ".[dev,docker]"

# Upgrade package
uv pip install --upgrade fastapi

# Uninstall
uv pip uninstall package-name
```

### Lock Files
```bash
# Generate lock file
uv pip compile requirements.in -o requirements.txt

# Sync environment to lock file
uv pip sync requirements.txt
```

## eMMA Specific Usage

### Backend Setup
```bash
cd server
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev,docker]"
```

### Docker Optimization
```dockerfile
# In Dockerfile - use uv for faster builds
FROM python:3.11-slim

# Install uv
RUN pip install uv

# Copy requirements first for caching
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy app code
COPY . .
```

### CI/CD Optimization
```yaml
# GitHub Actions
- name: Install uv
  run: pip install uv

- name: Install dependencies
  run: uv pip install --system -r requirements.txt
```

## Benefits over pip
- 10-100x faster installs
- Better dependency resolution
- Compatible with pip commands
- Lock file generation
- Built-in venv management

## Migration from pip
```bash
# Just replace pip with uv pip
pip install fastapi  →  uv pip install fastapi
pip freeze  →  uv pip freeze
pip list  →  uv pip list
```
