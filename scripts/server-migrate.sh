#!/usr/bin/env bash
# server-migrate.sh -- Migrate server deployment to slim Docker build
#
# Run as deploy user:  bash ~/app/scripts/server-migrate.sh
#
# What changed (v2.1):
#   - Root .dockerignore added: Docker build context now excludes desktop-only
#     files (CLI, GUI, build scripts), documentation, samples, templates,
#     styles, word-addin (TypeScript), and scripts.
#   - Dockerfile updated: only server-needed Python modules from word-addon/
#     are installed in the image (no cli.py, gui.py, __main__.py).
#   - Pandoc added to Docker image for Markdown/RST/ODT/RTF -> ACB HTML.
#   - Convert route now supports both to-Markdown and to-HTML directions.
#
# This script:
#   1. Verifies prerequisites
#   2. Pulls latest code (includes new .dockerignore, Dockerfile, routes)
#   3. Stops running containers gracefully
#   4. Removes old images (forces full rebuild with new .dockerignore)
#   5. Rebuilds and starts containers
#   6. Verifies the new build: health check, Pandoc availability, routes
#   7. Prunes dangling images / build cache
#   8. Shows before/after image size comparison
#
# Rollback: if the new build fails health checks, the script prints
#           recovery commands but does NOT auto-rollback (avoids masking
#           the real error).  The feedback-data volume is never touched.
set -euo pipefail

# --- Configuration (matches deploy-app.sh) ---
APP_ROOT="${APP_ROOT:-$HOME/app}"
WEB_ROOT="${WEB_ROOT:-$APP_ROOT/web}"
COMPOSE_FILE="docker-compose.prod.yml"
APP_DOMAIN="${APP_DOMAIN:-lp.csedesigns.com}"

# --- Pre-flight ---
echo "=== ACB Large Print -- Server Migration (slim build + Pandoc) ==="
echo ""

if [[ "$(whoami)" == "root" ]]; then
    echo "ERROR: Do not run as root. Run as the deploy user."
    exit 1
fi

if ! docker info &>/dev/null 2>&1; then
    echo "ERROR: Cannot connect to Docker."
    exit 1
fi

cd "$APP_ROOT"

if [[ ! -d ".git" ]]; then
    echo "ERROR: No git repo at $APP_ROOT. Expected a clone of acb-large-print-toolkit."
    exit 1
fi

# --- Step 1: Record old image size ---
echo "--- Step 1: Recording current image size ---"
OLD_PROJECT=$(basename "$WEB_ROOT")
OLD_IMAGE_ID=$(docker images --filter "reference=${OLD_PROJECT}-web" --format "{{.ID}}" 2>/dev/null | head -1 || true)
if [[ -n "$OLD_IMAGE_ID" ]]; then
    OLD_SIZE=$(docker images --format "{{.Size}}" "$OLD_IMAGE_ID" 2>/dev/null || echo "unknown")
    echo "  Current image: $OLD_IMAGE_ID ($OLD_SIZE)"
else
    OLD_SIZE="none"
    echo "  No existing image found (first deploy or different naming)."
fi
echo ""

# --- Step 2: Pull latest code ---
echo "--- Step 2: Pulling latest code ---"
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [[ "$LOCAL" == "$REMOTE" ]]; then
    echo "  Already up to date ($LOCAL)."
else
    git pull origin main
    echo "  Updated: $(git log --oneline -1)"
fi
echo ""

# --- Step 3: Verify new files exist ---
echo "--- Step 3: Verifying new files ---"
MISSING=0
for F in ".dockerignore" "web/Dockerfile" "word-addon/src/acb_large_print/pandoc_converter.py" "web/src/acb_large_print_web/routes/convert.py"; do
    if [[ -f "$APP_ROOT/$F" ]]; then
        echo "  OK: $F"
    else
        echo "  MISSING: $F"
        MISSING=1
    fi
done

if [[ "$MISSING" -eq 1 ]]; then
    echo ""
    echo "ERROR: Required files missing after pull. Check git status."
    exit 1
fi
echo ""

# --- Step 4: Stop current containers ---
echo "--- Step 4: Stopping current containers ---"
cd "$WEB_ROOT"
docker compose -f "$COMPOSE_FILE" down --timeout 30 2>/dev/null || true
echo "  Containers stopped."
echo ""

# --- Step 5: Remove old web image (force rebuild with new .dockerignore) ---
echo "--- Step 5: Removing old web image ---"
if [[ -n "$OLD_IMAGE_ID" ]]; then
    docker rmi "$OLD_IMAGE_ID" --force 2>/dev/null || true
    echo "  Old image $OLD_IMAGE_ID removed."
else
    echo "  No old image to remove."
fi
echo ""

# --- Step 6: Rebuild and start ---
echo "--- Step 6: Building new image and starting containers ---"
echo "  (This will take a minute -- installing Pandoc + Python deps)"
docker compose -f "$COMPOSE_FILE" up -d --build
echo "  Containers started."
echo ""

# --- Step 7: Health check ---
echo "--- Step 7: Waiting for health check ---"
ATTEMPTS=0
MAX_ATTEMPTS=30
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

if [[ "$HEALTHY" -eq 0 ]]; then
    echo ""
    echo "HEALTH CHECK FAILED after ${MAX_ATTEMPTS} attempts."
    echo ""
    echo "Debug commands:"
    echo "  docker compose -f $COMPOSE_FILE logs web --tail 50"
    echo "  docker compose -f $COMPOSE_FILE exec web python -c 'import acb_large_print; print(acb_large_print.__version__)'"
    echo ""
    echo "Rollback (if you need the old version running immediately):"
    echo "  cd $APP_ROOT && git checkout HEAD~1 -- web/Dockerfile .dockerignore"
    echo "  cd $WEB_ROOT && docker compose -f $COMPOSE_FILE up -d --build"
    exit 1
fi
echo "  Health check: PASSED"
echo ""

# --- Step 8: Verify Pandoc is available inside container ---
echo "--- Step 8: Verifying Pandoc inside container ---"
PANDOC_VER=$(docker compose -f "$COMPOSE_FILE" exec -T web pandoc --version 2>/dev/null | head -1 || echo "NOT FOUND")
echo "  $PANDOC_VER"

if [[ "$PANDOC_VER" == "NOT FOUND" ]]; then
    echo "  WARNING: Pandoc not found in container. convert-to-HTML will be unavailable."
fi
echo ""

# --- Step 9: Verify desktop-only files are NOT in the image ---
echo "--- Step 9: Verifying slim build (desktop files excluded) ---"
SLIM_OK=true
for MOD in cli gui __main__; do
    if docker compose -f "$COMPOSE_FILE" exec -T web python -c "import acb_large_print.${MOD}" 2>/dev/null; then
        echo "  WARNING: acb_large_print.${MOD} found in image (expected excluded)"
        SLIM_OK=false
    else
        echo "  OK: acb_large_print.${MOD} not in image"
    fi
done

if [[ "$SLIM_OK" == "true" ]]; then
    echo "  Slim build verified -- no desktop modules in image."
else
    echo "  NOTE: Desktop modules still present. Check .dockerignore placement."
fi
echo ""

# --- Step 10: Verify routes respond ---
echo "--- Step 10: Verifying web routes ---"
check_route() {
    local label="$1"
    local path="$2"
    local code
    code=$(docker compose -f "$COMPOSE_FILE" exec -T web python -c \
        "import urllib.request; r = urllib.request.urlopen('http://localhost:8000${path}'); print(r.status)" 2>/dev/null || echo "FAIL")
    if [[ "$code" == "200" ]]; then
        echo "  $label: OK"
    else
        echo "  $label: $code"
    fi
}

check_route "GET /" "/"
check_route "GET /audit/" "/audit/"
check_route "GET /fix/" "/fix/"
check_route "GET /convert/" "/convert/"
check_route "GET /about/" "/about/"
check_route "GET /health" "/health"
echo ""

# --- Step 11: Prune old images and build cache ---
echo "--- Step 11: Cleaning up ---"
PRUNED=$(docker image prune -f 2>&1 | tail -1)
echo "  Images: $PRUNED"
CACHE=$(docker builder prune -f 2>&1 | tail -1)
echo "  Build cache: $CACHE"
echo ""

# --- Step 12: Image size comparison ---
echo "--- Step 12: Image size comparison ---"
NEW_IMAGE_ID=$(docker images --filter "reference=*web*" --format "{{.ID}}" 2>/dev/null | head -1 || true)
if [[ -n "$NEW_IMAGE_ID" ]]; then
    NEW_SIZE=$(docker images --format "{{.Size}}" "$NEW_IMAGE_ID" 2>/dev/null || echo "unknown")
    echo "  Old: $OLD_SIZE"
    echo "  New: $NEW_SIZE"
else
    echo "  Could not determine new image size."
fi
echo ""

# --- Done ---
echo "=== Migration Complete ==="
echo ""
echo "Container status:"
docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}"
echo ""
echo "What was done:"
echo "  1. Pulled latest code"
echo "  2. Rebuilt Docker image with .dockerignore (excludes CLI, GUI, desktop files)"
echo "  3. Pandoc installed in container for Markdown/RST/ODT/RTF -> ACB HTML"
echo "  4. Old images pruned"
echo ""
echo "Test these URLs:"
echo "  https://${APP_DOMAIN}/"
echo "  https://${APP_DOMAIN}/convert/     (upload .md -> get ACB HTML)"
echo "  https://${APP_DOMAIN}/health"
echo ""
echo "The feedback-data volume was NOT modified."
echo ""
echo "Next steps:"
echo "  bash ~/app/scripts/post-deploy-check.sh   (verify cron, health, prune)"
