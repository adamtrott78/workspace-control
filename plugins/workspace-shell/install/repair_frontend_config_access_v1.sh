#!/usr/bin/env bash
# Restore the commissioned frontend.json access contract after the
# workspace-shell-mcp-v1 authority/source split accidentally installed the
# config as root:root 0600.
#
# This helper is intentionally incident-specific and source-pinned. It changes
# only frontend.json ownership/mode, then restarts the unprivileged MCP frontend
# and its dependent tunnel after local health proves the frontend is usable.
set -Eeuo pipefail

EXPECTED_SHA="01a95b61410e2f427b9885a19e6a0b9c5ee60a38"
FRONTEND="/etc/workspace-shell/frontend.json"
AUTHORITY="/etc/workspace-shell/authority/tasks/active/workspace-shell-mcp-v1.json"
SOURCE="/srv/workspace-shell/workspace-control"
MCP_SERVICE="workspace-shell-mcp.service"
TUNNEL_SERVICE="workspace-shell-tunnel.service"

fail() {
  printf 'WORKSPACE_SHELL_FRONTEND_ACCESS_REPAIR=FAIL reason=%s\n' "$*" >&2
  exit 70
}

echo "=== WORKSPACE SHELL FRONTEND CONFIG ACCESS REPAIR ==="

[ "$(sudo git -C "$SOURCE" rev-parse HEAD)" = "$EXPECTED_SHA" ] \
  || fail "execution source SHA mismatch"

sudo test -f "$FRONTEND" || fail "frontend config missing"
if sudo test -L "$FRONTEND"; then
  fail "frontend config must not be a symlink"
fi
sudo test -f "$AUTHORITY" || fail "authority capsule missing"

sudo /usr/bin/python3 - "$FRONTEND" "$AUTHORITY" "$EXPECTED_SHA" <<'PY'
import json
import pathlib
import sys

frontend_path = pathlib.Path(sys.argv[1])
authority_path = pathlib.Path(sys.argv[2])
expected_sha = sys.argv[3]

frontend = json.loads(frontend_path.read_text())
if frontend.get("authority_root") != "/etc/workspace-shell/authority":
    raise SystemExit("frontend authority_root mismatch")

authority = json.loads(authority_path.read_text())
repos = authority.get("repositories")
if not isinstance(repos, list):
    raise SystemExit("authority repositories missing")
matches = [
    repo
    for repo in repos
    if isinstance(repo, dict) and repo.get("name") == "workspace-control"
]
if len(matches) != 1:
    raise SystemExit("workspace-control authority binding ambiguous")
remote = matches[0].get("remote")
if not isinstance(remote, dict) or remote.get("checkpoint_sha") != expected_sha:
    raise SystemExit("authority checkpoint mismatch")
PY

[ "$(sudo systemctl show "$MCP_SERVICE" --property=User --value)" = "workspace-shell-mcp" ] \
  || fail "MCP service user drift"
[ "$(sudo systemctl show "$MCP_SERVICE" --property=Group --value)" = "workspace-shell-mcp" ] \
  || fail "MCP service group drift"

PRE_META="$(sudo stat -Lc '%U:%G:%a' "$FRONTEND")"
echo "FRONTEND_CONFIG_PRE_META=$PRE_META"

# The commissioned contract in activate_live.sh is root:workspace-shell-mcp 0640.
# Restore only that metadata; do not rewrite the config bytes.
sudo chown root:workspace-shell-mcp "$FRONTEND"
sudo chmod 0640 "$FRONTEND"

POST_META="$(sudo stat -Lc '%U:%G:%a' "$FRONTEND")"
[ "$POST_META" = "root:workspace-shell-mcp:640" ] \
  || fail "frontend config metadata repair did not hold"
sudo -u workspace-shell-mcp test -r "$FRONTEND" \
  || fail "frontend identity still cannot read frontend.json"

sudo -u workspace-shell-mcp /usr/bin/python3 - "$FRONTEND" <<'PY'
import json
import pathlib
import sys
obj = json.loads(pathlib.Path(sys.argv[1]).read_text())
if obj.get("authority_root") != "/etc/workspace-shell/authority":
    raise SystemExit("frontend config unreadable or authority_root changed")
PY

echo "FRONTEND_CONFIG_ACCESS=PASS meta=$POST_META"

sudo systemctl reset-failed "$MCP_SERVICE" >/dev/null 2>&1 || true
sudo systemctl restart "$MCP_SERVICE"

MCP_READY=0
for _ in $(seq 1 20); do
  if sudo systemctl is-active --quiet "$MCP_SERVICE" && \
     sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 2 \
       --cacert /etc/workspace-shell/tunnel/ca.crt \
       --cert /etc/workspace-shell/tunnel/client.crt \
       --key /etc/workspace-shell/tunnel/client.key \
       https://127.0.0.1:8797/healthz >/dev/null 2>&1; then
    MCP_READY=1
    break
  fi
  sleep 0.5
done
[ "$MCP_READY" = 1 ] || fail "MCP frontend did not become locally healthy"

INIT_RESPONSE="$(mktemp)"
trap 'rm -f "$INIT_RESPONSE"' EXIT
sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 5 \
  --cacert /etc/workspace-shell/tunnel/ca.crt \
  --cert /etc/workspace-shell/tunnel/client.crt \
  --key /etc/workspace-shell/tunnel/client.key \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  --data-binary '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"workspace-shell-frontend-access-repair","version":"0.1.0"}}}' \
  https://127.0.0.1:8797/mcp >"$INIT_RESPONSE"

sudo /usr/bin/python3 - "$INIT_RESPONSE" <<'PY'
import json
import pathlib
import sys
payload = json.loads(pathlib.Path(sys.argv[1]).read_text())
if payload.get("jsonrpc") != "2.0" or payload.get("id") != 1:
    raise SystemExit("invalid MCP initialize envelope")
result = payload.get("result")
if not isinstance(result, dict):
    raise SystemExit("MCP initialize missing result")
if result.get("serverInfo", {}).get("name") != "workspace-shell":
    raise SystemExit("MCP serverInfo mismatch")
PY
echo "LOCAL_MCP_INITIALIZE=PASS"

sudo systemctl restart "$TUNNEL_SERVICE"

TUNNEL_READY=0
for _ in $(seq 1 40); do
  HEALTH_URL="$(sudo -u workspace-shell-tunnel cat /var/lib/workspace-shell/tunnel/health.url 2>/dev/null || true)"
  case "$HEALTH_URL" in
    http://127.0.0.1:*)
      if /usr/bin/curl -fsS --max-time 2 "$HEALTH_URL/readyz" >/dev/null 2>&1; then
        TUNNEL_READY=1
        break
      fi
      ;;
  esac
  sleep 0.5
done
[ "$TUNNEL_READY" = 1 ] || fail "tunnel did not become ready"
echo "TUNNEL_READY=PASS"

for svc in \
  workspace-shell-job-launcher.service \
  workspace-shell-root-broker.service \
  "$MCP_SERVICE" \
  "$TUNNEL_SERVICE"
do
  sudo systemctl is-active --quiet "$svc" || fail "$svc is not active"
  ENABLED="$(sudo systemctl is-enabled "$svc" 2>/dev/null || true)"
  [ "$ENABLED" = "disabled" ] || fail "$svc boot state changed: $ENABLED"
done

sleep 3
sudo systemctl is-active --quiet "$MCP_SERVICE" \
  || fail "MCP frontend failed post-repair stability check"
sudo systemctl is-active --quiet "$TUNNEL_SERVICE" \
  || fail "tunnel failed post-repair stability check"

echo "SERVICES_ACTIVE_BOOT_DISABLED=PASS"
echo "WORKSPACE_SHELL_FRONTEND_ACCESS_REPAIR=PASS"
