#!/usr/bin/env bash
set -euo pipefail

systemctl disable --now \
  workspace-shell-tunnel.service \
  workspace-shell-mcp.service \
  workspace-shell-root-broker.service \
  workspace-shell-job-launcher.service

echo "WORKSPACE_SHELL_DISABLED=PASS"
