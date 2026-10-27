#!/usr/bin/env bash
set -Eeuo pipefail

# Workspace Heartbeat v0.4.8 + OpenAI Secure MCP Tunnel production cutover.
# This script is intentionally host-specific to the accepted Lambda deployment.

CANDIDATE_SHA="def7c5fe6498b1bd742d912c1490d1f7160cab5f"
ROLLBACK_SHA="9e5858738a4fd11801510e2839b0f94f19541506"
TUNNEL_ID="tunnel_6ae017d8655c8191976ef3bccc31f593"

CONTROL="$HOME/adamArchives/Adam/workspace-control"
RUNTIME_V047="$HOME/adamArchives/Adam/workspace-heartbeat-runtime-v047"
RUNTIME_V048="$HOME/adamArchives/Adam/workspace-heartbeat-runtime-v048"
PLUGIN_V047="$RUNTIME_V047/plugins/workspace-heartbeat"
PLUGIN_V048="$RUNTIME_V048/plugins/workspace-heartbeat"

CONDA="$HOME/miniforge3/bin/conda"
NODE="/home/atrott/miniforge3/envs/workspace-heartbeat-node/bin/node"
TUNNEL_CLIENT="$HOME/adamArchives/Adam/tooling/openai-tunnel-client/v0.0.18/unpacked/tunnel-client"
TUNNEL_CLIENT_VERSION_PREFIX="0.0.18+"

SESSION="workspace-heartbeat"
PORT=8787
PROFILE="workspace-heartbeat-production"
PROFILE_DIR="$HOME/.config/workspace-heartbeat/tunnel-client-profiles"
SECRET_DIR="$HOME/.config/workspace-heartbeat"
SECRET_FILE="$SECRET_DIR/tunnel-runtime-key"
STATE_DIR="$HOME/.local/state/workspace-heartbeat"
HEALTH_URL_FILE="$STATE_DIR/tunnel-health.url"
BIN_DIR="$HOME/bin"
ACTIVE_UP="$BIN_DIR/heartbeat-up"
ROLLBACK_UP="$BIN_DIR/heartbeat-up.v047-ngrok.rollback"
TUNNEL_UP="$BIN_DIR/heartbeat-up.v048-tunnel"
ROLLBACK_HELPER="$BIN_DIR/heartbeat-rollback-v047-ngrok"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

listener_pid() {
  local port="$1"
  ss -ltnp 2>/dev/null \
    | awk -v p=":${port}" '$4 ~ p"$" {print}' \
    | grep -o 'pid=[0-9]*' \
    | cut -d= -f2 \
    | head -n1 \
    || true
}

verify_runtime_pid() {
  local pid="$1" expected_cwd="$2" expected_sha="$3"
  [ -n "$pid" ] || return 1
  [ -d "/proc/$pid" ] || return 1
  local cwd exe sha
  cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
  exe="$(readlink -f "/proc/$pid/exe" 2>/dev/null || true)"
  sha="$(git -C "$cwd" rev-parse HEAD 2>/dev/null || true)"
  [ "$cwd" = "$expected_cwd" ] && [ "$exe" = "$NODE" ] && [ "$sha" = "$expected_sha" ]
}

if [ "$(id -u)" -eq 0 ]; then
  fail "run as the normal atrott user, not root"
fi

for cmd in git curl tmux ss grep awk cut head cp install chmod mkdir rm pgrep; do
  require_cmd "$cmd"
done

[ -x "$CONDA" ] || fail "missing conda launcher: $CONDA"
[ -x "$NODE" ] || fail "missing accepted Node executable: $NODE"
[ -x "$TUNNEL_CLIENT" ] || fail "missing staged tunnel-client: $TUNNEL_CLIENT"

TC_VERSION="$($TUNNEL_CLIENT --version 2>&1 | head -n1)"
case "$TC_VERSION" in
  "$TUNNEL_CLIENT_VERSION_PREFIX"*) ;;
  *) fail "unexpected tunnel-client version: $TC_VERSION" ;;
esac

echo "=== PRE-CUTOVER PRODUCTION PROVENANCE ==="
curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/" || fail "production Heartbeat :$PORT is not healthy"
echo

OLD_PID="$(listener_pid "$PORT")"
verify_runtime_pid "$OLD_PID" "$PLUGIN_V047" "$ROLLBACK_SHA" \
  || fail "current :$PORT listener is not the accepted v0.4.7 runtime"

echo "OLD_PID=$OLD_PID"
echo "OLD_CWD=$PLUGIN_V047"
echo "OLD_SHA=$ROLLBACK_SHA"
echo "TUNNEL_CLIENT=$TC_VERSION"

# A second tunnel-client polling the same tunnel during cutover could split queued
# requests between the acceptance runtime and production. Require the isolated
# acceptance daemon to be stopped first.
EXISTING_TUNNEL_PIDS="$(pgrep -f "${TUNNEL_CLIENT} run" || true)"
if [ -n "$EXISTING_TUNNEL_PIDS" ]; then
  echo "Existing tunnel-client run process(es): $EXISTING_TUNNEL_PIDS" >&2
  fail "stop the isolated acceptance tunnel (Ctrl-C in its terminal) before production cutover"
fi

echo
echo "=== PREPARE EXACT V0.4.8 RUNTIME ==="
git -C "$CONTROL" fetch origin workspace-heartbeat-secure-mcp-tunnel-v1-current-main

git -C "$CONTROL" cat-file -e "${CANDIDATE_SHA}^{commit}"

if [ -e "$RUNTIME_V048" ]; then
  [ -d "$RUNTIME_V048/.git" ] || [ -f "$RUNTIME_V048/.git" ] \
    || fail "$RUNTIME_V048 exists but is not a git worktree"
  [ "$(git -C "$RUNTIME_V048" rev-parse HEAD)" = "$CANDIDATE_SHA" ] \
    || fail "$RUNTIME_V048 exists at the wrong SHA"
else
  git -C "$CONTROL" worktree add --detach "$RUNTIME_V048" "$CANDIDATE_SHA"
fi

[ "$(git -C "$RUNTIME_V048" rev-parse HEAD)" = "$CANDIDATE_SHA" ] \
  || fail "v0.4.8 runtime SHA mismatch"

# v0.4.7 and v0.4.8 have the same declared depencies. Copy the already
# accepted dependency tree so the new production runtime is independent of the
# rollback worktree without resolving fresh transitive versions.
if [ ! -d "$PLUGIN_V048/node_modules" ]; then
  [ -d "$PLUGIN_V047/node_modules" ] || fail "accepted v0.4.7 node_modules missing"
  cp -a "$PLUGIN_V047/node_modules" "$PLUGIN_V048/node_modules"
fi

(
  cd "$PLUGIN_V048"
  "$CONDA" run --no-capture-output -n workspace-heartbeat-node npm test
)

echo "V048_NODE_TESTS=PASS"

echo
echo "=== PREPARE RESTRICTED RUNTIME SECRET ==="
mkdir -p "$SECRET_DIR" "$PROFILE_DIR" "$STATE_DIR" "$BIN_DIR"
chmod 700 "$SECRET_DIR" "$PROFILE_DIR" "$STATE_DIR"

if [ ! -s "$SECRET_FILE" ]; then
  echo "Enter the dedicated restricted Secure MCP Tunnel runtime key."
  echo "Input is hidden and will be stored only in $SECRET_FILE with mode 0600."
  read -rsp "Runtime key: " RUNTIME_KEY
  echo
  [ -n "$RUNTIME_KEY" ] || fail "empty runtime key"
  umask 077
  printf '%s' "$RUNTIME_KEY" > "$SECRET_FILE"
  unset RUNTIME_KEY
fi
chmod 600 "$SECRET_FILE"

SECRET_MODE="$(stat -c '%a' "$SECRET_FILE")"
[ "$SECRET_MODE" = "600" ] || fail "runtime key file mode is $SECRET_MODE, expected 600"
echo "SECRET_REFERENCE=file:$SECRET_FILE"
echo "SECRET_MODE=$SECRET_MODE"
echo "(secret value intentionally not printed)"

echo
echo "=== MATERIALIZE PRODUCTION TUNNEL PROFILE ==="
"$TUNNEL_CLIENT" init \
  --sample sample_mcp_remote_no_auth \
  --profile "$PROFILE" \
  --profile-dir "$PROFILE_DIR" \
  --tunnel-id "$TUNNEL_ID" \
  --mcp-server-url "http://127.0.0.1:${PORT}/mcp" \
  --health-listen-addr "127.0.0.1:0" \
  --control-plane-api-key-ref "file:$SECRET_FILE" \
  --force

if grep -R --binary-files=without-match -n 'sk-' "$PROFILE_DIR"; then
  fail "production profile unexpectedly contains an inline API key"
fi

echo "PROFILE_SECRET_SCAN=PASS"

# Doctor can safely target the currently running v0.4.7 server because this gate
# verifies control-plane auth, tunnel scope, profile parsing, ind local MCP
# reachability before we stop the rollback runtime.
"$TUNNEL_CLIENT" doctor \
  --profile "$PROFILE" \
  --profile-dir "$PROFILE_DIR" \
  --explain

echo "PRODUCTION_PROFILE_DOCTOR=PASS"

echo
echo "=== PRESERVE V0.4.7/NGROK ROLLBACK LAUNCHER ==="
[ -x "$ACTIVE_UP" ] || fail "missing existing launcher: $ACTIVE_UP"
if [ ! -e "$ROLLBACK_UP" ]; then
  cp -p "$ACTIVE_UP" "$ROLLBACK_UP"
fi
chmod 755 "$ROLLBACK_UP"

cat > "$TUNNEL_UP.tmp" <<'LAUNCHER'
#!/usr/bin/env bash
set -Eeuo pipefail

DIR="$HOME/adamArchives/Adam/workspace-heartbeat-runtime-v048/plugins/workspace-heartbeat"
CONTROL="$HOME/adamArchives/Adam/workspace-heartbeat-runtime-v048"
EXPECTED_SHA="def7c5fe6498b1bd742d912c1490d1f7160cab5f"
CONDA="$HOME/miniforge3/bin/conda"
NODE="/home/atrott/miniforge3/envs/workspace-heartbeat-node/bin/node"
TUNNEL_CLIENT="$HOME/adamArchives/Adam/tooling/openai-tunnel-client/v0.0.18/unpacked/tunnel-client"
PROFILE="workspace-heartbeat-production"
PROFILE_DIR="$HOME/.config/workspace-heartbeat/tunnel-client-profiles"
SECRET_FILE="$HOME/.config/workspace-heartbeat/tunnel-runtime-key"
STATE_DIR="$HOME/.local/state/workspace-heartbeat"
HEALTH_URL_FILE="$STATE_DIR/tunnel-health.url"
SESSION="workspace-heartbeat"
PORT=8787
TUNNEL_ID="tunnel_6ae017d8655c8191976ef3bccc31f593"

fail() { echo "ERROR: $*" >&2; exit 1; }

[ -x "$CONDA" ] || fail "missing conda launcher"
[ -x "$NODE" ] || fail "missing Node20 runtime"
[ -x "$TUNNEL_CLIENT" ] || fail "missing tunnel-client"
[ -s "$SECRET_FILE" ] || fail "missing tunnel runtime key file"
[ "$(stat -c '%a' "$SECRET_FILE")" = "600" ] || fail "tunnel runtime key file must be mode 0600"
[ "$(git -C "$CONTROL" rev-parse HEAD)" = "$EXPECTED_SHA" ] || fail "v0.4.8 runtime SHA mismatch"

mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
rm -f "$HEALTH_URL_FILE"

tmux kill-session -t "$SESSION" 2>/dev/null || true
sleep 0.2

if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)8787$'; then
  fail "port 8787 is occupied after stopping prior Heartbeat session"
fi

tmux new-session -d -s "$SESSION" -n mcp \
  "cd '$DIR' && exec '$CONDA' run --no-capture-output -n workspace-heartbeat-node npm start"

MCP_READY=0
for _ in $(seq 1 100); do
  if curl -fsS --max-time 1 "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
    MCP_READY=1
    break
  fi
  sleep 0.1
done

if [ "$MCP_READY" != "1" ]; then
  tmux capture-pane -pt "$SESSION:mcp" -S -80 2>/dev/null || true
  tmux kill-session -t "$SESSION" 2>/dev/null || true
  fail "v0.4.8 MCP server failed to become healthy"
fi

"$TUNNEL_CLIENT" doctor \
  --profile "$PROFILE" \
  --profile-dir "$PROFILE_DIR" \
  --explain >/dev/null

tmux new-window -t "$SESSION" -n tunnel \
  "exec '$TUNNEL_CLIENT' run --profile '$PROFILE' --profile-dir '$PROFILE_DIR' --health.url-file '$HEALTH_URL_FILE'"

TUNNEL_READY=0
for _ in $(seq 1 200); do
  if [ -s "$HEALTH_URL_FILE" ]; then
    HEALTH_URL="$(cat "$HEALTH_URL_FILE")"
    if curl -fsS --max-time 1 "$HEALTH_URL/readyz" >/dev/null 2>&1; then
      TUNNEL_READY=1
      break
    fi
  fi
  sleep 0.2
done

if [ "$TUNNEL_READY" != "1" ]; then
  tmux capture-pane -pt "$SESSION:tunnel" -S -120 2>/dev/null || true
  tmux kill-session -t "$SESSION" 2>/dev/null || true
  fail "Secure MCP Tunnel failed readiness"
fi

echo "Workspace Heartbeat started."
echo "SESSION=$SESSION"
echo "MCP=http://127.0.0.1:${PORT}/mcp"
echo "TUNNEL_ID=$TUNNEL_ID"
echo "TUNNEL_HEALTH=$HEALTH_URL"
LAUNCHER

install -m 0755 "$TUNNEL_UP.tmp" "$TUNNEL_UP"
rm -f "$TUNNEL_UP.tmp"

cat > "$ROLLBACK_HELPER.tmp" <<'ROLLBACK'
#!/usr/bin/env bash
set -Eeuo pipefail
ACTIVE="$HOME/bin/heartbeat-up"
ROLLBACK="$HOME/bin/heartbeat-up.v047-ngrok.rollback"
[ -x "$ROLLBACK" ] || { echo "ERROR: rollback launcher missing: $ROLLBACK" >&2; exit 1; }
tmux kill-session -t workspace-heartbeat 2>/dev/null || true
cp -p "$ROLLBACK" "$ACTIVE"
chmod 755 "$ACTIVE"
exec "$ACTIVE"
ROLLBACK
install -m 0755 "$ROLLBACK_HELPER.tmp" "$ROLLBACK_HELPER"
rm -f "$ROLLBACK_HELPER.tmp"

echo "ROLLBACK_LAUNCHER=$ROLLBACK_UP"
echo "ROLLBACK_HELPER=$ROLLBACK_HELPER"

echo
echo "=== CUT OVER NORMAL LAUNCHER ==="
cp -p "$TUNNEL_UP" "$ACTIVE_UP"
chmod 755 "$ACTIVE_UP"

tmux kill-session -t "$SESSION" 2>/dev/null || true
sleep 0.2

if ! "$ACTIVE_UP"; then
  echo "v0.4.8 tunnel launcher failed; restoring v0.4.7/ngrok rollback." >&2
  cp -p "$ROLLBACK_UP" "$ACTIVE_UP"
  chmod 755 "$ACTIVE_UP"
  "$ACTIVE_UP" || true
  fail "cutover launcher failed and rollback was attempted"
fi

echo
echo "=== POST-CUTOVER PROVENANCE ==="
NEW_PID="$(listener_pid "$PORT")"
verify_runtime_pid "$NEW_PID" "$PLUGIN_V048" "$CANDIDATE_SHA" \
  || {
    echo "post-cutover runtime provenance failed; invoking rollback" >&2
    "$ROLLBACK_HELPER" || true
    fail "post-cutover runtime provenance failed"
  }

if pgrep -af 'ngrok .*8787' >/dev/null 2>&1; then
  pgrep -af 'ngrok .*8787' >&2 || true
  "$ROLLBACK_HELPER" || true
  fail "ngrok still appears active on the normal Heartbeat path"
fi

TUNNEL_PIDS="$(pgrep -f "${TUNNEL_CLIENT} run" || true)"
[ -n "$TUNNEL_PIDS" ] || {
  "$ROLLBACK_HELPER" || true
  fail "tunnel-client is not running after cutover"
}

[ -s "$HEALTH_URL_FILE" ] || {
  "$ROLLBACK_HELPER" || true
  fail "tunnel health URL file missing after cutover"
}
HEALTH_URL="$(cat "$HEALTH_URL_FILE")"
curl -fsS --max-time 2 "$HEALTH_URL/readyz" >/dev/null \
  || {
    "$ROLLBACK_HELPER" || true
    fail "tunnel-client readiness failed after cutover"
  }

curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/"
echo

echo "NEW_PID=$NEW_PID"
echo "NEW_CWD=$PLUGIN_V048"
echo "NEW_SHA=$CANDIDATE_SHA"
echo "TUNNEL_PID(S)=$TUNNEL_PIDS"
echo "TUNNEL_HEALTH=$HEALTH_URL"
echo "ROLLBACK_HELPER=$ROLLBACK_HELPER"
echo "WORKSPACE_HEARTBEAT_V048_TUNNEL_CUTOVER_LOCAL_GATE=PASS"
