#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

die() {
  echo "ERROR=$*" >&2
  exit 70
}

[[ "${EUID}" -eq 0 ]] || die "ROOT_REQUIRED"
[[ "${WORKSPACE_CI_P3_PGVECTOR_AUTHORIZED:-}" == "YES" ]] || die "P3_PGVECTOR_AUTHORIZATION_REQUIRED"
[[ -n "${WORKSPACE_CI_P3_PGVECTOR_EXPECTED_SHA:-}" ]] || die "EXPECTED_SHA_REQUIRED"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
GIT=(git -c "safe.directory=$REPO_ROOT" -C "$REPO_ROOT")
HEAD="$("${GIT[@]}" rev-parse HEAD)"
[[ "$HEAD" == "$WORKSPACE_CI_P3_PGVECTOR_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "WORKSPACE_CONTROL_DIRTY"

INVOKER="${SUDO_USER:-}"
[[ -n "$INVOKER" && "$INVOKER" != "root" ]] || die "RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT"
INVOKER_HOME="$(getent passwd "$INVOKER" | awk -F: '{print $6}')"
[[ -d "$INVOKER_HOME" ]] || die "INVOKER_HOME_NOT_FOUND"

for cmd in curl gpg apt-get dpkg-deb sha256sum python3 runuser pg_config; do
  command -v "$cmd" >/dev/null 2>&1 || die "MISSING_TOOL:$cmd"
done
getent passwd ci-controller >/dev/null || die "CI_CONTROLLER_MISSING"
getent passwd ci-research-engine >/dev/null || die "CI_RESEARCH_ENGINE_MISSING"

PG_CONFIG="$(command -v pg_config)"
PGBIN="$("$PG_CONFIG" --bindir)"
PGSHARE="$("$PG_CONFIG" --sharedir)"
PKGLIBDIR="$("$PG_CONFIG" --pkglibdir)"
POSTGRES_VERSION="$("$PGBIN/postgres" --version)"
[[ "$POSTGRES_VERSION" == postgres\ \(PostgreSQL\)\ 14.* ]] || die "POSTGRES_MAJOR_NOT_14:$POSTGRES_VERSION"

TARGET_SO="$PKGLIBDIR/vector.so"
TARGET_EXT_DIR="$PGSHARE/extension"
TARGET_CONTROL="$TARGET_EXT_DIR/vector.control"
MANIFEST="/var/lib/workspace-ci/controller/pgvector14-0.8.6-ci-manifest.json"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$INVOKER_HOME/adamArchives/Adam/workspace-control-tmp/lambda-ci-p3-pgvector-$STAMP"
WORK="/var/lib/workspace-ci/controller/pgvector-bootstrap-$STAMP"
mkdir -p "$OUT" "$WORK"
chmod 0700 "$OUT"
chown ci-controller:workspace-ci-controller "$WORK"
chmod 0700 "$WORK"

PACKAGE="postgresql-14-pgvector"
VERSION="0.8.6-1.pgdg22.04+2"
PGDG_FINGERPRINT="B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8"
SOURCE_URL="https://apt.postgresql.org/pub/repos/apt"
KEY_URL="https://www.postgresql.org/media/keys/ACCC4CF8.asc"

MASTER_BEFORE="$(
  pgrep -af '^/usr/lib/postgresql/14/bin/postgres .* -D ' || true
)"
printf '%s\n' "$MASTER_BEFORE" > "$OUT/postgres-master-before.txt"

COPIED=0
SMOKE_ROOT=""
cleanup() {
  rc=$?
  set +e

  if [[ -n "$SMOKE_ROOT" ]]; then
    runuser -u ci-research-engine -- rm -rf -- "$SMOKE_ROOT" >/dev/null 2>&1 || true
  fi

  if [[ "$rc" -ne 0 && "$COPIED" == "1" ]]; then
    if [[ -f "$MANIFEST" ]]; then
      python3 - "$MANIFEST" <<'PY' >/tmp/workspace-ci-pgvector-rollback-paths.txt
import json,sys
p=json.load(open(sys.argv[1]))
for item in p.get("installed_files", []):
    print(item["path"])
PY
      while IFS= read -r path; do
        [[ -n "$path" ]] && rm -f -- "$path"
      done < /tmp/workspace-ci-pgvector-rollback-paths.txt
      rm -f /tmp/workspace-ci-pgvector-rollback-paths.txt
      rm -f -- "$MANIFEST"
    fi
  fi

  rm -rf -- "$WORK"
  chown -R "$INVOKER":"$(id -gn "$INVOKER")" "$OUT" >/dev/null 2>&1 || true
  exit "$rc"
}
trap cleanup EXIT

# Idempotent accepted state: exact extension already present and functional.
if [[ -r "$TARGET_CONTROL" && -r "$TARGET_SO" ]]; then
  if grep -Eq "^[[:space:]]*default_version[[:space:]]*=[[:space:]]*'0\.8\.6'" "$TARGET_CONTROL"; then
    echo "PGVECTOR_ALREADY_PRESENT=0.8.6" > "$OUT/bootstrap.txt"
  else
    die "EXISTING_PGVECTOR_VERSION_NOT_0_8_6"
  fi
else
  # Partial pre-existing state is unsafe to overwrite blindly.
  shopt -s nullglob
  existing_sql=("$TARGET_EXT_DIR"/vector--*.sql)
  shopt -u nullglob
  if [[ -e "$TARGET_CONTROL" || -e "$TARGET_SO" || "${#existing_sql[@]}" -gt 0 ]]; then
    die "PARTIAL_EXISTING_PGVECTOR_STATE"
  fi

  # Download using a temporary, signed PGDG apt configuration owned by the
  # unprivileged controller identity. Nothing is added to /etc/apt.
  runuser -u ci-controller -- env     WORK="$WORK" PACKAGE="$PACKAGE" VERSION="$VERSION"     PGDG_FINGERPRINT="$PGDG_FINGERPRINT" SOURCE_URL="$SOURCE_URL" KEY_URL="$KEY_URL"     bash -ceu '
      cd "$WORK"
      mkdir -p apt/lists/partial apt/archives/partial extracted
      curl -fsSL "$KEY_URL" -o apt/pgdg.asc

      fpr="$(gpg --batch --show-keys --with-colons apt/pgdg.asc |
             awk -F: '"'"'$1=="fpr"{print $10; exit}'"'"')"
      [[ "$fpr" == "$PGDG_FINGERPRINT" ]]

      cat > apt/sources.list <<EOF
deb [arch=amd64 signed-by=$WORK/apt/pgdg.asc] $SOURCE_URL jammy-pgdg main
EOF

      APT=(
        apt-get
        -o "Dir::Etc::sourcelist=$WORK/apt/sources.list"
        -o "Dir::Etc::sourceparts=-"
        -o "Dir::State::lists=$WORK/apt/lists"
        -o "Dir::Cache::archives=$WORK/apt/archives"
        -o "APT::Get::List-Cleanup=0"
        -o "APT::Sandbox::User=ci-controller"
      )

      "${APT[@]}" update
      "${APT[@]}" download "$PACKAGE=$VERSION"

      mapfile -t debs < <(find . -maxdepth 1 -type f -name "*.deb" -print)
      [[ "${#debs[@]}" -eq 1 ]]
      deb="${debs[0]}"

      [[ "$(dpkg-deb -f "$deb" Package)" == "$PACKAGE" ]]
      [[ "$(dpkg-deb -f "$deb" Version)" == "$VERSION" ]]
      [[ "$(dpkg-deb -f "$deb" Architecture)" == "amd64" ]]

      sha256sum "$deb" > package.sha256
      dpkg-deb -x "$deb" extracted
    '

  EXTRACTED="$WORK/extracted"
  STAGED_SO="$EXTRACTED$PKGLIBDIR/vector.so"
  STAGED_CONTROL="$EXTRACTED$TARGET_EXT_DIR/vector.control"
  [[ -r "$STAGED_SO" ]] || die "STAGED_VECTOR_SO_MISSING"
  [[ -r "$STAGED_CONTROL" ]] || die "STAGED_VECTOR_CONTROL_MISSING"
  grep -Eq "^[[:space:]]*default_version[[:space:]]*=[[:space:]]*'0\.8\.6'" "$STAGED_CONTROL" ||
    die "STAGED_VECTOR_VERSION_MISMATCH"

  mapfile -t STAGED_SQL < <(find "$EXTRACTED$TARGET_EXT_DIR" -maxdepth 1 -type f -name 'vector--*.sql' -print | sort)
  [[ "${#STAGED_SQL[@]}" -gt 0 ]] || die "STAGED_VECTOR_SQL_MISSING"

  install -o root -g root -m 0644 "$STAGED_SO" "$TARGET_SO"
  install -o root -g root -m 0644 "$STAGED_CONTROL" "$TARGET_CONTROL"

  INSTALLED_FILES=("$TARGET_SO" "$TARGET_CONTROL")
  for sql in "${STAGED_SQL[@]}"; do
    dst="$TARGET_EXT_DIR/$(basename "$sql")"
    install -o root -g root -m 0644 "$sql" "$dst"
    INSTALLED_FILES+=("$dst")
  done

  PACKAGE_SHA="$(awk '{print $1}' "$WORK/package.sha256")"
  python3 - "$MANIFEST" "$PACKAGE" "$VERSION" "$PACKAGE_SHA" "$HEAD" "${INSTALLED_FILES[@]}" <<'PY'
import hashlib,json,pathlib,sys
manifest,package,version,package_sha,control_sha,*paths=sys.argv[1:]
items=[]
for raw in paths:
    p=pathlib.Path(raw)
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    items.append({"path":str(p),"sha256":h})
payload={
    "schema_version":1,
    "purpose":"workspace-ci pgvector runtime for isolated P3 PostgreSQL",
    "package":package,
    "version":version,
    "download_sha256":package_sha,
    "workspace_control_sha":control_sha,
    "package_database_modified":False,
    "apt_configuration_modified":False,
    "production_database_modified":False,
    "production_service_restart_requested":False,
    "installed_files":items,
}
pathlib.Path(manifest).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PY
  chmod 0600 "$MANIFEST"
  COPIED=1
fi

# Smoke-test only against a fresh ci-research-engine-owned cluster on a Unix
# socket. This never connects to the production cluster.
SMOKE_ROOT="/srv/workspace-ci/research-engine/staging-cache/pgvector-smoke-$STAMP"
install -d -o ci-research-engine -g ci-research-engine -m 0700 "$SMOKE_ROOT"
runuser -u ci-research-engine -- env   PGBIN="$PGBIN" SMOKE_ROOT="$SMOKE_ROOT"   bash -ceu '
    data="$SMOKE_ROOT/data"
    sock="$SMOKE_ROOT/socket"
    mkdir -m 0700 "$data" "$sock"

    "$PGBIN/initdb" -D "$data" --username=research_engine --auth-local=trust --auth-host=reject --no-locale --encoding=UTF8 >/dev/null
    cat >> "$data/postgresql.conf" <<EOF
listen_addresses = ''
unix_socket_directories = '$sock'
port = 55434
EOF

    started=0
    stop_db() {
      rc=$?
      set +e
      if [[ "$started" == 1 ]]; then
        "$PGBIN/pg_ctl" -D "$data" -m fast -w stop >/dev/null 2>&1 || true
      fi
      exit "$rc"
    }
    trap stop_db EXIT

    "$PGBIN/pg_ctl" -D "$data" -w start >/dev/null
    started=1
    "$PGBIN/createdb" -h "$sock" -p 55434 -U research_engine research_engine
    version="$(
      "$PGBIN/psql" -h "$sock" -p 55434 -U research_engine -d research_engine         -v ON_ERROR_STOP=1 -Atc         "CREATE EXTENSION vector; SELECT extversion FROM pg_extension WHERE extname='vector';"
    )"
    [[ "$version" == "0.8.6" ]]
    "$PGBIN/psql" -h "$sock" -p 55434 -U research_engine -d research_engine       -v ON_ERROR_STOP=1 -Atc       "SELECT ('[1,2,3]'::vector <-> '[4,5,6]'::vector) > 0;" |
      grep -qx t
  '

MASTER_AFTER="$(
  pgrep -af '^/usr/lib/postgresql/14/bin/postgres .* -D ' || true
)"
printf '%s\n' "$MASTER_AFTER" > "$OUT/postgres-master-after.txt"
[[ "$MASTER_AFTER" == "$MASTER_BEFORE" ]] || die "PRODUCTION_POSTGRES_MASTER_CHANGED"

COPIED=0

python3 - "$OUT/lambda-ci-p3-pgvector.json" "$HEAD" "$POSTGRES_VERSION" "$MANIFEST" <<'PY'
import json,pathlib,sys
from datetime import datetime,timezone
report,control_sha,postgres_version,manifest=sys.argv[1:]
manifest_path=pathlib.Path(manifest)
installed=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
payload={
    "schema_version":1,
    "phase":"P3-PGVECTOR-DEPENDENCY",
    "decision":"PASS",
    "timestamp_utc":datetime.now(timezone.utc).isoformat(),
    "workspace_control_sha":control_sha,
    "postgres_version":postgres_version,
    "pgvector_version":"0.8.6",
    "pgvector_source":"PGDG signed temporary apt metadata + extracted package payload",
    "package_database_modified":False,
    "apt_configuration_modified":False,
    "production_database_modified":False,
    "production_postgres_master_unchanged":True,
    "ephemeral_unix_socket_smoke_test":"PASS",
    "manifest":str(manifest_path),
    "installed_files":installed.get("installed_files",[]),
}
pathlib.Path(report).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
print(json.dumps(payload,indent=2,sort_keys=True))
PY

chown -R "$INVOKER":"$(id -gn "$INVOKER")" "$OUT"

echo
echo "P3_PGVECTOR_BOOTSTRAP=PASS"
echo "REPORT=$OUT/lambda-ci-p3-pgvector.json"
