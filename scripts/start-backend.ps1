# SmartStore AI — Start the FastAPI backend (dev mode with auto-reload)
# Run from the project root:  .\scripts\start-backend.ps1

$Root       = $PSScriptRoot | Split-Path
$backendDir = Join-Path $Root "backend"
$activate   = Join-Path $backendDir "venv\Scripts\Activate.ps1"

if (-not (Test-Path $activate)) {
    Write-Error "Virtual environment not found. Run .\scripts\setup.ps1 first."
}

# Load .env so DATABASE_URL etc. are available
$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name  = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

. $activate

Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Cyan
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop.`n"

Set-Location $backendDir
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
