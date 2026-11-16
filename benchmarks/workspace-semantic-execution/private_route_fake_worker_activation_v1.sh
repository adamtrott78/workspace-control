#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

SEMANTIC_SHA="7c20097c5f177f23c16a765b95ce94d7161f0d29"
BASE_URL="https://gokhan-lambda-vector.tailca6171.ts.net"
EXPECTED_DNS_NAME="gokhan-lambda-vector.tailca6171.ts.net"
EXPECTED_TAILSCALE_LOGIN="adamtrott78@gmail.com"
BACKEND_PORT="8765"
PG_PORT="55436"
PG_PREFIX="/opt/workspace-ci/postgresql/postgresql-14.24-pgvector-0.8.6"
RUNTIME_ROOT="/tmp/workspace-semantic-execution-private-route-v1"
PGDATA="$RUNTIME_ROOT/postgres"
PGSOCKET="$RUNTIME_ROOT/socket"
SRCROOT="$RUNTIME_ROOT/source"
VENV="$RUNTIME_ROOT/venv"
REPORT="$RUNTIME_ROOT/fake-worker.log"
SERVE_BEFORE="$RUNTIME_ROOT/serve-before.json"
FUNNEL_BEFORE="$RUNTIME_ROOT/funnel-before.json"

SERVE_STARTED=0
POSTGRES_STARTED=0

fail() {
  echo "PRIVATE_ROUTE_ACTIVATION_ERROR=$*" >&2
  exit 70
}

cleanup() {
  rc=$?
  set +e
  if [[ "$SERVE_STARTED" == "1" ]]; then
    sudo tailscale serve --https=443 off >/dev/null 2>&1 || true
  fi
  if [[ "$POSTGRES_STARTED" == "1" ]]; then
    LD_LIBRARY_PATH="$PG_PREFIX/lib" "$PG_PREFIX/bin/pg_ctl"       -D "$PGDATA" -m fast -w stop >/dev/null 2>&1 || true
  fi
  rm -rf -- "$RUNTIME_ROOT" >/dev/null 2>&1 || true
  exit "$rc"
}
trap cleanup EXIT INT TERM

[[ "$(id -u)" -ne 0 ]] || fail "RUN_AS_OPERATOR_NOT_ROOT"
[[ "$(id -un)" == "atrott" ]] || fail "EXPECTED_OPERATOR_USER_ATROTT"

for cmd in git python3 tar sudo tailscale; do
  command -v "$cmd" >/dev/null 2>&1 || fail "MISSING_COMMAND:$cmd"
done
for cmd in postgres initdb pg_ctl createdb; do
  [[ -x "$PG_PREFIX/bin/$cmd" ]] || fail "MISSING_PINNED_POSTGRES_RUNTIME:$cmd"
done
[[ "$("$PG_PREFIX/bin/postgres" --version)" == "postgres (PostgreSQL) 14.24" ]]   || fail "POSTGRES_RUNTIME_VERSION_MISMATCH"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "NOT_IN_GIT_CHECKOUT"
git -C "$ROOT" cat-file -e "$SEMANTIC_SHA^{commit}" 2>/dev/null   || fail "SEMANTIC_SHA_NOT_AVAILABLE_LOCALLY"
[[ ! -e "$RUNTIME_ROOT" ]] || fail "RUNTIME_ROOT_ALREADY_EXISTS"
mkdir -m 0700 "$RUNTIME_ROOT" "$PGDATA" "$PGSOCKET" "$SRCROOT"

echo "=== PRIVATE ROUTE PREFLIGHT ==="
echo "SEMANTIC_SHA=$SEMANTIC_SHA"
echo "BASE_URL=$BASE_URL"

sudo -v

tailscale status --json >"$RUNTIME_ROOT/tailscale-status.json"
python3 - "$RUNTIME_ROOT/tailscale-status.json" <<'PY'
import json, sys
d=json.load(open(sys.argv[1], encoding="utf-8"))
self_node=d.get("Self") or {}
dns=str(self_node.get("DNSName") or "").rstrip(".")
if dns != "gokhan-lambda-vector.tailca6171.ts.net":
    raise SystemExit(f"TAILSCALE_DNS_MISMATCH:{dns!r}")
uid=self_node.get("UserID")
users=d.get("User") or {}
user=users.get(str(uid)) or users.get(uid) or {}
login=user.get("LoginName")
if login != "adamtrott78@gmail.com":
    raise SystemExit(f"TAILSCALE_LOGIN_MISMATCH:{login!r}")
print("TAILSCALE_HOST_BINDING=PASS")
print("TAILSCALE_LOGIN_BINDING=PASS")
PY

sudo tailscale serve status --json >"$SERVE_BEFORE"
sudo tailscale funnel status --json >"$FUNNEL_BEFORE"
python3 - "$SERVE_BEFORE" "$FUNNEL_BEFORE" <<'PY'
import json, sys
for path,label in ((sys.argv[1],"SERVE"),(sys.argv[2],"FUNNEL")):
    d=json.load(open(path, encoding="utf-8"))
    for key in ("TCP","Web","AllowFunnel","Services"):
        if d.get(key):
            raise SystemExit(f"PREEXISTING_{label}_CONFIG:{key}")
print("TAILSCALE_EXISTING_SERVE_FUNNEL_EMPTY=PASS")
PY

git -C "$ROOT" archive "$SEMANTIC_SHA"   semantic-execution   benchmarks/workspace-semantic-execution/live_fake_worker_transport_v1.py   | tar -x -C "$SRCROOT"
[[ -f "$SRCROOT/benchmarks/workspace-semantic-execution/live_fake_worker_transport_v1.py" ]]   || fail "HARNESS_EXTRACTION_FAILED"

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

sudo tailscale serve --bg --https=443 "http://127.0.0.1:$BACKEND_PORT"
SERVE_STARTED=1
sudo tailscale serve status --json >"$RUNTIME_ROOT/serve-active.json"
python3 - "$RUNTIME_ROOT/serve-active.json" <<'PY'
import json, sys
d=json.load(open(sys.argv[1], encoding="utf-8"))
tcp=d.get("TCP") or {}
if not (tcp.get("443") or {}).get("HTTPS"):
    raise SystemExit("SERVE_HTTPS_443_NOT_ACTIVE")
web=d.get("Web") or {}
entry=web.get("gokhan-lambda-vector.tailca6171.ts.net:443") or {}
handlers=entry.get("Handlers") or {}
proxy=(handlers.get("/") or {}).get("Proxy")
if proxy != "http://127.0.0.1:8765":
    raise SystemExit(f"SERVE_PROXY_MISMATCH:{proxy!r}")
if d.get("AllowFunnel"):
    raise SystemExit("FUNNEL_EXPOSURE_DETECTED")
print("TAILSCALE_SERVE_EXACT_BINDING=PASS")
print("TAILSCALE_FUNNEL_DISABLED=PASS")
PY

echo "=== LIVE FAKE WORKER TRANSPORT ==="
(
  cd "$SRCROOT"
  PYTHONPATH="$SRCROOT/semantic-execution/src"     "$VENV/bin/python"     benchmarks/workspace-semantic-execution/live_fake_worker_transport_v1.py       --base-url "$BASE_URL"       --serve-port "$BACKEND_PORT"
) | tee "$REPORT"

grep -q '^LIVE_FAKE_WORKER_TRANSPORT=.*"result":"PASS"' "$REPORT"   || fail "LIVE_FAKE_WORKER_TRANSPORT_NOT_PASS"

sudo tailscale serve --https=443 off
SERVE_STARTED=0
sudo tailscale serve status --json >"$RUNTIME_ROOT/serve-after.json"
python3 - "$RUNTIME_ROOT/serve-after.json" <<'PY'
import json, sys
d=json.load(open(sys.argv[1], encoding="utf-8"))
for key in ("TCP","Web","AllowFunnel","Services"):
    if d.get(key):
        raise SystemExit(f"SERVE_ROLLBACK_NOT_EMPTY:{key}")
print("TAILSCALE_SERVE_ROLLBACK=PASS")
PY

echo "PRIVATE_ROUTE_FAKE_WORKER_ACCEPTANCE=PASS"
