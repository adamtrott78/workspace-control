#!/usr/bin/env bash
# Persistent zero-provider tmux launcher for the unified 10-pair t007 wave.

set -u

SESSION="${MTH602_T007_WAVE_SESSION:-mth602-t007-wave}"
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
DASH="$HERE/mth602_t007_fullmatrix_local_dashboard.py"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed or not on PATH" >&2
  exit 2
fi

if [ ! -f "$DASH" ]; then
  echo "dashboard not found: $DASH" >&2
  exit 2
fi

sudo -v || exit $?

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" "sudo -E python3 '$DASH'"

echo "Started unified t007 wave dashboard: $SESSION"
echo "Provider polling: 0"
echo "Attach: tmux attach -t $SESSION"
exec tmux attach -t "$SESSION"
