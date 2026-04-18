#!/usr/bin/env bash
# deploy-app.sh -- Build and deploy the ACB Large Print web application
#
# Run as deploy user:  bash ~/app/scripts/deploy-app.sh
#
# This script:
#   - Validates that required files exist
#   - Optionally pulls latest code from Git (if .git directory exists)
#   - Creates a pre-deploy feedback DB backup (optional)
#   - Enables maintenance mode (users see "Under Maintenance" page)
#   - Builds and starts Docker containers
#   - Waits for health check
#   - Disables maintenance mode on success (site goes live)
#   - Rolls back to the previous Git revision on failed health check (when available)
#   - Shows status and URLs to test
set -euo pipefail

# --- Configuration ---
APP_ROOT="${APP_ROOT:-$HOME/app}"
WEB_ROOT="${WEB_ROOT:-$APP_ROOT/web}"
COMPOSE_FILE="docker-compose.prod.yml"
APP_DOMAIN="${APP_DOMAIN:-lp.csedesigns.com}"
APP_ALIAS_DOMAIN="${APP_ALIAS_DOMAIN:-}"
MAIN_DOMAIN="${MAIN_DOMAIN:-csedesigns.com}"
ENABLE_PREDEPLOY_BACKUP="${ENABLE_PREDEPLOY_BACKUP:-1}"

PRE_DEPLOY_COMMIT=""
ROLLED_BACK=0
MAINTENANCE_ENABLED=0

# --- Pre-flight checks ---
if [[ "$(whoami)" == "root" ]]; then
    echo "ERROR: Do not run this script as root. Run as the deploy user."
    exit 1
fi

if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker is not installed. Run bootstrap-server.sh first."
    exit 1
fi

if ! docker info &>/dev/null 2>&1; then
    echo "ERROR: Cannot connect to Docker. Is your user in the docker group?"
    echo "       Run: sudo usermod -aG docker $(whoami)"
    echo "       Then log out and back in."
    exit 1
fi

echo "=== ACB Large Print Toolkit -- Deploy ==="
echo ""
echo "App root:     $APP_ROOT"
echo "Web root:     $WEB_ROOT"
echo "Compose file: $COMPOSE_FILE"
echo ""

# Check required files
MISSING=0
for F in "$WEB_ROOT/$COMPOSE_FILE" "$WEB_ROOT/.env" "$WEB_ROOT/Caddyfile" "$WEB_ROOT/Dockerfile"; do
    if [[ ! -f "$F" ]]; then
        echo "ERROR: Required file missing: $F"
        MISSING=1
    fi
done

if [[ ! -d "$APP_ROOT/desktop/src/acb_large_print" ]]; then
    echo "ERROR: desktop/src/acb_large_print/ directory missing (needed for Docker build)."
    MISSING=1
fi

if [[ "$MISSING" -eq 1 ]]; then
    echo ""
    echo "Fix the missing files and re-run this script."
    exit 1
fi

# --- Optional: pull latest from Git ---
if [[ -d "$APP_ROOT/.git" ]]; then
    PRE_DEPLOY_COMMIT=$(cd "$APP_ROOT" && git rev-parse HEAD)
    echo "--- Git repository detected. Pulling latest code ---"
    cd "$APP_ROOT"
    git pull origin main
fi

# --- Optional: pre-deploy feedback DB backup ---
if [[ "$ENABLE_PREDEPLOY_BACKUP" == "1" ]]; then
    if [[ -x "$APP_ROOT/scripts/backup-feedback.sh" ]]; then
        echo "--- Creating pre-deploy feedback backup ---"
        bash "$APP_ROOT/scripts/backup-feedback.sh"
    else
        echo "--- Skipping pre-deploy backup (backup-feedback.sh not executable) ---"
    fi
fi

# --- Enable maintenance mode ---
echo "--- Enabling maintenance mode (users will see 'Under Maintenance') ---"
export MAINTENANCE_MODE=1
MAINTENANCE_ENABLED=1

# --- Build and start ---
cd "$WEB_ROOT"

echo "--- Building and starting containers ---"
docker compose -f "$COMPOSE_FILE" up -d --build

echo "--- Waiting for containers to become healthy ---"
ATTEMPTS=0
MAX_ATTEMPTS=40
HEALTHY=0
while [[ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ]]; do
    if docker compose -f "$COMPOSE_FILE" exec -T web python -c \
        "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
        HEALTHY=1
        break
    fi
    ATTEMPTS=$((ATTEMPTS + 1))
    printf "."
    sleep 3
done
echo ""

if [[ "$HEALTHY" -eq 1 ]]; then
    echo "--- Health check: PASSED ---"
    echo "--- Disabling maintenance mode (site is now live) ---"
    export MAINTENANCE_MODE=0
    docker compose -f "$COMPOSE_FILE" up -d --build
else
    echo "--- Health check: DID NOT PASS after ${MAX_ATTEMPTS} attempts ---"
    echo "    Check logs: docker compose -f $COMPOSE_FILE logs web --tail 30"
    echo "--- Disabling maintenance mode (reverting to previous version) ---"
    export MAINTENANCE_MODE=0

    # Best-effort rollback to previous known-good code revision when Git is available.
    if [[ -n "$PRE_DEPLOY_COMMIT" && -d "$APP_ROOT/.git" ]]; then
        echo "--- Attempting rollback to previous commit: $PRE_DEPLOY_COMMIT ---"
        cd "$APP_ROOT"
        git checkout -f "$PRE_DEPLOY_COMMIT"

        cd "$WEB_ROOT"
        docker compose -f "$COMPOSE_FILE" up -d --build

        echo "--- Waiting for rollback health check ---"
        ATTEMPTS=0
        MAX_ATTEMPTS=40
        while [[ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ]]; do
            if docker compose -f "$COMPOSE_FILE" exec -T web python -c \
                "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
                ROLLED_BACK=1
                break
            fi
            ATTEMPTS=$((ATTEMPTS + 1))
            printf "."
            sleep 3
        done
        echo ""

        if [[ "$ROLLED_BACK" -eq 1 ]]; then
            echo "--- Rollback health check: PASSED ---"
        else
            echo "--- Rollback health check: FAILED ---"
            echo "    Manual intervention required."
            exit 1
        fi
    else
        echo "--- Rollback unavailable (no Git commit baseline). ---"
        exit 1
    fi
fi

# --- Status ---
echo ""
echo "--- Container status ---"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "=== Deployment complete ==="
echo ""
if [[ "$ROLLED_BACK" -eq 1 ]]; then
    echo "NOTE: Deploy failed health checks and was rolled back to $PRE_DEPLOY_COMMIT."
    echo "      Investigate the failed revision before retrying deployment."
    echo ""
fi
echo "Test these URLs:"
echo "  https://${APP_DOMAIN}/"
echo "  https://${APP_DOMAIN}/health"
if [[ -n "$APP_ALIAS_DOMAIN" ]]; then
    echo "  https://${APP_ALIAS_DOMAIN}/"
    echo "  https://${APP_ALIAS_DOMAIN}/health"
fi
echo "  https://${MAIN_DOMAIN}/"
echo ""
echo "View logs:"
echo "  cd $WEB_ROOT && docker compose -f $COMPOSE_FILE logs --tail 50 -f"

# --- Pre-flight checks ---
if [[ "$(whoami)" == "root" ]]; then
    echo "ERROR: Do not run this script as root. Run as the deploy user."
    exit 1
fi

if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker is not installed. Run bootstrap-server.sh first."
    exit 1
fi

if ! docker info &>/dev/null 2>&1; then
    echo "ERROR: Cannot connect to Docker. Is your user in the docker group?"
    echo "       Run: sudo usermod -aG docker $(whoami)"
    echo "       Then log out and back in."
    exit 1
fi

echo "=== ACB Large Print Toolkit -- Deploy ==="
echo ""
echo "App root:     $APP_ROOT"
echo "Web root:     $WEB_ROOT"
echo "Compose file: $COMPOSE_FILE"
echo ""

# Check required files
MISSING=0
for F in "$WEB_ROOT/$COMPOSE_FILE" "$WEB_ROOT/.env" "$WEB_ROOT/Caddyfile" "$WEB_ROOT/Dockerfile"; do
    if [[ ! -f "$F" ]]; then
        echo "ERROR: Required file missing: $F"
        MISSING=1
    fi
done

if [[ ! -d "$APP_ROOT/desktop/src/acb_large_print" ]]; then
    echo "ERROR: desktop/src/acb_large_print/ directory missing (needed for Docker build)."
    MISSING=1
fi

if [[ "$MISSING" -eq 1 ]]; then
    echo ""
    echo "Fix the missing files and re-run this script."
    exit 1
fi

# --- Optional: pull latest from Git ---
if [[ -d "$APP_ROOT/.git" ]]; then
    PRE_DEPLOY_COMMIT=$(cd "$APP_ROOT" && git rev-parse HEAD)
    echo "--- Git repository detected. Pulling latest code ---"
    cd "$APP_ROOT"
    git pull origin main
fi

# --- Optional: pre-deploy feedback DB backup ---
if [[ "$ENABLE_PREDEPLOY_BACKUP" == "1" ]]; then
    if [[ -x "$APP_ROOT/scripts/backup-feedback.sh" ]]; then
        echo "--- Creating pre-deploy feedback backup ---"
        bash "$APP_ROOT/scripts/backup-feedback.sh"
    else
        echo "--- Skipping pre-deploy backup (backup-feedback.sh not executable) ---"
    fi
fi

# --- Build and start ---
cd "$WEB_ROOT"

echo "--- Building and starting containers ---"
docker compose -f "$COMPOSE_FILE" up -d --build

echo "--- Waiting for containers to become healthy ---"
ATTEMPTS=0
MAX_ATTEMPTS=40
HEALTHY=0
while [[ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ]]; do
    if docker compose -f "$COMPOSE_FILE" exec -T web python -c \
        "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
        HEALTHY=1
        break
    fi
    ATTEMPTS=$((ATTEMPTS + 1))
    printf "."
    sleep 3
done
echo ""

if [[ "$HEALTHY" -eq 1 ]]; then
    echo "--- Health check: PASSED ---"
else
    echo "--- Health check: DID NOT PASS after ${MAX_ATTEMPTS} attempts ---"
    echo "    Check logs: docker compose -f $COMPOSE_FILE logs web --tail 30"

    # Best-effort rollback to previous known-good code revision when Git is available.
    if [[ -n "$PRE_DEPLOY_COMMIT" && -d "$APP_ROOT/.git" ]]; then
        echo "--- Attempting rollback to previous commit: $PRE_DEPLOY_COMMIT ---"
        cd "$APP_ROOT"
        git checkout -f "$PRE_DEPLOY_COMMIT"

        cd "$WEB_ROOT"
        docker compose -f "$COMPOSE_FILE" up -d --build

        echo "--- Waiting for rollback health check ---"
        ATTEMPTS=0
        MAX_ATTEMPTS=40
        while [[ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ]]; do
            if docker compose -f "$COMPOSE_FILE" exec -T web python -c \
                "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
                ROLLED_BACK=1
                break
            fi
            ATTEMPTS=$((ATTEMPTS + 1))
            printf "."
            sleep 3
        done
        echo ""

        if [[ "$ROLLED_BACK" -eq 1 ]]; then
            echo "--- Rollback health check: PASSED ---"
        else
            echo "--- Rollback health check: FAILED ---"
            echo "    Manual intervention required."
            exit 1
        fi
    else
        echo "--- Rollback unavailable (no Git commit baseline). ---"
        exit 1
    fi
fi

# --- Status ---
echo ""
echo "--- Container status ---"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "=== Deployment complete ==="
echo ""
if [[ "$ROLLED_BACK" -eq 1 ]]; then
    echo "NOTE: Deploy failed health checks and was rolled back to $PRE_DEPLOY_COMMIT."
    echo "      Investigate the failed revision before retrying deployment."
    echo ""
fi
echo "Test these URLs:"
echo "  https://${APP_DOMAIN}/"
echo "  https://${APP_DOMAIN}/health"
if [[ -n "$APP_ALIAS_DOMAIN" ]]; then
    echo "  https://${APP_ALIAS_DOMAIN}/"
    echo "  https://${APP_ALIAS_DOMAIN}/health"
fi
echo "  https://${MAIN_DOMAIN}/"
echo ""
echo "View logs:"
echo "  cd $WEB_ROOT && docker compose -f $COMPOSE_FILE logs --tail 50 -f"
