#!/usr/bin/env bash
# manual-migration-cutover.sh -- Manual SQLite-to-Neon cutover with validation and rollback
#
# Run from local repo root:
#   bash scripts/manual-migration-cutover.sh --server deploy@YOUR_SERVER_IP
#
# What this script does:
#   1) Creates a clean, tracked-only code bundle from current HEAD
#   2) Uploads that bundle to the server and backs up current ~/app
#   3) Enables maintenance mode
#   4) Runs SQLite -> Postgres migration
#   5) Validates row counts (SQLite vs Postgres) for migrated tables
#   6) Runs health checks
#   7) Automatically rolls back app files and DB snapshot on failure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SERVER=""
REMOTE_APP_ROOT="${REMOTE_APP_ROOT:-~/app}"
REMOTE_TMP_ROOT="${REMOTE_TMP_ROOT:-~/tmp}"
INSTANCE_DIR_REL="${INSTANCE_DIR_REL:-instance}"
RUN_DEPLOY_APP="${RUN_DEPLOY_APP:-1}"
MIGRATE_TRUNCATE="${MIGRATE_TRUNCATE:-0}"
SKIP_STRICT_GIT_CLEAN="${SKIP_STRICT_GIT_CLEAN:-0}"

usage() {
    cat <<EOF
Usage:
  bash scripts/manual-migration-cutover.sh --server deploy@YOUR_SERVER_IP [options]

Required:
  --server USER@HOST          SSH target for deployment user

Optional:
  --remote-app-root PATH      Default: ~/app
  --remote-tmp-root PATH      Default: ~/tmp
  --instance-dir-rel PATH     Default: instance
  --skip-deploy-app           Only migrate + validate; do not run deploy-app.sh
  --truncate                  Pass --truncate to migrate_sqlite_to_neon.py
  --allow-dirty-git           Allow local dirty git tree (still ships tracked HEAD only)
  -h, --help                  Show this help

Environment:
  REMOTE_APP_ROOT             Override remote app root
  REMOTE_TMP_ROOT             Override remote tmp root
  INSTANCE_DIR_REL            Override SQLite dir relative to app root
  RUN_DEPLOY_APP              1 (default) or 0
  MIGRATE_TRUNCATE            1 or 0 (default)
  SKIP_STRICT_GIT_CLEAN       1 or 0 (default)
EOF
}

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --server)
            SERVER="${2:-}"
            shift 2
            ;;
        --remote-app-root)
            REMOTE_APP_ROOT="${2:-}"
            shift 2
            ;;
        --remote-tmp-root)
            REMOTE_TMP_ROOT="${2:-}"
            shift 2
            ;;
        --instance-dir-rel)
            INSTANCE_DIR_REL="${2:-}"
            shift 2
            ;;
        --skip-deploy-app)
            RUN_DEPLOY_APP=0
            shift
            ;;
        --truncate)
            MIGRATE_TRUNCATE=1
            shift
            ;;
        --allow-dirty-git)
            SKIP_STRICT_GIT_CLEAN=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown argument: $1"
            ;;
    esac
done

[[ -n "$SERVER" ]] || {
    usage
    die "--server is required"
}

command -v git >/dev/null 2>&1 || die "git is required"
command -v ssh >/dev/null 2>&1 || die "ssh is required"
command -v scp >/dev/null 2>&1 || die "scp is required"

if [[ "$SKIP_STRICT_GIT_CLEAN" != "1" ]]; then
    if ! git -C "$REPO_ROOT" diff --quiet || ! git -C "$REPO_ROOT" diff --cached --quiet; then
        die "Local git tree is dirty. Commit/stash changes or use --allow-dirty-git."
    fi
fi

log "Creating clean tracked-only bundle from HEAD"
TS="$(date -u +%Y%m%d-%H%M%S)"
HEAD_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD)"
BUNDLE_NAME="glow-cutover-${TS}-${HEAD_SHA:0:12}.tar.gz"
LOCAL_BUNDLE="${REPO_ROOT}/${BUNDLE_NAME}"

trap 'rm -f "$LOCAL_BUNDLE"' EXIT

git -C "$REPO_ROOT" archive --format=tar.gz -o "$LOCAL_BUNDLE" HEAD

log "Testing SSH connectivity to ${SERVER}"
ssh "$SERVER" "echo connected >/dev/null"

log "Uploading clean bundle to server"
ssh "$SERVER" "mkdir -p ${REMOTE_TMP_ROOT}"
scp "$LOCAL_BUNDLE" "${SERVER}:${REMOTE_TMP_ROOT}/${BUNDLE_NAME}"

log "Starting remote migration + validation + rollback-guard workflow"
ssh "$SERVER" \
    "BUNDLE_NAME='${BUNDLE_NAME}' REMOTE_APP_ROOT='${REMOTE_APP_ROOT}' REMOTE_TMP_ROOT='${REMOTE_TMP_ROOT}' INSTANCE_DIR_REL='${INSTANCE_DIR_REL}' RUN_DEPLOY_APP='${RUN_DEPLOY_APP}' MIGRATE_TRUNCATE='${MIGRATE_TRUNCATE}' bash -s" <<'REMOTE_EOF'
set -euo pipefail

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

REMOTE_APP_ROOT="${REMOTE_APP_ROOT:-~/app}"
REMOTE_TMP_ROOT="${REMOTE_TMP_ROOT:-~/tmp}"
INSTANCE_DIR_REL="${INSTANCE_DIR_REL:-instance}"
RUN_DEPLOY_APP="${RUN_DEPLOY_APP:-1}"
MIGRATE_TRUNCATE="${MIGRATE_TRUNCATE:-0}"

APP_ROOT="${REMOTE_APP_ROOT/#\~/$HOME}"
TMP_ROOT="${REMOTE_TMP_ROOT/#\~/$HOME}"
INSTANCE_DIR="${APP_ROOT}/${INSTANCE_DIR_REL}"
STAGING_DIR="${TMP_ROOT}/glow-cutover-${BUNDLE_NAME%.tar.gz}"

mkdir -p "$TMP_ROOT"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

ARCHIVE_PATH="${TMP_ROOT}/${BUNDLE_NAME}"
[[ -f "$ARCHIVE_PATH" ]] || { echo "ERROR: bundle not found at $ARCHIVE_PATH" >&2; exit 1; }

if [[ ! -d "$APP_ROOT" ]]; then
  echo "ERROR: APP root missing: $APP_ROOT" >&2
  exit 1
fi

if [[ ! -f "$APP_ROOT/web/.env" ]]; then
  echo "ERROR: Missing required env file: $APP_ROOT/web/.env" >&2
  exit 1
fi

log "Preparing backup paths"
TS="$(date -u +%Y%m%d-%H%M%S)"
BACKUP_ROOT="$HOME/backups"
APP_BACKUP_DIR="$BACKUP_ROOT/app"
DB_BACKUP_DIR="$BACKUP_ROOT/db"
mkdir -p "$APP_BACKUP_DIR" "$DB_BACKUP_DIR"
APP_BACKUP_TAR="$APP_BACKUP_DIR/app-pre-cutover-${TS}.tar.gz"
DB_BACKUP_SQL="$DB_BACKUP_DIR/pre-cutover-${TS}.sql"

ROLLBACK_NEEDED=0
MAINTENANCE_ON=0
DB_BACKUP_CREATED=0

rollback() {
  if [[ "$ROLLBACK_NEEDED" != "1" ]]; then
    return
  fi

  log "Rollback triggered"

  if [[ "$DB_BACKUP_CREATED" == "1" && -f "$DB_BACKUP_SQL" ]]; then
    if [[ -n "${PG_URL:-}" ]]; then
      log "Restoring PostgreSQL snapshot from $DB_BACKUP_SQL"
      psql "$PG_URL" -v ON_ERROR_STOP=1 -f "$DB_BACKUP_SQL" || true
    fi
  fi

  if [[ -f "$APP_BACKUP_TAR" ]]; then
    log "Restoring app files from $APP_BACKUP_TAR"
    rm -rf "$APP_ROOT"
    mkdir -p "$APP_ROOT"
    tar -xzf "$APP_BACKUP_TAR" -C "$APP_ROOT" --strip-components=1 || true
    chmod 700 "$APP_ROOT/scripts"/*.sh 2>/dev/null || true
  fi

  if [[ "$MAINTENANCE_ON" == "1" && -x "$APP_ROOT/scripts/maintenance-mode.sh" ]]; then
    log "Disabling maintenance mode after rollback"
    bash "$APP_ROOT/scripts/maintenance-mode.sh" off || true
  fi
}
trap rollback ERR

log "Backing up current app tree to $APP_BACKUP_TAR"
tar -czf "$APP_BACKUP_TAR" -C "$(dirname "$APP_ROOT")" "$(basename "$APP_ROOT")"

log "Extracting uploaded bundle"
tar -xzf "$ARCHIVE_PATH" -C "$STAGING_DIR"

log "Syncing staged files into app root"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "$STAGING_DIR"/ "$APP_ROOT"/
else
  find "$APP_ROOT" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a "$STAGING_DIR"/. "$APP_ROOT"/
fi
chmod 700 "$APP_ROOT/scripts"/*.sh 2>/dev/null || true

log "Loading DATABASE_URL from web/.env"
DATABASE_URL="$(grep -E '^DATABASE_URL=' "$APP_ROOT/web/.env" | tail -n1 | cut -d= -f2-)"
if [[ -z "$DATABASE_URL" ]]; then
  echo "ERROR: DATABASE_URL is missing in $APP_ROOT/web/.env" >&2
  exit 1
fi

PG_URL="$DATABASE_URL"
PG_URL="${PG_URL#\"}"
PG_URL="${PG_URL%\"}"
PG_URL="${PG_URL#\'}"
PG_URL="${PG_URL%\'}"
if [[ "$PG_URL" == postgresql+psycopg://* ]]; then
  PG_URL="postgresql://${PG_URL#postgresql+psycopg://}"
elif [[ "$PG_URL" == postgres://* ]]; then
  PG_URL="postgresql://${PG_URL#postgres://}"
fi

log "Creating PostgreSQL pre-migration snapshot"
pg_dump "$PG_URL" --clean --if-exists --no-owner --no-privileges > "$DB_BACKUP_SQL"
DB_BACKUP_CREATED=1

if [[ -x "$APP_ROOT/scripts/maintenance-mode.sh" ]]; then
  log "Enabling maintenance mode"
  bash "$APP_ROOT/scripts/maintenance-mode.sh" on
  MAINTENANCE_ON=1
fi

ROLLBACK_NEEDED=1

if [[ ! -d "$INSTANCE_DIR" ]]; then
  echo "ERROR: SQLite instance dir not found: $INSTANCE_DIR" >&2
  exit 1
fi

MIGRATE_ARGS=("$APP_ROOT/scripts/migrate_sqlite_to_neon.py" "--instance-dir" "$INSTANCE_DIR" "--target-url" "$DATABASE_URL")
if [[ "$MIGRATE_TRUNCATE" == "1" ]]; then
  MIGRATE_ARGS+=("--truncate")
fi

log "Running migration script"
python3 "${MIGRATE_ARGS[@]}"

log "Validating SQLite/PostgreSQL row counts"
python3 - "$INSTANCE_DIR" "$DATABASE_URL" <<'PYEOF'
import sqlite3
import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect, text

instance_dir = Path(sys.argv[1])
target_url = sys.argv[2]

sqlite_files = [
    "ai_quota.db",
    "feedback.db",
    "visitor_counter.db",
    "feature_flags.db",
    "glow_users.db",
    "admin_auth.db",
]

engine = create_engine(target_url)
pg_tables = set(inspect(engine).get_table_names())

failures = []
checked = 0

for file_name in sqlite_files:
    db_path = instance_dir / file_name
    if not db_path.exists():
        continue

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    table_rows = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [row[0] for row in table_rows]

    for table_name in table_names:
        if table_name.startswith("sqlite_"):
            continue
        if table_name not in pg_tables:
            failures.append(f"missing_postgres_table:{table_name}")
            continue

        sqlite_count = cur.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
        with engine.connect() as pg_conn:
            pg_count = pg_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()

        checked += 1
        if int(sqlite_count) != int(pg_count):
            failures.append(f"count_mismatch:{table_name}:sqlite={sqlite_count}:postgres={pg_count}")

    conn.close()

if failures:
    print("VALIDATION FAILED")
    for failure in failures:
        print(f" - {failure}")
    sys.exit(1)

print(f"VALIDATION PASSED: checked_tables={checked}")
PYEOF

if [[ "$RUN_DEPLOY_APP" == "1" ]]; then
  log "Running deploy-app.sh for final health-gated restart"
  bash "$APP_ROOT/scripts/deploy-app.sh"
else
  log "Skipping deploy-app.sh (--skip-deploy-app enabled)"
fi

if [[ "$MAINTENANCE_ON" == "1" ]]; then
  log "Disabling maintenance mode"
  bash "$APP_ROOT/scripts/maintenance-mode.sh" off
  MAINTENANCE_ON=0
fi

ROLLBACK_NEEDED=0
log "Cutover complete"
log "App backup: $APP_BACKUP_TAR"
log "DB backup:  $DB_BACKUP_SQL"
REMOTE_EOF

log "Manual migration cutover completed successfully"
