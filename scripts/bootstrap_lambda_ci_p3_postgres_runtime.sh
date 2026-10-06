#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

FAILURE_REASON=""
STAGE="startup"

die() {
  FAILURE_REASON="$*"
  echo "ERROR=$*" >&2
  exit 70
}

capture_production_postgres_listeners() {
  ss -H -ltnp 2>/dev/null |
    awk '$4 ~ /:5432$/ {print $4, $6}' |
    sort
}

[[ "${EUID}" -eq 0 ]] || die "ROOT_REQUIRED"
[[ "${WORKSPACE_CI_P3_RUNTIME_AUTHORIZED:-}" == "YES" ]] || die "P3_RUNTIME_AUTHORIZATION_REQUIRED"
[[ -n "${WORKSPACE_CI_P3_RUNTIME_EXPECTED_SHA:-}" ]] || die "EXPECTED_SHA_REQUIRED"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
GIT=(git -c "safe.directory=$REPO_ROOT" -C "$REPO_ROOT")
HEAD="$("${GIT[@]}" rev-parse HEAD)"
[[ "$HEAD" == "$WORKSPACE_CI_P3_RUNTIME_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "WORKSPACE_CONTROL_DIRTY"

# All privilege-switched subprocesses must inherit a neutral accessible cwd.
# This avoids runuser/sudo-style cwd warnings when the operator launches from
# a private project directory.
cd /

INVOKER="${SUDO_USER:-}"
[[ -n "$INVOKER" && "$INVOKER" != "root" ]] || die "RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT"
INVOKER_HOME="$(getent passwd "$INVOKER" | awk -F: '{print $6}')"
[[ -d "$INVOKER_HOME" ]] || die "INVOKER_HOME_NOT_FOUND"

for cmd in curl tar bzip2 sha256sum gcc make git perl python3 runuser ss; do
  command -v "$cmd" >/dev/null 2>&1 || die "MISSING_BUILD_TOOL:$cmd"
done
getent passwd ci-controller >/dev/null || die "CI_CONTROLLER_MISSING"
getent passwd ci-research-engine >/dev/null || die "CI_RESEARCH_ENGINE_MISSING"

POSTGRES_VERSION="14.24"
POSTGRES_ARCHIVE="postgresql-$POSTGRES_VERSION.tar.bz2"
POSTGRES_URL="https://ftp.postgresql.org/pub/source/v$POSTGRES_VERSION/$POSTGRES_ARCHIVE"
POSTGRES_SHA256="a7fa7ed3d558172355f51406097a7bd4f6b473be80f311ef7cda96bf383d8897"

PGVECTOR_VERSION="0.8.6"
PGVECTOR_COMMIT="8ee86c96f0fd72390f890aa8a336fda6d3ab4c6c"
PGVECTOR_REPO="https://github.com/pgvector/pgvector.git"

RUNTIME_ID="postgresql-$POSTGRES_VERSION-pgvector-$PGVECTOR_VERSION"
PREFIX="/opt/workspace-ci/postgresql/$RUNTIME_ID"
MANIFEST="/var/lib/workspace-ci/controller/$RUNTIME_ID-ci-manifest.json"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$INVOKER_HOME/adamArchives/Adam/workspace-control-tmp/lambda-ci-p3-runtime-$STAMP"
WORK="/var/lib/workspace-ci/controller/runtime-build-$STAMP"
SMOKE_ROOT="/srv/workspace-ci/research-engine/staging-cache/runtime-smoke-$STAMP"

mkdir -p "$OUT"
chmod 0700 "$OUT"

if [[ -e "$PREFIX" && ! -f "$MANIFEST" ]]; then
  die "PARTIAL_RUNTIME_WITHOUT_MANIFEST:$PREFIX"
fi
if [[ ! -e "$PREFIX" && -f "$MANIFEST" ]]; then
  die "MANIFEST_WITHOUT_RUNTIME:$MANIFEST"
fi

CREATED_PREFIX=0
SMOKE_STARTED=0
cleanup() {
  rc=$?
  set +e

  if [[ "$SMOKE_STARTED" == "1" && -x "$PREFIX/bin/pg_ctl" && -d "$SMOKE_ROOT/data" ]]; then
    runuser -u ci-research-engine -- env       LD_LIBRARY_PATH="$PREFIX/lib"       "$PREFIX/bin/pg_ctl" -D "$SMOKE_ROOT/data" -m fast -w stop >/dev/null 2>&1 || true
  fi

  if [[ -d "$SMOKE_ROOT" ]]; then
    runuser -u ci-research-engine -- rm -rf -- "$SMOKE_ROOT" >/dev/null 2>&1 || true
  fi

  PARTIAL_RUNTIME_REMOVED=false
  if [[ "$rc" -ne 0 && "$CREATED_PREFIX" == "1" ]]; then
    rm -rf -- "$PREFIX"
    rm -f -- "$MANIFEST"
    PARTIAL_RUNTIME_REMOVED=true
  fi

  rm -rf -- "$WORK"

  if [[ "$rc" -ne 0 ]]; then
    export P3_RUNTIME_RC="$rc"
    export P3_RUNTIME_STAGE="$STAGE"
    export P3_RUNTIME_FAILURE_REASON="$FAILURE_REASON"
    export P3_RUNTIME_PARTIAL_REMOVED="$PARTIAL_RUNTIME_REMOVED"
    export P3_RUNTIME_REPORT="$OUT/lambda-ci-p3-runtime.json"
    export P3_RUNTIME_HEAD="$HEAD"
    export P3_RUNTIME_PREFIX="$PREFIX"
    python3 - <<'PY'
import json, os, pathlib
from datetime import datetime, timezone

payload = {
    "schema_version": 1,
    "phase": "P3-ISOLATED-POSTGRES-RUNTIME",
    "decision": "FAIL",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "workspace_control_sha": os.environ["P3_RUNTIME_HEAD"],
    "prefix": os.environ["P3_RUNTIME_PREFIX"],
    "failure_stage": os.environ["P3_RUNTIME_STAGE"],
    "failure_reason": os.environ.get("P3_RUNTIME_FAILURE_REASON") or None,
    "exit_code": int(os.environ["P3_RUNTIME_RC"]),
    "partial_runtime_removed": os.environ["P3_RUNTIME_PARTIAL_REMOVED"] == "true",
}
pathlib.Path(os.environ["P3_RUNTIME_REPORT"]).write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
  fi

  chown -R "$INVOKER":"$(id -gn "$INVOKER")" "$OUT" >/dev/null 2>&1 || true
  exit "$rc"
}
trap cleanup EXIT

if [[ -e "$PREFIX" ]]; then
  STAGE="validate-existing-runtime"
  python3 - "$MANIFEST" "$POSTGRES_VERSION" "$POSTGRES_SHA256" "$PGVECTOR_VERSION" "$PGVECTOR_COMMIT" <<'PY'
import json,pathlib,sys
path=pathlib.Path(sys.argv[1])
expected={
    "postgres_version":sys.argv[2],
    "postgres_archive_sha256":sys.argv[3],
    "pgvector_version":sys.argv[4],
    "pgvector_commit":sys.argv[5],
}
data=json.loads(path.read_text())
for key,value in expected.items():
    if data.get(key) != value:
        raise SystemExit(f"manifest mismatch {key}: {data.get(key)!r} != {value!r}")
PY
  [[ -x "$PREFIX/bin/postgres" ]] || die "EXISTING_RUNTIME_POSTGRES_MISSING"
  [[ -x "$PREFIX/bin/initdb" ]] || die "EXISTING_RUNTIME_INITDB_MISSING"
  [[ -x "$PREFIX/bin/pg_ctl" ]] || die "EXISTING_RUNTIME_PG_CTL_MISSING"
  [[ -x "$PREFIX/bin/psql" ]] || die "EXISTING_RUNTIME_PSQL_MISSING"
  EXISTING_PGSHARE="$("$PREFIX/bin/pg_config" --sharedir)"
  [[ "$EXISTING_PGSHARE" == "$PREFIX" || "$EXISTING_PGSHARE" == "$PREFIX/"* ]] ||
    die "EXISTING_RUNTIME_SHAREDIR_OUTSIDE_PREFIX:$EXISTING_PGSHARE"
  [[ -r "$EXISTING_PGSHARE/extension/vector.control" ]] || die "EXISTING_RUNTIME_VECTOR_CONTROL_MISSING"
  grep -Eq "^[[:space:]]*default_version[[:space:]]*=[[:space:]]*'0\.8\.6'"     "$EXISTING_PGSHARE/extension/vector.control" ||
    die "EXISTING_RUNTIME_VECTOR_VERSION_MISMATCH"
  echo "RUNTIME_ALREADY_PRESENT=$RUNTIME_ID" > "$OUT/build.txt"
else
  STAGE="build-postgresql"
  install -d -o ci-controller -g workspace-ci-controller -m 0700 "$WORK"

  JOBS="$(nproc)"
  if [[ "$JOBS" -gt 12 ]]; then JOBS=12; fi

  runuser -u ci-controller -- env \
    WORK="$WORK" PREFIX="$PREFIX" JOBS="$JOBS" \
    POSTGRES_ARCHIVE="$POSTGRES_ARCHIVE" POSTGRES_URL="$POSTGRES_URL" \
    POSTGRES_SHA256="$POSTGRES_SHA256" \
    bash -seu <<'BUILD_POSTGRES'
cd "$WORK"
curl -fsSL --retry 3 --retry-delay 2 "$POSTGRES_URL" -o "$POSTGRES_ARCHIVE"
echo "$POSTGRES_SHA256  $POSTGRES_ARCHIVE" | sha256sum -c -

tar -xjf "$POSTGRES_ARCHIVE"
cd "postgresql-14.24"
./configure \
  --prefix="$PREFIX" \
  --without-readline \
  --without-zlib
make -j"$JOBS"
make DESTDIR="$WORK/postgres-stage" install
BUILD_POSTGRES

  STAGED_PREFIX="$WORK/postgres-stage$PREFIX"
  [[ -x "$STAGED_PREFIX/bin/postgres" ]] || die "STAGED_POSTGRES_MISSING"
  [[ -x "$STAGED_PREFIX/bin/initdb" ]] || die "STAGED_INITDB_MISSING"
  [[ -x "$STAGED_PREFIX/bin/pg_ctl" ]] || die "STAGED_PG_CTL_MISSING"
  [[ -x "$STAGED_PREFIX/bin/psql" ]] || die "STAGED_PSQL_MISSING"

  install -d -o root -g root -m 0755 "$(dirname "$PREFIX")"
  [[ ! -e "$PREFIX" ]] || die "RUNTIME_APPEARED_DURING_BUILD"
  cp -a -- "$STAGED_PREFIX" "$PREFIX"
  chown -R root:root "$PREFIX"
  chmod -R a+rX,go-w "$PREFIX"

  # The PostgreSQL build inherits the script's restrictive umask. Normalize
  # the promoted runtime so unprivileged ci-controller can execute pg_config
  # and read headers while keeping the tree root-owned and non-writable.
  runuser -u ci-controller -- test -x "$PREFIX/bin/pg_config" ||
    die "PROMOTED_PG_CONFIG_NOT_EXECUTABLE_BY_CI_CONTROLLER"
  runuser -u ci-controller -- test -r "$PREFIX/include/server/postgres.h" ||
    die "PROMOTED_POSTGRES_HEADERS_NOT_READABLE_BY_CI_CONTROLLER"

  CREATED_PREFIX=1

  STAGE="build-pgvector"
  runuser -u ci-controller -- env \
    WORK="$WORK" PREFIX="$PREFIX" JOBS="$JOBS" \
    PGVECTOR_REPO="$PGVECTOR_REPO" PGVECTOR_COMMIT="$PGVECTOR_COMMIT" \
    bash -seu <<'BUILD_PGVECTOR'
cd "$WORK"
git clone --no-checkout "$PGVECTOR_REPO" pgvector
git -C pgvector fetch --depth=1 origin "$PGVECTOR_COMMIT"
git -C pgvector checkout --detach "$PGVECTOR_COMMIT"
[[ "$(git -C pgvector rev-parse HEAD)" == "$PGVECTOR_COMMIT" ]]

make -C pgvector -j"$JOBS" PG_CONFIG="$PREFIX/bin/pg_config"
make -C pgvector PG_CONFIG="$PREFIX/bin/pg_config" \
  DESTDIR="$WORK/vector-stage" install
BUILD_PGVECTOR

  STAGE="validate-staged-pgvector"
  PKGLIBDIR="$("$PREFIX/bin/pg_config" --pkglibdir)"
  PGSHARE="$("$PREFIX/bin/pg_config" --sharedir)"
  [[ "$PKGLIBDIR" == "$PREFIX" || "$PKGLIBDIR" == "$PREFIX/"* ]] ||
    die "PKGLIBDIR_OUTSIDE_PREFIX:$PKGLIBDIR"
  [[ "$PGSHARE" == "$PREFIX" || "$PGSHARE" == "$PREFIX/"* ]] ||
    die "PGSHARE_OUTSIDE_PREFIX:$PGSHARE"

  VECTOR_STAGE_ROOT="$WORK/vector-stage"
  VECTOR_STAGE_SO="$VECTOR_STAGE_ROOT$PKGLIBDIR/vector.so"
  VECTOR_STAGE_CONTROL="$VECTOR_STAGE_ROOT$PGSHARE/extension/vector.control"
  [[ -r "$VECTOR_STAGE_SO" ]] || die "STAGED_VECTOR_SO_MISSING:$VECTOR_STAGE_SO"
  [[ -r "$VECTOR_STAGE_CONTROL" ]] || die "STAGED_VECTOR_CONTROL_MISSING:$VECTOR_STAGE_CONTROL"
  grep -Eq "^[[:space:]]*default_version[[:space:]]*=[[:space:]]*'0\.8\.6'"     "$VECTOR_STAGE_CONTROL" ||
    die "STAGED_VECTOR_VERSION_MISMATCH"

  STAGE="promote-pgvector"
  cp -a -- "$VECTOR_STAGE_ROOT$PREFIX/." "$PREFIX/"
  chown -R root:root "$PREFIX"
  chmod -R a+rX,go-w "$PREFIX"

  python3 - "$MANIFEST" "$HEAD" "$PREFIX"     "$POSTGRES_VERSION" "$POSTGRES_SHA256" "$PGVECTOR_VERSION" "$PGVECTOR_COMMIT" <<'PY'
import hashlib,json,pathlib,subprocess,sys
manifest,control_sha,prefix,pg_version,pg_sha,vec_version,vec_commit=sys.argv[1:]
root=pathlib.Path(prefix)
important=[
    root/"bin/postgres",
    root/"bin/initdb",
    root/"bin/pg_ctl",
    root/"bin/psql",
    pathlib.Path(subprocess.check_output([str(root/"bin/pg_config"), "--pkglibdir"], text=True).strip())/"vector.so",
    pathlib.Path(subprocess.check_output([str(root/"bin/pg_config"), "--sharedir"], text=True).strip())/"extension/vector.control",
]
files=[]
for p in important:
    files.append({"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
payload={
    "schema_version":1,
    "purpose":"isolated workspace-ci PostgreSQL + pgvector runtime",
    "workspace_control_sha":control_sha,
    "prefix":prefix,
    "postgres_version":pg_version,
    "postgres_archive_sha256":pg_sha,
    "pgvector_version":vec_version,
    "pgvector_commit":vec_commit,
    "host_package_database_modified":False,
    "host_apt_configuration_modified":False,
    "production_database_modified":False,
    "production_service_restart_requested":False,
    "important_files":files,
}
pathlib.Path(manifest).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PY
  chmod 0600 "$MANIFEST"
fi

STAGE="smoke-test"
POSTGRES_REPORTED="$("$PREFIX/bin/postgres" --version)"
[[ "$POSTGRES_REPORTED" == "postgres (PostgreSQL) $POSTGRES_VERSION" ]] ||
  die "RUNTIME_POSTGRES_VERSION_MISMATCH:$POSTGRES_REPORTED"

BEFORE_POSTGRES_LISTENERS="$(capture_production_postgres_listeners)"
printf '%s\n' "$BEFORE_POSTGRES_LISTENERS" > "$OUT/production-postgres-listeners-before.txt"

install -d -o ci-research-engine -g ci-research-engine -m 0700 "$SMOKE_ROOT"
runuser -u ci-research-engine -- env \
  PREFIX="$PREFIX" SMOKE_ROOT="$SMOKE_ROOT" LD_LIBRARY_PATH="$PREFIX/lib" \
  bash -seu <<'SMOKE_RUNTIME'
data="$SMOKE_ROOT/data"
sock="$SMOKE_ROOT/socket"
mkdir -m 0700 "$data" "$sock"

started=0
stop_db() {
  rc=$?
  set +e
  if [[ "$started" == "1" ]]; then
    "$PREFIX/bin/pg_ctl" -D "$data" -m fast -w stop >/dev/null 2>&1 || true
  fi
  exit "$rc"
}
trap stop_db EXIT

"$PREFIX/bin/initdb" \
  -D "$data" \
  --username=research_engine \
  --auth-local=trust \
  --auth-host=reject \
  --no-locale \
  --encoding=UTF8 \
  >/dev/null

cat >> "$data/postgresql.conf" <<EOF
listen_addresses = ''
unix_socket_directories = '$sock'
port = 55435
EOF

"$PREFIX/bin/pg_ctl" -D "$data" -w start >/dev/null
started=1
"$PREFIX/bin/createdb" \
  -h "$sock" -p 55435 -U research_engine research_engine

version="$(
  "$PREFIX/bin/psql" \
    -h "$sock" -p 55435 -U research_engine -d research_engine \
    -v ON_ERROR_STOP=1 -Atc \
    "CREATE EXTENSION vector; SELECT extversion FROM pg_extension WHERE extname='vector';"
)"
[[ "$version" == "0.8.6" ]]

"$PREFIX/bin/psql" \
  -h "$sock" -p 55435 -U research_engine -d research_engine \
  -v ON_ERROR_STOP=1 -Atc \
  "SELECT ('[1,2,3]'::vector <-> '[4,5,6]'::vector) > 0;" |
  grep -qx t

"$PREFIX/bin/pg_ctl" -D "$data" -m fast -w stop >/dev/null
started=0
SMOKE_RUNTIME
SMOKE_STARTED=0

AFTER_POSTGRES_LISTENERS="$(capture_production_postgres_listeners)"
printf '%s\n' "$AFTER_POSTGRES_LISTENERS" > "$OUT/production-postgres-listeners-after.txt"
[[ "$AFTER_POSTGRES_LISTENERS" == "$BEFORE_POSTGRES_LISTENERS" ]] ||
  die "PRODUCTION_POSTGRES_LISTENER_IDENTITY_CHANGED"

rm -rf -- "$SMOKE_ROOT"

STAGE="write-pass-receipt"
python3 - "$OUT/lambda-ci-p3-runtime.json"   "$HEAD" "$PREFIX" "$POSTGRES_VERSION" "$POSTGRES_SHA256"   "$PGVECTOR_VERSION" "$PGVECTOR_COMMIT" "$MANIFEST" <<'PY'
import json,pathlib,sys
from datetime import datetime,timezone
(
    report,control_sha,prefix,pg_version,pg_sha,vec_version,vec_commit,manifest
)=sys.argv[1:]
payload={
    "schema_version":1,
    "phase":"P3-ISOLATED-POSTGRES-RUNTIME",
    "decision":"PASS",
    "timestamp_utc":datetime.now(timezone.utc).isoformat(),
    "workspace_control_sha":control_sha,
    "prefix":prefix,
    "postgres_version":pg_version,
    "postgres_source_sha256":pg_sha,
    "pgvector_version":vec_version,
    "pgvector_commit":vec_commit,
    "runtime_owner":"root:root",
    "runtime_writable_by_project_runner":False,
    "host_package_database_modified":False,
    "host_apt_configuration_modified":False,
    "production_database_modified":False,
    "production_postgres_listener_identity_unchanged":True,
    "ephemeral_unix_socket_smoke_test":"PASS",
    "manifest":manifest,
}
pathlib.Path(report).write_text(
    json.dumps(payload,indent=2,sort_keys=True)+"\n",
    encoding="utf-8",
)
print(json.dumps(payload,indent=2,sort_keys=True))
PY

chown -R "$INVOKER":"$(id -gn "$INVOKER")" "$OUT"
CREATED_PREFIX=0

echo
echo "P3_ISOLATED_RUNTIME_BOOTSTRAP=PASS"
echo "REPORT=$OUT/lambda-ci-p3-runtime.json"
