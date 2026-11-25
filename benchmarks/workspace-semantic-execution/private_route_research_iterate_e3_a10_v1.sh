#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

BASE_URL="https://gokhan-lambda-vector.tailca6171.ts.net"
ROUTE_PATH="/operator-bridge/v1"
BACKEND_PORT="8765"
PG_PORT="55437"
PG_PREFIX="/opt/workspace-ci/postgresql/postgresql-14.24-pgvector-0.8.6"
RUNTIME_ROOT="/tmp/workspace-semantic-execution-e3-a10-v1"
PGDATA="$RUNTIME_ROOT/postgres"
PGSOCKET="$RUNTIME_ROOT/socket"
SRCROOT="$RUNTIME_ROOT/source"
VENV="$RUNTIME_ROOT/venv"
SERVE_OBSERVED="$RUNTIME_ROOT/serve-observed.json"
FUNNEL_OBSERVED="$RUNTIME_ROOT/funnel-observed.json"
SERVE_BEFORE="$RUNTIME_ROOT/serve-before.json"
FUNNEL_BEFORE="$RUNTIME_ROOT/funnel-before.json"
BINDING_MANIFEST_REL="architecture/workspace-semantic-execution-e3-live-binding-manifest.v0.1.json"
CLOSURE_REL="benchmarks/workspace-semantic-execution/e3_live_binding_closure_v1.py"
AUTHORITY_REL="architecture/workspace-semantic-execution-research-iterate-e3-a10-live-authority.v0.1.json"
AUTHORITY_ID="workspace-semantic-execution-research-iterate-e3-a10-live-authority-v0.1"
REPO_URL="https://github.com/adamtrott78/workspace-control.git"
WINDOWS_READY_MARKER="E3_A10_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS"
REVIEW_HEAD=""
ROUTE_ATTEMPTED=0
POSTGRES_STARTED=0

fail() {
  echo "E3_A10_ACTIVATION_ERROR=$*" >&2
  exit 70
}

remove_route_only() {
  sudo tailscale serve --https=443 --set-path="$ROUTE_PATH" off >/dev/null 2>&1
}

verify_restored_snapshot() {
  local after_serve="$RUNTIME_ROOT/serve-cleanup.json"
  local after_funnel="$RUNTIME_ROOT/funnel-cleanup.json"
  sudo tailscale serve status --json >"$after_serve" || return 1
  sudo tailscale funnel status --json >"$after_funnel" || return 1
  python3 - "$SERVE_BEFORE" "$FUNNEL_BEFORE" "$after_serve" "$after_funnel" <<'PY'
import json, sys

def load(path):
    d=json.load(open(path, encoding="utf-8")) or {}
    if not isinstance(d, dict):
        raise SystemExit(f"STATUS_JSON_NOT_OBJECT:{path}")
    return {
        "TCP": d.get("TCP") or {},
        "Web": d.get("Web") or {},
        "AllowFunnel": d.get("AllowFunnel") or {},
        "Services": d.get("Services") or {},
    }

before_serve=load(sys.argv[1])
before_funnel=load(sys.argv[2])
after_serve=load(sys.argv[3])
after_funnel=load(sys.argv[4])
if after_serve != before_serve:
    raise SystemExit(
        f"SERVE_ROLLBACK_MISMATCH:before={before_serve!r}:after={after_serve!r}"
    )
if after_funnel != before_funnel:
    raise SystemExit(
        f"FUNNEL_ROLLBACK_MISMATCH:before={before_funnel!r}:after={after_funnel!r}"
    )
PY
}

cleanup() {
  rc=$?
  set +e
  cleanup_ok=1
  if [[ "$ROUTE_ATTEMPTED" == "1" ]]; then
    if remove_route_only && verify_restored_snapshot; then
      echo "E3_A10_CLEANUP_ROUTE_RESTORED=PASS"
      ROUTE_ATTEMPTED=0
    else
      echo "E3_A10_CLEANUP_ROUTE_RESTORED=FAIL" >&2
      cleanup_ok=0
    fi
  fi
  if [[ "$POSTGRES_STARTED" == "1" ]]; then
    LD_LIBRARY_PATH="$PG_PREFIX/lib" "$PG_PREFIX/bin/pg_ctl"       -D "$PGDATA" -m fast -w stop >/dev/null 2>&1 || cleanup_ok=0
  fi
  if [[ "$cleanup_ok" == "1" ]]; then
    rm -rf -- "$RUNTIME_ROOT" >/dev/null 2>&1 || true
  else
    echo "E3_A10_CLEANUP_EVIDENCE_PRESERVED=$RUNTIME_ROOT" >&2
    if [[ "$rc" == "0" ]]; then rc=71; fi
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

[[ "$(id -u)" -ne 0 ]] || fail "RUN_AS_OPERATOR_NOT_ROOT"
[[ "$(id -un)" == "atrott" ]] || fail "EXPECTED_OPERATOR_USER_ATROTT"

for cmd in git python3 tar sudo tailscale ss; do
  command -v "$cmd" >/dev/null 2>&1 || fail "MISSING_COMMAND:$cmd"
done
for cmd in postgres initdb pg_ctl createdb; do
  [[ -x "$PG_PREFIX/bin/$cmd" ]] || fail "MISSING_PINNED_POSTGRES_RUNTIME:$cmd"
done
[[ "$("$PG_PREFIX/bin/postgres" --version)" == "postgres (PostgreSQL) 14.24" ]] \
  || fail "POSTGRES_RUNTIME_VERSION_MISMATCH"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "NOT_IN_GIT_CHECKOUT"
[[ ! -e "$RUNTIME_ROOT" ]] || fail "RUNTIME_ROOT_ALREADY_EXISTS"
mkdir -m 0700 "$RUNTIME_ROOT" "$PGDATA" "$PGSOCKET" "$SRCROOT"

BINDING_VALUES="$RUNTIME_ROOT/binding-values.txt"
python3 "$ROOT/$CLOSURE_REL" \
  --repo-root "$ROOT" \
  --authority "$AUTHORITY_REL" \
  --manifest "$BINDING_MANIFEST_REL" \
  --expected-authority-id "$AUTHORITY_ID" \
  --emit-lines >"$BINDING_VALUES" \
  || fail "BINDING_CLOSURE_PRECHECK_FAILED"
mapfile -t BV <"$BINDING_VALUES"
[[ "${#BV[@]}" -eq 26 ]] || fail "BINDING_CLOSURE_FIELD_COUNT_MISMATCH:${#BV[@]}"
CANDIDATE_BRANCH="${BV[0]}"
CANDIDATE_BASELINE="${BV[1]}"
ROOT_PACKET_SHA256="${BV[2]}"
WRAPPER_REL="${BV[3]}"
EXPECTED_WRAPPER_BLOB="${BV[4]}"
E2_HARNESS_REL="${BV[5]}"
EXPECTED_E2_HARNESS_BLOB="${BV[6]}"
OBSERVER_REL="${BV[7]}"
EXPECTED_OBSERVER_BLOB="${BV[8]}"
CLOSURE_REL="${BV[9]}"
EXPECTED_CLOSURE_BLOB="${BV[10]}"
FIXTURE_REL="${BV[11]}"
EXPECTED_FIXTURE_BLOB="${BV[12]}"
WORKER_RESULT_SCHEMA_REVIEW_HEAD="${BV[13]}"
WORKER_RESULT_SCHEMA_BLOB="${BV[14]}"
A8_FRONTEND_REVIEW_HEAD="${BV[15]}"
A8_FRONTEND_SOURCE_HEAD="${BV[16]}"
A8_FRONTEND_SRC_TREE="${BV[17]}"
ACCEPTED_A7_DEV_HARNESS_BLOB="${BV[18]}"
OPERATOR_TRANSPORT_HEAD="${BV[19]}"
SOURCE_HEAD="${BV[20]}"
SEMANTIC_SHA="${BV[21]}"
EXPECTED_OPERATOR_HTTP_BLOB="${BV[22]}"
EXPECTED_PACKET_COMPILER_BLOB="${BV[23]}"
REVIEW_HEAD="${BV[24]}"
BINDING_MANIFEST_BLOB="${BV[25]}"

REMOTE_CANDIDATE="$(git ls-remote "$REPO_URL" "refs/heads/$CANDIDATE_BRANCH" | awk '{print $1}')"
python3 "$ROOT/$CLOSURE_REL" \
  --repo-root "$ROOT" \
  --authority "$AUTHORITY_REL" \
  --manifest "$BINDING_MANIFEST_REL" \
  --expected-authority-id "$AUTHORITY_ID" \
  --candidate-head "$REMOTE_CANDIDATE" \
  || fail "BINDING_CLOSURE_CANDIDATE_FAILED"
echo "E3_A10_BINDING_CLOSURE=PASS"
echo "E3_A10_CANDIDATE_BASELINE=PASS"
echo "=== E3-A10 PRIVATE ROUTE PREFLIGHT ==="
echo "SEMANTIC_SHA=$SEMANTIC_SHA"
echo "BASE_URL=$BASE_URL"
echo "ROUTE_PATH=$ROUTE_PATH"

sudo -v

tailscale status --json >"$RUNTIME_ROOT/tailscale-status.json"
EXPECTED_TAILSCALE_LOGIN="$(python3 - "$RUNTIME_ROOT/tailscale-status.json" <<'PY'
import json, sys
d=json.load(open(sys.argv[1], encoding="utf-8"))
self_node=d.get("Self") or {}
dns=str(self_node.get("DNSName") or "").rstrip(".")
if dns != "gokhan-lambda-vector.tailca6171.ts.net":
    raise SystemExit(f"TAILSCALE_DNS_MISMATCH:{dns!r}")
self_uid=self_node.get("UserID")
if self_uid is None:
    raise SystemExit("TAILSCALE_SELF_USER_ID_MISSING")
peer_match=None
for peer in (d.get("Peer") or {}).values():
    pdns=str(peer.get("DNSName") or "").rstrip(".")
    phost=str(peer.get("HostName") or "")
    if pdns == "desktop-ub9p70p.tailca6171.ts.net" or phost == "desktop-ub9p70p":
        peer_match=peer
        break
if peer_match is None:
    raise SystemExit("TAILSCALE_WINDOWS_OPERATOR_PEER_MISSING")
if peer_match.get("UserID") != self_uid:
    raise SystemExit("TAILSCALE_OPERATOR_OWNER_MISMATCH")
users=d.get("User") or {}
user=users.get(str(self_uid)) or users.get(self_uid) or {}
login=user.get("LoginName")
if not isinstance(login, str) or not login or any(ord(ch) < 0x20 for ch in login):
    raise SystemExit("TAILSCALE_LOGIN_INVALID")
print(login, end="")
PY
)"
[[ -n "$EXPECTED_TAILSCALE_LOGIN" ]] || fail "TAILSCALE_LOGIN_DERIVATION_FAILED"
echo "TAILSCALE_HOST_BINDING=PASS"
echo "TAILSCALE_OPERATOR_PEER_BINDING=PASS"
echo "TAILSCALE_LOGIN_BINDING=PASS"

sudo tailscale serve status --json >"$SERVE_OBSERVED"
sudo tailscale funnel status --json >"$FUNNEL_OBSERVED"
STALE_ROUTE_STATE="$(python3 - "$SERVE_OBSERVED" "$FUNNEL_OBSERVED" <<'PY'
import json, sys
HOST="gokhan-lambda-vector.tailca6171.ts.net:443"
ROOT_PROXY="http://127.0.0.1:8888"
ROUTE="/operator-bridge/v1"
ROUTE_PROXY="http://127.0.0.1:8765/operator-bridge/v1"

def load(path, label):
    d=json.load(open(path, encoding="utf-8")) or {}
    if not isinstance(d, dict):
        raise SystemExit(f"{label}_STATUS_JSON_NOT_OBJECT")
    return d

def relevant(d):
    return {
        "TCP": d.get("TCP") or {},
        "Web": d.get("Web") or {},
        "AllowFunnel": d.get("AllowFunnel") or {},
        "Services": d.get("Services") or {},
    }

def classify(label, d):
    if d.get("AllowFunnel"):
        raise SystemExit(f"{label}_FUNNEL_EXPOSURE_DETECTED")
    if d.get("Services"):
        raise SystemExit(f"{label}_UNEXPECTED_SERVICE_CONFIG")
    tcp=d.get("TCP") or {}
    if set(tcp) != {"443"} or not (tcp.get("443") or {}).get("HTTPS"):
        raise SystemExit(f"{label}_HTTPS_443_SHAPE_MISMATCH:{tcp!r}")
    web=d.get("Web") or {}
    if set(web) != {HOST}:
        raise SystemExit(f"{label}_WEB_HOST_SHAPE_MISMATCH:{sorted(web)!r}")
    handlers=(web[HOST] or {}).get("Handlers") or {}
    root=(handlers.get("/") or {}).get("Proxy")
    if root != ROOT_PROXY:
        raise SystemExit(f"{label}_JUPYTER_ROOT_MAPPING_MISMATCH:{handlers!r}")
    route_keys=[k for k in (ROUTE, ROUTE + "/") if k in handlers]
    allowed={"/", *route_keys}
    if set(handlers) != allowed:
        raise SystemExit(f"{label}_UNEXPECTED_HANDLER_SET:{handlers!r}")
    if len(route_keys) > 1:
        raise SystemExit(f"{label}_AMBIGUOUS_E3_ROUTE:{handlers!r}")
    if not route_keys:
        return "CLEAN"
    route_proxy=(handlers[route_keys[0]] or {}).get("Proxy")
    if route_proxy != ROUTE_PROXY:
        raise SystemExit(f"{label}_E3_A10_ROUTE_PROXY_MISMATCH:{route_proxy!r}")
    return "EXACT_STALE_ROUTE"

serve=load(sys.argv[1], "SERVE")
funnel=load(sys.argv[2], "FUNNEL")
serve_state=classify("SERVE", serve)
funnel_state=classify("FUNNEL", funnel)
if relevant(serve) != relevant(funnel):
    raise SystemExit("SERVE_FUNNEL_STATUS_VIEW_MISMATCH")
if serve_state != funnel_state:
    raise SystemExit(f"SERVE_FUNNEL_ROUTE_STATE_MISMATCH:{serve_state}:{funnel_state}")
print(serve_state, end="")
PY
)"

if [[ "$STALE_ROUTE_STATE" == "EXACT_STALE_ROUTE" ]]; then
  if sudo ss -H -ltn | awk -v p=":$BACKEND_PORT" '$4 ~ (p "$") { found=1 } END { exit(found ? 0 : 1) }'; then
    fail "STALE_E3_A10_ROUTE_BACKEND_LISTENER_PRESENT"
  fi
  remove_route_only || fail "STALE_E3_A10_ROUTE_CLEAR_FAILED"
  echo "TAILSCALE_STALE_E3_A10_ROUTE_CLEARED=PASS"
elif [[ "$STALE_ROUTE_STATE" != "CLEAN" ]]; then
  fail "STALE_E3_A10_ROUTE_CLASSIFICATION_INVALID:$STALE_ROUTE_STATE"
fi

sudo tailscale serve status --json >"$SERVE_BEFORE"
sudo tailscale funnel status --json >"$FUNNEL_BEFORE"
python3 - "$SERVE_BEFORE" "$FUNNEL_BEFORE" <<'PY'
import json, sys
HOST="gokhan-lambda-vector.tailca6171.ts.net:443"
ROOT_PROXY="http://127.0.0.1:8888"
ROUTE="/operator-bridge/v1"

def load(path, label):
    d=json.load(open(path, encoding="utf-8")) or {}
    if not isinstance(d, dict):
        raise SystemExit(f"{label}_STATUS_JSON_NOT_OBJECT")
    return d

def relevant(d):
    return {
        "TCP": d.get("TCP") or {},
        "Web": d.get("Web") or {},
        "AllowFunnel": d.get("AllowFunnel") or {},
        "Services": d.get("Services") or {},
    }

serve=load(sys.argv[1], "SERVE")
funnel=load(sys.argv[2], "FUNNEL")
for label,d in (("SERVE",serve),("FUNNEL",funnel)):
    if d.get("AllowFunnel"):
        raise SystemExit(f"{label}_FUNNEL_EXPOSURE_DETECTED")
    if d.get("Services"):
        raise SystemExit(f"{label}_UNEXPECTED_SERVICE_CONFIG")
    tcp=d.get("TCP") or {}
    if set(tcp) != {"443"} or not (tcp.get("443") or {}).get("HTTPS"):
        raise SystemExit(f"{label}_HTTPS_443_SHAPE_MISMATCH:{tcp!r}")
    web=d.get("Web") or {}
    if set(web) != {HOST}:
        raise SystemExit(f"{label}_WEB_HOST_SHAPE_MISMATCH:{sorted(web)!r}")
    handlers=(web[HOST] or {}).get("Handlers") or {}
    if handlers != {"/":{"Proxy":ROOT_PROXY}}:
        raise SystemExit(f"{label}_CLEAN_ROOT_MAPPING_MISMATCH:{handlers!r}")
    if ROUTE in handlers or ROUTE + "/" in handlers:
        raise SystemExit(f"{label}_E3_A10_ROUTE_STILL_PRESENT")
if relevant(serve) != relevant(funnel):
    raise SystemExit("SERVE_FUNNEL_STATUS_VIEW_MISMATCH")
print("TAILSCALE_EXISTING_JUPYTER_ROOT_BINDING=PASS")
print("TAILSCALE_E3_A10_ROUTE_ABSENT=PASS")
print("TAILSCALE_FUNNEL_DISABLED=PASS")
PY

git -C "$ROOT" cat-file -e "$SEMANTIC_SHA^{commit}" 2>/dev/null \
  || fail "SEMANTIC_SHA_NOT_AVAILABLE_LOCALLY"
LIVE_OPERATOR_HTTP_BLOB="$(git -C "$ROOT" rev-parse "$SEMANTIC_SHA:semantic-execution/src/workspace_semantic_execution/adapters/operator_bridge_http.py")"
[[ "$LIVE_OPERATOR_HTTP_BLOB" == "$EXPECTED_OPERATOR_HTTP_BLOB" ]] \
  || fail "LIVE_SEMANTIC_OPERATOR_HTTP_BLOB_MISMATCH:$LIVE_OPERATOR_HTTP_BLOB"
LIVE_PACKET_COMPILER_BLOB="$(git -C "$ROOT" rev-parse "$SEMANTIC_SHA:semantic-execution/src/workspace_semantic_execution/application/packet_compiler.py")"
[[ "$LIVE_PACKET_COMPILER_BLOB" == "$EXPECTED_PACKET_COMPILER_BLOB" ]] \
  || fail "LIVE_SEMANTIC_PACKET_COMPILER_BLOB_MISMATCH:$LIVE_PACKET_COMPILER_BLOB"
git -C "$ROOT" cat-file -e "$REVIEW_HEAD^{commit}" 2>/dev/null \
  || fail "E3_A10_REVIEW_HEAD_UNAVAILABLE:$REVIEW_HEAD"
git -C "$ROOT" merge-base --is-ancestor "$REVIEW_HEAD" HEAD \
  || fail "E3_A10_REVIEW_NOT_ANCESTOR"
echo "E3_A10_AUTHORITY_BINDING=PASS"
echo "E3_A10_SEMANTIC_LIVE_BINDING=PASS"
echo "E3_A10_PRELIVE_WINDOWS_CONFIRMATION_REQUIRED=$WINDOWS_READY_MARKER"
WINDOWS_READY="${E3_A10_WINDOWS_READY_CONFIRMATION:-}"
[[ "$WINDOWS_READY" == "$WINDOWS_READY_MARKER" ]] || fail "WINDOWS_READY_CONFIRMATION_MISMATCH"
echo "E3_A10_WINDOWS_READY_GATE=PASS"
git -C "$ROOT" archive "$SEMANTIC_SHA" semantic-execution | tar -x -C "$SRCROOT"
mkdir -p "$SRCROOT/benchmarks/workspace-semantic-execution" "$SRCROOT/architecture"
cp -- "$ROOT/$WRAPPER_REL" "$SRCROOT/$WRAPPER_REL"
cp -- "$ROOT/$E2_HARNESS_REL" "$SRCROOT/$E2_HARNESS_REL"
cp -- "$ROOT/$OBSERVER_REL" "$SRCROOT/$OBSERVER_REL"
cp -- "$ROOT/$CLOSURE_REL" "$SRCROOT/$CLOSURE_REL"
cp -- "$ROOT/$BINDING_MANIFEST_REL" "$SRCROOT/$BINDING_MANIFEST_REL"
mkdir -p -- "$SRCROOT/$(dirname "$FIXTURE_REL")"
cp -- "$ROOT/$FIXTURE_REL" "$SRCROOT/$FIXTURE_REL"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --disable-pip-version-check --no-input   'psycopg[binary]==3.3.9'
"$VENV/bin/python" - <<'PY'
import importlib.metadata
assert importlib.metadata.version("psycopg") == "3.3.9"
print("PSYCOPG_DEPENDENCY_PIN=PASS")
PY

LD_LIBRARY_PATH="$PG_PREFIX/lib" "$PG_PREFIX/bin/initdb"   -D "$PGDATA"   --username=atrott   --auth-local=trust   --auth-host=reject   --no-locale   --encoding=UTF8 >/dev/null
cat >>"$PGDATA/postgresql.conf" <<EOF
listen_addresses = ''
unix_socket_directories = '$PGSOCKET'
port = $PG_PORT
EOF
LD_LIBRARY_PATH="$PG_PREFIX/lib" "$PG_PREFIX/bin/pg_ctl"   -D "$PGDATA" -w start >/dev/null
POSTGRES_STARTED=1
LD_LIBRARY_PATH="$PG_PREFIX/lib" "$PG_PREFIX/bin/createdb"   -h "$PGSOCKET" -p "$PG_PORT" -U atrott semantic_execution

export SEMANTIC_EXECUTION_POSTGRES_DSN="host=$PGSOCKET port=$PG_PORT user=atrott dbname=semantic_execution"
export WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN="$EXPECTED_TAILSCALE_LOGIN"

ROUTE_ATTEMPTED=1
sudo tailscale serve --bg --https=443 --set-path="$ROUTE_PATH"   "http://127.0.0.1:$BACKEND_PORT$ROUTE_PATH"

sudo tailscale serve status --json >"$RUNTIME_ROOT/serve-active.json"
python3 - "$RUNTIME_ROOT/serve-active.json" <<'PY'
import json, sys
HOST="gokhan-lambda-vector.tailca6171.ts.net:443"
ROUTE="/operator-bridge/v1"
d=json.load(open(sys.argv[1], encoding="utf-8")) or {}
if not isinstance(d, dict):
    raise SystemExit("SERVE_ACTIVE_JSON_NOT_OBJECT")
if d.get("AllowFunnel"):
    raise SystemExit("FUNNEL_EXPOSURE_DETECTED")
handlers=((d.get("Web") or {}).get(HOST) or {}).get("Handlers") or {}
root=(handlers.get("/") or {}).get("Proxy")
route=(handlers.get(ROUTE) or handlers.get(ROUTE + "/") or {}).get("Proxy")
if root != "http://127.0.0.1:8888":
    raise SystemExit(f"JUPYTER_ROOT_MAPPING_CHANGED:{root!r}")
if route != "http://127.0.0.1:8765/operator-bridge/v1":
    raise SystemExit(f"OPERATOR_ROUTE_PROXY_MISMATCH:{route!r}")
print("TAILSCALE_JUPYTER_ROOT_PRESERVED=PASS")
print("TAILSCALE_E3_A10_ROUTE_EXACT_BINDING=PASS")
print("TAILSCALE_FUNNEL_DISABLED=PASS")
PY

PYTHONPATH="$SRCROOT/semantic-execution/src" \
  "$VENV/bin/python" "$WRAPPER_REL" \
    --source-head "$SOURCE_HEAD" \
    --review-head "$REVIEW_HEAD" \
    --authority-head "$(git -C "$ROOT" rev-parse HEAD)" \
    --binding-manifest "$SRCROOT/$BINDING_MANIFEST_REL" \
    --serve-port "$BACKEND_PORT" \
    --candidate-timeout-seconds 1200 \
    --sample-interval-seconds 1.0 \
    --preflight-only \
  || fail "E3_A10_WRAPPER_DETERMINISTIC_PREFLIGHT_FAILED"
echo "E3_A10_DETERMINISTIC_PREFLIGHT=PASS"
echo "E3_A10_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS"
set +e
(
  cd "$SRCROOT"
  PYTHONPATH="$SRCROOT/semantic-execution/src"     "$VENV/bin/python"     "$WRAPPER_REL"       --source-head "$SOURCE_HEAD"       --review-head "$REVIEW_HEAD"       --authority-head "$(git -C "$ROOT" rev-parse HEAD)"       --binding-manifest "$SRCROOT/$BINDING_MANIFEST_REL"       --serve-port "$BACKEND_PORT"       --candidate-timeout-seconds 1200       --sample-interval-seconds 1.0
)
CAL_RC=$?
set -e

remove_route_only
verify_restored_snapshot
ROUTE_ATTEMPTED=0
echo "TAILSCALE_EXISTING_CONFIG_EXACTLY_RESTORED=PASS"
echo "TAILSCALE_JUPYTER_ROOT_ROLLBACK_PRESERVED=PASS"

LD_LIBRARY_PATH="$PG_PREFIX/lib" "$PG_PREFIX/bin/pg_ctl"   -D "$PGDATA" -m fast -w stop >/dev/null
POSTGRES_STARTED=0

if [[ "$CAL_RC" -ne 0 ]]; then
  echo "E3_A10_RESEARCH_ITERATE_PROCESS_EXIT=$CAL_RC" >&2
  exit "$CAL_RC"
fi

echo "PRIVATE_ROUTE_RESEARCH_ITERATE_E3_A10_V1=PASS"
