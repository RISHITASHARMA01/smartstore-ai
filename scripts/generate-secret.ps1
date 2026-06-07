# SmartStore AI — Generate a secure random SECRET_KEY
# Run from anywhere:  .\scripts\generate-secret.ps1

$bytes  = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$secret = [System.BitConverter]::ToString($bytes) -replace '-', '' | ForEach-Object { $_.ToLower() }

Write-Host ""
Write-Host "Your SECRET_KEY:" -ForegroundColor Cyan
Write-Host $secret -ForegroundColor Green
Write-Host ""
Write-Host "Add this to your .env file:" -ForegroundColor White
Write-Host "  SECRET_KEY=$secret"
Write-Host ""

# Offer to write directly to .env
$envFile = Join-Path ($PSScriptRoot | Split-Path) ".env"
if (Test-Path $envFile) {
    $answer = Read-Host "Write SECRET_KEY to .env now? (y/N)"
    if ($answer -eq "y" -or $answer -eq "Y") {
        $content = Get-Content $envFile
        $updated = $content -replace '^SECRET_KEY=.*', "SECRET_KEY=$secret"
        $updated | Set-Content $envFile
        Write-Host "SECRET_KEY updated in .env" -ForegroundColor Green
    }
}
