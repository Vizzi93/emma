# ============================================================
# eMMA Docker Script (PowerShell)
# ============================================================
# Startet eMMA mit Docker Compose
# Usage: .\emma-docker.ps1 [-Stop] [-Restart] [-Logs] [-Status]
# ============================================================

param(
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs,
    [switch]$Status,
    [switch]$Clean,
    [switch]$Build,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Farben
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Blue }
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Err { Write-Host "[ERROR] $args" -ForegroundColor Red }

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  eMMA Docker - Enterprise Multi-Model Agent Management" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

# Hilfe anzeigen
function Show-Help {
    Show-Banner
    Write-Host "Usage: .\emma-docker.ps1 [OPTION]"
    Write-Host ""
    Write-Host "Optionen:"
    Write-Host "  (keine)     Startet eMMA mit Docker"
    Write-Host "  -Build      Startet mit Rebuild der Images"
    Write-Host "  -Stop       Stoppt eMMA"
    Write-Host "  -Restart    Startet eMMA neu"
    Write-Host "  -Logs       Zeigt die Logs an"
    Write-Host "  -Status     Zeigt den Status der Container"
    Write-Host "  -Clean      Stoppt und entfernt alle Container/Volumes"
    Write-Host "  -Help       Zeigt diese Hilfe"
    Write-Host ""
    exit 0
}

# Docker pruefen
function Test-Docker {
    Write-Info "Pruefe Docker..."
    try {
        $null = docker info 2>&1
        Write-Success "Docker laeuft"
        return $true
    } catch {
        Write-Err "Docker laeuft nicht! Bitte Docker Desktop starten."
        return $false
    }
}

# .env erstellen falls nicht vorhanden
function Initialize-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Info "Erstelle .env aus .env.example..."
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Success ".env erstellt"
        } else {
            Write-Warn ".env.example nicht gefunden, erstelle minimale .env..."
            @"
# eMMA Configuration
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
DB_PASSWORD=emma_dev_password
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=DEBUG
"@ | Out-File -FilePath ".env" -Encoding UTF8
            Write-Success "Minimale .env erstellt"
        }
    } else {
        Write-Info ".env existiert bereits"
    }
}

# Netzwerk-Konflikte bereinigen
function Clear-NetworkConflicts {
    Write-Info "Pruefe auf Netzwerk-Konflikte..."
    $networks = docker network ls --format "{{.Name}}" 2>$null
    foreach ($net in $networks) {
        if ($net -match "emma" -and $net -ne "emma-repo_emma-network") {
            Write-Warn "Entferne konfliktierendes Netzwerk: $net"
            docker network rm $net 2>$null
        }
    }
}

# eMMA starten
function Start-Emma {
    Show-Banner

    if (-not (Test-Docker)) { exit 1 }

    Initialize-EnvFile
    Clear-NetworkConflicts

    if ($Build) {
        Write-Info "Starte eMMA mit Rebuild..."
        docker-compose up -d --build
    } else {
        Write-Info "Starte eMMA..."
        docker-compose up -d
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Success "eMMA wurde gestartet!"
        Write-Host ""
        Start-Sleep -Seconds 3
        Show-Status
        Write-Host ""
        Write-Host "API:  http://localhost:8000" -ForegroundColor Green
        Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Err "Fehler beim Starten von eMMA"
        exit 1
    }
}

# eMMA stoppen
function Stop-Emma {
    Show-Banner
    Write-Info "Stoppe eMMA..."
    docker-compose down
    Write-Success "eMMA wurde gestoppt"
}

# Status anzeigen
function Show-Status {
    Write-Info "Container-Status:"
    docker-compose ps
}

# Logs anzeigen
function Show-Logs {
    Write-Info "Zeige Logs (Ctrl+C zum Beenden)..."
    docker-compose logs -f
}

# Alles bereinigen
function Clear-All {
    Show-Banner
    Write-Warn "Stoppe und entferne alle eMMA Container und Volumes..."
    docker-compose down -v --remove-orphans
    Write-Success "Bereinigung abgeschlossen"
}

# Hauptlogik
if ($Help) { Show-Help }
elseif ($Stop) { Stop-Emma }
elseif ($Restart) { Stop-Emma; Start-Emma }
elseif ($Logs) { Show-Logs }
elseif ($Status) { Show-Status }
elseif ($Clean) { Clear-All }
else { Start-Emma }
