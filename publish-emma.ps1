# ============================================================
# eMMA GitHub Publish Script
# ============================================================
# Erstellt automatisch eine neue Version und pusht zu GitHub
# Usage: .\publish-emma.ps1 [-Major] [-Minor] [-Patch] [-Message "..."]
# ============================================================

param(
    [switch]$Major,      # 1.0.0 -> 2.0.0
    [switch]$Minor,      # 1.0.0 -> 1.1.0
    [switch]$Patch,      # 1.0.0 -> 1.0.1 (Standard)
    [string]$Message,    # Custom Commit-Nachricht
    [switch]$DryRun,     # Nur anzeigen, nichts ausfuehren
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
    Write-Host "  eMMA - GitHub Publish Script" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

# Hilfe
function Show-Help {
    Show-Banner
    Write-Host "Usage: .\publish-emma.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Versions-Optionen (waehle eine):"
    Write-Host "  -Patch     Patch-Version erhoehen: 1.0.0 -> 1.0.1 (Standard)"
    Write-Host "  -Minor     Minor-Version erhoehen: 1.0.0 -> 1.1.0"
    Write-Host "  -Major     Major-Version erhoehen: 1.0.0 -> 2.0.0"
    Write-Host ""
    Write-Host "Weitere Optionen:"
    Write-Host "  -Message   Custom Commit-Nachricht (optional)"
    Write-Host "  -DryRun    Zeigt an was passieren wuerde, ohne auszufuehren"
    Write-Host "  -Help      Zeigt diese Hilfe"
    Write-Host ""
    Write-Host "Beispiele:"
    Write-Host "  .\publish-emma.ps1                    # Patch-Release"
    Write-Host "  .\publish-emma.ps1 -Minor             # Minor-Release"
    Write-Host "  .\publish-emma.ps1 -Major             # Major-Release"
    Write-Host '  .\publish-emma.ps1 -Message "Bugfix"  # Mit Nachricht'
    Write-Host ""
    exit 0
}

# Git pruefen
function Test-Git {
    try {
        $null = git status 2>&1
        return $true
    } catch {
        Write-Err "Git nicht gefunden oder kein Git-Repository!"
        return $false
    }
}

# Aktuelle Version lesen
function Get-CurrentVersion {
    $versionFile = Join-Path $PSScriptRoot "VERSION"
    if (Test-Path $versionFile) {
        $version = (Get-Content $versionFile -Raw).Trim()
        if ($version -match '^\d+\.\d+\.\d+$') {
            return $version
        }
    }

    # Fallback: Letzten Git-Tag lesen
    $lastTag = git describe --tags --abbrev=0 2>$null
    if ($lastTag -match 'v?(\d+\.\d+\.\d+)') {
        return $matches[1]
    }

    return "0.0.0"
}

# Version erhoehen
function Get-NextVersion {
    param([string]$Current, [string]$Type)

    $parts = $Current.Split('.')
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    $patch = [int]$parts[2]

    switch ($Type) {
        "major" { $major++; $minor = 0; $patch = 0 }
        "minor" { $minor++; $patch = 0 }
        "patch" { $patch++ }
    }

    return "$major.$minor.$patch"
}

# Aenderungen anzeigen
function Show-Changes {
    Write-Info "Aktuelle Aenderungen:"
    Write-Host ""

    $status = git status --short
    if ($status) {
        $status | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    } else {
        Write-Host "  (keine Aenderungen)" -ForegroundColor Gray
    }
    Write-Host ""
}

# VERSION-Datei aktualisieren
function Update-VersionFile {
    param([string]$Version)

    $versionFile = Join-Path $PSScriptRoot "VERSION"
    $Version | Set-Content $versionFile -NoNewline
    Write-Success "VERSION-Datei aktualisiert: $Version"
}

# Hauptlogik
function Publish-Emma {
    Show-Banner

    if (-not (Test-Git)) { exit 1 }

    # Versionstyp bestimmen
    $versionType = "patch"
    if ($Major) { $versionType = "major" }
    elseif ($Minor) { $versionType = "minor" }

    # Versionen berechnen
    $currentVersion = Get-CurrentVersion
    $newVersion = Get-NextVersion -Current $currentVersion -Type $versionType

    Write-Info "Aktuelle Version: $currentVersion"
    Write-Info "Neue Version:     $newVersion ($versionType)"
    Write-Host ""

    # Aenderungen anzeigen
    Show-Changes

    # Pruefen ob es Aenderungen gibt
    $hasChanges = (git status --porcelain) -ne $null
    if (-not $hasChanges) {
        Write-Warn "Keine Aenderungen zum Committen gefunden."
        $confirm = Read-Host "Trotzdem eine neue Version erstellen? (j/N)"
        if ($confirm -ne "j" -and $confirm -ne "J") {
            Write-Info "Abgebrochen."
            exit 0
        }
    }

    # Commit-Nachricht
    if (-not $Message) {
        $Message = "Release v$newVersion"
    }

    Write-Info "Commit-Nachricht: $Message"
    Write-Info "Git-Tag: v$newVersion"
    Write-Host ""

    # DryRun?
    if ($DryRun) {
        Write-Warn "DRY-RUN: Keine Aenderungen werden durchgefuehrt."
        Write-Host ""
        Write-Host "Folgende Befehle wuerden ausgefuehrt:" -ForegroundColor Gray
        Write-Host "  1. VERSION-Datei auf $newVersion setzen"
        Write-Host "  2. git add ."
        Write-Host "  3. git commit -m `"$Message`""
        Write-Host "  4. git tag -a v$newVersion -m `"Release v$newVersion`""
        Write-Host "  5. git push origin main"
        Write-Host "  6. git push origin v$newVersion"
        Write-Host ""
        exit 0
    }

    # Bestaetigung
    $confirm = Read-Host "Fortfahren? (J/n)"
    if ($confirm -eq "n" -or $confirm -eq "N") {
        Write-Info "Abgebrochen."
        exit 0
    }

    Write-Host ""

    # 1. VERSION-Datei aktualisieren
    Update-VersionFile -Version $newVersion

    # 2. Alle Aenderungen stagen
    Write-Info "Stage alle Aenderungen..."
    git add .

    # 3. Commit erstellen
    Write-Info "Erstelle Commit..."
    $commitMessage = @"
$Message

Release v$newVersion

Generated with eMMA Publish Script
"@
    git commit -m $commitMessage
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Commit fehlgeschlagen!"
        exit 1
    }
    Write-Success "Commit erstellt"

    # 4. Tag erstellen
    Write-Info "Erstelle Tag v$newVersion..."
    git tag -a "v$newVersion" -m "Release v$newVersion"
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Tag-Erstellung fehlgeschlagen!"
        exit 1
    }
    Write-Success "Tag v$newVersion erstellt"

    # 5. Push zum Remote
    Write-Info "Push zu GitHub..."

    # Branch pushen
    $branch = git rev-parse --abbrev-ref HEAD
    git push origin $branch
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Push fehlgeschlagen!"
        exit 1
    }

    # Tag pushen
    git push origin "v$newVersion"
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Tag-Push fehlgeschlagen!"
        exit 1
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Success "Release v$newVersion erfolgreich veroeffentlicht!"
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "GitHub Repository: " -NoNewline
    $remote = git remote get-url origin
    Write-Host $remote -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Naechste Schritte:" -ForegroundColor Yellow
    Write-Host "  - Besuche GitHub um Release Notes hinzuzufuegen"
    Write-Host "  - URL: $($remote -replace '\.git$', '')/releases/tag/v$newVersion"
    Write-Host ""
}

# Ausfuehren
if ($Help) { Show-Help }
else { Publish-Emma }
