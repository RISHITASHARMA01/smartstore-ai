# SmartStore AI — Full project setup for Windows
# Run from the project root:  .\scripts\setup.ps1
#
# Requirements: Python 3.11+, Node 20+, Docker Desktop

param(
    [switch]$SkipDocker,
    [switch]$SkipFrontend
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    WARN: $msg" -ForegroundColor Yellow }

$Root = $PSScriptRoot | Split-Path   # project root (one level up from scripts/)

Write-Step "Checking prerequisites"

# Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3.11+ not found. Install from https://www.python.org/downloads/"
}
$pyVer = python --version
Write-Ok $pyVer

# Node
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node 20+ not found. Install from https://nodejs.org/"
}
$nodeVer = node --version
Write-Ok "Node $nodeVer"

# Docker (optional)
if (-not $SkipDocker) {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Warn "Docker not found — skipping PostgreSQL container. Install Docker Desktop or use an existing PostgreSQL instance."
        $SkipDocker = $true
    } else {
        Write-Ok "Docker $(docker --version)"
    }
}

# ── .env ─────────────────────────────────────────────────────────────────────
Write-Step "Configuring environment"
$envFile  = Join-Path $Root ".env"
$envExample = Join-Path $Root ".env.example"

if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Ok "Created .env from .env.example"
    Write-Warn "Edit .env and set SECRET_KEY and GEMINI_API_KEY before running the app."
} else {
    Write-Ok ".env already exists — skipping"
}

# ── PostgreSQL via Docker ─────────────────────────────────────────────────────
if (-not $SkipDocker) {
    Write-Step "Starting PostgreSQL container"
    $running = docker ps --filter "name=smartstore-db" --format "{{.Names}}" 2>$null
    if ($running -eq "smartstore-db") {
        Write-Ok "smartstore-db already running"
    } else {
        $exists = docker ps -a --filter "name=smartstore-db" --format "{{.Names}}" 2>$null
        if ($exists -eq "smartstore-db") {
            docker start smartstore-db | Out-Null
            Write-Ok "Restarted existing smartstore-db container"
        } else {
            docker run -d `
                --name smartstore-db `
                -e POSTGRES_PASSWORD=password `
                -e POSTGRES_DB=smartstore `
                -p 5432:5432 `
                postgres:15-alpine | Out-Null
            Write-Ok "Created and started smartstore-db container"
            Start-Sleep -Seconds 3
        }
    }
}

# ── Backend ───────────────────────────────────────────────────────────────────
Write-Step "Setting up Python backend"
$backendDir = Join-Path $Root "backend"
$venvDir    = Join-Path $backendDir "venv"

if (-not (Test-Path $venvDir)) {
    Write-Host "    Creating virtual environment..."
    python -m venv $venvDir
    Write-Ok "Virtual environment created"
} else {
    Write-Ok "Virtual environment already exists"
}

# Activate venv
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
. $activateScript

Write-Host "    Installing Python dependencies..."
pip install -r (Join-Path $backendDir "requirements.txt") --quiet
Write-Ok "Dependencies installed"

# Run Alembic migrations
Write-Step "Running database migrations"
Set-Location $Root
alembic upgrade head
Write-Ok "Migrations applied"

# ── Frontend ──────────────────────────────────────────────────────────────────
if (-not $SkipFrontend) {
    Write-Step "Setting up Node.js frontend"
    $frontendDir = Join-Path $Root "frontend"
    Set-Location $frontendDir
    Write-Host "    Installing npm dependencies..."
    npm install --silent
    Write-Ok "npm packages installed"
    Set-Location $Root
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Edit .env — set SECRET_KEY and GEMINI_API_KEY"
Write-Host "  2. Start backend:   .\scripts\start-backend.ps1"
Write-Host "  3. Start frontend:  .\scripts\start-frontend.ps1"
Write-Host "  OR"
Write-Host "  4. Docker Compose:  docker compose up --build"
