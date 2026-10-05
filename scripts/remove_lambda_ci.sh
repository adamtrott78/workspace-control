#!/usr/bin/env bash
# Static P1 uninstall/recovery skeleton. Do not run before an authorized P2/Pilot.
set -Eeuo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: must run as root" >&2
  exit 70
fi
if [[ "${1:-}" != "--confirm-remove-workspace-ci" ]]; then
  echo "Usage: $0 --confirm-remove-workspace-ci" >&2
  exit 71
fi

"$(dirname "$0")/lambda_ci_kill_switch.sh" --confirm-workspace-ci-kill

# Only exact workspace-ci service/config paths are eligible for removal.
for path in \
  /etc/systemd/system/workspace-ci-controller.service \
  /etc/systemd/system/workspace-ci-provisioner.service \
  /etc/systemd/system/workspace-ci-provisioner.socket
do
  [[ -e "$path" ]] && rm -f -- "$path"
done

systemctl daemon-reload

echo "NOTE=Project data/cache/user deletion is intentionally NOT automatic."
echo "NOTE=Runner/controller users and /srv/workspace-ci require separate reviewed removal after evidence preservation."
echo "WORKSPACE_CI_STATIC_UNINSTALL=COMPLETE"
