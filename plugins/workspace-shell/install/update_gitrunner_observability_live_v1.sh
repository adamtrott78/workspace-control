#!/usr/bin/env bash
set -Euo pipefail

# Transactional in-place update for the already accepted Workspace Shell v1.
#
# Changes only the GitRunner troubleshooting surface:
# - Workspace Shell MCP server code
# - root job-launcher code
# - frontend exact unit allowlist
# - launcher exact unit/log/maintenance-receipt read configuration
# - Workspace Shell authority artifact + matching broker verifier policy digest
#
# Explicitly preserves:
# - ChatGPT plugin/App identity
# - Secure MCP Tunnel ID/profile/runtime key
# - local TLS identities
# - frontend request-signing identity
# - accepted execution checkout /srv/workspace-shell/workspace-control
# - independent trusted authority root /etc/workspace-shell/authority
# - helper registry + trusted issuers + revocations
# - systemd unit definitions and boot-disabled state
# - all GitRunner v3 activation/canary state

ACCEPTED_DURABLE_HEAD="44b4e4f2020450c81cec56e86b711cdee7e651d9"
ACCEPTED_EXECUTION_SHA="01a95b61410e2f427b9885a19e6a0b9c5ee60a38"

ACCEPTED_SERVER_BLOB="1b6323099350f03f4958087ee71b0c345e1aaee2"
ACCEPTED_LAUNCHER_BLOB="f013957705d59b1442ee90a2a375afe631895099"
ACCEPTED_POLICY_BLOB="89fad48503bdf06e2f650cfc55a5fcaa561f857b"

CANDIDATE_SERVER_BLOB="ddc6cece98cf3c6057b7cd1b3208c1249d1c06d2"
CANDIDATE_LAUNCHER_BLOB="137ebebe46b63550abfb404e12ab0e1fd338ba12"
CANDIDATE_POLICY_BLOB="c2a18332cf4a3b13f48f3fd3cac0291ea294ae60"

ROOT="$(git rev-parse --show-toplevel)"
EXPECTED_HEAD="${1:-}"
CONFIRM="${WORKSPACE_SHELL_UPDATE_CONFIRM:-}"

RUNTIME="/opt/workspace-shell/runtime/plugins/workspace-shell"
SERVER_DST="$RUNTIME/server.js"
LAUNCHER_DST="$RUNTIME/root/job_launcher.py"
POLICY_DST="/etc/workspace-shell/policy/workspace-shell-mcp-authority-v2.json"
FRONTEND_CFG="/etc/workspace-shell/frontend.json"
LAUNCHER_CFG="/etc/workspace-shell/job-launcher.json"
BROKER_VERIFIER_CFG="/etc/workspace-shell/broker-verifier.json"

EXEC_SOURCE="/srv/workspace-shell/workspace-control"
AUTHORITY_ROOT="/etc/workspace-shell/authority"

TUNNEL_RUNTIME_KEY="/etc/workspace-shell/tunnel/runtime-key"
TUNNEL_CLIENT_KEY="/etc/workspace-shell/tunnel/client.key"
TUNNEL_CLIENT_CERT="/etc/workspace-shell/tunnel/client.crt"
TUNNEL_CA="/etc/workspace-shell/tunnel/ca.crt"
FRONTEND_SERVER_KEY="/etc/workspace-shell/frontend/server.key"
FRONTEND_SERVER_CERT="/etc/workspace-shell/frontend/server.crt"
FRONTEND_SIGNING_KEY="/etc/workspace-shell/frontend/request-signing.key"
FRONTEND_SIGNING_PUB="/etc/workspace-shell/frontend/request-signing.pub"
TUNNEL_PROFILE_DIR="/etc/workspace-shell/tunnel-client-profiles"

HELPER_REGISTRY="/etc/workspace-shell/helpers/registry.json"
TRUSTED_ISSUERS="/etc/workspace-shell/approval/trusted-issuers.json"
REVOCATIONS="/etc/workspace-shell/approval/revocations.json"

SERVICES=(
  workspace-shell-job-launcher.service
  workspace-shell-root-broker.service
  workspace-shell-mcp.service
  workspace-shell-tunnel.service
)

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

sha256_file() {
  sudo sha256sum "$1" | awk '{print $1}'
}

git_blob_file() {
  git hash-object "$1"
}

require_exact_git_sha() {
  [[ "$1" =~ ^[0-9a-f]{40}$ ]] || fail "$2 must be a full lowercase Git SHA"
}

service_active() {
  [ "$(systemctl is-active "$1" 2>/dev/null || true)" = "active" ]
}

service_boot_disabled() {
  local state
  state="$(systemctl is-enabled "$1" 2>/dev/null || true)"
  [ "$state" != "enabled" ]
}

ROOT="$(cd "$ROOT" && pwd)"
[ -n "$EXPECTED_HEAD" ] || fail "usage: $0 <exact-validated-head>"
require_exact_git_sha "$EXPECTED_HEAD" expected_head
[ "$CONFIRM" = "APPLY_GITRUNNER_OBSERVABILITY_V1" ]   || fail "set WORKSPACE_SHELL_UPDATE_CONFIRM=APPLY_GITRUNNER_OBSERVABILITY_V1"

cd "$ROOT"
OBSERVED_HEAD="$(git rev-parse HEAD)"
[ "$OBSERVED_HEAD" = "$EXPECTED_HEAD" ]   || fail "operator checkout HEAD does not match expected head"
[ -z "$(git status --porcelain=v1 --untracked-files=normal)" ]   || fail "operator checkout is dirty"
git merge-base --is-ancestor "$ACCEPTED_DURABLE_HEAD" "$EXPECTED_HEAD"   || fail "candidate does not descend from accepted Workspace Shell durable head"

echo "=== WORKSPACE SHELL OBSERVABILITY UPDATE: PREFLIGHT ==="

[ "$(sudo git -C "$EXEC_SOURCE" rev-parse HEAD)" = "$ACCEPTED_EXECUTION_SHA" ]   || fail "installed execution source is not the accepted live SHA"
[ -z "$(sudo git -C "$EXEC_SOURCE" status --porcelain=v1 --untracked-files=normal)" ]   || fail "installed execution source is dirty"
[ -d "$AUTHORITY_ROOT" ] || fail "trusted authority root is missing"

[ "$(git_blob_file "$SERVER_DST")" = "$ACCEPTED_SERVER_BLOB" ]   || fail "installed server.js is not the accepted live blob"
[ "$(git_blob_file "$LAUNCHER_DST")" = "$ACCEPTED_LAUNCHER_BLOB" ]   || fail "installed job_launcher.py is not the accepted live post-repair blob"
[ "$(git_blob_file "$POLICY_DST")" = "$ACCEPTED_POLICY_BLOB" ]   || fail "installed Workspace Shell policy is not the accepted live blob"

[ "$(git_blob_file "$ROOT/plugins/workspace-shell/server.js")" = "$CANDIDATE_SERVER_BLOB" ]   || fail "candidate server.js blob mismatch"
[ "$(git_blob_file "$ROOT/plugins/workspace-shell/root/job_launcher.py")" = "$CANDIDATE_LAUNCHER_BLOB" ]   || fail "candidate job_launcher.py blob mismatch"
[ "$(git_blob_file "$ROOT/architecture/workspace-shell-mcp-authority-v2.json")" = "$CANDIDATE_POLICY_BLOB" ]   || fail "candidate policy blob mismatch"

for svc in "${SERVICES[@]}"; do
  service_active "$svc" || fail "$svc is not active before update"
  service_boot_disabled "$svc" || fail "$svc is unexpectedly boot-enabled"
done

[ "$(stat -c '%U:%G:%a' "$FRONTEND_CFG")" = "root:workspace-shell-mcp:640" ]   || fail "frontend.json metadata does not match accepted contract"
[ "$(stat -c '%U:%G:%a' "$LAUNCHER_CFG")" = "root:root:644" ]   || fail "job-launcher.json metadata does not match accepted contract"
[ "$(stat -c '%U:%G:%a' "$BROKER_VERIFIER_CFG")" = "root:root:644" ]   || fail "broker-verifier.json metadata does not match accepted contract"

for path in   "$TUNNEL_RUNTIME_KEY"   "$TUNNEL_CLIENT_KEY"   "$TUNNEL_CLIENT_CERT"   "$TUNNEL_CA"   "$FRONTEND_SERVER_KEY"   "$FRONTEND_SERVER_CERT"   "$FRONTEND_SIGNING_KEY"   "$FRONTEND_SIGNING_PUB"   "$HELPER_REGISTRY"   "$TRUSTED_ISSUERS"   "$REVOCATIONS"; do
  sudo test -f "$path" || fail "preserved identity/authority file missing: $path"
done

TMP="$(mktemp -d /tmp/workspace-shell-observability-update.XXXXXX)"
MUTATION_STARTED=0
COMMITTED=0
UPDATE_ROOT="/var/lib/workspace-shell/updates/$EXPECTED_HEAD"

rollback_if_needed() {
  local rc="$?"
  trap - EXIT
  if [ "$MUTATION_STARTED" = "1" ] && [ "$COMMITTED" != "1" ]; then
    echo "=== WORKSPACE SHELL OBSERVABILITY UPDATE: ROLLBACK ===" >&2
    sudo systemctl stop       workspace-shell-tunnel.service       workspace-shell-mcp.service       workspace-shell-root-broker.service       workspace-shell-job-launcher.service >/dev/null 2>&1 || true

    sudo install -o root -g root -m 0644 "$UPDATE_ROOT/backup/server.js" "$SERVER_DST" || true
    sudo install -o root -g root -m 0755 "$UPDATE_ROOT/backup/job_launcher.py" "$LAUNCHER_DST" || true
    sudo install -o root -g root -m 0644 "$UPDATE_ROOT/backup/workspace-shell-mcp-authority-v2.json" "$POLICY_DST" || true
    sudo install -o root -g workspace-shell-mcp -m 0640 "$UPDATE_ROOT/backup/frontend.json" "$FRONTEND_CFG" || true
    sudo install -o root -g root -m 0644 "$UPDATE_ROOT/backup/job-launcher.json" "$LAUNCHER_CFG" || true
    sudo install -o root -g root -m 0644 "$UPDATE_ROOT/backup/broker-verifier.json" "$BROKER_VERIFIER_CFG" || true

    sudo systemctl start workspace-shell-job-launcher.service >/dev/null 2>&1 || true
    sudo systemctl start workspace-shell-root-broker.service >/dev/null 2>&1 || true
    sudo systemctl start workspace-shell-mcp.service >/dev/null 2>&1 || true
    sudo rm -f /var/lib/workspace-shell/tunnel/health.url
    sudo systemctl start workspace-shell-tunnel.service >/dev/null 2>&1 || true

    python3 - "$TMP/rollback-receipt.json" "$EXPECTED_HEAD" "$rc" <<'PY'
import json, sys
from datetime import datetime, timezone
path, head, rc = sys.argv[1:]
data = {
    "schema": "workspace-shell-observability-update-rollback.v1",
    "status": "ROLLED_BACK",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "expected_head": head,
    "failed_exit_code": int(rc),
}
open(path, "w", encoding="utf-8").write(
    json.dumps(data, indent=2, sort_keys=True) + "\n"
)
PY
    if [ -f "$TMP/rollback-receipt.json" ]; then
      sudo install -o root -g root -m 0600         "$TMP/rollback-receipt.json" "$UPDATE_ROOT/rollback-receipt.json" || true
    fi
  fi
  rm -rf "$TMP"
  exit "$rc"
}
trap rollback_if_needed EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

PRESERVED_BEFORE="$TMP/preserved-before.sha256"
for path in   "$TUNNEL_RUNTIME_KEY"   "$TUNNEL_CLIENT_KEY"   "$TUNNEL_CLIENT_CERT"   "$TUNNEL_CA"   "$FRONTEND_SERVER_KEY"   "$FRONTEND_SERVER_CERT"   "$FRONTEND_SIGNING_KEY"   "$FRONTEND_SIGNING_PUB"   "$HELPER_REGISTRY"   "$TRUSTED_ISSUERS"   "$REVOCATIONS"; do
  printf '%s  %s\n' "$(sha256_file "$path")" "$path" >> "$PRESERVED_BEFORE"
done
sudo find "$TUNNEL_PROFILE_DIR" -maxdepth 1 -type f -print0   | sort -z   | while IFS= read -r -d '' path; do
      printf '%s  %s\n' "$(sha256_file "$path")" "$path"
    done >> "$PRESERVED_BEFORE"

cp "$ROOT/plugins/workspace-shell/server.js" "$TMP/server.js"
cp "$ROOT/plugins/workspace-shell/root/job_launcher.py" "$TMP/job_launcher.py"
cp "$ROOT/architecture/workspace-shell-mcp-authority-v2.json" "$TMP/policy.json"
sudo cat "$FRONTEND_CFG" > "$TMP/frontend.json"
sudo cat "$LAUNCHER_CFG" > "$TMP/job-launcher.json"
sudo cat "$BROKER_VERIFIER_CFG" > "$TMP/broker-verifier.json"

python3 -   "$ROOT/plugins/workspace-shell/install/render_install.py"   "$TMP/frontend.json"   "$TMP/job-launcher.json"   "$TMP/broker-verifier.json"   "$TMP/policy.json" <<'PY'
import hashlib
import json
import runpy
import sys

renderer, frontend_path, launcher_path, verifier_path, policy_path = sys.argv[1:]
ns = runpy.run_path(renderer)
units = list(ns["ALLOWED_UNITS"])

frontend = json.load(open(frontend_path, encoding="utf-8"))
launcher = json.load(open(launcher_path, encoding="utf-8"))
verifier = json.load(open(verifier_path, encoding="utf-8"))

# Preserve endpoint, socket, identity, certificate-pin, source-root, and
# design-authority fields. Change only the new observability configuration.
frontend["allowed_units"] = units
launcher["allowed_units"] = units
launcher["journalctl_path"] = "/usr/bin/journalctl"
launcher["maintenance_controller_receipt_root"] = (
    "/var/lib/workspace-ci/maintenance-controller/receipts"
)

policy_bytes = open(policy_path, "rb").read()
verifier["policy_artifact_sha256"] = hashlib.sha256(policy_bytes).hexdigest()

for path, value in (
    (frontend_path, frontend),
    (launcher_path, launcher),
    (verifier_path, verifier),
):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(value, fh, indent=2, sort_keys=True)
        fh.write("\n")
PY

# Candidate sanity before touching live files.
"/opt/workspace-shell/node/bin/node" --check "$TMP/server.js"
python3 -m py_compile "$TMP/job_launcher.py"
for f in   "$TMP/policy.json"   "$TMP/frontend.json"   "$TMP/job-launcher.json"   "$TMP/broker-verifier.json"; do
  python3 -m json.tool "$f" >/dev/null
done

python3 - "$TMP/broker-verifier.json" "$TMP/policy.json" <<'PY'
import hashlib, json, sys
cfg=json.load(open(sys.argv[1], encoding="utf-8"))
digest=hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()
assert cfg["policy_artifact_sha256"] == digest
print("BROKER_POLICY_DIGEST_BINDING=PASS")
PY

sudo test ! -e "$UPDATE_ROOT" || fail "update receipt/backup root already exists for this head"
sudo install -d -o root -g root -m 0700 "$UPDATE_ROOT"
sudo install -d -o root -g root -m 0700 "$UPDATE_ROOT/backup"

sudo cp -a "$SERVER_DST" "$UPDATE_ROOT/backup/server.js"
sudo cp -a "$LAUNCHER_DST" "$UPDATE_ROOT/backup/job_launcher.py"
sudo cp -a "$POLICY_DST" "$UPDATE_ROOT/backup/workspace-shell-mcp-authority-v2.json"
sudo cp -a "$FRONTEND_CFG" "$UPDATE_ROOT/backup/frontend.json"
sudo cp -a "$LAUNCHER_CFG" "$UPDATE_ROOT/backup/job-launcher.json"
sudo cp -a "$BROKER_VERIFIER_CFG" "$UPDATE_ROOT/backup/broker-verifier.json"

echo "PREFLIGHT=PASS"
echo "=== WORKSPACE SHELL OBSERVABILITY UPDATE: MUTATION BEGIN ==="
MUTATION_STARTED=1

sudo systemctl stop workspace-shell-tunnel.service
sudo systemctl stop workspace-shell-mcp.service
sudo systemctl stop workspace-shell-root-broker.service
sudo systemctl stop workspace-shell-job-launcher.service

sudo install -o root -g root -m 0644 "$TMP/server.js" "$SERVER_DST"
sudo install -o root -g root -m 0755 "$TMP/job_launcher.py" "$LAUNCHER_DST"
sudo install -o root -g root -m 0644 "$TMP/policy.json" "$POLICY_DST"
sudo install -o root -g workspace-shell-mcp -m 0640 "$TMP/frontend.json" "$FRONTEND_CFG"
sudo install -o root -g root -m 0644 "$TMP/job-launcher.json" "$LAUNCHER_CFG"
sudo install -o root -g root -m 0644 "$TMP/broker-verifier.json" "$BROKER_VERIFIER_CFG"

[ "$(git_blob_file "$SERVER_DST")" = "$CANDIDATE_SERVER_BLOB" ]   || fail "installed candidate server.js blob mismatch"
[ "$(git_blob_file "$LAUNCHER_DST")" = "$CANDIDATE_LAUNCHER_BLOB" ]   || fail "installed candidate job_launcher.py blob mismatch"
[ "$(git_blob_file "$POLICY_DST")" = "$CANDIDATE_POLICY_BLOB" ]   || fail "installed candidate policy blob mismatch"

# Prove accepted execution and independent authority snapshots were untouched.
[ "$(sudo git -C "$EXEC_SOURCE" rev-parse HEAD)" = "$ACCEPTED_EXECUTION_SHA" ]   || fail "execution source changed during observability update"
[ -d "$AUTHORITY_ROOT" ] || fail "authority root disappeared during update"

PRESERVED_AFTER="$TMP/preserved-after.sha256"
for path in   "$TUNNEL_RUNTIME_KEY"   "$TUNNEL_CLIENT_KEY"   "$TUNNEL_CLIENT_CERT"   "$TUNNEL_CA"   "$FRONTEND_SERVER_KEY"   "$FRONTEND_SERVER_CERT"   "$FRONTEND_SIGNING_KEY"   "$FRONTEND_SIGNING_PUB"   "$HELPER_REGISTRY"   "$TRUSTED_ISSUERS"   "$REVOCATIONS"; do
  printf '%s  %s\n' "$(sha256_file "$path")" "$path" >> "$PRESERVED_AFTER"
done
sudo find "$TUNNEL_PROFILE_DIR" -maxdepth 1 -type f -print0   | sort -z   | while IFS= read -r -d '' path; do
      printf '%s  %s\n' "$(sha256_file "$path")" "$path"
    done >> "$PRESERVED_AFTER"
cmp -s "$PRESERVED_BEFORE" "$PRESERVED_AFTER"   || fail "preserved tunnel/TLS/signing/helper/trust material changed"

sudo systemctl start workspace-shell-job-launcher.service
sudo systemctl start workspace-shell-root-broker.service
sudo systemctl start workspace-shell-mcp.service

LOCAL_READY=0
for _ in $(seq 1 100); do
  if sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 1     --cacert /etc/workspace-shell/tunnel/ca.crt     --cert /etc/workspace-shell/tunnel/client.crt     --key /etc/workspace-shell/tunnel/client.key     https://127.0.0.1:8797/healthz >/dev/null 2>&1; then
    LOCAL_READY=1
    break
  fi
  sleep 0.1
done
[ "$LOCAL_READY" = "1" ] || fail "local Workspace Shell health did not recover"
echo "LOCAL_MTLS_HEALTH=PASS"

INIT_RESPONSE="$TMP/mcp-initialize.json"
sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 5   --cacert /etc/workspace-shell/tunnel/ca.crt   --cert /etc/workspace-shell/tunnel/client.crt   --key /etc/workspace-shell/tunnel/client.key   -H 'content-type: application/json'   -H 'accept: application/json, text/event-stream'   --data-binary '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"workspace-shell-update","version":"0.1.0"}}}'   https://127.0.0.1:8797/mcp >"$INIT_RESPONSE"

python3 - "$INIT_RESPONSE" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
assert d.get("jsonrpc") == "2.0"
assert isinstance(d.get("result"), dict)
assert d["result"].get("serverInfo", {}).get("name") == "workspace-shell"
print("LOCAL_MCP_INITIALIZE=PASS")
PY

TOOLS_RESPONSE="$TMP/mcp-tools-list.json"
sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 5   --cacert /etc/workspace-shell/tunnel/ca.crt   --cert /etc/workspace-shell/tunnel/client.crt   --key /etc/workspace-shell/tunnel/client.key   -H 'content-type: application/json'   -H 'accept: application/json, text/event-stream'   --data-binary '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'   https://127.0.0.1:8797/mcp >"$TOOLS_RESPONSE"

python3 - "$TOOLS_RESPONSE" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
tools = d.get("result", {}).get("tools", [])
inspect = next(x for x in tools if x.get("name") == "workspace_shell_inspect")
schema = inspect.get("inputSchema", {})
op = schema.get("properties", {}).get("operation", {})
values = set(op.get("enum", []))
required = {
    "unit_state",
    "unit_logs_redacted",
    "maintenance_receipt",
    "runtime_inventory",
    "receipt_status",
}
missing = required - values
assert not missing, f"inspect schema missing operations: {sorted(missing)}"
print("LOCAL_MCP_TOOL_SCHEMA=PASS")
PY

sudo rm -f /var/lib/workspace-shell/tunnel/health.url
sudo systemctl start workspace-shell-tunnel.service

TUNNEL_READY=0
HEALTH_URL=""
for _ in $(seq 1 200); do
  HEALTH_CANDIDATE=""
  if HEALTH_CANDIDATE="$(sudo cat /var/lib/workspace-shell/tunnel/health.url 2>/dev/null)"     && [ -n "$HEALTH_CANDIDATE" ]; then
    HEALTH_URL="$HEALTH_CANDIDATE"
    if curl -fsS --max-time 1 "$HEALTH_URL/readyz" >/dev/null 2>&1; then
      TUNNEL_READY=1
      break
    fi
  fi
  sleep 0.2
done
[ "$TUNNEL_READY" = "1" ] || fail "Secure MCP Tunnel did not become ready"
echo "TUNNEL_READY=PASS"

for svc in "${SERVICES[@]}"; do
  service_active "$svc" || fail "$svc is not active after update"
  service_boot_disabled "$svc" || fail "$svc became boot-enabled"
done
echo "SERVICES_ACTIVE_BOOT_DISABLED=PASS"

: > "$PRESERVED_AFTER"
for path in   "$TUNNEL_RUNTIME_KEY"   "$TUNNEL_CLIENT_KEY"   "$TUNNEL_CLIENT_CERT"   "$TUNNEL_CA"   "$FRONTEND_SERVER_KEY"   "$FRONTEND_SERVER_CERT"   "$FRONTEND_SIGNING_KEY"   "$FRONTEND_SIGNING_PUB"   "$HELPER_REGISTRY"   "$TRUSTED_ISSUERS"   "$REVOCATIONS"; do
  printf '%s  %s\n' "$(sha256_file "$path")" "$path" >> "$PRESERVED_AFTER"
done
sudo find "$TUNNEL_PROFILE_DIR" -maxdepth 1 -type f -print0   | sort -z   | while IFS= read -r -d '' path; do
      printf '%s  %s\n' "$(sha256_file "$path")" "$path"
    done >> "$PRESERVED_AFTER"
cmp -s "$PRESERVED_BEFORE" "$PRESERVED_AFTER"   || fail "preserved identity/helper/trust material changed after restart"

RECEIPT_TMP="$TMP/update-receipt.json"
python3 -   "$RECEIPT_TMP"   "$EXPECTED_HEAD"   "$ACCEPTED_EXECUTION_SHA"   "$CANDIDATE_SERVER_BLOB"   "$CANDIDATE_LAUNCHER_BLOB"   "$CANDIDATE_POLICY_BLOB"   "$HEALTH_URL" <<'PY'
import json, sys
from datetime import datetime, timezone

(path, head, execution_sha, server_blob, launcher_blob, policy_blob, health_url) = sys.argv[1:]
receipt = {
    "schema": "workspace-shell-observability-update-receipt.v1",
    "status": "PASS",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "validated_operator_head": head,
    "preserved_execution_source_sha": execution_sha,
    "installed_blobs": {
        "server_js": server_blob,
        "job_launcher_py": launcher_blob,
        "authority_policy": policy_blob,
    },
    "preserved": {
        "plugin_app_identity": True,
        "tunnel_id_and_profile": True,
        "tunnel_runtime_key": True,
        "tls_identity": True,
        "request_signing_identity": True,
        "authority_root": True,
        "execution_source": True,
        "helper_registry_and_trust_stores": True,
        "boot_disabled_state": True,
    },
    "validation": {
        "broker_policy_digest_binding": "PASS",
        "local_mtls_health": "PASS",
        "local_mcp_initialize": "PASS",
        "local_mcp_tool_schema": "PASS",
        "tunnel_ready": "PASS",
        "services_active_boot_disabled": "PASS",
    },
    "tunnel_health_url": health_url,
}
open(path, "w", encoding="utf-8").write(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n"
)
PY

sudo install -o root -g root -m 0600   "$RECEIPT_TMP" "$UPDATE_ROOT/update-receipt.json"

COMMITTED=1
trap - EXIT INT TERM
rm -rf "$TMP"

echo "WORKSPACE_SHELL_GITRUNNER_OBSERVABILITY_UPDATE=PASS"
echo "VALIDATED_HEAD=$EXPECTED_HEAD"
echo "PRESERVED_EXECUTION_SOURCE=$ACCEPTED_EXECUTION_SHA"
echo "UPDATE_RECEIPT=$UPDATE_ROOT/update-receipt.json"
echo "TUNNEL_HEALTH=$HEALTH_URL"
echo "NEXT_GATE=CHATGPT_FRESH_TOOL_SCHEMA_ACCEPTANCE"
