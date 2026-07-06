# Deploy latest main: git pull + rebuild containers + health check.
# -Auto: for the scheduled task; exits silently when already up to date.
param([switch]$Auto)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

git fetch origin main --quiet
$local = git rev-parse HEAD
$remote = git rev-parse origin/main
if ($Auto -and $local -eq $remote) { exit 0 }

"$(Get-Date -Format s) deploying $($remote.Substring(0,7))"
git merge --ff-only origin/main
docker compose -p infra -f infra/docker-compose.yml --env-file .env --project-directory infra up -d --build

$deadline = (Get-Date).AddMinutes(3)
do {
    Start-Sleep -Seconds 5
    try { $ok = (Invoke-WebRequest -UseBasicParsing http://localhost:8000/health -TimeoutSec 5).StatusCode -eq 200 } catch { $ok = $false }
} until ($ok -or (Get-Date) -gt $deadline)

if (-not $ok) { "$(Get-Date -Format s) deploy FAILED: backend health check timed out"; exit 1 }
"$(Get-Date -Format s) deploy ok"
