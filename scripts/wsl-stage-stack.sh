#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-up}"
PORT="${GLOW_WSL_PORT:-8000}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
WEB_ROOT="$REPO_ROOT/web"

cd "$WEB_ROOT"

compose() {
  docker compose -f docker-compose.yml -f docker-compose.wsl.yml "$@"
}

case "$ACTION" in
  up)
    export GLOW_ENABLE_AI="${GLOW_ENABLE_AI:-0}"
    export GLOW_ENABLE_AI_CHAT="${GLOW_ENABLE_AI_CHAT:-0}"
    export GLOW_ENABLE_AI_WHISPERER="${GLOW_ENABLE_AI_WHISPERER:-0}"
    export GLOW_ENABLE_AI_HEADING_FIX="${GLOW_ENABLE_AI_HEADING_FIX:-0}"
    export GLOW_ENABLE_AI_ALT_TEXT="${GLOW_ENABLE_AI_ALT_TEXT:-0}"
    export GLOW_ENABLE_AI_MARKITDOWN_LLM="${GLOW_ENABLE_AI_MARKITDOWN_LLM:-0}"

    compose up -d --build

    for attempt in $(seq 1 40); do
      if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null; then
        exit 0
      fi
      sleep 3
    done

    compose logs --tail 50 web pipeline
    exit 1
    ;;
  down)
    compose down
    ;;
  logs)
    compose logs --tail 50 web pipeline
    ;;
  *)
    echo "Usage: $0 {up|down|logs}" >&2
    exit 2
    ;;
esac