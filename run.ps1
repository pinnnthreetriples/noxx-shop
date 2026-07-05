# Dev helper for running the stack on Windows via Docker Desktop (no WSL / make needed).
# Usage:  .\run.ps1 up | down | build | seed | logs | ps | backend-shell
param([Parameter(Position=0)][string]$cmd = "ps")

$ErrorActionPreference = "Stop"
$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
$root   = $PSScriptRoot
$file   = Join-Path $root "infra\docker-compose.yml"
$envf   = Join-Path $root ".env"
# Core services only — bot and cloudflared need tokens we don't have.
$core   = @("postgres","redis","backend","admin","media-server")

function Compose { & $docker -c desktop-linux compose -p infra -f $file --env-file $envf --project-directory (Join-Path $root "infra") @args }

switch ($cmd) {
  "up"            { Compose up -d --build @core }
  "down"          { Compose down }
  "build"         { Compose build @core }
  "seed"          { Compose exec backend python -m scripts.seed }
  "logs"          { Compose logs -f }
  "ps"            { Compose ps }
  "backend-shell" { Compose exec backend bash }
  default         { Write-Host "Unknown command '$cmd'. Use: up | down | build | seed | logs | ps | backend-shell" }
}
