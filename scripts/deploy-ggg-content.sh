#!/usr/bin/env bash
# deploy-ggg-content.sh -- Sync podcast site assets into ~/app/ggg and roll stack
#
# Usage (from the server):
#   bash ~/app/scripts/deploy-ggg-content.sh ~/ggg
#
# Notes:
#   - This script copies content from a server-local source directory.
#   - Keep MP3 files in server storage; do not commit media into Git.
#   - The main rollout still uses existing Glow scripts.

set -euo pipefail

APP_ROOT="${APP_ROOT:-$HOME/app}"
WEB_ROOT="${WEB_ROOT:-$APP_ROOT/web}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
MAINT_SCRIPT="${MAINT_SCRIPT:-$APP_ROOT/scripts/maintenance-mode.sh}"
DEPLOY_SCRIPT="${DEPLOY_SCRIPT:-$APP_ROOT/scripts/deploy-app.sh}"
SRC_DIR="${1:-$HOME/ggg}"
DEST_DIR="${DEST_DIR:-$APP_ROOT/ggg}"

if [[ ! -d "$SRC_DIR" ]]; then
    echo "ERROR: Source directory not found: $SRC_DIR"
    echo "Pass a source directory, for example:"
    echo "  bash ~/app/scripts/deploy-ggg-content.sh ~/ggg"
    exit 1
fi

if [[ ! -f "$WEB_ROOT/$COMPOSE_FILE" ]]; then
    echo "ERROR: Missing compose file: $WEB_ROOT/$COMPOSE_FILE"
    exit 1
fi

if [[ ! -x "$MAINT_SCRIPT" ]]; then
    echo "ERROR: Missing or non-executable maintenance script: $MAINT_SCRIPT"
    exit 1
fi

if [[ ! -x "$DEPLOY_SCRIPT" ]]; then
    echo "ERROR: Missing or non-executable deploy script: $DEPLOY_SCRIPT"
    exit 1
fi

mkdir -p "$DEST_DIR"

echo "--- Syncing GGG content ---"
echo "Source:      $SRC_DIR"
echo "Destination: $DEST_DIR"
rsync -av --delete --exclude '.git/' "$SRC_DIR/" "$DEST_DIR/"

if [[ -f "$DEST_DIR/generator/generate-site.js" && -f "$DEST_DIR/generator/validate-feed.js" ]]; then
    if command -v node >/dev/null 2>&1; then
        echo "--- Regenerating and validating feed ---"
        (cd "$DEST_DIR" && node generator/generate-site.js && node generator/validate-feed.js)
    else
        echo "WARN: Node.js not found; skipping feed regeneration/validation."
    fi
else
    echo "WARN: Generator scripts not found; skipping feed regeneration/validation."
fi

echo "--- Rolling deployment with existing Glow scripts ---"
bash "$MAINT_SCRIPT" on

set +e
bash "$DEPLOY_SCRIPT"
DEPLOY_EXIT=$?
set -e

bash "$MAINT_SCRIPT" off

if [[ "$DEPLOY_EXIT" -ne 0 ]]; then
    echo "ERROR: deploy-app.sh failed with exit code $DEPLOY_EXIT"
    exit "$DEPLOY_EXIT"
fi

echo "--- GGG deployment complete ---"
echo "Verify:"
echo "  curl -I https://lp.csedesigns.com/ggg/"
echo "  curl -I https://lp.csedesigns.com/ggg/feed.xml"
