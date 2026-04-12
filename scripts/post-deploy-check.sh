#!/usr/bin/env bash
# post-deploy-check.sh -- Post-deployment maintenance tasks
#
# Run as deploy user:  bash ~/app/scripts/post-deploy-check.sh
#
# This script:
#   - Installs the backup cron job (daily at 2 AM) if not already set
#   - Installs the disk usage alert cron job (weekly Sunday 6 AM)
#   - Verifies Docker is enabled on boot
#   - Prunes unused Docker images
#   - Runs a quick site health check
set -euo pipefail

# --- Pre-flight checks ---
if [[ "$(whoami)" == "root" ]]; then
    echo "ERROR: Run this as the deploy user, not root."
    exit 1
fi

echo "=== Post-Deploy Maintenance ==="
echo ""

# --- 1. Backup cron job ---
BACKUP_CRON="0 2 * * * /home/deploy/app/scripts/backup-feedback.sh >> /home/deploy/backups/backup.log 2>&1"
DISK_CRON="0 6 * * 0 df -h / | awk 'NR==2 && int(\$5)>80' >> /home/deploy/disk-alerts.log 2>&1"

echo "--- Checking cron jobs ---"

CURRENT_CRON=$(crontab -l 2>/dev/null || true)

CHANGED=false

if echo "$CURRENT_CRON" | grep -qF "backup-feedback.sh"; then
    echo "  Backup cron job: already installed"
else
    CURRENT_CRON=$(printf '%s\n%s\n' "$CURRENT_CRON" "# Daily feedback DB backup at 2 AM")
    CURRENT_CRON=$(printf '%s\n%s\n' "$CURRENT_CRON" "$BACKUP_CRON")
    CHANGED=true
    echo "  Backup cron job: ADDED (daily at 2 AM)"
fi

if echo "$CURRENT_CRON" | grep -qF "disk-alerts.log"; then
    echo "  Disk alert cron job: already installed"
else
    CURRENT_CRON=$(printf '%s\n%s\n' "$CURRENT_CRON" "# Weekly disk usage warning (Sunday 6 AM)")
    CURRENT_CRON=$(printf '%s\n%s\n' "$CURRENT_CRON" "$DISK_CRON")
    CHANGED=true
    echo "  Disk alert cron job: ADDED (Sunday 6 AM)"
fi

if [[ "$CHANGED" == "true" ]]; then
    echo "$CURRENT_CRON" | crontab -
    echo "  Crontab updated."
else
    echo "  No cron changes needed."
fi

echo ""

# --- 2. Docker enabled on boot ---
echo "--- Checking Docker boot status ---"
if systemctl is-enabled docker >/dev/null 2>&1; then
    echo "  Docker: enabled on boot"
else
    echo "  Docker: NOT enabled -- enabling now..."
    sudo systemctl enable docker
    echo "  Docker: enabled"
fi
echo ""

# --- 3. Prune unused Docker images ---
echo "--- Pruning unused Docker images ---"
RECLAIMED=$(docker image prune -f 2>&1)
echo "  $RECLAIMED" | tail -1
echo ""

# --- 4. Site health checks ---
echo "--- Running health checks ---"

check_url() {
    local label="$1"
    local url="$2"
    local code
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null || echo "000")
    if [[ "$code" == "200" ]]; then
        echo "  $label: OK ($code)"
    else
        echo "  $label: PROBLEM ($code)"
    fi
}

check_url "lp.csedesigns.com/health" "https://lp.csedesigns.com/health"
check_url "lp.csedesigns.com/" "https://lp.csedesigns.com/"
check_url "csedesigns.com/" "https://csedesigns.com/"

echo ""
echo "--- Container status ---"
docker compose -f ~/app/web/docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}"

echo ""
echo "=== Done ==="
