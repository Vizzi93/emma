#Requires -Version 5.1
# ============================================================
# eMMA Setup Script for Windows
# ============================================================

$ErrorActionPreference = "Stop"
$ProjectDir = $PSScriptRoot

# Colors
function Write-Step { param($msg) Write-Host "`n[*] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[-] $msg" -ForegroundColor Red }

# Banner
Clear-Host
Write-Host @"

  ███████╗███╗   ███╗███╗   ███╗ █████╗
  ██╔════╝████╗ ████║████╗ ████║██╔══██╗
  █████╗  ██╔████╔██║██╔████╔██║███████║
  ██╔══╝  ██║╚██╔╝██║██║╚██╔╝██║██╔══██║
  ███████╗██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║
  ╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝

         Setup Script v2.0 (Windows)

"@ -ForegroundColor Magenta

# 1. Check Docker
Write-Step "Pruefe Docker..."

$dockerInstalled = $false
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker gefunden: $dockerVersion"
        $dockerInstalled = $true
    }
} catch {}

if (-not $dockerInstalled) {
    Write-Err "Docker ist nicht installiert oder laeuft nicht!"
    Write-Host "`n    Bitte installiere Docker Desktop:" -ForegroundColor Yellow
    Write-Host "    https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host "`n    Nach der Installation Docker Desktop starten und erneut ausfuehren.`n" -ForegroundColor Yellow
    exit 1
}

# Check if Docker daemon is running
try {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Success "Docker Daemon laeuft"
} catch {
    Write-Err "Docker Daemon laeuft nicht!"
    Write-Host "    Bitte Docker Desktop starten und erneut ausfuehren." -ForegroundColor Yellow
    exit 1
}

# 2. Create secrets directory and generate keys
Write-Step "Erstelle Secrets..."

$SecretsDir = Join-Path $ProjectDir "secrets"
if (-not (Test-Path $SecretsDir)) {
    New-Item -ItemType Directory -Path $SecretsDir -Force | Out-Null
}

# Generate signing key (RSA)
$SigningKey = Join-Path $SecretsDir "config-signing.pem"
if (-not (Test-Path $SigningKey)) {
    Write-Host "    Generiere RSA Signing Key..." -ForegroundColor Gray

    # Use OpenSSL if available, otherwise use .NET
    $opensslAvailable = $null -ne (Get-Command openssl -ErrorAction SilentlyContinue)

    if ($opensslAvailable) {
        openssl genrsa -out $SigningKey 2048 2>$null
        openssl rsa -in $SigningKey -pubout -out (Join-Path $SecretsDir "config-signing.pub.pem") 2>$null
    } else {
        # Fallback: Create RSA key using .NET (compatible with .NET Framework 4.x)
        $rsa = [System.Security.Cryptography.RSACryptoServiceProvider]::new(2048)

        # Export private key in PKCS#8 format and convert to PEM
        $privateKeyBytes = $rsa.ExportPkcs8PrivateKey()
        $privateKeyBase64 = [Convert]::ToBase64String($privateKeyBytes)
        $privateKeyPem = "-----BEGIN PRIVATE KEY-----`n"
        for ($i = 0; $i -lt $privateKeyBase64.Length; $i += 64) {
            $lineLength = [Math]::Min(64, $privateKeyBase64.Length - $i)
            $privateKeyPem += $privateKeyBase64.Substring($i, $lineLength) + "`n"
        }
        $privateKeyPem += "-----END PRIVATE KEY-----"

        # Export public key and convert to PEM
        $publicKeyBytes = $rsa.ExportSubjectPublicKeyInfo()
        $publicKeyBase64 = [Convert]::ToBase64String($publicKeyBytes)
        $publicKeyPem = "-----BEGIN PUBLIC KEY-----`n"
        for ($i = 0; $i -lt $publicKeyBase64.Length; $i += 64) {
            $lineLength = [Math]::Min(64, $publicKeyBase64.Length - $i)
            $publicKeyPem += $publicKeyBase64.Substring($i, $lineLength) + "`n"
        }
        $publicKeyPem += "-----END PUBLIC KEY-----"

        $privateKeyPem | Set-Content -Path $SigningKey -NoNewline
        $publicKeyPem | Set-Content -Path (Join-Path $SecretsDir "config-signing.pub.pem") -NoNewline
        $rsa.Dispose()
    }
    Write-Success "RSA Signing Key erstellt"
} else {
    Write-Success "Signing Key existiert bereits"
}

# Generate secret key
$SecretKeyFile = Join-Path $SecretsDir "secret_key"
if (-not (Test-Path $SecretKeyFile)) {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $secretKey = [System.BitConverter]::ToString($bytes) -replace '-',''
    $secretKey | Set-Content -Path $SecretKeyFile -NoNewline
    Write-Success "Secret Key erstellt"
} else {
    Write-Success "Secret Key existiert bereits"
}

# Generate DB password
$DbPasswordFile = Join-Path $SecretsDir "db_password"
if (-not (Test-Path $DbPasswordFile)) {
    $bytes = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $dbPassword = [Convert]::ToBase64String($bytes) -replace '[/+=]',''
    $dbPassword.Substring(0, [Math]::Min(24, $dbPassword.Length)) | Set-Content -Path $DbPasswordFile -NoNewline
    Write-Success "DB Password erstellt"
} else {
    Write-Success "DB Password existiert bereits"
}

# 3. Create .env file
Write-Step "Erstelle .env Datei..."

$EnvFile = Join-Path $ProjectDir ".env"
$secretKey = Get-Content $SecretKeyFile -Raw
$dbPassword = Get-Content $DbPasswordFile -Raw

if (-not (Test-Path $EnvFile)) {
    @"
# eMMA Development Configuration
# Generated by setup-emma.ps1 on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

ENVIRONMENT=development
DEBUG=true

# Database
DB_PASSWORD=$dbPassword

# Security
SECRET_KEY=$secretKey
JWT_SECRET_KEY=$secretKey
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Agent Provisioning
AGENT_BINARY_BASE_URL=http://localhost:8000
CONFIG_SIGNING_KEY_ID=emma-config-dev

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=console
"@ | Set-Content -Path $EnvFile -Encoding UTF8
    Write-Success ".env Datei erstellt"
} else {
    Write-Success ".env Datei existiert bereits"
}

# 4. Start Docker Compose
Write-Step "Starte Docker Container..."

Set-Location $ProjectDir

Write-Host "    Starte PostgreSQL und warte auf Bereitschaft..." -ForegroundColor Gray
docker compose up -d postgres

# Wait for postgres
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    $result = docker compose exec -T postgres pg_isready -U emma -d emma 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "PostgreSQL ist bereit"
        break
    }
    $attempt++
    Start-Sleep -Seconds 1
}

if ($attempt -eq $maxAttempts) {
    Write-Err "PostgreSQL konnte nicht gestartet werden"
    exit 1
}

# Run migrations
Write-Host "    Fuehre Datenbank-Migrationen aus..." -ForegroundColor Gray
docker compose run --rm migrations
Write-Success "Migrationen abgeschlossen"

# Start all services
Write-Host "    Starte alle Services..." -ForegroundColor Gray
docker compose up -d

# Wait for API
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Success "API ist bereit"
            break
        }
    } catch {}
    $attempt++
    Start-Sleep -Seconds 2
}

# 5. Show status
Write-Host @"

================================================================================
"@ -ForegroundColor Green
Write-Host "                    SETUP ERFOLGREICH!" -ForegroundColor Green
Write-Host @"
================================================================================
"@ -ForegroundColor Green

Write-Host "`nServices Status:" -ForegroundColor Yellow
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n--- URLs ---" -ForegroundColor Yellow
Write-Host "Frontend:           " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API:        " -NoNewline; Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Dokumentation:  " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan

Write-Host "`n--- Nuetzliche Befehle ---" -ForegroundColor Yellow
Write-Host "Logs anzeigen:      " -NoNewline; Write-Host "docker compose logs -f" -ForegroundColor White
Write-Host "Services stoppen:   " -NoNewline; Write-Host "docker compose down" -ForegroundColor White
Write-Host "Neustarten:         " -NoNewline; Write-Host "docker compose restart" -ForegroundColor White
Write-Host "Status pruefen:     " -NoNewline; Write-Host "docker compose ps" -ForegroundColor White

Write-Host @"

================================================================================
"@ -ForegroundColor Green
