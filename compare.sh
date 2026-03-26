#!/usr/bin/env bash
# compare.sh — Build all containers, run benchmarks, print side-by-side report
#
# Usage:
#   ./compare.sh [--skip-build] [--only custom|official|yolo]
#
# Requirements:
#   - Docker (docker compose v2)
#   - ANTHROPIC_API_KEY exported

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESULTS_DIR="$SCRIPT_DIR/results"
SKIP_BUILD=false
ONLY=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-build) SKIP_BUILD=true; shift ;;
    --only) ONLY="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

# ── Validate ─────────────────────────────────────────────────────────────────
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set." >&2
  echo "  Export it first:  export ANTHROPIC_API_KEY=sk-ant-..." >&2
  exit 1
fi

# ── Build ─────────────────────────────────────────────────────────────────────
if [[ "$SKIP_BUILD" == false ]]; then
  echo "Building containers..."
  if [[ -z "$ONLY" ]]; then
    docker compose build
  else
    docker compose build "$ONLY"
  fi
fi

# ── Run ───────────────────────────────────────────────────────────────────────
mkdir -p "$RESULTS_DIR/custom" "$RESULTS_DIR/official" "$RESULTS_DIR/yolo"

run_container() {
  local svc=$1
  echo ""
  echo "━━━ Running: $svc ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  docker compose run --rm \
    -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    -v "$RESULTS_DIR/$svc:/results" \
    "$svc"
}

if [[ -z "$ONLY" ]]; then
  run_container custom
  run_container official
  run_container yolo
else
  run_container "$ONLY"
fi

# ── Report ────────────────────────────────────────────────────────────────────
echo ""
echo "━━━ Generating report ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$SCRIPT_DIR/benchmark/report.py" \
  "$RESULTS_DIR/custom/custom.json" \
  "$RESULTS_DIR/official/official.json" \
  "$RESULTS_DIR/yolo/yolo.json"
