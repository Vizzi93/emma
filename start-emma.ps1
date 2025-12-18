# ============================================================
# eMMA Startup Script
# Startet Backend und Frontend Server
# ============================================================

param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$Setup,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$ServerDir = Join-Path $ProjectRoot "server"
$ClientDir = Join-Path $ProjectRoot "client"

# Farben
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Show-Help {
    Write-Host ""
    Write-Host "eMMA Startup Script" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verwendung:" -ForegroundColor Yellow
    Write-Host "  .\start-emma.ps1           # Startet Backend und Frontend"
    Write-Host "  .\start-emma.ps1 -Backend  # Startet nur Backend"
    Write-Host "  .\start-emma.ps1 -Frontend # Startet nur Frontend"
    Write-Host "  .\start-emma.ps1 -Setup    # Initialisiert Datenbank und Admin"
    Write-Host "  .\start-emma.ps1 -Help     # Zeigt diese Hilfe"
    Write-Host ""
    Write-Host "URLs:" -ForegroundColor Yellow
    Write-Host "  Frontend:  http://localhost:3000"
    Write-Host "  Backend:   http://localhost:8000"
    Write-Host "  API Docs:  http://localhost:8000/docs"
    Write-Host ""
    Write-Host "Login:" -ForegroundColor Yellow
    Write-Host "  E-Mail:    admin@example.com"
    Write-Host "  Passwort:  admin123"
    Write-Host ""
}

function Test-Prerequisites {
    Write-Info "Pruefe Voraussetzungen..."

    # Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "Python: $pythonVersion"
    } catch {
        Write-Err "Python nicht gefunden. Bitte installieren: https://python.org"
        exit 1
    }

    # Node.js
    try {
        $nodeVersion = node --version 2>&1
        Write-Success "Node.js: $nodeVersion"
    } catch {
        Write-Err "Node.js nicht gefunden. Bitte installieren: https://nodejs.org"
        exit 1
    }

    # npm
    try {
        $npmVersion = npm --version 2>&1
        Write-Success "npm: $npmVersion"
    } catch {
        Write-Err "npm nicht gefunden."
        exit 1
    }
}

function Initialize-Environment {
    Write-Info "Initialisiere Umgebung..."

    # Backend .env erstellen falls nicht vorhanden
    $envFile = Join-Path $ServerDir ".env"
    if (-not (Test-Path $envFile)) {
        Write-Info "Erstelle .env Datei..."

        $secretKey = -join ((48..57) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
        $jwtSecret = -join ((48..57) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

        $envContent = @"
# eMMA Backend Configuration - Development
ENVIRONMENT=development
DEBUG=true

# Database (SQLite for development)
DATABASE_URL=sqlite+aiosqlite:///./emma.db

# Security
SECRET_KEY=$secretKey

# JWT Authentication
JWT_SECRET_KEY=$jwtSecret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
ALLOWED_HOSTS=["localhost","127.0.0.1"]

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Agent Provisioning
AGENT_BINARY_BASE_URL=http://localhost:8000/agents
CONFIG_SIGNING_KEY_ID=emma-dev-key
CONFIG_SIGNING_PRIVATE_KEY=dev-signing-key-not-for-production

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=console

# API Configuration
API_V1_PREFIX=/v1
API_TITLE=eMMA Monitoring API
API_VERSION=1.0.0
"@
        $envContent | Out-File -FilePath $envFile -Encoding UTF8
        Write-Success ".env Datei erstellt"
    } else {
        Write-Success ".env Datei existiert bereits"
    }
}

function Install-Dependencies {
    Write-Info "Installiere Abhaengigkeiten..."

    # Backend Dependencies
    Write-Info "Backend Dependencies..."
    Push-Location $ServerDir
    try {
        pip install -e ".[dev]" --quiet 2>$null
        Write-Success "Backend Dependencies installiert"
    } catch {
        Write-Warn "Backend Dependencies Installation fehlgeschlagen"
    }
    Pop-Location

    # Frontend Dependencies
    Write-Info "Frontend Dependencies..."
    Push-Location $ClientDir
    try {
        if (-not (Test-Path "node_modules")) {
            npm install --silent 2>$null
            Write-Success "Frontend Dependencies installiert"
        } else {
            Write-Success "Frontend Dependencies bereits vorhanden"
        }
    } catch {
        Write-Warn "Frontend Dependencies Installation fehlgeschlagen"
    }
    Pop-Location
}

function Initialize-Database {
    Write-Info "Initialisiere Datenbank..."

    Push-Location $ServerDir
    try {
        python -m alembic upgrade head 2>$null
        Write-Success "Datenbank Migrationen ausgefuehrt"
    } catch {
        Write-Warn "Datenbank Migration fehlgeschlagen"
    }

    # Admin User erstellen
    $dbFile = Join-Path $ServerDir "emma.db"
    if (Test-Path $dbFile) {
        try {
            python create_admin.py 2>$null
            Write-Success "Admin User erstellt: admin@example.com / admin123"
        } catch {
            Write-Info "Admin User existiert bereits"
        }
    }
    Pop-Location
}

function Start-Backend {
    Write-Info "Starte Backend Server..."

    Push-Location $ServerDir
    $env:PYTHONUNBUFFERED = "1"

    Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" -NoNewWindow

    Write-Success "Backend gestartet: http://localhost:8000"
    Write-Info "API Dokumentation: http://localhost:8000/docs"
    Pop-Location
}

function Start-Frontend {
    Write-Info "Starte Frontend Server..."

    Push-Location $ClientDir

    Start-Process -FilePath "npm" -ArgumentList "run", "dev" -NoNewWindow

    Write-Success "Frontend gestartet: http://localhost:3000"
    Pop-Location
}

# ============================================================
# Main
# ============================================================

if ($Help) {
    Show-Help
    exit 0
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "     eMMA - Enterprise Monitoring App      " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Test-Prerequisites

if ($Setup) {
    Initialize-Environment
    Install-Dependencies
    Initialize-Database
    Write-Host ""
    Write-Success "Setup abgeschlossen!"
    Write-Host ""
    exit 0
}

# Pruefe ob Setup noetig ist
$dbFile = Join-Path $ServerDir "emma.db"
if (-not (Test-Path $dbFile)) {
    Write-Warn "Datenbank nicht gefunden. Fuehre Setup aus..."
    Initialize-Environment
    Install-Dependencies
    Initialize-Database
}

# Starte Services
$startBoth = -not $Backend -and -not $Frontend

if ($Backend -or $startBoth) {
    Start-Backend
    Start-Sleep -Seconds 2
}

if ($Frontend -or $startBoth) {
    Start-Frontend
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "     eMMA ist gestartet!                   " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:  " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor Yellow
Write-Host "  Backend:   " -NoNewline; Write-Host "http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs:  " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Login:" -ForegroundColor Cyan
Write-Host "  E-Mail:    admin@example.com"
Write-Host "  Passwort:  admin123"
Write-Host ""
Write-Host "  Druecke Strg+C um die Server zu stoppen" -ForegroundColor Gray
Write-Host ""

# Halte das Skript am Laufen
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Info "Beende Server..."
}
