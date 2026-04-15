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
#   - Runs site and container health checks
#   - Fails deploy verification when required services are unhealthy
#   - Emits troubleshooting diagnostics for failing services
set -euo pipefail

APP_ROOT="${APP_ROOT:-$HOME/app}"
WEB_ROOT="${WEB_ROOT:-$APP_ROOT/web}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
APP_DOMAIN="${APP_DOMAIN:-lp.csedesigns.com}"
APP_ALIAS_DOMAIN="${APP_ALIAS_DOMAIN:-}"
LOG_DIR="${LOG_DIR:-$HOME/deploy-logs}"
TS="$(date -u +%Y%m%d-%H%M%S)"
LOG_FILE="${LOG_DIR}/post-deploy-check-${TS}.log"
LATEST_LOG_FILE="${LOG_DIR}/post-deploy-check-latest.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

finalize_log() {
    cp "$LOG_FILE" "$LATEST_LOG_FILE" 2>/dev/null || true
    echo "Latest log pointer: $LATEST_LOG_FILE"
}

trap finalize_log EXIT

compose() {
    docker compose -f "$WEB_ROOT/$COMPOSE_FILE" "$@"
}

service_cid() {
    local service="$1"
    compose ps -q "$service" | head -n 1
}

dump_service_diagnostics() {
    local service="$1"
    local cid
    cid="$(service_cid "$service")"

    echo "--- Diagnostics: $service ---"
    if [[ -z "$cid" ]]; then
        echo "  Container not found for service '$service'."
        return
    fi

    echo "  Container ID: $cid"
    docker inspect --format '  State={{.State.Status}} Health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" || true
    echo "  Recent health log entries:"
    docker inspect --format '{{if .State.Health}}{{range .State.Health.Log}}  - {{.Start}} exit={{.ExitCode}} output={{printf "%q" .Output}}{{println}}{{end}}{{else}}  - none{{end}}' "$cid" || true
    echo "  Last 120 service log lines:"
    compose logs --tail 120 "$service" || true

    if [[ "$service" == "ollama" ]]; then
        echo "  Ollama probe from inside container (ollama list):"
        compose exec -T ollama ollama list || true
    fi
}

wait_for_service_healthy() {
    local service="$1"
    local timeout_seconds="$2"
    local interval_seconds="${3:-5}"
    local max_attempts=$((timeout_seconds / interval_seconds))
    local attempt=1

    if (( max_attempts < 1 )); then
        max_attempts=1
    fi

    echo "--- Waiting for service health: $service (timeout ${timeout_seconds}s) ---"
    while (( attempt <= max_attempts )); do
        local cid state health
        cid="$(service_cid "$service")"
        if [[ -z "$cid" ]]; then
            echo "  $service: container missing (attempt $attempt/$max_attempts)"
        else
            state="$(docker inspect --format '{{.State.Status}}' "$cid" 2>/dev/null || echo unknown)"
            health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" 2>/dev/null || echo unknown)"
            echo "  $service: state=$state health=$health (attempt $attempt/$max_attempts)"
            if [[ "$state" == "running" && "$health" == "healthy" ]]; then
                return 0
            fi
        fi
        sleep "$interval_seconds"
        attempt=$((attempt + 1))
    done
    return 1
}

# --- Pre-flight checks ---
if [[ "$(whoami)" == "root" ]]; then
    echo "ERROR: Run this as the deploy user, not root."
    exit 1
fi

echo "=== Post-Deploy Maintenance ==="
echo "Log file: $LOG_FILE"
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
    local required="${3:-false}"
    local code
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null || echo "000")
    if [[ "$code" == "200" ]]; then
        echo "  $label: OK ($code)"
        return 0
    else
        echo "  $label: PROBLEM ($code)"
        if [[ "$required" == "true" ]]; then
            return 1
        fi
        return 0
    fi
}

URL_FAIL=0
check_url "${APP_DOMAIN}/health" "https://${APP_DOMAIN}/health" true || URL_FAIL=1
check_url "${APP_DOMAIN}/" "https://${APP_DOMAIN}/" true || URL_FAIL=1
if [[ -n "$APP_ALIAS_DOMAIN" ]]; then
    check_url "${APP_ALIAS_DOMAIN}/health" "https://${APP_ALIAS_DOMAIN}/health" true || URL_FAIL=1
    check_url "${APP_ALIAS_DOMAIN}/" "https://${APP_ALIAS_DOMAIN}/" true || URL_FAIL=1
fi
check_url "csedesigns.com/" "https://csedesigns.com/"

echo ""
echo "--- Container status ---"
compose ps --format "table {{.Name}}\t{{.Status}}"

echo ""
echo "--- Required service health gates ---"
SERVICE_FAIL=0
for svc in pipeline web ollama; do
    if ! wait_for_service_healthy "$svc" 180 5; then
        echo "  $svc: FAILED health gate"
        SERVICE_FAIL=1
        dump_service_diagnostics "$svc"
    else
        echo "  $svc: passed health gate"
    fi
done

echo ""
if [[ "$URL_FAIL" -ne 0 || "$SERVICE_FAIL" -ne 0 ]]; then
    echo "=== Post-deploy verification FAILED ==="
    echo "See log file: $LOG_FILE"
    exit 1
fi

echo "=== Post-deploy verification PASSED ==="
echo "Log saved: $LOG_FILE"
