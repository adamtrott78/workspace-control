#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_HEAD="f999b25a866f25c95243cbbd6d1377a799fafb78"
SOURCE_REPO_URL="https://github.com/adamtrott78/workspace-control.git"
SOURCE_BRANCH="workspace-shell-mcp-v1-current-main"
ATTEST_SHA256="d44cda1f6f13f814e093bef9228410f319d504c76cf80ba8e6d2ecbb8d321353"
DESIGN_AUTHORITY_SHA="0c24e42ea57a3e23af01351a5974d5f09f3ce319"
PROFILE="workspace-shell-production"

NODE_ENV_SOURCE="/home/atrott/miniforge3/envs/workspace-heartbeat-node"
DEPENDENCY_SOURCE="/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v048/plugins/workspace-heartbeat/node_modules"
TUNNEL_CLIENT_SOURCE="/home/atrott/adamArchives/Adam/tooling/openai-tunnel-client/v0.0.18/unpacked/tunnel-client"

FRONTEND_UID=41010
WORKER_UID=41011
TUNNEL_UID=41012

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd -P)"
[ -d "$ROOT/.git" ] || [ -f "$ROOT/.git" ] || fail "activation script is not inside a Git checkout"
OPERATOR_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
EVIDENCE="$ROOT/plugins/workspace-shell/install/evidence/lambda-host-attestation.f999b25a.json"
TMP="$(mktemp -d /tmp/workspace-shell-activate.XXXXXX)"
SOURCE="$TMP/source"
BUNDLE="$TMP/bundle"
MUTATION_STARTED=0
COMMITTED=0

SERVICES=(
  workspace-shell-tunnel.service
  workspace-shell-mcp.service
  workspace-shell-root-broker.service
  workspace-shell-job-launcher.service
)

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

cleanup_tmp() {
  rm -rf "$TMP" >/dev/null 2>&1 || true
}

rollback() {
  set +e
  echo "=== WORKSPACE SHELL ACTIVATION ROLLBACK: BEGIN ==="
  for svc in "${SERVICES[@]}"; do
    sudo systemctl stop "$svc" >/dev/null 2>&1 || true
    sudo systemctl disable "$svc" >/dev/null 2>&1 || true
  done
  sudo rm -f \
    /etc/systemd/system/workspace-shell-job-launcher.service \
    /etc/systemd/system/workspace-shell-root-broker.service \
    /etc/systemd/system/workspace-shell-mcp.service \
    /etc/systemd/system/workspace-shell-tunnel.service
  sudo systemctl daemon-reload >/dev/null 2>&1 || true
  sudo systemctl reset-failed >/dev/null 2>&1 || true

  sudo rm -rf \
    /etc/workspace-shell \
    /opt/workspace-shell \
    /run/workspace-shell-control \
    /var/lib/workspace-shell \
    /srv/workspace-shell

  for user in workspace-shell-tunnel workspace-shell-exec workspace-shell-mcp; do
    sudo userdel "$user" >/dev/null 2>&1 || true
  done
  for group in workspace-shell-tunnel workspace-shell-exec workspace-shell-mcp; do
    sudo groupdel "$group" >/dev/null 2>&1 || true
  done
  echo "=== WORKSPACE SHELL ACTIVATION ROLLBACK: END ==="
}

on_exit() {
  rc=$?
  if [ "$rc" -ne 0 ] && [ "$MUTATION_STARTED" = "1" ] && [ "$COMMITTED" != "1" ]; then
    rollback
  fi
  cleanup_tmp
  exit "$rc"
}
trap on_exit EXIT
trap 'exit 130' INT TERM

if [ "$(id -u)" -eq 0 ]; then
  fail "run as the normal operator user, not root"
fi

for cmd in git python3 sha256sum awk sudo systemctl systemd-sysusers systemd-tmpfiles openssl curl cp install rm mkdir grep getent id find stat; do
  require_cmd "$cmd"
done

echo "=== WORKSPACE SHELL LIVE ACTIVATION: PREFLIGHT ==="
echo "OPERATOR_HEAD=$OPERATOR_HEAD"
echo "SOURCE_HEAD=$SOURCE_HEAD"
[ -z "$(git -C "$ROOT" status --porcelain=v1 --untracked-files=normal)" ] \
  || fail "operator checkout is dirty"

[ -f "$EVIDENCE" ] || fail "final host attestation evidence is missing"
[ "$(sha256_file "$EVIDENCE")" = "$ATTEST_SHA256" ] \
  || fail "final host attestation digest mismatch"

GIT_TERMINAL_PROMPT=0 git -c credential.helper= clone   --no-checkout   --filter=blob:none   --branch "$SOURCE_BRANCH"   "$SOURCE_REPO_URL"   "$SOURCE" >/dev/null
git -C "$SOURCE" config core.hooksPath /dev/null
GIT_TERMINAL_PROMPT=0 git -C "$SOURCE" -c credential.helper= checkout --detach "$SOURCE_HEAD" >/dev/null
git -C "$SOURCE" remote remove origin >/dev/null 2>&1 || true

[ "$(git -C "$SOURCE" rev-parse HEAD)" = "$SOURCE_HEAD" ] \
  || fail "prepared source head mismatch"
[ -z "$(git -C "$SOURCE" status --porcelain=v1 --untracked-files=normal)" ] \
  || fail "prepared source is dirty"

[ -x "$NODE_ENV_SOURCE/bin/node" ] || fail "accepted Node environment is missing"
[ -r "$NODE_ENV_SOURCE/ssl/openssl.cnf" ] || fail "accepted Node OpenSSL config is missing"
[ "$("$NODE_ENV_SOURCE/bin/node" --version)" = "v20.20.2" ] \
  || fail "accepted Node runtime version changed"
[ -d "$DEPENDENCY_SOURCE" ] || fail "accepted Node dependency source is missing"
for dep in "@modelcontextprotocol/sdk" "@modelcontextprotocol/ext-apps" "zod"; do
  [ -e "$DEPENDENCY_SOURCE/$dep" ] || fail "accepted dependency source lacks $dep"
done
[ -x "$TUNNEL_CLIENT_SOURCE" ] || fail "accepted tunnel-client is missing"
case "$("$TUNNEL_CLIENT_SOURCE" --version 2>&1 | head -n1)" in
  0.0.18+*) ;;
  *) fail "unexpected tunnel-client version" ;;
esac

LIVE_ATTEST="$TMP/live-attestation.json"
python3 "$ROOT/plugins/workspace-shell/install/host_attest.py" \
  --source-root "$SOURCE" \
  --source-sha "$SOURCE_HEAD" \
  --strict > "$LIVE_ATTEST"

python3 - "$LIVE_ATTEST" <<'PY'
import json, sys
d=json.load(open(sys.argv[1]))
assert d["decision"] == "READY_FOR_INSTALL_PLAN"
assert d["blockers"] == []
assert d["source"]["head"]["stdout"] == "f999b25a866f25c95243cbbd6d1377a799fafb78"
assert d["source"]["status"]["stdout"] == ""
assert d["planned_listener"]["occupied"] is False
expected={
  "workspace-shell-mcp": (41010,41010),
  "workspace-shell-exec": (41011,41011),
  "workspace-shell-tunnel": (41012,41012),
}
seen={}
for x in d["planned_identities"]:
    seen[x["name"]] = (x["uid"],x["gid"])
    assert x["name_user"]["exists"] is False
    assert x["name_group"]["exists"] is False
    assert x["numeric_uid"]["exists"] is False
    assert x["numeric_gid"]["exists"] is False
assert seen == expected
for x in d["planned_paths"]:
    assert x["exists"] is False
for x in d["planned_units"]:
    assert x["returncode"] == 0
    assert x["properties"]["LoadState"] == "not-found"
print("LIVE_PREACTIVATION_ATTESTATION=PASS")
PY

POLICY_SHA256="$(sha256_file "$ROOT/architecture/workspace-shell-mcp-authority-v2.json")"
[ "$POLICY_SHA256" = "$(sha256_file "$SOURCE/architecture/workspace-shell-mcp-authority-v2.json")" ] \
  || fail "accepted policy artifact drifted between target source and runtime head"
python3 "$ROOT/plugins/workspace-shell/install/render_install.py" \
  --attestation "$EVIDENCE" \
  --output-dir "$BUNDLE" \
  --source-sha "$SOURCE_HEAD" \
  --runtime-source-sha "$OPERATOR_HEAD" \
  --design-authority-sha "$DESIGN_AUTHORITY_SHA" \
  --policy-artifact-sha256 "$POLICY_SHA256" >/dev/null

python3 - "$BUNDLE/install-manifest.json" "$OPERATOR_HEAD" <<'PY'
import json, sys
d=json.load(open(sys.argv[1]))
runtime_head=sys.argv[2]
assert d["source_sha"] == "f999b25a866f25c95243cbbd6d1377a799fafb78"
assert d["runtime_source_sha"] == runtime_head
assert d["attestation_sha256"] == "d44cda1f6f13f814e093bef9228410f319d504c76cf80ba8e6d2ecbb8d321353"
assert d["activation_sealed"] is False
assert d["requires_activation_seal"] is True
assert d["privileged_helpers_enabled"] is False
assert d["operator_trust_store_state"] == "EMPTY_FAIL_CLOSED"
assert d["identities"] == {
  "frontend":{"uid":41010,"gid":41010},
  "worker":{"uid":41011,"gid":41011},
  "tunnel":{"uid":41012,"gid":41012},
}
print("UNSEALED_INSTALL_BUNDLE=PASS")
PY

TUNNEL_ID="${WORKSPACE_SHELL_TUNNEL_ID:-}"
if [ -z "$TUNNEL_ID" ]; then
  read -rp "Dedicated Workspace Shell tunnel ID: " TUNNEL_ID
fi
[[ "$TUNNEL_ID" =~ ^tunnel_([a-z0-9]{4}_)?[a-z0-9]{32}$ ]] \
  || fail "invalid dedicated tunnel ID format"

echo "TUNNEL_ID=$TUNNEL_ID"
echo "PREFLIGHT=PASS"
echo
echo "The next phase mutates only the new Workspace Shell principals/paths/units."
echo "Any failure before COMMIT triggers automatic rollback."
read -rp "Type ACTIVATE_WORKSPACE_SHELL to continue: " CONFIRM
[ "$CONFIRM" = "ACTIVATE_WORKSPACE_SHELL" ] || fail "activation not authorized"

MUTATION_STARTED=1
echo "=== WORKSPACE SHELL LIVE ACTIVATION: MUTATION BEGIN ==="

sudo systemd-sysusers "$BUNDLE/workspace-shell-sysusers.conf"

[ "$(id -u workspace-shell-mcp)" = "$FRONTEND_UID" ] || fail "frontend UID mismatch"
[ "$(id -u workspace-shell-exec)" = "$WORKER_UID" ] || fail "worker UID mismatch"
[ "$(id -u workspace-shell-tunnel)" = "$TUNNEL_UID" ] || fail "tunnel UID mismatch"
[ "$(getent group workspace-shell-mcp | cut -d: -f3)" = "$FRONTEND_UID" ] || fail "frontend GID mismatch"
[ "$(getent group workspace-shell-exec | cut -d: -f3)" = "$WORKER_UID" ] || fail "worker GID mismatch"
[ "$(getent group workspace-shell-tunnel | cut -d: -f3)" = "$TUNNEL_UID" ] || fail "tunnel GID mismatch"
echo "FIXED_IDENTITIES=PASS"

sudo systemd-tmpfiles --create "$BUNDLE/workspace-shell-tmpfiles.conf"
sudo install -d -o root -g root -m 0755 \
  /etc/workspace-shell \
  /etc/workspace-shell/policy \
  /etc/workspace-shell/helpers \
  /etc/workspace-shell/approval
sudo install -d -o workspace-shell-mcp -g workspace-shell-mcp -m 0700 \
  /etc/workspace-shell/frontend
sudo install -d -o workspace-shell-tunnel -g workspace-shell-tunnel -m 0700 \
  /etc/workspace-shell/tunnel \
  /etc/workspace-shell/tunnel-client-profiles
sudo install -d -o root -g root -m 0755 \
  /opt/workspace-shell/bin \
  /opt/workspace-shell/runtime/plugins

echo "=== STAGE IMMUTABLE SOURCE/RUNTIME ==="
sudo cp -a "$SOURCE" /srv/workspace-shell/workspace-control
sudo chown -R root:root /srv/workspace-shell/workspace-control
sudo chmod -R go-w /srv/workspace-shell/workspace-control
sudo git -C /srv/workspace-shell/workspace-control remote remove origin >/dev/null 2>&1 || true
[ "$(sudo git -C /srv/workspace-shell/workspace-control rev-parse HEAD)" = "$SOURCE_HEAD" ] \
  || fail "installed source SHA mismatch"

sudo cp -a "$NODE_ENV_SOURCE" /opt/workspace-shell/node
sudo chown -R root:root /opt/workspace-shell/node
sudo chmod -R go-w /opt/workspace-shell/node
STAGED_OPENSSL_CONF="/opt/workspace-shell/node/ssl/openssl.cnf"
sudo test -r "$STAGED_OPENSSL_CONF" || fail "staged Node OpenSSL config is missing"
[ "$(OPENSSL_CONF="$STAGED_OPENSSL_CONF" /opt/workspace-shell/node/bin/node --version)" = "v20.20.2" ] \
  || fail "staged Node runtime failed"
sudo -u workspace-shell-mcp env OPENSSL_CONF="$STAGED_OPENSSL_CONF" \
  /opt/workspace-shell/node/bin/node --version >/dev/null \
  || fail "frontend identity cannot initialize staged Node/OpenSSL runtime"
echo "STAGED_NODE_OPENSSL_BINDING=PASS"

sudo cp -a "$ROOT/plugins/workspace-shell" /opt/workspace-shell/runtime/plugins/workspace-shell
sudo cp -a "$DEPENDENCY_SOURCE" /opt/workspace-shell/runtime/plugins/workspace-shell/node_modules
sudo chown -R root:root /opt/workspace-shell/runtime
sudo chmod -R go-w /opt/workspace-shell/runtime

sudo install -o root -g root -m 0755 "$TUNNEL_CLIENT_SOURCE" /opt/workspace-shell/bin/tunnel-client
case "$(/opt/workspace-shell/bin/tunnel-client --version 2>&1 | head -n1)" in
  0.0.18+*) ;;
  *) fail "staged tunnel-client failed version proof" ;;
esac

(
  export OPENSSL_CONF="$STAGED_OPENSSL_CONF"
  cd /opt/workspace-shell/runtime/plugins/workspace-shell
  /opt/workspace-shell/node/bin/node --check server.js
  /opt/workspace-shell/node/bin/node --test test/core.test.js test/broker-verifier.test.js
)
sudo python3 -m py_compile \
  /opt/workspace-shell/runtime/plugins/workspace-shell/root/job_launcher.py \
  /opt/workspace-shell/runtime/plugins/workspace-shell/root/root_broker.py \
  /opt/workspace-shell/runtime/plugins/workspace-shell/root/runtime_common.py \
  /opt/workspace-shell/runtime/plugins/workspace-shell/install/render_tunnel_profile.py \
  /opt/workspace-shell/runtime/plugins/workspace-shell/install/validate_tunnel_doctor.py
echo "STAGED_RUNTIME_TESTS=PASS"

echo "=== INSTALL STATIC FAIL-CLOSED CONFIG ==="
sudo install -o root -g root -m 0644 "$BUNDLE/workspace-shell-mcp-authority-v2.json" \
  /etc/workspace-shell/policy/workspace-shell-mcp-authority-v2.json
sudo install -o root -g root -m 0644 "$BUNDLE/profiles.v1.json" /etc/workspace-shell/profiles.v1.json
sudo install -o root -g root -m 0644 "$BUNDLE/helper-registry.v2.json" /etc/workspace-shell/helpers/registry.json
sudo install -o root -g root -m 0644 "$BUNDLE/trusted-issuers.empty.json" /etc/workspace-shell/approval/trusted-issuers.json
sudo install -o root -g root -m 0644 "$BUNDLE/revocations.empty.json" /etc/workspace-shell/approval/revocations.json
sudo install -o root -g root -m 0644 "$BUNDLE/job-launcher.json" /etc/workspace-shell/job-launcher.json
sudo install -o root -g root -m 0600 "$BUNDLE/root-broker.json" /etc/workspace-shell/root-broker.json
sudo install -o root -g root -m 0644 "$BUNDLE/broker-verifier.json" /etc/workspace-shell/broker-verifier.json

echo "=== GENERATE DEDICATED LOCAL TLS + REQUEST-SIGNING IDENTITIES ==="
sudo openssl req -x509 -newkey rsa:3072 -sha256 -nodes \
  -keyout /etc/workspace-shell/.local-ca.key \
  -out /etc/workspace-shell/.local-ca.crt \
  -days 3650 -subj "/CN=Workspace Shell Local CA" >/dev/null 2>&1
sudo chmod 0600 /etc/workspace-shell/.local-ca.key
sudo chmod 0644 /etc/workspace-shell/.local-ca.crt

sudo openssl req -new -newkey rsa:2048 -nodes \
  -keyout /etc/workspace-shell/frontend/server.key \
  -out /etc/workspace-shell/.server.csr \
  -subj "/CN=127.0.0.1" >/dev/null 2>&1
printf '%s\n' \
  'subjectAltName=IP:127.0.0.1' \
  'extendedKeyUsage=serverAuth' \
  | sudo tee /etc/workspace-shell/.server.ext >/dev/null
sudo openssl x509 -req \
  -in /etc/workspace-shell/.server.csr \
  -CA /etc/workspace-shell/.local-ca.crt \
  -CAkey /etc/workspace-shell/.local-ca.key \
  -CAcreateserial \
  -out /etc/workspace-shell/frontend/server.crt \
  -days 825 -sha256 -extfile /etc/workspace-shell/.server.ext >/dev/null 2>&1

sudo openssl req -new -newkey rsa:2048 -nodes \
  -keyout /etc/workspace-shell/tunnel/client.key \
  -out /etc/workspace-shell/.client.csr \
  -subj "/CN=workspace-shell-tunnel" >/dev/null 2>&1
printf '%s\n' 'extendedKeyUsage=clientAuth' \
  | sudo tee /etc/workspace-shell/.client.ext >/dev/null
sudo openssl x509 -req \
  -in /etc/workspace-shell/.client.csr \
  -CA /etc/workspace-shell/.local-ca.crt \
  -CAkey /etc/workspace-shell/.local-ca.key \
  -CAcreateserial \
  -out /etc/workspace-shell/tunnel/client.crt \
  -days 825 -sha256 -extfile /etc/workspace-shell/.client.ext >/dev/null 2>&1

sudo install -o workspace-shell-mcp -g workspace-shell-mcp -m 0644 \
  /etc/workspace-shell/.local-ca.crt /etc/workspace-shell/frontend/client-ca.crt
sudo install -o workspace-shell-tunnel -g workspace-shell-tunnel -m 0644 \
  /etc/workspace-shell/.local-ca.crt /etc/workspace-shell/tunnel/ca.crt
sudo chown workspace-shell-mcp:workspace-shell-mcp \
  /etc/workspace-shell/frontend/server.key \
  /etc/workspace-shell/frontend/server.crt
sudo chmod 0600 /etc/workspace-shell/frontend/server.key
sudo chmod 0644 /etc/workspace-shell/frontend/server.crt
sudo chown workspace-shell-tunnel:workspace-shell-tunnel \
  /etc/workspace-shell/tunnel/client.key \
  /etc/workspace-shell/tunnel/client.crt
sudo chmod 0600 /etc/workspace-shell/tunnel/client.key
sudo chmod 0644 /etc/workspace-shell/tunnel/client.crt

sudo openssl genpkey -algorithm Ed25519 \
  -out /etc/workspace-shell/frontend/request-signing.key >/dev/null 2>&1
sudo openssl pkey \
  -in /etc/workspace-shell/frontend/request-signing.key \
  -pubout \
  -out /etc/workspace-shell/frontend/request-signing.pub >/dev/null 2>&1
sudo chown workspace-shell-mcp:workspace-shell-mcp /etc/workspace-shell/frontend/request-signing.key
sudo chmod 0600 /etc/workspace-shell/frontend/request-signing.key
sudo chown root:root /etc/workspace-shell/frontend/request-signing.pub
sudo chmod 0644 /etc/workspace-shell/frontend/request-signing.pub

sudo rm -f \
  /etc/workspace-shell/.local-ca.key \
  /etc/workspace-shell/.local-ca.crt \
  /etc/workspace-shell/.local-ca.srl \
  /etc/workspace-shell/.server.csr \
  /etc/workspace-shell/.server.ext \
  /etc/workspace-shell/.client.csr \
  /etc/workspace-shell/.client.ext
echo "DEDICATED_LOCAL_IDENTITIES=PASS"

TUNNEL_PROFILE_RENDERER="/opt/workspace-shell/runtime/plugins/workspace-shell/install/render_tunnel_profile.py"
sudo -u workspace-shell-tunnel test -r "$TUNNEL_PROFILE_RENDERER" \
  || fail "staged tunnel profile renderer is not readable by tunnel identity"
sudo -u workspace-shell-tunnel env HOME=/var/lib/workspace-shell/tunnel \
  /usr/bin/python3 "$TUNNEL_PROFILE_RENDERER" \
  --profile "$PROFILE" \
  --profile-dir /etc/workspace-shell/tunnel-client-profiles \
  --tunnel-id "$TUNNEL_ID" \
  --api-key-ref file:/etc/workspace-shell/tunnel/runtime-key \
  --ca-bundle /etc/workspace-shell/tunnel/ca.crt \
  --client-cert /etc/workspace-shell/tunnel/client.crt \
  --client-key /etc/workspace-shell/tunnel/client.key \
  --force >/dev/null

PROFILE_PATH="/etc/workspace-shell/tunnel-client-profiles/${PROFILE}.yaml"
sudo -u workspace-shell-tunnel test -f "$PROFILE_PATH" \
  || fail "Workspace Shell tunnel profile was not rendered"
sudo chown workspace-shell-tunnel:workspace-shell-tunnel "$PROFILE_PATH"
sudo chmod 0600 "$PROFILE_PATH"
sudo -u workspace-shell-tunnel test -r "$PROFILE_PATH" \
  || fail "Workspace Shell tunnel profile is not readable by tunnel identity"

if sudo grep -R --binary-files=without-match -n 'sk-' /etc/workspace-shell/tunnel-client-profiles; then
  fail "tunnel profile unexpectedly contains an inline API key"
fi
echo "TUNNEL_PROFILE_SECRET_SCAN=PASS"

echo "=== SEAL INSTALL BUNDLE WITH PUBLIC CLIENT CERTIFICATE ==="
sudo python3 "$ROOT/plugins/workspace-shell/install/seal_install.py" \
  --bundle-dir "$BUNDLE" \
  --tunnel-client-cert /etc/workspace-shell/tunnel/client.crt \
  --openssl-path /usr/bin/openssl >/dev/null
[ -f "$BUNDLE/frontend.json" ] || fail "activation seal did not produce frontend.json"
[ ! -e "$BUNDLE/frontend.unsealed.json" ] || fail "unsealed frontend config survived activation seal"

sudo install -o root -g workspace-shell-mcp -m 0640 "$BUNDLE/frontend.json" /etc/workspace-shell/frontend.json
sudo install -o root -g root -m 0644 "$BUNDLE/install-manifest.json" /etc/workspace-shell/install-manifest.json

echo "=== INSTALL SYSTEMD UNITS DISABLED-BY-DEFAULT ==="
for svc in workspace-shell-job-launcher workspace-shell-root-broker workspace-shell-mcp workspace-shell-tunnel; do
  sudo install -o root -g root -m 0644 "$BUNDLE/${svc}.service" "/etc/systemd/system/${svc}.service"
done
sudo systemctl daemon-reload
for svc in "${SERVICES[@]}"; do
  sudo systemctl disable "$svc" >/dev/null 2>&1 || true
done

sudo tee /opt/workspace-shell/bin/workspace-shell-disable >/dev/null <<'DISABLE'
#!/usr/bin/env bash
set -euo pipefail
systemctl stop workspace-shell-tunnel.service workspace-shell-mcp.service workspace-shell-root-broker.service workspace-shell-job-launcher.service
echo "WORKSPACE_SHELL_DISABLED=PASS"
DISABLE
sudo chmod 0755 /opt/workspace-shell/bin/workspace-shell-disable
sudo chown root:root /opt/workspace-shell/bin/workspace-shell-disable

echo "=== START LOCAL CONTROL PLANE ==="
sudo systemctl start workspace-shell-job-launcher.service
sudo systemctl start workspace-shell-root-broker.service
sudo systemctl start workspace-shell-mcp.service

LOCAL_READY=0
for _ in $(seq 1 100); do
  if sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 1 \
    --cacert /etc/workspace-shell/tunnel/ca.crt \
    --cert /etc/workspace-shell/tunnel/client.crt \
    --key /etc/workspace-shell/tunnel/client.key \
    https://127.0.0.1:8797/healthz >/dev/null 2>&1; then
    LOCAL_READY=1
    break
  fi
  sleep 0.1
done
if [ "$LOCAL_READY" != "1" ]; then
  echo "=== LOCAL CONTROL PLANE DIAGNOSTICS: BEGIN ===" >&2
  for svc in workspace-shell-job-launcher.service workspace-shell-root-broker.service workspace-shell-mcp.service; do
    echo "--- ${svc}: state ---" >&2
    sudo systemctl show "$svc" --no-pager \
      --property=Id,LoadState,ActiveState,SubState,MainPID,ExecMainCode,ExecMainStatus,Result,User,Group,FragmentPath,NRestarts,MemoryCurrent,MemoryPeak \
      2>&1 | head -n 100 >&2 || true
    echo "--- ${svc}: journal ---" >&2
    sudo journalctl -u "$svc" -n 80 --no-pager --output=short-iso \
      2>&1 | tail -n 80 >&2 || true
  done
  echo "=== LOCAL CONTROL PLANE DIAGNOSTICS: END ===" >&2
  fail "Workspace Shell local mTLS health check failed"
fi
echo "LOCAL_MTLS_HEALTH=PASS"

echo "Enter the dedicated Workspace Shell Secure MCP Tunnel runtime key."
echo "The value is hidden and written only to a 0600 file owned by workspace-shell-tunnel."
read -rsp "Runtime key: " RUNTIME_KEY
echo
[ -n "$RUNTIME_KEY" ] || fail "empty runtime key"
printf '%s' "$RUNTIME_KEY" \
  | sudo tee /etc/workspace-shell/tunnel/runtime-key >/dev/null
unset RUNTIME_KEY
sudo chown workspace-shell-tunnel:workspace-shell-tunnel /etc/workspace-shell/tunnel/runtime-key
sudo chmod 0600 /etc/workspace-shell/tunnel/runtime-key
echo "TUNNEL_RUNTIME_KEY_STAGED=PASS"

echo "=== PRE-TUNNEL LOCAL CONTROL PLANE RECHECK ==="
if ! sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 2 \
  --cacert /etc/workspace-shell/tunnel/ca.crt \
  --cert /etc/workspace-shell/tunnel/client.crt \
  --key /etc/workspace-shell/tunnel/client.key \
  https://127.0.0.1:8797/healthz >/dev/null 2>&1; then
  echo "=== PRE-TUNNEL MCP DIAGNOSTICS: BEGIN ===" >&2
  sudo systemctl show workspace-shell-mcp.service --no-pager \
    --property=Id,LoadState,ActiveState,SubState,MainPID,ExecMainCode,ExecMainStatus,Result,User,Group,FragmentPath \
    2>&1 | head -n 80 >&2 || true
  sudo journalctl -u workspace-shell-mcp.service -n 120 --no-pager --output=short-iso \
    2>&1 | tail -n 120 >&2 || true
  echo "=== PRE-TUNNEL MCP DIAGNOSTICS: END ===" >&2
  fail "Workspace Shell local mTLS endpoint disappeared before tunnel startup"
fi
echo "PRE_TUNNEL_LOCAL_MTLS_RECHECK=PASS"
TUNNEL_DOCTOR_RECEIPT="SKIPPED_V0_0_18_DOCTOR_MTLS_DIAGNOSTIC_INCOMPATIBILITY"

sudo rm -f /var/lib/workspace-shell/tunnel/health.url
sudo systemctl start workspace-shell-tunnel.service

TUNNEL_READY=0
HEALTH_URL=""
for _ in $(seq 1 200); do
  HEALTH_CANDIDATE=""
  if HEALTH_CANDIDATE="$(sudo cat /var/lib/workspace-shell/tunnel/health.url 2>/dev/null)" \
    && [ -n "$HEALTH_CANDIDATE" ]; then
    HEALTH_URL="$HEALTH_CANDIDATE"
    if curl -fsS --max-time 1 "$HEALTH_URL/readyz" >/dev/null 2>&1; then
      TUNNEL_READY=1
      break
    fi
  fi
  sleep 0.2
done
if [ "$TUNNEL_READY" != "1" ]; then
  echo "=== SECURE MCP TUNNEL DIAGNOSTICS: BEGIN ===" >&2
  for svc in workspace-shell-tunnel.service workspace-shell-mcp.service; do
    echo "--- ${svc}: state ---" >&2
    sudo systemctl show "$svc" --no-pager \
      --property=Id,LoadState,ActiveState,SubState,MainPID,ExecMainCode,ExecMainStatus,Result,User,Group,FragmentPath,NRestarts,MemoryCurrent,MemoryPeak \
      2>&1 | head -n 100 >&2 || true
    echo "--- ${svc}: journal ---" >&2
    sudo journalctl -u "$svc" -n 120 --no-pager --output=short-iso \
      2>&1 | tail -n 120 >&2 || true
  done
  HEALTH_CANDIDATE=""
  if HEALTH_CANDIDATE="$(sudo cat /var/lib/workspace-shell/tunnel/health.url 2>/dev/null)" \
    && [ -n "$HEALTH_CANDIDATE" ]; then
    HEALTH_URL="$HEALTH_CANDIDATE"
    echo "TUNNEL_HEALTH_URL=$HEALTH_URL" >&2
    curl -fsS --max-time 2 "$HEALTH_URL/healthz" >&2 || true
    curl -fsS --max-time 2 "$HEALTH_URL/readyz" >&2 || true
  else
    echo "TUNNEL_HEALTH_URL=UNAVAILABLE" >&2
  fi
  echo "=== SECURE MCP TUNNEL DIAGNOSTICS: END ===" >&2
  fail "Secure MCP Tunnel failed readiness"
fi
echo "TUNNEL_READY=PASS"

for svc in "${SERVICES[@]}"; do
  [ "$(systemctl is-active "$svc")" = "active" ] || fail "$svc is not active"
  ENABLED="$(systemctl is-enabled "$svc" 2>/dev/null || true)"
  [ "$ENABLED" != "enabled" ] || fail "$svc unexpectedly enabled at boot"
done
echo "SERVICES_ACTIVE_BOOT_DISABLED=PASS"

MANIFEST_SHA="$(sudo sha256sum /etc/workspace-shell/install-manifest.json | awk '{print $1}')"
TUNNEL_VERSION="$(/opt/workspace-shell/bin/tunnel-client --version 2>&1 | head -n1)"
sudo install -d -o root -g root -m 0700 /var/lib/workspace-shell/commissioning
python3 - "$OPERATOR_HEAD" "$SOURCE_HEAD" "$ATTEST_SHA256" "$MANIFEST_SHA" "$TUNNEL_ID" "$TUNNEL_VERSION" "$HEALTH_URL" "$TUNNEL_DOCTOR_RECEIPT" > "$TMP/activation-receipt.json" <<'PY'
import datetime as dt, json, sys
operator,source,attest,manifest,tunnel_id,tunnel_version,health,doctor=sys.argv[1:]
print(json.dumps({
  "schema":"workspace-shell-activation-receipt.v1",
  "timestamp_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
  "operator_head":operator,
  "runtime_source_head":operator,
  "source_head":source,
  "host_attestation_sha256":attest,
  "install_manifest_sha256":manifest,
  "tunnel_id":tunnel_id,
  "tunnel_client_version":tunnel_version,
  "tunnel_health_url":health,
  "boot_enabled":False,
  "privileged_helpers_enabled":False,
  "operator_trust_store_state":"EMPTY_FAIL_CLOSED",
  "local_mtls_health":"PASS",
  "tunnel_doctor":doctor,
  "tunnel_ready":"PASS",
},indent=2,sort_keys=True))
PY
sudo install -o root -g root -m 0600 "$TMP/activation-receipt.json" \
  /var/lib/workspace-shell/commissioning/activation-receipt.json

COMMITTED=1
echo
echo "=== WORKSPACE SHELL LIVE ACTIVATION: PASS ==="
echo "SOURCE_HEAD=$SOURCE_HEAD"
echo "OPERATOR_HEAD=$OPERATOR_HEAD"
echo "TUNNEL_ID=$TUNNEL_ID"
echo "TUNNEL_HEALTH=$HEALTH_URL"
echo "ACTIVATION_RECEIPT=/var/lib/workspace-shell/commissioning/activation-receipt.json"
echo "EMERGENCY_DISABLE=/opt/workspace-shell/bin/workspace-shell-disable"
echo "BOOT_ENABLEMENT=DISABLED"
echo "PRIVILEGED_HELPERS=EMPTY_FAIL_CLOSED"
echo "NEXT_GATE=CHATGPT_PLUGIN_LIVE_ACCEPTANCE"
