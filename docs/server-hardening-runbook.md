# Prod host hardening runbook

A consolidated runnable version of the steps below lives in `infra/prod-hardening.ps1`.

A checklist the operator runs **by hand** on the machine that actually runs
`infra/docker-compose.yml` in production. Nothing here was run against prod — this is a plan to
execute, not a script that already executed.

## What prod actually is (read this first)

Every deploy artifact in this repo (`run.ps1`, `deploy.ps1`, project memory) points to
**Windows + Docker Desktop**, driven from PowerShell — there is no Linux server anywhere in this
stack's deploy path:

- `run.ps1` calls `C:\Program Files\Docker\Docker\resources\bin\docker.exe -c desktop-linux`.
- `deploy.ps1` runs from Windows Task Scheduler, does `git merge --ff-only`, `docker ... pull`,
  `docker ... up -d --no-build`, and health-checks `http://localhost:8000/health`.
- Project memory (`telegram-bot0video-dev-prod-split`) confirms prod has moved between a Windows
  laptop and a Windows PC over time, but always the same tooling: Docker Desktop on Windows,
  images built in GitHub CI (`ghcr.io`) and pulled, never built on the prod box itself.

**This runbook assumes a Windows 10/11 host running Docker Desktop.** Sections below say clearly
where a step is a Windows-native action (firewall, updates, scheduled tasks) vs. a step that runs
*inside* a Linux container (Postgres, cloudflared — those images are `alpine`/Debian-based Linux,
even though the host OS is Windows). Two sections (fail2ban, SSH) are classically Linux tools; each
has a Windows-appropriate substitute noted, since the honest answer for this box is "these don't
apply the way they would on a Linux VPS."

Do not run any command below against prod without knowing which machine is currently prod — check
`deploy.ps1 -Status` or ask the operator first.

---

## 1. Remote access (SSH) — key-only, no passwords, no admin/root

Project memory records that SSH to the prod machine has been attempted before and is currently
**parked/not working** (`ssh_dispatch_run_fatal: Unknown error [preauth]` on Windows' OpenSSH
Server, `telegram-bot0video-dev-prod-split`). Two honest options:

**Option A (recommended) — no SSH at all.** The whole point of the Cloudflare named tunnel
(`noxx-prod`) is that it's an *outbound-only* connection — nothing needs to reach in. If the
operator manages this box physically (keyboard/monitor) or via a screen-share tool, there's no
need to run an SSH server that's just one more thing to harden and patch. Uninstall/disable the
Windows optional feature "OpenSSH Server" if it's not actually in use:

```powershell
Get-WindowsCapability -Online -Name OpenSSH.Server* | Remove-WindowsCapability -Online
Stop-Service sshd -Confirm:$false -ErrorAction SilentlyContinue
Set-Service sshd -StartupType Disabled -ErrorAction SilentlyContinue
```

**Option B — if SSH is needed**, once it's actually working, harden `C:\ProgramData\ssh\sshd_config`:

```
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
# Windows has no "root", but if an Administrator-group account has an authorized key,
# treat it the same way: don't allow that account to accept a password over SSH either.
```

Restart the service after editing: `Restart-Service sshd`.

Either way: never leave `PasswordAuthentication yes` (or the Windows equivalent — RDP with a
password and no network-level restriction) reachable from outside the LAN. If Remote Desktop is
used instead of SSH for admin access, restrict it with Windows Firewall to a specific trusted
source IP or VPN range, never "Any".

- [ ] Decide: SSH in use or not. If not, disable the OpenSSH Server feature (Option A).
- [ ] If in use, confirm `PasswordAuthentication no` in `sshd_config` and key-only login works.

## 2. Firewall — ideally zero inbound ports

With the Cloudflare named tunnel, the `cloudflared` container makes an **outbound** connection to
Cloudflare's edge and routes `app.noxxshop.com` / `api.noxxshop.com` / `admin.noxxshop.com` traffic
over that tunnel to the other containers by their Docker service name (`miniapp:80`, `backend:8000`,
`admin:3000` — confirmed in project memory). **No inbound port forwarding is required for the
site to work at all.**

Target state: Windows Defender Firewall blocks all unsolicited inbound connections, full stop.

```powershell
# Confirm default inbound action is Block for all profiles
Get-NetFirewallProfile | Select-Object Name, DefaultInboundAction

# If anything is set to Allow, fix it:
Set-NetFirewallProfile -Profile Domain,Private,Public -DefaultInboundAction Block
```

Check for any inbound rules that were added for local debugging (e.g. someone opened 8000/3000/5432
for LAN access) and remove them — local dev access to `run.ps1` services should go through
`http://localhost:...` from the same machine, not the network:

```powershell
Get-NetFirewallRule -Direction Inbound -Enabled True | Where-Object { $_.Action -eq 'Allow' } |
  Select-Object DisplayName, Profile
```

- [ ] Default inbound action is Block on all three profiles.
- [ ] No stray inbound Allow rules for 3389 (RDP), 22 (SSH), 5432, 6379, 8000, 3000, 9000, 5175
      unless deliberately scoped to a specific trusted source IP.

## 3. Postgres / Redis not exposed publicly

`infra/docker-compose.yml` currently publishes both to every network interface on the host:

```yaml
  postgres:
    ports:
      - "5432:5432"
  redis:
    ports:
      - "6379:6379"
```

Docker Desktop on Windows binds `"5432:5432"` to `0.0.0.0` by default — reachable from the LAN (and
from the internet if anything ever port-forwards it), not just `localhost`. Neither service needs
to be reachable from outside the Docker network: `backend` reaches both over the compose network by
service name (`postgres`, `redis`), and `cloudflared` never talks to them directly.

Fix — bind to loopback only, still allows `run.ps1`/local debugging via `127.0.0.1`:

```yaml
  postgres:
    ports:
      - "127.0.0.1:5432:5432"
  redis:
    ports:
      - "127.0.0.1:6379:6379"
```

The same reasoning applies to `backend` (`8000`), `admin` (`3000`), `media-server` (`9000`), and
`miniapp` (`5175`) — the tunnel doesn't need any of these published to the host network either,
only the internal compose network. Binding all five to `127.0.0.1:<port>:<port>` is a good extra
step if LAN access to the admin/API from another device on the network isn't actually used; skip it
if someone deliberately relies on hitting `http://<lan-ip>:3000` from a phone on the same Wi-Fi.

After editing, apply with the existing tooling (don't run this against prod without confirming it's
actually the prod machine first):

```powershell
docker -c desktop-linux compose -p infra -f infra/docker-compose.yml --env-file .env --project-directory infra up -d
```

- [ ] `postgres` port binding changed to `127.0.0.1:5432:5432`.
- [ ] `redis` port binding changed to `127.0.0.1:6379:6379`.
- [ ] (Optional) same treatment for `backend`/`admin`/`media-server`/`miniapp` host ports if LAN
      access to them isn't needed.
- [ ] `docker ps` / `netstat -ano | findstr 5432` confirms it's no longer bound to `0.0.0.0`.

## 4. fail2ban for sshd — Linux tool, doesn't apply as-is on Windows

fail2ban is Linux-only (it parses `/var/log/auth.log` or systemd journal entries that Windows'
`sshd` doesn't produce in the same form). Since Section 1 already recommends disabling SSH entirely
if it's not in active use, this mostly becomes moot. If SSH genuinely stays enabled on this Windows
box:

- Windows equivalent: **IPBan** (open-source, Windows-native "ban an IP after N failed logins",
  watches the Windows Security event log for both RDP and OpenSSH failed-logon events) is the
  closest analog — install it if SSH/RDP must stay reachable from anywhere beyond a single trusted
  IP.
- Cheaper alternative that needs no new software: Windows' built-in **Account Lockout Policy**
  (`secpol.msc` → Account Policies → Account Lockout Policy) locks an account out after N bad
  password attempts — doesn't ban the IP, but stops brute-force password guessing outright, and
  combined with `PasswordAuthentication no` (Section 1) there's no password to brute-force anyway.

- [ ] Decide: is SSH/RDP reachable from outside a single trusted IP? If yes, install IPBan or
      equivalent. If no (recommended), skip this section.

## 5. Automatic security updates

Two separate things need to stay patched: Windows itself, and the Linux base images inside
containers.

**Windows:** Settings → Windows Update → Advanced options:
- "Receive updates for other Microsoft products when you update Windows" → On.
- Keep automatic restart enabled (schedule active hours to avoid restarting mid-deploy).

**Docker Desktop:** check Settings → Software Updates → keep "Automatically check for updates" on.

**Container base images** — these are *not* automatically refreshed by the current deploy pipeline.
`deploy.ps1` only pulls the five app images built in CI (`backend`, `bot`, `media-server`, `admin`,
`miniapp`); `postgres:16-alpine` and `redis:7-alpine` come straight from Docker Hub and are **never
re-pulled** by the automated deploy (a documented gotcha: Docker Hub is blocked without a VPN on
this machine). Periodically, by hand:

```powershell
docker -c desktop-linux pull postgres:16-alpine
docker -c desktop-linux pull redis:7-alpine
docker -c desktop-linux compose -p infra -f infra/docker-compose.yml --env-file .env --project-directory infra up -d postgres redis
```

- [ ] Windows Update set to automatic, including other Microsoft products.
- [ ] Docker Desktop auto-update on.
- [ ] Calendar reminder (monthly) to manually re-pull `postgres:16-alpine` / `redis:7-alpine`.

## 6. Cloudflare R2 — no public listing, scoped tokens

**Disable bucket listing / unscoped public access:**
1. Cloudflare dashboard → R2 → the media bucket → **Settings** → **Public Access**.
2. Confirm the bucket's default `r2.dev` public URL is **Disabled** — only the connected custom
   domain (`media.noxxshop.com`) should serve objects.
3. Don't attach a Worker or route that implements S3 `ListObjects`/directory browsing on this
   bucket — object keys should only be reachable if the exact key is known (as returned by the API).

**Scoped API tokens** (used by the backend via `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` in `.env`):
1. R2 → **Manage R2 API Tokens** → **Create API Token**.
2. Permissions: **Object Read & Write**, scoped to **this bucket only** — not "Admin Read & Write"
   and not account-wide.
3. If a broader-scoped token was used when this was first set up, rotate it (create the new scoped
   token, update `.env`, restart `backend`, then delete the old token in the R2 dashboard).

- [ ] `r2.dev` public URL disabled for the media bucket.
- [ ] No Worker/route exposes object listing.
- [ ] R2 API token used by the backend is scoped to the one bucket, not account-wide.

## 7. Encrypted offsite backups of Postgres

**Dump** (the memory file `telegram-bot0video-dev-prod-split` documents a real gotcha here: piping
`docker exec ... pg_dump` straight through a PowerShell redirect mangles UTF-8/Cyrillic text twice —
dump to a file *inside* the container first, then `docker cp` the bytes out untouched):

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
docker exec infra-postgres-1 pg_dump -U video_shop -f "/tmp/noxx-$stamp.dump" video_shop
docker cp "infra-postgres-1:/tmp/noxx-$stamp.dump" ".\backups\noxx-$stamp.dump"
docker exec infra-postgres-1 rm "/tmp/noxx-$stamp.dump"
```

**Encrypt** before it leaves the machine — either `age` (simpler, modern) or `openssl`:

```powershell
# age (recommended): generate a keypair once (age-keygen -o backup-key.txt), keep the
# public key here and the private key ONLY offsite/in a password manager.
age -r <AGE_PUBLIC_KEY> -o ".\backups\noxx-$stamp.dump.age" ".\backups\noxx-$stamp.dump"
Remove-Item ".\backups\noxx-$stamp.dump"

# or openssl, if age isn't installed:
openssl enc -aes-256-cbc -pbkdf2 -salt -in ".\backups\noxx-$stamp.dump" -out ".\backups\noxx-$stamp.dump.enc" -pass pass:<CHANGE_ME_PASSPHRASE>
Remove-Item ".\backups\noxx-$stamp.dump"
```

Never commit the passphrase/private key to this repo or paste it into chat — store it in a
password manager, separate from the backup files themselves.

**Schedule** it the same way `deploy.ps1` is already scheduled (Task Scheduler), e.g. nightly:

```powershell
schtasks /create /tn "NoxX Postgres Backup" /tr "powershell -ExecutionPolicy Bypass -File C:\path\to\backup.ps1" /sc daily /st 03:00
```

**Offsite:** copy the encrypted file to somewhere that isn't this machine — a separate cloud bucket
(a *different* R2 bucket than the media one, or any other provider), or a second physical location.
Encrypted-at-rest means it's safe to hand to a generic cloud storage provider.

**Retention suggestion:** keep the last 7 daily backups + the last 4 weekly (e.g. every Sunday) +
the last 3 monthly — prune older ones on the same schedule so storage doesn't grow unbounded.

- [ ] Backup script written using the `pg_dump` → `docker cp` sequence above (not a PowerShell
      redirect).
- [ ] Dumps encrypted with `age` or `openssl` before leaving the container/host.
- [ ] Scheduled via Task Scheduler, daily.
- [ ] Encrypted backups copied to a location that isn't this machine.
- [ ] Retention/pruning in place (7 daily / 4 weekly / 3 monthly, or similar).

## 8. Rotate default/initial secrets

`apps/backend/app/core/config.py` already refuses to start with placeholder secrets outside
`APP_ENV=development` (`jwt_secret`, `admin_jwt_secret`, `internal_api_secret` — checked against
known placeholder strings). That guard doesn't cover every secret below, so rotate all of these by
hand. **Names only — do not open or paste the actual prod `.env` anywhere, including in chat with
an assistant.**

| Secret (env var name) | Lives in | Notes |
|---|---|---|
| `JWT_SECRET` | prod `.env` | Signs miniapp user JWTs |
| `ADMIN_JWT_SECRET` | prod `.env` | Signs admin-panel JWTs |
| `ADMIN_DEFAULT_PASSWORD` | prod `.env`, only read at first-admin seed | Change the admin's actual password via the admin UI/DB afterward too — this env var only seeds the first login |
| `POSTGRES_PASSWORD` | prod `.env` | Also update inside the running Postgres role if rotating post-deploy: `ALTER USER video_shop WITH PASSWORD '<CHANGE_ME>';` |
| `INTERNAL_API_SECRET` | prod `.env` (shared by `backend` and `bot`) | Guards the bot↔backend internal API |
| `ORBCHAIN_WEBHOOK_SECRET` | prod `.env` | Also re-register the new value with OrbChain if their webhook config stores it independently |
| `CLOUDFLARE_TUNNEL_TOKEN` | prod `.env` | Rotate via Cloudflare Zero Trust → Tunnels → `noxx-prod` if it's ever been exposed |
| `R2_SECRET_ACCESS_KEY` | prod `.env` | Rotate via R2 → Manage API Tokens (see Section 6) |
| `BOT_TOKEN` | prod `.env` | Rotate via @BotFather `/revoke` — remember only one process can hold a Telegram bot token at a time (409 conflicts documented in project memory) |
| `VITE_SENTRY_DSN` | GitHub repo secret + prod `.env` build arg | Public-by-design, not a real secret — rotating isn't security-critical, just for hygiene if leaked alongside something else |

For each: generate a new random value (`openssl rand -hex 32` works for the JWT/internal secrets),
update prod `.env`, redeploy/restart the affected container(s), then confirm the old value no
longer works before considering it done.

- [ ] `JWT_SECRET` rotated.
- [ ] `ADMIN_JWT_SECRET` rotated.
- [ ] `ADMIN_DEFAULT_PASSWORD` changed (env var + actual admin account password).
- [ ] `POSTGRES_PASSWORD` rotated (env var + `ALTER USER`).
- [ ] `INTERNAL_API_SECRET` rotated.
- [ ] `ORBCHAIN_WEBHOOK_SECRET` rotated (and re-registered with OrbChain if needed).
- [ ] `CLOUDFLARE_TUNNEL_TOKEN` rotated if there's any reason to think it leaked.
- [ ] `R2_SECRET_ACCESS_KEY` rotated to a freshly scoped token.
- [ ] `BOT_TOKEN` rotated via BotFather if there's any reason to think it leaked.

---

## One-evening summary

Realistic order to knock this out in one sitting: **2 → 3 → 6 → 8 → 7 → 5**, then decide on
**1 → 4** together (they're linked — no SSH means no fail2ban needed). Sections 2, 3, and 6 are pure
configuration with no downtime. Section 8 (secret rotation) needs a restart of the affected
containers, so do it during a moment you don't mind a few seconds of API downtime. Section 7
(backups) is the one most worth not skipping even if time runs out.
