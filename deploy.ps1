# Deploy: pull ready images from ghcr.io (built by GitHub CI) + restart + health check.
# -Auto: for the scheduled task; exits silently when nothing changed.
# One-time laptop setup: docker login ghcr.io (PAT with read:packages).
param([switch]$Auto)
Set-Location $PSScriptRoot

git fetch origin main --quiet 2>$null
git merge --ff-only origin/main --quiet 2>$null

$compose = @('compose', '-p', 'infra', '-f', 'infra/docker-compose.yml', '--env-file', '.env', '--project-directory', 'infra')
$services = @('backend', 'bot', 'media-server', 'admin', 'miniapp')

# pull only our five ghcr images: postgres/redis/cloudflared live on Docker Hub,
# which is unreachable from here without a VPN
if ($Auto) { docker @compose pull --quiet @services *> $null }
else { docker @compose pull @services }
if ($LASTEXITCODE -ne 0) { "$(Get-Date -Format s) deploy FAILED: image pull (docker login ghcr.io done?)"; exit 1 }

$up = docker @compose up -d --no-build 2>&1
if ($LASTEXITCODE -ne 0) { $up | ForEach-Object { "$_" }; "$(Get-Date -Format s) deploy FAILED: compose up"; exit 1 }

# compose prints "Started"/"Created" only for containers it actually replaced
$changed = ($up | Select-String 'Started|Created').Count
if ($Auto -and $changed -eq 0) { exit 0 }

"$(Get-Date -Format s) deploying $(git rev-parse --short HEAD): changed=$changed"
$deadline = (Get-Date).AddMinutes(3)
do {
    Start-Sleep -Seconds 5
    try { $ok = (Invoke-WebRequest -UseBasicParsing http://localhost:8000/health -TimeoutSec 5).StatusCode -eq 200 } catch { $ok = $false }
} until ($ok -or (Get-Date) -gt $deadline)
if (-not $ok) { "$(Get-Date -Format s) deploy FAILED: backend health check timed out"; exit 1 }
"$(Get-Date -Format s) deploy ok"
