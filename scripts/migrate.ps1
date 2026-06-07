# SmartStore AI — Run Alembic database migrations
# Run from the project root:  .\scripts\migrate.ps1

param(
    [string]$Revision = "head",
    [string]$Message  = ""
)

$Root     = $PSScriptRoot | Split-Path
$activate = Join-Path $Root "backend\venv\Scripts\Activate.ps1"

if (-not (Test-Path $activate)) {
    Write-Error "Virtual environment not found. Run .\scripts\setup.ps1 first."
}

# Load .env
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
Set-Location $Root

if ($Message) {
    Write-Host "Generating new migration: $Message" -ForegroundColor Cyan
    alembic revision --autogenerate -m $Message
} else {
    Write-Host "Upgrading to: $Revision" -ForegroundColor Cyan
    alembic upgrade $Revision
}
