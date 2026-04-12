#!/usr/bin/env bash
# bootstrap-server.sh -- One-time server setup for Ubuntu 24.04 VPS
#
# Run as root:  bash bootstrap-server.sh
#
# This script:
#   - Updates the system
#   - Installs base packages (git, curl, dnsutils, python3, etc.)
#   - Installs Docker Engine and Compose plugin
#   - Installs fail2ban and configures it for SSH
#   - Installs unattended-upgrades for automatic security patches
#   - Configures UFW firewall (SSH, HTTP, HTTPS)
#   - Creates a swap file (if none exists)
#   - Creates the deploy user (if not exists)
#
# This script does NOT:
#   - Modify SSH configuration (too risky to automate -- do it manually)
#   - Copy SSH keys (must be done from your local machine)
#   - Create .env or Caddyfile (environment-specific)
#
# After running this script, follow the manual steps in deployment.md:
#   Path A (SSH key login):
#     1. Copy your SSH key to the deploy user
#     2. Verify key-based login in a second terminal
#     3. Harden SSH (disable password auth and root login)
#   Path B (password login only):
#     1. Verify password login as deploy
#     2. Harden SSH (disable root login, keep password auth)
set -euo pipefail

# --- Configuration ---
DEPLOY_USER="deploy"
SWAP_SIZE="2G"

# --- Pre-flight checks ---
if [[ "$(id -u)" -ne 0 ]]; then
    echo "ERROR: This script must be run as root."
    exit 1
fi

echo "=== ACB Large Print Toolkit -- Server Bootstrap ==="
echo ""

# --- Step 1: Update and full-upgrade system ---
echo "--- Updating and upgrading system packages ---"
apt update
DEBIAN_FRONTEND=noninteractive apt-get \
    -o Dpkg::Options::="--force-confdef" \
    -o Dpkg::Options::="--force-confold" \
    -y full-upgrade
apt-get -y autoremove --purge
apt-get -y autoclean

# --- Step 2: Install base packages ---
echo "--- Installing base packages ---"
apt install -y \
    git \
    curl \
    ca-certificates \
    unzip \
    dnsutils \
    python3 \
    software-properties-common \
    gnupg \
    lsb-release

# --- Step 3: Install Docker ---
echo "--- Installing Docker Engine and Compose plugin ---"
install -m 0755 -d /etc/apt/keyrings

if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
fi

if [[ ! -f /etc/apt/sources.list.d/docker.list ]]; then
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
fi

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker

echo "--- Docker installed: $(docker --version) ---"
echo "--- Compose installed: $(docker compose version) ---"

# --- Step 4: Install and configure fail2ban ---
echo "--- Installing fail2ban ---"
apt install -y fail2ban

tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# --- Step 5: Install unattended-upgrades ---
echo "--- Enabling automatic security updates ---"
apt install -y unattended-upgrades
echo 'Unattended-Upgrade::Automatic-Reboot "false";' > /etc/apt/apt.conf.d/51auto-reboot-off
dpkg-reconfigure -plow unattended-upgrades

# --- Step 6: Configure UFW ---
echo "--- Configuring firewall ---"
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
echo "--- Firewall status ---"
ufw status verbose

# --- Step 7: Create swap file ---
if [[ ! -f /swapfile ]]; then
    echo "--- Creating ${SWAP_SIZE} swap file ---"
    fallocate -l "$SWAP_SIZE" /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    if ! grep -q '/swapfile' /etc/fstab; then
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
    echo "--- Swap enabled ---"
else
    echo "--- Swap file already exists, skipping ---"
fi

# --- Step 8: Create deploy user ---
if id "$DEPLOY_USER" &>/dev/null; then
    echo "--- User '$DEPLOY_USER' already exists ---"
else
    echo "--- Creating user '$DEPLOY_USER' ---"
    adduser --disabled-password --gecos "" "$DEPLOY_USER"
    usermod -aG sudo "$DEPLOY_USER"
    echo "--- Set a password for $DEPLOY_USER ---"
    passwd "$DEPLOY_USER"
fi

usermod -aG docker "$DEPLOY_USER"

# --- Step 9: Create directory structure ---
echo "--- Creating directories ---"
sudo -u "$DEPLOY_USER" mkdir -p "/home/$DEPLOY_USER/app"
sudo -u "$DEPLOY_USER" mkdir -p "/home/$DEPLOY_USER/backups"

# --- Done ---
echo ""
echo "=== Bootstrap complete ==="
echo ""
echo "NEXT STEPS (do these manually -- see deployment.md):"
echo ""
echo "  PATH A (SSH key login -- recommended):"
echo "  1. From your LOCAL machine, copy your SSH key:"
echo "       ssh-copy-id ${DEPLOY_USER}@$(hostname -I | awk '{print $1}')"
echo "  2. In a SECOND terminal, verify key-based login:"
echo "       ssh ${DEPLOY_USER}@$(hostname -I | awk '{print $1}')"
echo "  3. ONLY after step 2 succeeds, harden SSH:"
echo "       sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config"
echo "       sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config"
echo "       systemctl restart sshd"
echo ""
echo "  PATH B (password login only):"
echo "  1. From your LOCAL machine, verify password login:"
echo "       ssh ${DEPLOY_USER}@$(hostname -I | awk '{print $1}')"
echo "  2. Harden SSH (disable root, keep password auth):"
echo "       sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config"
echo "       sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config"
echo "       systemctl restart ssh || systemctl restart sshd"
echo ""
echo "WARNING: Do NOT disable PasswordAuthentication unless you have verified key-based login works."
echo "         If locked out, use SolusVM VNC console at https://nerdvm.racknerd.com/"
