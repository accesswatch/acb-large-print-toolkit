#!/usr/bin/env bash
# restore-feedback.sh -- Restore the feedback database from a backup
#
# Usage:  bash ~/app/scripts/restore-feedback.sh /path/to/backup.db
#
# This script:
#   - Validates the backup file exists and looks like a SQLite database
#   - Asks for confirmation
#   - Stops the web container
#   - Copies the backup into the Docker volume
#   - Starts the web container
#   - Verifies the health check passes
set -euo pipefail

# --- Configuration ---
WEB_ROOT="${WEB_ROOT:-$HOME/app/web}"
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/backups}"
COMPOSE_FILE="docker-compose.prod.yml"

# --- Usage ---
if [[ $# -lt 1 ]]; then
    echo "Usage: restore-feedback.sh <backup-file>"
    echo ""
    echo "Available backups:"
    if [[ -d "$BACKUP_ROOT" ]]; then
        ls -lh "$BACKUP_ROOT"/feedback-*.db 2>/dev/null || echo "  (none found in $BACKUP_ROOT)"
    else
        echo "  Backup directory does not exist: $BACKUP_ROOT"
    fi
    exit 1
fi

BACKUP_FILE="$1"

# --- Pre-flight checks ---
if [[ "$(whoami)" == "root" ]]; then
    echo "ERROR: Do not run this script as root."
    exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

if [[ ! -f "$WEB_ROOT/$COMPOSE_FILE" ]]; then
    echo "ERROR: Compose file not found: $WEB_ROOT/$COMPOSE_FILE"
    exit 1
fi

# Basic check that the file looks like a SQLite database
if ! head -c 16 "$BACKUP_FILE" | grep -q "SQLite format 3"; then
    echo "ERROR: File does not appear to be a SQLite database: $BACKUP_FILE"
    exit 1
fi

SIZE=$(stat --format='%s' "$BACKUP_FILE" 2>/dev/null || stat -f'%z' "$BACKUP_FILE" 2>/dev/null || echo "unknown")

echo "=== Feedback Database Restore ==="
echo ""
echo "Backup file: $BACKUP_FILE"
echo "Size:        $SIZE bytes"
echo ""
echo "WARNING: This will replace the current feedback database."
echo "         The web container will be stopped briefly."
echo ""
read -rp "Type 'yes' to continue: " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

cd "$WEB_ROOT"

# --- Stop web container ---
echo "--- Stopping web container ---"
docker compose -f "$COMPOSE_FILE" stop web

# --- Copy backup into volume ---
echo "--- Restoring database ---"
docker compose -f "$COMPOSE_FILE" cp "$BACKUP_FILE" web:/app/instance/feedback.db

# --- Start web container ---
echo "--- Starting web container ---"
docker compose -f "$COMPOSE_FILE" start web

# --- Wait and verify ---
echo "--- Waiting for health check ---"
ATTEMPTS=0
MAX_ATTEMPTS=10
HEALTHY=0
while [[ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ]]; do
    if docker compose -f "$COMPOSE_FILE" exec -T web python -c \
        "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
        HEALTHY=1
        break
    fi
    ATTEMPTS=$((ATTEMPTS + 1))
    sleep 2
done

if [[ "$HEALTHY" -eq 1 ]]; then
    echo "--- Health check: PASSED ---"
    echo ""
    echo "=== Restore complete ==="
else
    echo "--- Health check: FAILED ---"
    echo "    Check logs: docker compose -f $COMPOSE_FILE logs web --tail 30"
    exit 1
fi
