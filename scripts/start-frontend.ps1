# SmartStore AI — Start the React/Vite frontend (dev mode with HMR)
# Run from the project root:  .\scripts\start-frontend.ps1

$Root        = $PSScriptRoot | Split-Path
$frontendDir = Join-Path $Root "frontend"

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Error "node_modules not found. Run .\scripts\setup.ps1 first."
}

Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop.`n"

Set-Location $frontendDir
npm run dev
