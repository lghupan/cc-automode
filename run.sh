#!/usr/bin/env bash
# run.sh — Launch Claude Code with auto mode classifier active
#
# What this does:
#   1. Validates ANTHROPIC_API_KEY is set (required by classifier.py)
#   2. Installs anthropic Python SDK if missing
#   3. Resets the per-session denial state (fresh start each run)
#   4. Launches `claude --dangerously-skip-permissions` so Claude Code
#      does not pause for interactive permission prompts — the
#      classifier.py PreToolUse hook is the actual security gate.
#
# Usage:
#   ./run.sh [claude arguments...]
#   ./run.sh --print "implement feature X"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Validate API key ─────────────────────────────────────────────────────────
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "[auto-mode] ERROR: ANTHROPIC_API_KEY is not set." >&2
  echo "  Export it first:  export ANTHROPIC_API_KEY=sk-ant-..." >&2
  exit 1
fi

# ── Install dependencies if missing ──────────────────────────────────────────
if ! python3 -c "import anthropic" 2>/dev/null; then
  echo "[auto-mode] Installing anthropic Python SDK..." >&2
  pip3 install anthropic 2>&1 | tail -5
fi

# ── Reset denial state for a clean session ───────────────────────────────────
# (classifier.py also resets on session_id mismatch, but explicit is clearer)
rm -f "$PWD/.automode-state.json"

echo "[auto-mode] Starting Claude Code with auto mode classifier active."
echo "[auto-mode] Classifier:            $SCRIPT_DIR/classifier.py"
echo "[auto-mode] Max consecutive blocks: $((3))"
echo "[auto-mode] Max total blocks:       $((20))"
echo ""

# ── Launch Claude Code ────────────────────────────────────────────────────────
# --dangerously-skip-permissions  → layer 2: Claude Code won't pause for edits
# The PreToolUse hook in .claude/settings.json runs classifier.py for all tools
exec claude --dangerously-skip-permissions "$@"
