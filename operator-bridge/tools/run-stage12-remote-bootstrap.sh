#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "$#" -ne 4 ]]; then
  echo "D4_WOP_REMOTE_ARGUMENT_COUNT_MISMATCH=$#" >&2
  exit 64
fi

SOURCE_SHA="$1"
LINUX_REL="$2"
LINUX_BLOB="$3"
TOKEN="$4"
REPO_URL="https://github.com/adamtrott78/workspace-control.git"
D="/tmp/workspace-stage12-wop-\${TOKEN}"

cleanup_outer() {
  rm -rf -- "$D" >/dev/null 2>&1 || true
}
trap cleanup_outer EXIT

[[ "$SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "D4_WOP_REMOTE_SOURCE_SHA_INVALID=$SOURCE_SHA" >&2; exit 64; }
[[ "$LINUX_BLOB" =~ ^[0-9a-f]{40}$ ]] || { echo "D4_WOP_REMOTE_LINUX_BLOB_INVALID=$LINUX_BLOB" >&2; exit 64; }
[[ "$TOKEN" =~ ^[0-9a-f]{32}$ ]] || { echo "D4_WOP_REMOTE_TOKEN_INVALID=$TOKEN" >&2; exit 64; }
[[ "$LINUX_REL" == "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh" ]] || { echo "D4_WOP_REMOTE_LINUX_PATH_INVALID=$LINUX_REL" >&2; exit 64; }
[[ ! -e "$D" ]] || { echo "D4_WOP_REMOTE_STAGE_EXISTS=$D" >&2; exit 70; }

git init -q "$D"
git -C "$D" remote add origin "$REPO_URL"
git -C "$D" fetch --no-tags origin workspace-semantic-execution-migration-v1
if ! git -C "$D" cat-file -e "$SOURCE_SHA^{commit}" 2>/dev/null; then
  git -C "$D" fetch --no-tags origin "$SOURCE_SHA"
fi
git -C "$D" cat-file -e "$SOURCE_SHA^{commit}"
git -C "$D" checkout --detach "$SOURCE_SHA" >/dev/null

ACTUAL="$(git -C "$D" rev-parse HEAD)"
[[ "$ACTUAL" == "$SOURCE_SHA" ]] || { echo "D4_WOP_REMOTE_SOURCE_MISMATCH=$ACTUAL" >&2; exit 70; }

ACTUAL_BLOB="$(git -C "$D" rev-parse "\${SOURCE_SHA}:\${LINUX_REL}")"
[[ "$ACTUAL_BLOB" == "$LINUX_BLOB" ]] || { echo "D4_WOP_REMOTE_LINUX_BLOB_MISMATCH=$ACTUAL_BLOB" >&2; exit 70; }

echo "D4_WOP_REMOTE_EXACT_BINDINGS=PASS"
export STAGE12_WINDOWS_READY_CONFIRMATION="STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS"
cd "$D"
set +e
bash "$LINUX_REL"
RC=$?
set -e
exit "$RC"
