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
  /etc/systemd/system/workspace-ci-controller-gpu.service.d/network.conf \
  /etc/systemd/system/workspace-ci-controller-gpu.service \
  /etc/systemd/system/workspace-ci-controller.service.d/network.conf \
  /etc/systemd/system/workspace-ci-controller.service \
  /etc/systemd/system/workspace-ci-provisioner.service \
  /etc/systemd/system/workspace-ci-provisioner.socket \
  /opt/workspace-ci/controller/lambda-ci-controller \
  /opt/workspace-ci/controller/stage-pat \
  /opt/workspace-ci/provisioner/lambda_ci_admission.py \
  /opt/workspace-ci/provisioner/lambda_ci_provisioner.py \
  /opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py \
  /opt/workspace-ci/provisioner/lambda_ci_runtime.py \
  /opt/workspace-ci/cache-manager/lambda_ci_trusted_cache.py \
  /etc/workspace-ci/projects/research-engine.json \
  /etc/workspace-ci/lambda-ci-systemd-profiles.v1.json \
  /etc/workspace-ci/lambda-ci-upstream-pins.v1.json \
  /etc/workspace-ci/lambda-ci-workload-policy.v1.json
do
  [[ -e "$path" ]] && rm -f -- "$path"
done

systemctl daemon-reload

echo "NOTE=Controller credential and provisioner evidence/state are intentionally preserved for reviewed follow-up."
echo "NOTE=Project data/cache/user deletion is intentionally NOT automatic."
echo "NOTE=Runner/controller users and /srv/workspace-ci require separate reviewed removal after evidence preservation."
echo "WORKSPACE_CI_STATIC_UNINSTALL=COMPLETE"
