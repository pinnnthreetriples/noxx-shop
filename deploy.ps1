# Deploy: pull ready images from ghcr.io (built by GitHub CI) + restart + health check.
# Runs from the Task Scheduler every 5 min and renders live progress in the console window
# it pops, so it's obvious whether main changed, whether images are downloading (docker's own
# per-image % bars), and how the run ended. Every run also appends one line to deploy.log.
# -Auto:   scheduled/unattended run (no end-of-run pause). Omit it for a manual run.
# -Status: just print the recent deploy history from deploy.log and exit (the run window
#          flashes shut on "nothing to deploy", so this is how you check what happened).
# One-time laptop setup: docker login ghcr.io (PAT with read:packages).
param([switch]$Auto, [switch]$Status)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

$compose  = @('compose', '-p', 'infra', '-f', 'infra/docker-compose.yml', '--env-file', '.env', '--project-directory', 'infra')
$services = @('backend', 'bot', 'media-server', 'admin', 'miniapp')
$started  = Get-Date

function Line($text, $color = 'Gray') { Write-Host $text -ForegroundColor $color }
function Done($sw, $text, $color = 'Green') { Line ("  [OK]   {0,-24}{1,6:0.0}s" -f $text, $sw.Elapsed.TotalSeconds) $color }
function Fail($text) { Line "  [FAIL] $text" 'Red' }
function Finish($result, $note) {
    $secs = [int]((Get-Date) - $started).TotalSeconds
    "$(Get-Date -Format s)`t$result`t$(git rev-parse --short HEAD)`t$note`t${secs}s" |
        Add-Content -Path (Join-Path $PSScriptRoot 'deploy.log')
}

if ($Status) {
    $log = Join-Path $PSScriptRoot 'deploy.log'
    Line ''
    Line '  recent deploys (newest last)' 'Cyan'
    Line ('  ' + ('-' * 44)) 'DarkGray'
    if (-not (Test-Path $log)) { Line '  no runs logged yet' 'DarkGray'; exit 0 }
    Get-Content $log -Tail 15 | ForEach-Object {
        $f = $_ -split "`t"           # time, result, sha, note, secs
        $color = switch ($f[1]) { 'ok' { 'Green' } 'FAILED' { 'Red' } default { 'DarkGray' } }
        Line ("  {0}  {1,-8} {2,-8} {3,4}  {4}" -f $f[0], $f[1], $f[2], $f[4], $f[3]) $color
    }
    exit 0
}

Line ''
Line "  NoxX deploy   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" 'Cyan'
Line ('  ' + ('-' * 44)) 'DarkGray'

# 1) sync main; capture before/after so we can tell the user exactly what (if anything) changed
$sw = [Diagnostics.Stopwatch]::StartNew()
$before = (git rev-parse HEAD).Trim()
git fetch origin main --quiet 2>$null
git merge --ff-only origin/main --quiet 2>$null
$after = (git rev-parse HEAD).Trim()
$sw.Stop()
if ($before -eq $after) {
    Done $sw 'main already up to date' 'DarkGray'
} else {
    Done $sw "main -> $($after.Substring(0,7))"
    git log --oneline "$before..$after" | ForEach-Object { Line "         + $_" 'DarkGray' }
}

# 2) pull our five ghcr images with docker's native progress bars, streamed straight to the
# window (no capture -> docker keeps its TTY animation with per-image %). postgres/redis/
# cloudflared live on Docker Hub, unreachable from here without a VPN, so we never pull them.
Line ''
Line '  downloading images from ghcr.io ...' 'Yellow'
docker @compose --progress tty pull @services
if ($LASTEXITCODE -ne 0) { Fail 'image pull (docker login ghcr.io done?)'; Finish 'FAILED' 'pull'; exit 1 }

# 3) restart. compose prints "Started"/"Created" only for containers it actually replaced.
Line ''
$sw = [Diagnostics.Stopwatch]::StartNew()
$up = docker @compose --progress plain up -d --no-build 2>&1
$sw.Stop()
if ($LASTEXITCODE -ne 0) { $up | ForEach-Object { Line "  $_" 'Red' }; Fail 'compose up'; Finish 'FAILED' 'up'; exit 1 }
$changed = ($up | Select-String 'Started|Created').Count
if ($changed -eq 0) {
    Done $sw 'containers already current' 'DarkGray'
    Line ''
    Line '  Nothing to deploy.' 'DarkGray'
    Finish 'nochange' '-'
    exit 0
}
Done $sw "$changed container(s) replaced"

# 4) health-check with a live countdown to the 3-minute deadline
Line ''
Line "  deploying $($after.Substring(0,7)) - waiting for backend health" 'Yellow'
$deadline = (Get-Date).AddMinutes(3)
$ok = $false
do {
    $left = [int][math]::Ceiling(($deadline - (Get-Date)).TotalSeconds)
    Write-Host ("`r  [..]   backend /health ...{0,4}s until timeout " -f $left) -NoNewline -ForegroundColor DarkGray
    Start-Sleep -Seconds 5
    try { $ok = (Invoke-WebRequest -UseBasicParsing http://localhost:8000/health -TimeoutSec 5).StatusCode -eq 200 } catch { $ok = $false }
} until ($ok -or (Get-Date) -gt $deadline)
Write-Host ("`r" + (' ' * 52) + "`r") -NoNewline
if (-not $ok) { Fail 'backend health check timed out'; Finish 'FAILED' 'health'; exit 1 }

# 5) summary
$total = [int]((Get-Date) - $started).TotalSeconds
Line ('  ' + ('-' * 44)) 'DarkGray'
Line "  DEPLOYED  $($after.Substring(0,7))   $changed container(s)   ${total}s" 'Green'
Line "  $(git log -1 --pretty=%s)" 'DarkGray'
Finish 'ok' "$changed changed"
if (-not $Auto) { Line ''; Read-Host '  press Enter to close' | Out-Null }
