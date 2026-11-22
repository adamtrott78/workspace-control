#!/usr/bin/env bash
# Persistent zero-GitHub-API tmux launcher for the PA3-PA8/t007 tight60 rerun.
# This launcher performs no network access. The dashboard itself is host-local only.

set -u

SESSION="${MTH602_T007_TMUX_SESSION:-mth602-t007}"
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
DASH="$HERE/mth602_t007_rerun_local_dashboard.py"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed or not on PATH" >&2
  exit 2
fi

if [ ! -f "$DASH" ]; then
  echo "dashboard not found: $DASH" >&2
  exit 2
fi

# Replace only this observer session. This does not touch the scientific runner.
tmux kill-session -t "$SESSION" 2>/dev/null || true

# sudo is observational here: it is needed because the isolated scientific
# runner may hide process arguments and runner-temp directories from the user.
tmux new-session -d -s "$SESSION" "sudo -E python3 '$DASH'"

echo "Started tmux dashboard: $SESSION"
echo "GitHub/provider polling: 0"
echo "Attach: tmux attach -t $SESSION"
exec tmux attach -t "$SESSION"
