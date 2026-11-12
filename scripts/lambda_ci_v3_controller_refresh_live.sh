#!/usr/bin/env bash
set -euo pipefail

BASE_SOURCE_HEAD="09c46818252991f6a55aaeedbcf046c554e2ffee"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
SOURCE_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
TMP="$(mktemp -d /tmp/workspace-ci-v3-controller-refresh.XXXXXX)"

cleanup() {
  rm -rf "$TMP" >/dev/null 2>&1 || sudo -n rm -rf "$TMP" >/dev/null 2>&1 || true
}
trap cleanup EXIT

test -z "$(git -C "$ROOT" status --porcelain --untracked-files=no)"
git -C "$ROOT" cat-file -e "$SOURCE_HEAD^{commit}"

echo "=== V3 CONTROLLER REFRESH: BEGIN ==="
echo "SOURCE_HEAD=$SOURCE_HEAD"
echo "BASE_SOURCE_HEAD=$BASE_SOURCE_HEAD"

sudo -v
command -v curl >/dev/null
command -v sha256sum >/dev/null

GO_ARCHIVE="$TMP/go1.26.3.linux-amd64.tar.gz"
GO_SHA256="2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556"

echo "CONTROLLER_REFRESH_GO_DOWNLOAD=BEGIN"
curl -fsSL --retry 3 \
  -o "$GO_ARCHIVE" \
  "https://go.dev/dl/go1.26.3.linux-amd64.tar.gz"
echo "CONTROLLER_REFRESH_GO_DOWNLOAD=PASS"

echo "CONTROLLER_REFRESH_GO_CHECKSUM=BEGIN"
printf '%s  %s\n' "$GO_SHA256" "$GO_ARCHIVE" | sha256sum -c -
echo "CONTROLLER_REFRESH_GO_CHECKSUM=PASS"

tar -C "$TMP" -xzf "$GO_ARCHIVE"
GO_BIN="$TMP/go/bin/go"
test "$("$GO_BIN" env GOVERSION)" = "go1.26.3"
echo "CONTROLLER_REFRESH_GO_VERSION=PASS version=go1.26.3"

echo "CONTROLLER_REFRESH_APPLY=BEGIN"
APPLY_LOG="$TMP/apply.log"
set +e
sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
  "$ROOT/scripts/lambda_ci_v3_controller_refresh.py" \
  --repo-root "$ROOT" \
  --apply \
  --expected-source-head "$SOURCE_HEAD" \
  --base-source-head "$BASE_SOURCE_HEAD" \
  --go-bin "$GO_BIN" \
  | tee "$APPLY_LOG"
APPLY_RC=${PIPESTATUS[0]}
set -e
if [[ "$APPLY_RC" -ne 0 ]]; then
  echo "STOP_CONTROLLER_REFRESH_APPLY_FAILED rc=$APPLY_RC"
  exit "$APPLY_RC"
fi

REFRESH_RECEIPT="$(
  awk -F= '/^CONTROLLER_REFRESH_RECEIPT=/{print $2}' "$APPLY_LOG" | tail -n 1
)"
if [[ -z "$REFRESH_RECEIPT" ]]; then
  echo "STOP_CONTROLLER_REFRESH_RECEIPT_MISSING"
  exit 1
fi
echo "CONTROLLER_REFRESH_APPLY=PASS receipt=$REFRESH_RECEIPT"

echo "CONTROLLER_REFRESH_VERIFY=BEGIN"
sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
  "$ROOT/scripts/lambda_ci_v3_controller_refresh.py" \
  --verify-active \
  --expected-source-head "$SOURCE_HEAD" \
  --base-source-head "$BASE_SOURCE_HEAD"
echo "CONTROLLER_REFRESH_VERIFY=PASS"

echo "CONTROLLER_REFRESH_RETRY_HISTORY=BEGIN"
sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
  "$ROOT/scripts/lambda_ci_v3_controller_refresh.py" \
  --verify-retry-history \
  --target-class "workspace-control-control-small-v1"
echo "CONTROLLER_REFRESH_RETRY_HISTORY=PASS"

echo "=== V3 CONTROLLER REFRESH: PASS ==="
