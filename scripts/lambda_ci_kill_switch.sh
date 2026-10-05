#!/usr/bin/env bash
# Static P1 recovery artifact. Intended for authorized root use only.
set -Eeuo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: must run as root" >&2
  exit 70
fi
if [[ "${1:-}" != "--confirm-workspace-ci-kill" ]]; then
  echo "Usage: $0 --confirm-workspace-ci-kill" >&2
  exit 71
fi

systemctl stop workspace-ci-controller.service 2>/dev/null || true
systemctl stop workspace-ci-provisioner.socket workspace-ci-provisioner.service 2>/dev/null || true

mapfile -t units < <(
  systemctl list-units --all --plain --no-legend 'workspace-ci-*.service' 2>/dev/null |
  awk '{print $1}' |
  grep -E '^workspace-ci-[A-Za-z0-9_.@-]+\.service$' || true
)

for unit in "${units[@]:-}"; do
  [[ -n "$unit" ]] || continue
  systemctl stop "$unit" 2>/dev/null || true
  systemctl kill --kill-who=all --signal=KILL "$unit" 2>/dev/null || true
done

echo "WORKSPACE_CI_KILL_SWITCH=COMPLETE"
echo "NOTE=No project repositories or production services were intentionally modified."
