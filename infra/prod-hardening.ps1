#Requires -Version 7
<#
================================================================================
 REVIEW BEFORE RUNNING.

 This script is meant to be READ, then run ONE SECTION AT A TIME by hand on
 the PROD Windows host only. It is NOT meant to be executed top-to-bottom in
 one go, and it is NOT idempotent-safe for every section -- read each
 function before calling it.

 Assumptions:
   - Windows 10/11 host running Docker Desktop (this is where noxx-shop prod
     actually runs -- see docs/server-hardening-runbook.md).
   - PowerShell 7+ (pwsh).
   - Running as Administrator (several sections touch firewall / account
     policy / Windows services and will fail or no-op without elevation).
   - You are physically on / connected to the correct prod machine. Check
     `deploy.ps1 -Status` or ask the operator first -- nothing here should
     ever be run against the wrong box.
   - Repo layout: this file lives at `infra/prod-hardening.ps1`, run from the
     repo root (same root as `run.ps1`, `deploy.ps1`, and the prod `.env`).

 How to use:
   1. Open this file in an editor, read the section(s) you intend to run.
   2. Dot-source it to load the functions without executing anything:
        . .\infra\prod-hardening.ps1
   3. Call ONE function at a time, e.g.:
        Invoke-DbLeastPrivilegeRole
      Each function prints what it is about to do and asks for an explicit
      "YES" confirmation before touching anything.

 Companion docs (read these first -- this script only operationalizes them):
   - docs/db-least-privilege.md          (Section 1)
   - docs/server-hardening-runbook.md    (Sections 2-9)
================================================================================
#>

$ErrorActionPreference = 'Stop'

# Repo root = parent of this script's directory (infra/..).
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot 'infra\docker-compose.yml'
$EnvFile     = Join-Path $RepoRoot '.env'
$DockerExe   = if (Test-Path 'C:\Program Files\Docker\Docker\resources\bin\docker.exe') {
    'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
} else { 'docker' }

function Confirm-Step {
    param([Parameter(Mandatory)][string]$Message)
    Write-Host $Message -ForegroundColor Yellow
    $answer = Read-Host 'Type YES to proceed, anything else to abort'
    if ($answer -ne 'YES') { Write-Host 'Aborted.' -ForegroundColor Red; return $false }
    return $true
}

function Test-IsAdministrator {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Idempotent-ish helper: set or add KEY=VALUE in a dotenv-style file.
# Only touches the one line for $Key; leaves everything else untouched.
function Set-DotEnvValue {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Key,
        [Parameter(Mandatory)][string]$Value
    )
    if (-not (Test-Path $Path)) { throw "Env file not found: $Path" }
    $lines = Get-Content -Path $Path
    $pattern = "^\s*$Key\s*="
    $found = $false
    $updated = foreach ($line in $lines) {
        if ($line -match $pattern) { $found = $true; "$Key=$Value" } else { $line }
    }
    if (-not $found) { $updated += "$Key=$Value" }
    Set-Content -Path $Path -Value $updated
    Write-Host "  $Key updated in $Path" -ForegroundColor Green
}

# ============================================================================
# SECTION 1 -- DB least-privilege role (docs/db-least-privilege.md)
# ============================================================================
# Order matters: migrate under the PRIVILEGED role first, THEN create the
# restricted role, THEN flip the app over. Doing it out of order can leave
# the app pointed at a role with no DDL rights before the schema exists.
function Invoke-DbLeastPrivilegeRole {
    param(
        # Superuser/owner creds already in prod .env (POSTGRES_USER/PASSWORD).
        [string]$PgSuperUser = $env:POSTGRES_USER,
        [string]$PgDb        = $env:POSTGRES_DB,
        [string]$PostgresContainer = 'infra-postgres-1',
        # Password for the NEW restricted role. Never a real value in this file.
        [string]$AppPassword = '<CHANGE_ME>'
    )
    Write-Host @"
This will, in order:
  1. Confirm the Alembic migration has already run against the PRIVILEGED
     role (you must have already set RUN_MIGRATIONS=1 + ALEMBIC_DATABASE_URL
     and restarted `backend` once -- see docs/db-least-privilege.md step 1).
  2. Run apps/backend/scripts/create_app_db_role.sql inside container
     '$PostgresContainer' as the superuser, creating role 'noxx_app'
     (SELECT/INSERT/UPDATE/DELETE only, no DDL).
  3. Freeze the privileged connection string into ALEMBIC_DATABASE_URL in
     $EnvFile (so future `RUN_MIGRATIONS=1` runs still use the privileged
     role after step 4 repoints DATABASE_URL).
  4. Set DB_AUTO_SCHEMA=0 and repoint DATABASE_URL (via POSTGRES_USER /
     POSTGRES_PASSWORD, which docker-compose.yml interpolates into
     DATABASE_URL for the backend service) at 'noxx_app'.
  5. Remind you to `docker compose up -d backend bot` to pick up the change.

If $PgSuperUser is currently 'video_shop' with a real password, that is fine --
this only ever prints role NAMES, never the actual superuser password.
"@
    if (-not (Confirm-Step 'Proceed with Section 1 (DB least-privilege role)?')) { return }

    if ($AppPassword -eq '<CHANGE_ME>') {
        Write-Host 'Set -AppPassword to a real, freshly generated password before running for real.' -ForegroundColor Red
        return
    }
    if (-not $PgSuperUser -or -not $PgDb) {
        Write-Host 'Pass -PgSuperUser / -PgDb explicitly, or ensure POSTGRES_USER / POSTGRES_DB are set in this shell.' -ForegroundColor Red
        return
    }

    Write-Host "Have you already confirmed 'alembic current' shows 50d45b971a38 (head) against the privileged role? (docs/db-least-privilege.md step 1)" -ForegroundColor Yellow
    if ((Read-Host 'Type YES to confirm') -ne 'YES') { Write-Host 'Run the migration first. Aborting.' -ForegroundColor Red; return }

    # Step 2: create the restricted role.
    $sqlPath = Join-Path $RepoRoot 'apps\backend\scripts\create_app_db_role.sql'
    Get-Content -Raw -Path $sqlPath |
        & $DockerExe exec -i $PostgresContainer psql -U $PgSuperUser -d $PgDb -v app_password="$AppPassword"

    # Step 3: freeze the privileged URL into ALEMBIC_DATABASE_URL BEFORE we
    # repoint POSTGRES_USER/PASSWORD below -- otherwise the privileged
    # connection string is lost once those vars point at noxx_app.
    $privilegedPassword = Read-Host "Enter the CURRENT privileged Postgres password (for '$PgSuperUser'), used only to build ALEMBIC_DATABASE_URL" -AsSecureString
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($privilegedPassword))
    $alembicUrl = "postgresql+asyncpg://${PgSuperUser}:${plain}@postgres:5432/${PgDb}"
    Set-DotEnvValue -Path $EnvFile -Key 'ALEMBIC_DATABASE_URL' -Value $alembicUrl
    $plain = $null

    # Step 4: turn off runtime DDL and repoint the app at noxx_app.
    Set-DotEnvValue -Path $EnvFile -Key 'DB_AUTO_SCHEMA' -Value '0'
    Set-DotEnvValue -Path $EnvFile -Key 'POSTGRES_USER' -Value 'noxx_app'
    Set-DotEnvValue -Path $EnvFile -Key 'POSTGRES_PASSWORD' -Value $AppPassword

    Write-Host @"
Done editing $EnvFile. Now apply it:
  & '$DockerExe' -c desktop-linux compose -p infra -f '$ComposeFile' --env-file '$EnvFile' --project-directory '$(Join-Path $RepoRoot "infra")' up -d backend bot
Then confirm the backend still starts and DB reads/writes work (check
`docker logs infra-backend-1`), and that RUN_MIGRATIONS is back to 0 in .env
for normal restarts (it's only needed=1 for the one-time migration run).
"@
}

# ============================================================================
# SECTION 2 -- Postgres / Redis loopback bind (docs/server-hardening-runbook.md #3)
# ============================================================================
function Invoke-PostgresRedisLoopbackBind {
    Write-Host @"
This will edit $ComposeFile, changing:
  postgres:  ports: "5432:5432"  ->  "127.0.0.1:5432:5432"
  redis:     ports: "6379:6379"  ->  "127.0.0.1:6379:6379"
so neither is reachable from the LAN/internet, only from the Docker host
itself and other containers on the compose network (which use the service
name, not the published port, anyway). Then runs `docker compose up -d`.

Review the diff with `git diff infra/docker-compose.yml` after this runs,
before committing/keeping it on the prod host's checkout.
"@
    if (-not (Confirm-Step 'Proceed with Section 2 (loopback bind Postgres/Redis)?')) { return }

    $content = Get-Content -Raw -Path $ComposeFile
    if ($content -match '127\.0\.0\.1:5432:5432' -and $content -match '127\.0\.0\.1:6379:6379') {
        Write-Host 'Already bound to loopback for both services. Nothing to do.' -ForegroundColor Green
        return
    }
    $content = $content -replace '(\s+)- "5432:5432"', '$1- "127.0.0.1:5432:5432"'
    $content = $content -replace '(\s+)- "6379:6379"', '$1- "127.0.0.1:6379:6379"'
    Set-Content -Path $ComposeFile -Value $content -NoNewline
    Write-Host 'Edited. Diff:' -ForegroundColor Green
    git -C $RepoRoot diff -- infra/docker-compose.yml

    Write-Host 'Apply with: ' -NoNewline
    Write-Host "& '$DockerExe' -c desktop-linux compose -p infra -f '$ComposeFile' --env-file '$EnvFile' --project-directory '$(Join-Path $RepoRoot "infra")' up -d" -ForegroundColor Cyan
    Write-Host 'Optional extra step (only if LAN access to admin/API/media/miniapp is not used): apply the same 127.0.0.1: prefix to backend (8000), admin (3000), media-server (9000), miniapp (5175) ports in the same file.' -ForegroundColor Yellow
}

# ============================================================================
# SECTION 3 -- Windows firewall (docs/server-hardening-runbook.md #2)
# ============================================================================
function Invoke-WindowsFirewallLockdown {
    Write-Host @"
This will:
  1. Show current DefaultInboundAction per profile, and set it to Block on
     Domain/Private/Public if it isn't already.
  2. List enabled inbound Allow rules, flagging any covering ports
     5432, 6379, 8000, 3000, 9000, 5175, 3389 (RDP), 22 (SSH) -- the tunnel
     is outbound-only, so none of these need to be reachable from outside.
  3. Ask, per flagged rule, whether to disable it.
"@
    if (-not (Confirm-Step 'Proceed with Section 3 (firewall lockdown)?')) { return }
    if (-not (Test-IsAdministrator)) { Write-Host 'Not running as Administrator -- firewall cmdlets will likely fail.' -ForegroundColor Red }

    Get-NetFirewallProfile | Select-Object Name, DefaultInboundAction | Format-Table
    Set-NetFirewallProfile -Profile Domain,Private,Public -DefaultInboundAction Block
    Write-Host 'Default inbound action set to Block on all profiles.' -ForegroundColor Green

    $watchPorts = @('5432','6379','8000','3000','9000','5175','3389','22')
    $rules = Get-NetFirewallRule -Direction Inbound -Enabled True | Where-Object { $_.Action -eq 'Allow' }
    foreach ($rule in $rules) {
        $ports = ($rule | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue).LocalPort -join ','
        if ($watchPorts | Where-Object { $ports -match $_ }) {
            Write-Host "Flagged rule: '$($rule.DisplayName)' (profile: $($rule.Profile), ports: $ports)" -ForegroundColor Yellow
            if ((Read-Host 'Disable this rule? (y/N)') -eq 'y') {
                Disable-NetFirewallRule -Name $rule.Name
                Write-Host '  Disabled.' -ForegroundColor Green
            }
        }
    }
}

# ============================================================================
# SECTION 4 -- Remote access: SSH / RDP (docs/server-hardening-runbook.md #1)
# ============================================================================
function Invoke-RemoteAccessHardening {
    param(
        # Only used for the RDP-restriction branch below.
        [string]$TrustedAdminIP = '<CHANGE_ME_IP>'
    )
    Write-Host @"
Two independent options -- pick the one that matches reality on this box:
  A) SSH not in use (recommended, tunnel is outbound-only): disable the
     OpenSSH Server optional feature entirely.
  B) SSH in use: this function will NOT touch sshd_config for you (that's a
     one-line edit, not worth scripting) -- see docs/server-hardening-runbook.md
     Section 1 Option B for the exact settings (PasswordAuthentication no,
     PubkeyAuthentication yes, PermitRootLogin no).
Also offers to add a Firewall rule restricting RDP (3389) to a single
trusted source IP, if RDP is used for admin access.
"@
    if (-not (Confirm-Step 'Proceed with Section 4 (remote access hardening)?')) { return }
    if (-not (Test-IsAdministrator)) { Write-Host 'Not running as Administrator -- these commands will likely fail.' -ForegroundColor Red }

    if ((Read-Host 'Is SSH in active use on this box? (y/N)') -ne 'y') {
        Get-WindowsCapability -Online -Name OpenSSH.Server* | Remove-WindowsCapability -Online
        Stop-Service sshd -Confirm:$false -ErrorAction SilentlyContinue
        Set-Service sshd -StartupType Disabled -ErrorAction SilentlyContinue
        Write-Host 'OpenSSH Server disabled.' -ForegroundColor Green
    } else {
        Write-Host 'Leaving SSH alone -- go edit C:\ProgramData\ssh\sshd_config by hand per the runbook, then Restart-Service sshd.' -ForegroundColor Yellow
    }

    if ((Read-Host 'Is RDP used for admin access to this box? (y/N)') -eq 'y') {
        if ($TrustedAdminIP -eq '<CHANGE_ME_IP>') {
            Write-Host 'Pass -TrustedAdminIP with a real IP/CIDR before restricting RDP.' -ForegroundColor Red
        } else {
            New-NetFirewallRule -DisplayName 'RDP from trusted admin IP only' -Direction Inbound `
                -LocalPort 3389 -Protocol TCP -RemoteAddress $TrustedAdminIP -Action Allow
            Write-Host "RDP restricted to $TrustedAdminIP. Remember to remove/tighten the default 'Remote Desktop' built-in rules so they don't also allow Any." -ForegroundColor Green
        }
    }
}

# ============================================================================
# SECTION 5 -- Account lockout policy / IPBan (docs/server-hardening-runbook.md #4)
# ============================================================================
function Invoke-AccountLockoutPolicy {
    Write-Host @"
Windows has no fail2ban, but Account Lockout Policy is the built-in
equivalent for brute-force PASSWORD guessing (not IP banning): after N bad
attempts, the account locks for a duration. Combined with disabling password
auth (Section 4), there's no password to brute-force anyway.

This will run:
  net accounts /lockoutthreshold:5 /lockoutduration:30 /lockoutwindow:30
(5 bad attempts, 30 minute lockout/window -- adjust if you want different
numbers).

If SSH/RDP must stay reachable from more than one trusted IP, consider
installing IPBan (https://github.com/DigitalRuby/IPBan) separately -- it
actually bans by IP by watching the Security event log. This script does
NOT install third-party software; that's a manual step if you want it.
"@
    if (-not (Confirm-Step 'Proceed with Section 5 (account lockout policy)?')) { return }
    if (-not (Test-IsAdministrator)) { Write-Host 'Not running as Administrator -- net accounts will likely fail.' -ForegroundColor Red }

    net accounts /lockoutthreshold:5 /lockoutduration:30 /lockoutwindow:30
    net accounts
}

# ============================================================================
# SECTION 6 -- Automatic Windows updates (docs/server-hardening-runbook.md #5)
# ============================================================================
function Invoke-WindowsAutoUpdates {
    Write-Host @"
This only PRINTS the checklist -- Windows Update settings + Docker Desktop's
auto-update toggle are both GUI-only (Settings -> Windows Update -> Advanced
options; Docker Desktop -> Settings -> Software Updates), nothing safe to
script here. It also reminds you that postgres:16-alpine / redis:7-alpine
are pulled straight from Docker Hub and are NEVER auto-refreshed by
deploy.ps1 -- re-pull them by hand periodically:

  & '$DockerExe' -c desktop-linux pull postgres:16-alpine
  & '$DockerExe' -c desktop-linux pull redis:7-alpine
  & '$DockerExe' -c desktop-linux compose -p infra -f '$ComposeFile' --env-file '$EnvFile' --project-directory '$(Join-Path $RepoRoot "infra")' up -d postgres redis
"@
    if (-not (Confirm-Step 'Show Section 6 checklist?')) { return }
    Write-Host @'
  [ ] Windows Update -> Advanced options -> "Receive updates for other
      Microsoft products when you update Windows" -> On.
  [ ] Automatic restart enabled, with active hours set to avoid a reboot
      mid-deploy.
  [ ] Docker Desktop -> Settings -> Software Updates -> "Automatically
      check for updates" -> On.
  [ ] Calendar reminder (monthly) to manually re-pull postgres:16-alpine and
      redis:7-alpine (see commands above) -- Docker Hub is blocked without a
      VPN on this machine per project memory, so this cannot be automated
      via deploy.ps1 right now.
'@
}

# ============================================================================
# SECTION 7 -- Encrypted offsite Postgres backup (docs/server-hardening-runbook.md #7)
# ============================================================================
function Invoke-EncryptedPostgresBackup {
    param(
        [string]$PostgresContainer = 'infra-postgres-1',
        [string]$PgUser = $env:POSTGRES_USER,
        [string]$PgDb   = $env:POSTGRES_DB,
        [string]$BackupDir = (Join-Path $RepoRoot 'backups'),
        # Never a real passphrase in this file -- pass it at the prompt or via -Passphrase.
        [string]$Passphrase = '<CHANGE_ME>',
        [string]$AgePublicKey = ''
    )
    Write-Host @"
This will:
  1. pg_dump INSIDE the container to a temp file (NOT through a PowerShell
     redirect -- that's a known gotcha that mangles UTF-8/Cyrillic text),
     then `docker cp` the bytes out untouched, then delete the temp file
     inside the container.
  2. Encrypt the dump with `age` if installed (recommended, needs
     -AgePublicKey), otherwise `openssl aes-256-cbc` with -Passphrase.
  3. Print the retention suggestion (7 daily / 4 weekly / 3 monthly) and the
     `schtasks` command to schedule this nightly -- it does NOT register the
     scheduled task itself; review the command before running it.
Offsite copy (to somewhere that isn't this machine) is a manual step this
script does not perform.
"@
    if (-not (Confirm-Step 'Proceed with Section 7 (encrypted Postgres backup)?')) { return }

    if (-not $PgUser -or -not $PgDb) {
        Write-Host 'Pass -PgUser / -PgDb explicitly, or ensure POSTGRES_USER / POSTGRES_DB are set in this shell.' -ForegroundColor Red
        return
    }
    if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir | Out-Null }

    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $dumpName = "noxx-$stamp.dump"
    & $DockerExe exec $PostgresContainer pg_dump -U $PgUser -f "/tmp/$dumpName" $PgDb
    & $DockerExe cp "${PostgresContainer}:/tmp/$dumpName" (Join-Path $BackupDir $dumpName)
    & $DockerExe exec $PostgresContainer rm "/tmp/$dumpName"
    Write-Host "Dump written to $(Join-Path $BackupDir $dumpName)" -ForegroundColor Green

    $dumpPath = Join-Path $BackupDir $dumpName
    $ageCmd = Get-Command age -ErrorAction SilentlyContinue
    if ($ageCmd -and $AgePublicKey) {
        & age -r $AgePublicKey -o "$dumpPath.age" $dumpPath
        Remove-Item $dumpPath
        Write-Host "Encrypted with age -> $dumpPath.age" -ForegroundColor Green
    } elseif ($Passphrase -ne '<CHANGE_ME>') {
        & openssl enc -aes-256-cbc -pbkdf2 -salt -in $dumpPath -out "$dumpPath.enc" -pass "pass:$Passphrase"
        Remove-Item $dumpPath
        Write-Host "Encrypted with openssl -> $dumpPath.enc" -ForegroundColor Green
    } else {
        Write-Host "Not encrypted -- pass -AgePublicKey (with age installed) or a real -Passphrase, then encrypt $dumpPath manually before it leaves this machine." -ForegroundColor Red
        return
    }

    Write-Host @"
Retention suggestion: keep last 7 daily + last 4 weekly (e.g. every Sunday)
+ last 3 monthly, prune older on the same schedule.

To schedule nightly (review this before running -- it does not run here):
  schtasks /create /tn "NoxX Postgres Backup" /tr "pwsh -ExecutionPolicy Bypass -File $PSCommandPath -Command Invoke-EncryptedPostgresBackup" /sc daily /st 03:00

Copy the encrypted file somewhere that isn't this machine (separate cloud
bucket, different R2 bucket than the media one, or a second physical
location) -- that step is manual and outside this script.
"@
}

# ============================================================================
# SECTION 8 -- Secret rotation checklist (docs/server-hardening-runbook.md #8)
# ============================================================================
# Prints WHERE each secret lives. Does not generate or print any real value.
function Show-SecretRotationChecklist {
    Write-Host @'
Secret rotation checklist -- names and locations only, no values here or
anywhere else. Generate new random values yourself (e.g. `openssl rand -hex
32` for the JWT/internal secrets), update prod .env, restart the affected
container(s), then confirm the OLD value no longer works.

  [ ] JWT_SECRET              -- prod .env                 (signs miniapp user JWTs)
  [ ] ADMIN_JWT_SECRET        -- prod .env                 (signs admin-panel JWTs)
  [ ] ADMIN_DEFAULT_PASSWORD  -- prod .env (seed only)      (also change the actual admin
                                                              account password via admin UI/DB)
  [ ] POSTGRES_PASSWORD       -- prod .env                  (also: ALTER USER <user> WITH
                                                              PASSWORD '<new>'; inside postgres)
  [ ] INTERNAL_API_SECRET     -- prod .env (backend + bot)  (bot<->backend internal API)
  [ ] ORBCHAIN_WEBHOOK_SECRET -- prod .env                  (also re-register with OrbChain
                                                              if their config stores it)
  [ ] CLOUDFLARE_TUNNEL_TOKEN -- prod .env                  (rotate via Cloudflare Zero Trust
                                                              -> Tunnels -> noxx-prod)
  [ ] R2_SECRET_ACCESS_KEY    -- prod .env                  (rotate via R2 -> Manage API
                                                              Tokens, scoped to one bucket)
  [ ] BOT_TOKEN                -- prod .env                 (rotate via @BotFather /revoke;
                                                              only one process can hold it)

Never paste real values from prod .env into a chat/assistant session.
'@
}

# ============================================================================
# SECTION 9 -- Cloudflare R2 verify (docs/server-hardening-runbook.md #6)
# ============================================================================
# Manual dashboard check -- this only reminds, it makes no network calls.
function Show-R2VerifyReminder {
    Write-Host @'
R2 public-dev-URL has already been verified DISABLED for the media bucket
(confirmed live, per operator). This is a reminder to re-check periodically,
not an automated check:

  [ ] Cloudflare dashboard -> R2 -> media bucket -> Settings -> Public
      Access -> confirm the default r2.dev URL is still Disabled.
  [ ] Only the custom domain (media.noxxshop.com) serves objects.
  [ ] No Worker/route on this bucket implements S3 ListObjects/directory
      browsing.
  [ ] R2 API token used by the backend (R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY)
      is scoped to the one bucket, Object Read & Write only -- not
      account-wide Admin.
'@
}

Write-Host @"
Loaded prod-hardening.ps1 functions. Nothing has been executed yet. Call one
function at a time, e.g.:
  Invoke-DbLeastPrivilegeRole
  Invoke-PostgresRedisLoopbackBind
  Invoke-WindowsFirewallLockdown
  Invoke-RemoteAccessHardening
  Invoke-AccountLockoutPolicy
  Invoke-WindowsAutoUpdates
  Invoke-EncryptedPostgresBackup
  Show-SecretRotationChecklist
  Show-R2VerifyReminder
"@
