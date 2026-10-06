#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

die() {
  echo "ERROR=$*" >&2
  exit 70
}

[[ "${EUID}" -eq 0 ]] || die "ROOT_REQUIRED"
[[ "${WORKSPACE_CI_GO_BOOTSTRAP_AUTHORIZED:-}" == "YES" ]] || die "GO_BOOTSTRAP_AUTHORIZATION_REQUIRED"
[[ -n "${WORKSPACE_CI_GO_EXPECTED_SHA:-}" ]] || die "EXPECTED_SHA_REQUIRED"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
GIT=(git -c "safe.directory=$REPO_ROOT" -C "$REPO_ROOT")
HEAD="$("${GIT[@]}" rev-parse HEAD)"
[[ "$HEAD" == "$WORKSPACE_CI_GO_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "WORKSPACE_CONTROL_DIRTY"

INVOKER="${SUDO_USER:-}"
[[ -n "$INVOKER" && "$INVOKER" != "root" ]] || die "RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT"
INVOKER_HOME="$(getent passwd "$INVOKER" | awk -F: '{print $6}')"
[[ -d "$INVOKER_HOME" ]] || die "INVOKER_HOME_NOT_FOUND"

getent passwd ci-controller >/dev/null || die "MISSING_IDENTITY:ci-controller"
getent group workspace-ci-controller >/dev/null || die "MISSING_GROUP:workspace-ci-controller"
[[ "$(uname -s)" == "Linux" ]] || die "LINUX_REQUIRED"
[[ "$(uname -m)" == "x86_64" ]] || die "X86_64_REQUIRED"

for cmd in curl sha256sum tar python3 runuser; do
  command -v "$cmd" >/dev/null || die "MISSING_COMMAND:$cmd"
done

readarray -t PIN < <(
  python3 - "$REPO_ROOT/architecture/lambda-ci-upstream-pins.v1.json" <<'PY'
import json, pathlib, sys
data=json.loads(pathlib.Path(sys.argv[1]).read_text())
go=data["go_toolchain"]
for key in ("version","source_url","source_sha256","install_prefix","architecture"):
    print(go[key])
PY
)
[[ "${#PIN[@]}" -eq 5 ]] || die "GO_PIN_PARSE_FAILED"
VERSION="${PIN[0]}"
URL="${PIN[1]}"
SHA256="${PIN[2]}"
TARGET="${PIN[3]}"
ARCH="${PIN[4]}"

[[ "$VERSION" == "1.26.3" ]] || die "UNEXPECTED_GO_VERSION_PIN:$VERSION"
[[ "$ARCH" == "linux-amd64" ]] || die "UNEXPECTED_GO_ARCH_PIN:$ARCH"
[[ "$TARGET" == "/opt/workspace-ci/go/1.26.3" ]] || die "UNEXPECTED_GO_PREFIX:$TARGET"
[[ "$SHA256" =~ ^[0-9a-f]{64}$ ]] || die "INVALID_GO_SHA256_PIN"

if [[ -x "$TARGET/bin/go" ]]; then
  EXISTING="$("$TARGET/bin/go" env GOVERSION 2>/dev/null || true)"
  [[ "$EXISTING" == "go$VERSION" ]] || die "EXISTING_GO_PREFIX_VERSION_DRIFT:$EXISTING"
  echo "P5_GO_TOOLCHAIN=REUSE"
  echo "GO_VERSION=$EXISTING"
  echo "GO_PREFIX=$TARGET"
  exit 0
fi
[[ ! -e "$TARGET" ]] || die "GO_PREFIX_EXISTS_BUT_INVALID"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$INVOKER_HOME/adamArchives/Adam/workspace-control-tmp/lambda-ci-go-$STAMP"
mkdir -p "$OUT"
chmod 0700 "$OUT"

install -d -o root -g root -m 0755 /opt/workspace-ci/go
STAGE="/opt/workspace-ci/go/.stage-go-$VERSION-$$"
install -d -o ci-controller -g workspace-ci-controller -m 0700 "$STAGE"
ARCHIVE="$STAGE/go$VERSION.linux-amd64.tar.gz"
PROMOTED=false

rollback() {
  local rc=$?
  trap - ERR
  rm -rf -- "$STAGE"
  if [[ "$PROMOTED" == "true" ]]; then
    rm -rf -- "$TARGET"
  fi
  echo "P5_GO_TOOLCHAIN_ROLLBACK=COMPLETE" >&2
  exit "$rc"
}
trap rollback ERR

runuser -u ci-controller -- \
  curl --fail --location --silent --show-error \
    --proto '=https' --tlsv1.2 \
    --output "$ARCHIVE" "$URL"

ACTUAL_SHA="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
[[ "$ACTUAL_SHA" == "$SHA256" ]] || die "GO_SHA256_MISMATCH:$ACTUAL_SHA"

runuser -u ci-controller -- tar -xzf "$ARCHIVE" -C "$STAGE"
[[ -x "$STAGE/go/bin/go" ]] || die "GO_ARCHIVE_LAYOUT_INVALID"
STAGED_VERSION="$("$STAGE/go/bin/go" env GOVERSION 2>/dev/null || true)"
[[ "$STAGED_VERSION" == "go$VERSION" ]] || die "STAGED_GO_VERSION_DRIFT:$STAGED_VERSION"

rm -f -- "$ARCHIVE"
mv -- "$STAGE/go" "$TARGET"
PROMOTED=true
chown -R root:root "$TARGET"
chmod -R a+rX,go-w "$TARGET"

FINAL_VERSION="$("$TARGET/bin/go" env GOVERSION 2>/dev/null || true)"
[[ "$FINAL_VERSION" == "go$VERSION" ]] || die "PROMOTED_GO_VERSION_DRIFT:$FINAL_VERSION"
[[ "$(stat -c '%U:%G' "$TARGET")" == "root:root" ]] || die "GO_PREFIX_OWNER_DRIFT"
if find "$TARGET" -xdev \( -perm -0020 -o -perm -0002 \) -print -quit | grep -q .; then
  die "GO_PREFIX_GROUP_OR_WORLD_WRITABLE"
fi

rm -rf -- "$STAGE"
PROMOTED=false

python3 - "$OUT/lambda-ci-go-toolchain.json" "$HEAD" "$VERSION" "$URL" "$SHA256" "$TARGET" <<'PY'
import json, pathlib, sys
from datetime import datetime, timezone
path, head, version, url, sha256, prefix = sys.argv[1:]
payload = {
    "schema_version": 1,
    "phase": "P5-go-toolchain",
    "decision": "PASS",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "workspace_control_sha": head,
    "go_version": version,
    "source_url": url,
    "source_sha256": sha256,
    "install_prefix": prefix,
    "runtime_owner": "root:root",
    "runtime_group_or_world_writable": False,
    "host_package_database_modified": False,
    "system_go_replaced": False,
    "download_identity": "ci-controller",
}
pathlib.Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, indent=2, sort_keys=True))
PY

chown -R "$INVOKER":"$(id -gn "$INVOKER")" "$OUT"
trap - ERR

echo "P5_GO_TOOLCHAIN=PASS"
echo "REPORT=$OUT/lambda-ci-go-toolchain.json"
echo "NEXT=Rerun the exact P5 install bootstrap."
