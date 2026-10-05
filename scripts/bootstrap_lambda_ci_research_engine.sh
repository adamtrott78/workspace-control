#!/usr/bin/env bash
# STATIC P1 ARTIFACT. DO NOT RUN until the owning task explicitly enters P2.
set -Eeuo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: bootstrap must be run as root during an authorized P2 gate" >&2
  exit 70
fi

if [[ "${WORKSPACE_CI_P2_AUTHORIZED:-}" != "YES" ]]; then
  echo "ERROR: P2 authorization guard not present; refusing host mutation" >&2
  exit 71
fi

# This script intentionally remains a guarded skeleton in P1.
# P2 must fill exact package/controller install locations only after:
# - P1 compatibility probe PASS
# - static review PASS
# - GitHub App/PAT credential plan accepted
# - systemd device/network sandbox probes PASS

echo "P2_BOOTSTRAP_GUARD=PASS"
echo "NO_MUTATION_IMPLEMENTED_IN_P1=true"
exit 72
