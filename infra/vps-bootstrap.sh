#!/usr/bin/env bash
# One-time VPS bootstrap for noxx-shop. Run as root on a fresh Ubuntu box
# (paste into the provider's web Terminal). Idempotent — safe to re-run.
# Creates a non-root 'noxx' user with the deploy key, installs Docker,
# adds swap + firewall + fail2ban + unattended upgrades.
# It does NOT disable password/root SSH — that happens only after key
# login is verified, to avoid locking ourselves out.
set -euo pipefail

DEPLOY_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEHsm9gIo0IHMVT/QhJZpUZDm6D7Rh6pvx6WE28xGdKg claude-noxx-prod"

echo "[1/6] user noxx"
id noxx &>/dev/null || adduser --disabled-password --gecos "" noxx
usermod -aG sudo noxx
echo "noxx ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/noxx && chmod 440 /etc/sudoers.d/noxx
install -d -m 700 -o noxx -g noxx /home/noxx/.ssh
grep -qF "$DEPLOY_KEY" /home/noxx/.ssh/authorized_keys 2>/dev/null || echo "$DEPLOY_KEY" >> /home/noxx/.ssh/authorized_keys
chmod 600 /home/noxx/.ssh/authorized_keys && chown noxx:noxx /home/noxx/.ssh/authorized_keys

echo "[2/6] swap 2G"
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "[3/6] docker"
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi
usermod -aG docker noxx
systemctl enable --now docker

echo "[4/6] firewall (only SSH in; tunnel is outbound)"
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y ufw fail2ban unattended-upgrades
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw --force enable

echo "[5/6] fail2ban + auto-updates"
systemctl enable --now fail2ban
dpkg-reconfigure -f noninteractive unattended-upgrades || true

echo "[6/6] done"
echo "OK: noxx user ready, docker $(docker --version), swap on, ufw active."
echo "Next: verify key login from the PC, then harden sshd."
