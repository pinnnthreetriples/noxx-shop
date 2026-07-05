# Postgres backup: pg_dump (custom format, compressed) -> backups\noxx_<date>.dump
# Restore: docker exec -i infra-postgres-1 sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean' < file.dump
# Schedule daily via Task Scheduler:
#   powershell -NoProfile -File C:\Users\user\Documents\telegram-bot0Video\scripts\backup-db.ps1
param(
    [string]$BackupDir = (Join-Path $PSScriptRoot '..\backups'),
    [int]$Keep = 14
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $BackupDir | Out-Null
$stamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$file = Join-Path $BackupDir "noxx_$stamp.dump"

docker.exe -c desktop-linux exec infra-postgres-1 sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F c -f /tmp/backup.dump'
docker.exe -c desktop-linux cp infra-postgres-1:/tmp/backup.dump $file
docker.exe -c desktop-linux exec infra-postgres-1 rm -f /tmp/backup.dump

# rotation: keep the newest $Keep dumps
Get-ChildItem $BackupDir -Filter 'noxx_*.dump' | Sort-Object Name -Descending | Select-Object -Skip $Keep | Remove-Item -Confirm:$false

Write-Host "Backup written: $file ($([math]::Round((Get-Item $file).Length / 1KB)) KB)"
