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
#   - Waits for health check with per-attempt container diagnostics
#   - Probes /health JSON and prints full readiness breakdown on pass AND fail
#   - Disables maintenance mode on success (site goes live)
#   - Rolls back to the previous Git revision on failed health check (when available)
#   - Dumps tail logs from every service on health check failure
#   - Shows status and URLs to test
#   - Writes full deploy log to ~/deploy-logs/deploy-YYYYMMDD-HHMMSS.log
set -euo pipefail

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
LOG_DIR="${LOG_DIR:-$HOME/deploy-logs}"
DEPLOY_TS="$(date -u +%Y%m%d-%H%M%S)"
LOG_FILE="${LOG_DIR}/deploy-${DEPLOY_TS}.log"
LATEST_LOG_FILE="${LOG_DIR}/deploy-latest.log"

mkdir -p "$LOG_DIR"
# Tee all stdout+stderr to the log file for the entire script run
exec > >(tee -a "$LOG_FILE") 2>&1

# Emit timestamped lines so every event is traceable in the log
log_ts() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

finalize_log() {
    cp "$LOG_FILE" "$LATEST_LOG_FILE" 2>/dev/null || true
    log_ts "Full deploy log: $LOG_FILE"
    log_ts "Latest log link: $LATEST_LOG_FILE"
}
trap finalize_log EXIT

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_ROOT="${APP_ROOT:-$HOME/app}"
WEB_ROOT="${WEB_ROOT:-$APP_ROOT/web}"
COMPOSE_FILE="docker-compose.prod.yml"
APP_DOMAIN="${APP_DOMAIN:-lp.csedesigns.com}"
APP_ALIAS_DOMAIN="${APP_ALIAS_DOMAIN:-}"
MAIN_DOMAIN="${MAIN_DOMAIN:-csedesigns.com}"
ENABLE_PREDEPLOY_BACKUP="${ENABLE_PREDEPLOY_BACKUP:-1}"
HEALTH_MAX_ATTEMPTS="${HEALTH_MAX_ATTEMPTS:-40}"
HEALTH_SLEEP="${HEALTH_SLEEP:-3}"
COMPOSE_REMOVE_ORPHANS="${COMPOSE_REMOVE_ORPHANS:-1}"
CLEANUP_ON_SUCCESS="${CLEANUP_ON_SUCCESS:-1}"
CLEANUP_ON_ROLLBACK="${CLEANUP_ON_ROLLBACK:-0}"
CLEANUP_IMAGE_PRUNE="${CLEANUP_IMAGE_PRUNE:-1}"
CLEANUP_BUILDER_PRUNE="${CLEANUP_BUILDER_PRUNE:-0}"
CLEANUP_BUILDER_KEEP_STORAGE="${CLEANUP_BUILDER_KEEP_STORAGE:-4GB}"


PRE_DEPLOY_COMMIT=""
ROLLED_BACK=0
MAINTENANCE_ENABLED=0

# ---------------------------------------------------------------------------
# Helper: container state + health one-liner
# ---------------------------------------------------------------------------
container_state() {
    local service="$1"
    local cid
    cid="$(docker compose -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null | head -n1)"
    if [[ -z "$cid" ]]; then
        echo "state=<no container>"
        return
    fi
    local state health last_log
    state="$(docker inspect --format '{{.State.Status}}' "$cid" 2>/dev/null || echo unknown)"
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" 2>/dev/null || echo unknown)"
    last_log="$(docker logs --tail 1 "$cid" 2>&1 | tr '\n' ' ' | cut -c1-120)"
    echo "state=${state} health=${health} last_log=\"${last_log}\""
}

# ---------------------------------------------------------------------------
# Helper: dump service log tail on failure
# ---------------------------------------------------------------------------
dump_service_logs() {
    local service="$1"
    local lines="${2:-40}"
    log_ts "--- Log tail: $service (last $lines lines) ---"
    docker compose -f "$COMPOSE_FILE" logs --tail "$lines" "$service" 2>&1 || true
}

# ---------------------------------------------------------------------------
# Helper: optional cleanup of stale Docker artifacts
# ---------------------------------------------------------------------------
run_optional_cleanup() {
    local phase="${1:-deploy}"

    log_ts "--- Cleanup phase ($phase): begin ---"

    if [[ "$CLEANUP_IMAGE_PRUNE" == "1" ]]; then
        log_ts "    Pruning dangling/unused images (docker image prune -f)"
        docker image prune -f || true
    else
        log_ts "    Skipping image prune (CLEANUP_IMAGE_PRUNE=$CLEANUP_IMAGE_PRUNE)"
    fi

    if [[ "$CLEANUP_BUILDER_PRUNE" == "1" ]]; then
        log_ts "    Pruning builder cache with keep-storage=$CLEANUP_BUILDER_KEEP_STORAGE"
        docker builder prune -f --keep-storage "$CLEANUP_BUILDER_KEEP_STORAGE" || true
    else
        log_ts "    Skipping builder prune (CLEANUP_BUILDER_PRUNE=$CLEANUP_BUILDER_PRUNE)"
    fi

    log_ts "--- Cleanup phase ($phase): complete ---"
}

# ---------------------------------------------------------------------------
# Helper: probe /health inside the web container and print full JSON
# ---------------------------------------------------------------------------
probe_health_json() {
    local label="${1:-health}"
    log_ts "--- $label: probing /health JSON ---"
    docker compose -f "$COMPOSE_FILE" exec -T web python -c "
import urllib.request, json, sys
try:
    with urllib.request.urlopen('http://localhost:8000/health', timeout=5) as r:
        body = r.read().decode()
        payload = json.loads(body)
        print(json.dumps(payload, indent=2))
        services_ok = all(v.get('status') == 'ok' for v in payload.get('services', {}).values())
        # budget uses 'ok'/'exhausted'; chat/vision/whisperer use 'ready'/'not-ready'/'not-configured'
        readiness = payload.get('readiness', {})
        features_ok = all(
            v.get('status') in ('ready', 'ok', 'not-configured')
            for v in readiness.values()
        )
        sys.exit(0 if services_ok and features_ok else 1)
except Exception as exc:
    print(f'PROBE ERROR: {exc}', file=sys.stderr)
    sys.exit(1)
" 2>&1 || true
}

# ---------------------------------------------------------------------------
# Helper: wait for health, with per-attempt diagnostics
# ---------------------------------------------------------------------------
wait_for_health() {
    local phase="${1:-deploy}"  # "deploy" or "rollback"
    local attempts=0
    local healthy=0

    # All log output goes to stderr so callers can capture stdout safely:
    #   HEALTHY="$(wait_for_health "deploy")"
    # captures only the final "0" or "1", not the log lines.
    log_ts "--- Waiting for /health (max ${HEALTH_MAX_ATTEMPTS} attempts, ${HEALTH_SLEEP}s interval) ---" >&2

    while [[ "$attempts" -lt "$HEALTH_MAX_ATTEMPTS" ]]; do
        attempts=$((attempts + 1))
        log_ts "  Attempt $attempts/${HEALTH_MAX_ATTEMPTS} [$phase]" >&2

        # Per-service container state
        for svc in pipeline web; do
            log_ts "    $svc: $(container_state "$svc")" >&2
        done

        if docker compose -f "$COMPOSE_FILE" exec -T web python -c \
            "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)" 2>/dev/null; then
            healthy=1
            break
        fi

        log_ts "  /health not ready yet -- waiting ${HEALTH_SLEEP}s" >&2
        sleep "$HEALTH_SLEEP"
    done

    echo "$healthy"
}



# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
log_ts "=== ACB Large Print Toolkit -- Deploy (script started) ==="
log_ts "Log file: $LOG_FILE"
echo ""

if [[ "$(whoami)" == "root" ]]; then
    log_ts "ERROR: Do not run this script as root. Run as the deploy user."
    exit 1
fi

if ! command -v docker &>/dev/null; then
    log_ts "ERROR: Docker is not installed. Run bootstrap-server.sh first."
    exit 1
fi

if ! docker info &>/dev/null 2>&1; then
    log_ts "ERROR: Cannot connect to Docker daemon."
    log_ts "       Ensure your user is in the docker group: sudo usermod -aG docker $(whoami)"
    log_ts "       Then log out and back in."
    exit 1
fi

log_ts "App root:     $APP_ROOT"
log_ts "Web root:     $WEB_ROOT"
log_ts "Compose file: $COMPOSE_FILE"
log_ts "Domain:       $APP_DOMAIN"
echo ""

# Check required files
MISSING=0
for F in "$WEB_ROOT/$COMPOSE_FILE" "$WEB_ROOT/.env" "$WEB_ROOT/Caddyfile" "$WEB_ROOT/Dockerfile"; do
    if [[ ! -f "$F" ]]; then
        log_ts "ERROR: Required file missing: $F"
        MISSING=1
    else
        log_ts "OK: $F exists"
    fi
done

if [[ ! -d "$APP_ROOT/desktop/src/acb_large_print" ]]; then
    log_ts "ERROR: desktop/src/acb_large_print/ directory missing (needed for Docker build)."
    MISSING=1
fi

if [[ "$MISSING" -eq 1 ]]; then
    echo ""
    log_ts "Fix the missing files and re-run this script."
    exit 1
fi

# ---------------------------------------------------------------------------
# Optional: pull latest from Git
# ---------------------------------------------------------------------------
if [[ -d "$APP_ROOT/.git" ]]; then
    PRE_DEPLOY_COMMIT=$(cd "$APP_ROOT" && git rev-parse HEAD)
    log_ts "--- Git: pre-deploy commit = $PRE_DEPLOY_COMMIT ---"
    log_ts "--- Git: pulling latest code from origin/main ---"
    cd "$APP_ROOT"
    git pull origin main
    POST_PULL_COMMIT=$(git rev-parse HEAD)
    log_ts "--- Git: post-pull commit  = $POST_PULL_COMMIT ---"
    if [[ "$PRE_DEPLOY_COMMIT" == "$POST_PULL_COMMIT" ]]; then
        log_ts "--- Git: no new commits (already up to date) ---"
    else
        log_ts "--- Git: $(git log --oneline "$PRE_DEPLOY_COMMIT".."$POST_PULL_COMMIT") ---"
    fi
fi

# ---------------------------------------------------------------------------
# Optional: pre-deploy feedback DB backup
# ---------------------------------------------------------------------------
if [[ "$ENABLE_PREDEPLOY_BACKUP" == "1" ]]; then
    if [[ -x "$APP_ROOT/scripts/backup-feedback.sh" ]]; then
        log_ts "--- Creating pre-deploy feedback backup ---"
        bash "$APP_ROOT/scripts/backup-feedback.sh"
        log_ts "--- Backup complete ---"
    else
        log_ts "--- Skipping pre-deploy backup (backup-feedback.sh not executable) ---"
    fi
fi

# ---------------------------------------------------------------------------
# Enable maintenance mode
# ---------------------------------------------------------------------------
log_ts "--- Enabling maintenance mode (MAINTENANCE_MODE=1) ---"
export MAINTENANCE_MODE=1
MAINTENANCE_ENABLED=1

# ---------------------------------------------------------------------------
# Build and start containers
# ---------------------------------------------------------------------------
cd "$WEB_ROOT"

log_ts "--- Building and starting containers (docker compose up -d --build) ---"
log_ts "    Build output follows:"
if [[ "$COMPOSE_REMOVE_ORPHANS" == "1" ]]; then
    docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans
else
    docker compose -f "$COMPOSE_FILE" up -d --build
fi
log_ts "--- docker compose up complete ---"

# Show initial container state immediately after launch
log_ts "--- Initial container state after launch ---"
docker compose -f "$COMPOSE_FILE" ps
echo ""

# ---------------------------------------------------------------------------
# Wait for health check
# ---------------------------------------------------------------------------
HEALTHY="$(wait_for_health "deploy")"
echo ""

if [[ "$HEALTHY" -eq 1 ]]; then
    log_ts "--- Health check: PASSED ---"
    probe_health_json "Full health readiness on success"

    log_ts "--- Disabling maintenance mode (site is now live) ---"
    export MAINTENANCE_MODE=0
    MAINTENANCE_ENABLED=0
    if [[ "$COMPOSE_REMOVE_ORPHANS" == "1" ]]; then
        docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans
    else
        docker compose -f "$COMPOSE_FILE" up -d --build
    fi
    log_ts "--- Maintenance mode disabled successfully ---"

    # Force the proxy to pick up bind-mounted Caddyfile changes. A plain
    # `docker compose up -d --build` can leave the long-lived Caddy container
    # running with stale config even though the file on disk has changed.
    log_ts "--- Validating Caddy configuration ---"
    docker run --rm \
        -v "$WEB_ROOT/Caddyfile:/etc/caddy/Caddyfile:ro" \
        caddy:2-alpine \
        caddy validate --config /etc/caddy/Caddyfile

    log_ts "--- Recreating Caddy container to apply updated proxy configuration ---"
    docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate caddy

    log_ts "--- Caddy container state after recreation ---"
    docker compose -f "$COMPOSE_FILE" ps caddy

    # ---------------------------------------------------------------------------
    # Ensure Kokoro speech model files are present in the speech-models volume.
    # The Dockerfile attempts to pre-download them at build time, but that step
    # is a best-effort (network may be unavailable in the build environment).
    # This post-deploy step guarantees the files exist in the running container.
    # It is a no-op if the files are already there, so it is safe to run every
    # deployment.
    # ---------------------------------------------------------------------------
    log_ts "--- Ensuring Kokoro speech model files are present ---"
    docker compose -f "$COMPOSE_FILE" exec -T web python -c "
import os, sys
from pathlib import Path
model_dir = Path(os.environ.get('GLOW_SPEECH_MODEL_DIR', '/app/instance/speech_models'))
onnx_file = model_dir / 'kokoro-v0_19.onnx'
json_file  = model_dir / 'voices.json'
if onnx_file.exists() and json_file.exists():
    print(f'Kokoro models already present in {model_dir} -- skipping download.')
    sys.exit(0)
print(f'Kokoro models not found in {model_dir} -- downloading from Hugging Face Hub...')
try:
    import huggingface_hub as h
    model_dir.mkdir(parents=True, exist_ok=True)
    h.hf_hub_download('hexgrad/Kokoro-82M', 'kokoro-v0_19.onnx', local_dir=str(model_dir))
    h.hf_hub_download('hexgrad/Kokoro-82M', 'voices.json',       local_dir=str(model_dir))
    print('Kokoro models downloaded successfully.')
except Exception as exc:
    print(f'WARNING: Kokoro model download failed: {exc}')
    print('Speech Demo will show Not Ready until models are added manually.')
    print('Manual install: docker compose exec web python -c \"import huggingface_hub as h; h.hf_hub_download(\\\"hexgrad/Kokoro-82M\\\", \\\"kokoro-v0_19.onnx\\\", local_dir=\\\"/app/instance/speech_models\\\"); h.hf_hub_download(\\\"hexgrad/Kokoro-82M\\\", \\\"voices.json\\\", local_dir=\\\"/app/instance/speech_models\\\")\"')
" 2>&1 || log_ts "WARNING: Could not exec into web container to check speech models."
    log_ts "--- Speech model check complete ---"

    # If Kokoro models are now present, ensure GLOW_ENABLE_SPEECH=true in feature_flags.json
    SPEECH_FLAG_FILE="$APP_ROOT/instance/feature_flags.json"
    if docker compose -f "$COMPOSE_FILE" exec -T web python -c "
import os
from pathlib import Path
d = Path(os.environ.get('GLOW_SPEECH_MODEL_DIR', '/app/instance/speech_models'))
exit(0 if (d / 'kokoro-v0_19.onnx').exists() else 1)
" 2>/dev/null; then
        if [[ -f "$SPEECH_FLAG_FILE" ]]; then
            if ! python3 -c "import json; d=json.load(open('$SPEECH_FLAG_FILE')); exit(0 if d.get('GLOW_ENABLE_SPEECH') else 1)" 2>/dev/null; then
                log_ts "--- Enabling GLOW_ENABLE_SPEECH in feature_flags.json (models present) ---"
                python3 -c "
import json
p = '$SPEECH_FLAG_FILE'
d = json.load(open(p))
d['GLOW_ENABLE_SPEECH'] = True
open(p,'w').write(json.dumps(d, indent=2) + '\n')
print('GLOW_ENABLE_SPEECH enabled.')
"
            else
                log_ts "--- GLOW_ENABLE_SPEECH already enabled in feature_flags.json ---"
            fi
        fi
    fi

    if [[ "$CLEANUP_ON_SUCCESS" == "1" ]]; then
        run_optional_cleanup "success"
    else
        log_ts "--- Skipping cleanup on success (CLEANUP_ON_SUCCESS=$CLEANUP_ON_SUCCESS) ---"
    fi

else
    log_ts "--- Health check: FAILED after ${HEALTH_MAX_ATTEMPTS} attempts ---"
    probe_health_json "Partial health state on failure"

    log_ts "--- Dumping recent container logs for all services ---"
    dump_service_logs pipeline 60
    dump_service_logs web 80
    dump_service_logs caddy 20

    log_ts "--- Docker container inspect (web) ---"
    WEB_CID="$(docker compose -f "$COMPOSE_FILE" ps -q web 2>/dev/null | head -n1)"
    if [[ -n "$WEB_CID" ]]; then
        docker inspect --format '
Container: {{.Name}}
  State:   {{.State.Status}}
  Started: {{.State.StartedAt}}
  Error:   {{.State.Error}}
  Health:  {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}
' "$WEB_CID" || true
    fi

    log_ts "--- Disabling maintenance mode before rollback ---"
    export MAINTENANCE_MODE=0
    MAINTENANCE_ENABLED=0

    if [[ -n "$PRE_DEPLOY_COMMIT" && -d "$APP_ROOT/.git" ]]; then
        log_ts "--- Attempting rollback to previous commit: $PRE_DEPLOY_COMMIT ---"
        cd "$APP_ROOT"
        git checkout -f "$PRE_DEPLOY_COMMIT"
        log_ts "--- Rollback checkout complete; rebuilding containers ---"

        cd "$WEB_ROOT"
        if [[ "$COMPOSE_REMOVE_ORPHANS" == "1" ]]; then
            docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans
        else
            docker compose -f "$COMPOSE_FILE" up -d --build
        fi
        log_ts "--- Rollback containers started ---"

        ROLLBACK_HEALTHY="$(wait_for_health "rollback")"
        echo ""

        if [[ "$ROLLBACK_HEALTHY" -eq 1 ]]; then
            ROLLED_BACK=1
            log_ts "--- Rollback health check: PASSED ---"
            probe_health_json "Rollback health readiness"

            if [[ "$CLEANUP_ON_ROLLBACK" == "1" ]]; then
                run_optional_cleanup "rollback"
            else
                log_ts "--- Skipping cleanup after rollback (CLEANUP_ON_ROLLBACK=$CLEANUP_ON_ROLLBACK) ---"
            fi
        else
            log_ts "--- Rollback health check: FAILED ---"
            dump_service_logs web 60
            log_ts "    Manual intervention required."
            exit 1
        fi
    else
        log_ts "--- Rollback unavailable (no Git commit baseline or no .git directory). ---"
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Final status
# ---------------------------------------------------------------------------
echo ""
log_ts "--- Final container status ---"
docker compose -f "$COMPOSE_FILE" ps

echo ""
log_ts "=== Deployment complete ==="
echo ""
if [[ "$ROLLED_BACK" -eq 1 ]]; then
    log_ts "NOTE: Deploy failed and was rolled back to $PRE_DEPLOY_COMMIT."
    log_ts "      Investigate the failed revision before retrying deployment."
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
echo "Live log tail:"
echo "  cd $WEB_ROOT && docker compose -f $COMPOSE_FILE logs --tail 50 -f"
echo ""
echo "Deploy log:"
echo "  cat $LOG_FILE"
echo "  cat $LATEST_LOG_FILE   # always points to the most recent deploy"
