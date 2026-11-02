#!/usr/bin/env bash
# Bounded second live v3 class canary: PADataset CPU only.
# Operator checkout may advance for orchestration fixes, but canary generation,
# controller override binding, migration helper, and workflow blob remain pinned
# to the already-accepted controller source generation below.
set -euo pipefail


BASE_SOURCE_HEAD="09c46818252991f6a55aaeedbcf046c554e2ffee"
CONTROLLER_SOURCE_HEAD="3e8a231483413ba3a16d405ba61b55d0ab9ff3aa"
MIGRATION_HELPER_SOURCE_HEAD="2af7c8bba198b5b0e58ede6f8d34d0b64c8ed0af"
TARGET_CLASS="padataset-gpu-single-public-v1"
TARGET_SCALE_SET="lambda-padataset-gpu-single-public"
WORKFLOW_PATH=".github/workflows/workspace-ci-v3-migration-canary-padataset-gpu-single-public-v1.yml"
EXPECTED_WORKFLOW_BLOB="9311657f079aa1894d16d5e83ed0b18a813af487"
REPOSITORY="adamtrott78/PADataset"
TARGET_GITHUB_URL="https://github.com/adamtrott78/PADataset"

V3_CREDENTIAL_DIR="/var/lib/workspace-ci/v3/credentials/padataset"
V3_TOKEN="$V3_CREDENTIAL_DIR/github-token"
V3_ENV="$V3_CREDENTIAL_DIR/controller.env"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
OPERATOR_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
SOURCE_HEAD="$CONTROLLER_SOURCE_HEAD"
test -z "$(git -C "$ROOT" status --porcelain --untracked-files=no)"
TMP="$(mktemp -d /tmp/workspace-ci-v3-first-canary.XXXXXX)"
SOURCE_TREE="$TMP/source"
TX_HELPER="$TMP/lambda_ci_v3_migration_transaction.py"
EXPECTED_TX_HELPER_BLOB="d859cbcc4f8d2d25a76495e2159def2d6ac0c850"
CANARY_OUT="$TMP/canary"
PREFLIGHT_BIN="$TMP/v3-canary-preflight"
TX_RECEIPT=""
RUN_ID=""
DISPATCHED_AT=""
CANARY_WORKFLOW_ID=""
ROLLBACK_DONE=0

cleanup_files() {
  local target_unit="workspace-ci-v3-controller@$TARGET_CLASS.service"
  if ! systemctl is-active --quiet "$target_unit"; then
    sudo -n rm -f "$V3_TOKEN" "$V3_ENV" >/dev/null 2>&1 || true
  else
    echo "RECOVERY_CREDENTIALS_RETAINED_ACTIVE_TARGET=$target_unit"
  fi
  git -C "$ROOT" worktree remove --force "$SOURCE_TREE" >/dev/null 2>&1 || true
  rm -rf "$TMP" >/dev/null 2>&1 || sudo -n rm -rf "$TMP" >/dev/null 2>&1 || true
}

cancel_dispatched_canary() {
  if [[ -n "$RUN_ID" ]]; then
    gh api --method POST \
      "repos/$REPOSITORY/actions/runs/$RUN_ID/cancel" \
      >/dev/null 2>&1 || true
    return 0
  fi
  if [[ -z "$DISPATCHED_AT" ]]; then
    return 0
  fi

  local runs_endpoint="repos/$REPOSITORY/actions/runs"
  if [[ -n "$CANARY_WORKFLOW_ID" ]]; then
    runs_endpoint="repos/$REPOSITORY/actions/workflows/$CANARY_WORKFLOW_ID/runs"
  fi

  while read -r candidate; do
    [[ -n "$candidate" ]] || continue
    gh api --method POST \
      "repos/$REPOSITORY/actions/runs/$candidate/cancel" \
      >/dev/null 2>&1 || true
  done < <(
    gh api --method GET \
      "$runs_endpoint" \
      -f event=workflow_dispatch \
      -f branch=main \
      -f per_page=100 \
      --jq ".workflow_runs[] | select(.created_at >= \"$DISPATCHED_AT\" and (.status == \"queued\" or .status == \"in_progress\" or .status == \"waiting\" or .status == \"requested\" or .status == \"pending\")) | .id" \
      2>/dev/null || true
  )
}

rollback_transaction() {
  if [[ -z "$TX_RECEIPT" || "$ROLLBACK_DONE" -eq 1 ]]; then
    return 0
  fi

  echo "RECOVERY_ROLLBACK=BEGIN"

  cancel_dispatched_canary

  for _ in $(seq 1 60); do
    if sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$TX_HELPER"       --repo-root "$SOURCE_TREE"       --rollback "$TX_RECEIPT"
    then
      ROLLBACK_DONE=1
      TX_RECEIPT=""
      echo "RECOVERY_ROLLBACK=PASS"
      return 0
    fi
    sleep 2
  done

  echo "RECOVERY_ROLLBACK=FAILED"
  return 1
}

on_exit() {
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    rollback_transaction || true
  fi
  cleanup_files
  exit "$rc"
}
trap on_exit EXIT

echo "=== V3 PADATASET GPU CANARY: BEGIN ==="
echo "OPERATOR_HEAD=$OPERATOR_HEAD"
echo "CONTROLLER_SOURCE_HEAD=$SOURCE_HEAD"
echo "MIGRATION_HELPER_SOURCE_HEAD=$MIGRATION_HELPER_SOURCE_HEAD"
echo "BASE_SOURCE_HEAD=$BASE_SOURCE_HEAD"
echo "TARGET_CLASS=$TARGET_CLASS"

sudo -v
command -v gh >/dev/null
gh auth status >/dev/null

require_path() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    echo "STOP_MISSING_PATH=$path"
    return 1
  fi
  echo "PREFLIGHT_PATH=PASS $path"
}

require_active() {
  local unit="$1"
  if ! systemctl is-active --quiet "$unit"; then
    echo "STOP_EXPECTED_ACTIVE_UNIT=$unit"
    systemctl status --no-pager --full "$unit" || true
    return 1
  fi
  echo "PREFLIGHT_ACTIVE=PASS $unit"
}

require_inactive() {
  local unit="$1"
  local active_state sub_state
  active_state="$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || true)"
  sub_state="$(systemctl show "$unit" -p SubState --value 2>/dev/null || true)"
  if systemctl is-active --quiet "$unit" || [[ "$active_state" == "activating" || "$sub_state" == "auto-restart" ]]; then
    echo "STOP_EXPECTED_INACTIVE_UNIT=$unit active_state=${active_state:-unknown} sub_state=${sub_state:-unknown}"
    systemctl status --no-pager --full "$unit" || true
    return 1
  fi
  echo "PREFLIGHT_INACTIVE=PASS $unit active_state=${active_state:-unknown} sub_state=${sub_state:-unknown}"
}

require_not_enabled() {
  local unit="$1"
  local state
  state="$(systemctl is-enabled "$unit" 2>/dev/null || true)"
  if systemctl is-enabled --quiet "$unit"; then
    echo "STOP_EXPECTED_NOT_BOOT_ENABLED_UNIT=$unit state=$state"
    return 1
  fi
  echo "PREFLIGHT_NOT_BOOT_ENABLED=PASS $unit state=${state:-unknown}"
}

# Root services from Input #2 must remain active; every class stays inactive.
require_active workspace-ci-v3-reconciler.service
require_active workspace-ci-v3-provisioner.service
require_not_enabled workspace-ci-v3-reconciler.service
require_not_enabled workspace-ci-v3-provisioner.service
require_inactive workspace-ci-controller@research-engine-gpu.service

sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
  /opt/workspace-ci/v3/reconciler/lambda_ci_v3_reconciler.py \
  --verify-installed \
  --manifest /etc/workspace-ci/v3/install-manifest.json
echo "LIVE_EFFECTIVE_GENERATION_VERIFY=PASS"

for class_id in   workspace-control-control-small-v1   padataset-gpu-single-public-v1   padataset-gpu-single-public-v1   research-cpu-public-v1   research-gpu-single-public-v1   research-gpu-single-runtime-v1   research-model-single-offline-v1   research-model-dual-offline-v1   research-model-dual-public-v1
do
  require_inactive "workspace-ci-v3-controller@${class_id}.service"
  require_not_enabled "workspace-ci-v3-controller@${class_id}.service"
done

echo "LIVE_PREFLIGHT_ROOT_AND_CLASS_STATE=PASS"

# Prior failed canaries are durable history only when the authority marker is
# exactly paired with a transaction that reached the terminal safe rollback phase.
echo "CANARY_RETRY_HISTORY_CHECK=BEGIN"
if ! sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
  "$ROOT/scripts/lambda_ci_v3_controller_refresh.py" \
  --verify-retry-history \
  --target-class "$TARGET_CLASS"
then
  echo "STOP_CANARY_RETRY_HISTORY_FAILED"
  exit 1
fi
echo "CANARY_WORKFLOW_ID_RESOLVE=BEGIN"
set +e
CANARY_WORKFLOW_META="$(
  gh api --method GET \
    "repos/$REPOSITORY/actions/workflows" \
    -f per_page=100 \
    --jq ".workflows | map(select(.path == \"$WORKFLOW_PATH\")) | [length, (.[0].id // 0)] | @tsv"
)"
CANARY_WORKFLOW_META_RC=$?
set -e
if [[ "$CANARY_WORKFLOW_META_RC" -ne 0 ]]; then
  echo "STOP_CANARY_WORKFLOW_ID_QUERY_FAILED rc=$CANARY_WORKFLOW_META_RC"
  exit "$CANARY_WORKFLOW_META_RC"
fi
read -r CANARY_WORKFLOW_COUNT CANARY_WORKFLOW_ID <<< "$CANARY_WORKFLOW_META"
if [[ "$CANARY_WORKFLOW_COUNT" != "1" || -z "$CANARY_WORKFLOW_ID" || "$CANARY_WORKFLOW_ID" == "0" ]]; then
  echo "STOP_CANARY_WORKFLOW_ID_RESOLUTION count=${CANARY_WORKFLOW_COUNT:-unknown} id=${CANARY_WORKFLOW_ID:-unknown}"
  exit 1
fi
echo "CANARY_WORKFLOW_ID_RESOLVE=PASS id=$CANARY_WORKFLOW_ID"

echo "CANARY_RUN_HISTORY_CHECK=BEGIN"
set +e
CANARY_RUN_META="$(
  gh api --method GET \
    "repos/$REPOSITORY/actions/workflows/$CANARY_WORKFLOW_ID/runs" \
    -f event=workflow_dispatch \
    -f branch=main \
    -f per_page=100 \
    --jq '.workflow_runs | [length, (map(select(.status != "completed")) | length)] | @tsv'
)"
CANARY_RUN_HISTORY_RC=$?
set -e
if [[ "$CANARY_RUN_HISTORY_RC" -ne 0 ]]; then
  echo "STOP_CANARY_RUN_HISTORY_QUERY_FAILED rc=$CANARY_RUN_HISTORY_RC"
  exit "$CANARY_RUN_HISTORY_RC"
fi
read -r CANARY_PRIOR_RUN_COUNT CANARY_ACTIVE_RUN_COUNT <<< "$CANARY_RUN_META"
if [[ "$CANARY_ACTIVE_RUN_COUNT" != "0" ]]; then
  echo "STOP_ACTIVE_CANARY_WORKFLOW_RUNS count=$CANARY_ACTIVE_RUN_COUNT"
  gh api --method GET \
    "repos/$REPOSITORY/actions/workflows/$CANARY_WORKFLOW_ID/runs" \
    -f event=workflow_dispatch \
    -f branch=main \
    -f per_page=100 \
    --jq '.workflow_runs[] | select(.status != "completed") | [.id,.status,.conclusion,.created_at,.head_sha] | @tsv' || true
  exit 1
fi
echo "PREFLIGHT_NO_ACTIVE_CANARY_WORKFLOW_RUN=PASS prior_terminal_runs=$CANARY_PRIOR_RUN_COUNT"
# The base Input #1 generation remains immutable for root services/config.
# The effective class-controller executable is a separately reviewed inactive
# override bound to this exact reviewed source head.
sudo env EXPECTED_BASE_HEAD="$BASE_SOURCE_HEAD" /usr/bin/python3 - <<'PY'
import json
import os
import pathlib

manifest = json.loads(
    pathlib.Path("/etc/workspace-ci/v3/install-manifest.json").read_text()
)
assert manifest["source_head"] == os.environ["EXPECTED_BASE_HEAD"]
assert manifest["controller_state"] == "INACTIVE"
assert manifest["route_state"] == "DISABLED"
print("BASE_INSTALLED_GENERATION_BINDING=PASS")
PY

echo "CONTROLLER_OVERRIDE_BINDING_CHECK=BEGIN"
if ! sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
  "$ROOT/scripts/lambda_ci_v3_controller_refresh.py" \
  --verify-active \
  --expected-source-head "$SOURCE_HEAD" \
  --base-source-head "$BASE_SOURCE_HEAD"
then
  echo "STOP_CONTROLLER_OVERRIDE_BINDING_FAILED"
  exit 1
fi
echo "CONTROLLER_OVERRIDE_BINDING=PASS"
# Create an immutable worktree for the exact live generation.
git -C "$ROOT" cat-file -e "$SOURCE_HEAD^{commit}"
git -C "$ROOT" worktree add --detach "$SOURCE_TREE" "$SOURCE_HEAD" >/dev/null
test "$(git -C "$SOURCE_TREE" rev-parse HEAD)" = "$SOURCE_HEAD"
test -z "$(git -C "$SOURCE_TREE" status --porcelain --untracked-files=no)"

git -C "$ROOT" cat-file -e "$MIGRATION_HELPER_SOURCE_HEAD^{commit}"
TX_TREE_BLOB="$(git -C "$ROOT" ls-tree "$MIGRATION_HELPER_SOURCE_HEAD" -- scripts/lambda_ci_v3_migration_transaction.py | awk '{print $3}')"
test "$TX_TREE_BLOB" = "$EXPECTED_TX_HELPER_BLOB"

git -C "$ROOT" show "$MIGRATION_HELPER_SOURCE_HEAD:scripts/lambda_ci_v3_migration_transaction.py" > "$TX_HELPER"
chmod 0555 "$TX_HELPER"
test "$(git hash-object "$TX_HELPER")" = "$EXPECTED_TX_HELPER_BLOB"
require_path "$TX_HELPER"
echo "TRANSACTION_HELPER_SOURCE=EXACT_GIT_OBJECT"

# Exact Go 1.26.3 toolchain for the reviewed scale-set preflight helper.
GO_ARCHIVE="$TMP/go1.26.3.linux-amd64.tar.gz"
GO_SHA256="2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556"

echo "GO_TOOLCHAIN_DOWNLOAD=BEGIN"
if ! curl -fsSL --retry 3 \
  -o "$GO_ARCHIVE" \
  "https://go.dev/dl/go1.26.3.linux-amd64.tar.gz"
then
  echo "STOP_GO_TOOLCHAIN_DOWNLOAD_FAILED"
  exit 1
fi
echo "GO_TOOLCHAIN_DOWNLOAD=PASS"

echo "GO_TOOLCHAIN_CHECKSUM=BEGIN"
if ! printf '%s  %s\n' "$GO_SHA256" "$GO_ARCHIVE" | sha256sum -c -; then
  echo "STOP_GO_TOOLCHAIN_CHECKSUM_FAILED"
  exit 1
fi
echo "GO_TOOLCHAIN_CHECKSUM=PASS"

echo "GO_TOOLCHAIN_EXTRACT=BEGIN"
if ! tar -C "$TMP" -xzf "$GO_ARCHIVE"; then
  echo "STOP_GO_TOOLCHAIN_EXTRACT_FAILED"
  exit 1
fi
echo "GO_TOOLCHAIN_EXTRACT=PASS"

GO_BIN="$TMP/go/bin/go"
echo "GO_TOOLCHAIN_VERSION_CHECK=BEGIN"
set +e
GO_VERSION="$("$GO_BIN" env GOVERSION)"
GO_VERSION_RC=$?
set -e
if [[ "$GO_VERSION_RC" -ne 0 ]]; then
  echo "STOP_GO_TOOLCHAIN_VERSION_QUERY_FAILED rc=$GO_VERSION_RC"
  exit "$GO_VERSION_RC"
fi
if [[ "$GO_VERSION" != "go1.26.3" ]]; then
  echo "STOP_GO_TOOLCHAIN_VERSION_MISMATCH actual=$GO_VERSION"
  exit 1
fi
echo "GO_TOOLCHAIN_VERSION_CHECK=PASS version=$GO_VERSION"

echo "V3_CANARY_PREFLIGHT_BUILD=BEGIN"
set +e
GOTOOLCHAIN=local \
GOMODCACHE="$TMP/gomodcache" \
GOCACHE="$TMP/gocache" \
"$GO_BIN" -C "$ROOT/controller/lambda-ci-controller" \
  build -mod=readonly -trimpath \
  -o "$PREFLIGHT_BIN" \
  ./cmd/v3-canary-preflight
PREFLIGHT_BUILD_RC=$?
set -e
if [[ "$PREFLIGHT_BUILD_RC" -ne 0 ]]; then
  echo "STOP_V3_CANARY_PREFLIGHT_BUILD_FAILED rc=$PREFLIGHT_BUILD_RC"
  exit "$PREFLIGHT_BUILD_RC"
fi
if [[ ! -x "$PREFLIGHT_BIN" ]]; then
  echo "STOP_V3_CANARY_PREFLIGHT_BUILD_OUTPUT_MISSING path=$PREFLIGHT_BIN"
  exit 1
fi
echo "V3_CANARY_PREFLIGHT_BUILD=PASS"

# Stage the already-authenticated operator GitHub token only for this
# bounded canary. It is never printed and is removed after safe rollback.
umask 077

echo "V3_PADATASET_CREDENTIAL_RESET=BEGIN"
if systemctl is-active --quiet "workspace-ci-v3-controller@$TARGET_CLASS.service"; then
  echo "STOP_CREDENTIAL_RESET_TARGET_ACTIVE"
  exit 1
fi
if ! sudo -n rm -f "$V3_TOKEN" "$V3_ENV"; then
  echo "STOP_CREDENTIAL_RESET_FAILED"
  exit 1
fi
if sudo -n test -e "$V3_TOKEN" || sudo -n test -e "$V3_ENV"; then
  echo "STOP_CREDENTIAL_RESET_RESIDUE"
  exit 1
fi
echo "V3_PADATASET_CREDENTIAL_RESET=PASS"

echo "V3_PADATASET_GH_TOKEN_EXPORT=BEGIN"
TOKEN_EXPORT_METHOD=""

# Newer gh releases provide `gh auth token`. Older releases on Lambda may
# still expose the authenticated token only through `gh auth status
# --show-token`. Capture every token-bearing diagnostic to mode-0600 temp
# files and never print their contents.
set +e
gh auth token > "$TMP/operator-token" 2> "$TMP/gh-auth-token.err"
GH_TOKEN_RC=$?
set -e

if [[ "$GH_TOKEN_RC" -eq 0 && -s "$TMP/operator-token" ]]; then
  TOKEN_EXPORT_METHOD="auth-token"
else
  rm -f "$TMP/operator-token"
  echo "V3_PADATASET_GH_TOKEN_PRIMARY_UNAVAILABLE rc=$GH_TOKEN_RC"

  set +e
  NO_COLOR=1 gh auth status \
    --hostname github.com \
    --show-token \
    > "$TMP/gh-auth-status-token" 2>&1
  GH_STATUS_TOKEN_RC=$?
  set -e
  if [[ "$GH_STATUS_TOKEN_RC" -ne 0 ]]; then
    echo "STOP_GH_AUTH_STATUS_TOKEN_EXPORT_FAILED rc=$GH_STATUS_TOKEN_RC"
    rm -f "$TMP/gh-auth-token.err" "$TMP/gh-auth-status-token"
    exit "$GH_STATUS_TOKEN_RC"
  fi

  if ! env \
    STATUS_TOKEN_FILE="$TMP/gh-auth-status-token" \
    OUTPUT_TOKEN_FILE="$TMP/operator-token" \
    /usr/bin/python3 - <<'PY'
import os
import pathlib
import re

status_path = pathlib.Path(os.environ["STATUS_TOKEN_FILE"])
output_path = pathlib.Path(os.environ["OUTPUT_TOKEN_FILE"])

tokens = []
for line in status_path.read_text(errors="replace").splitlines():
    match = re.search(r"(?:^|\s)Token:\s*(\S+)\s*$", line)
    if not match:
        continue
    token = match.group(1)
    if not token or "*" in token or any(ch.isspace() for ch in token):
        continue
    if token not in tokens:
        tokens.append(token)

if len(tokens) != 1:
    raise SystemExit("expected exactly one unmasked token in gh auth status output")

output_path.write_text(tokens[0] + "\\n")
output_path.chmod(0o600)
PY
  then
    echo "STOP_GH_AUTH_STATUS_TOKEN_PARSE_FAILED"
    rm -f "$TMP/gh-auth-token.err" "$TMP/gh-auth-status-token" "$TMP/operator-token"
    exit 1
  fi
  TOKEN_EXPORT_METHOD="auth-status-show-token"
fi

rm -f "$TMP/gh-auth-token.err" "$TMP/gh-auth-status-token"

if [[ ! -s "$TMP/operator-token" ]]; then
  echo "STOP_GH_AUTH_TOKEN_EXPORT_EMPTY"
  rm -f "$TMP/operator-token"
  exit 1
fi

echo "V3_PADATASET_GH_TOKEN_VERIFY=BEGIN"
EXPORTED_TOKEN=""
IFS= read -r EXPORTED_TOKEN < "$TMP/operator-token" || true
if [[ -z "$EXPORTED_TOKEN" ]]; then
  echo "STOP_GH_AUTH_TOKEN_VERIFY_EMPTY"
  rm -f "$TMP/operator-token"
  exit 1
fi
set +e
EXPORTED_LOGIN="$(
  env GH_TOKEN="$EXPORTED_TOKEN" \
    gh api user --jq '.login' 2>/dev/null
)"
EXPORTED_LOGIN_RC=$?
set -e
unset EXPORTED_TOKEN
if [[ "$EXPORTED_LOGIN_RC" -ne 0 ]]; then
  echo "STOP_GH_AUTH_TOKEN_VERIFY_FAILED rc=$EXPORTED_LOGIN_RC"
  rm -f "$TMP/operator-token"
  exit "$EXPORTED_LOGIN_RC"
fi
if [[ "$EXPORTED_LOGIN" != "adamtrott78" ]]; then
  echo "STOP_GH_AUTH_TOKEN_IDENTITY_MISMATCH"
  rm -f "$TMP/operator-token"
  exit 1
fi
echo "V3_PADATASET_GH_TOKEN_VERIFY=PASS"
echo "V3_PADATASET_GH_TOKEN_EXPORT=PASS method=$TOKEN_EXPORT_METHOD"

echo "V3_PADATASET_TOKEN_INSTALL=BEGIN"
if ! sudo install -o root -g ci-gh-padataset -m 0640 \
  "$TMP/operator-token" "$V3_TOKEN"
then
  echo "STOP_V3_PADATASET_TOKEN_INSTALL_FAILED"
  rm -f "$TMP/operator-token"
  exit 1
fi
rm -f "$TMP/operator-token"
echo "V3_PADATASET_TOKEN_INSTALL=PASS"

echo "V3_PADATASET_ENV_INSTALL=BEGIN"
printf 'WORKSPACE_CI_PAT_FILE=%s\n' "$V3_TOKEN" > "$TMP/controller.env"
if ! sudo install -o root -g ci-gh-padataset -m 0640 \
  "$TMP/controller.env" "$V3_ENV"
then
  echo "STOP_V3_PADATASET_ENV_INSTALL_FAILED"
  exit 1
fi
echo "V3_PADATASET_ENV_INSTALL=PASS"

echo "V3_PADATASET_CREDENTIAL_ATTEST=BEGIN"
if ! sudo env V3_TOKEN="$V3_TOKEN" /usr/bin/python3 - <<'PY'; then
import grp
import os
import pathlib
import stat

for raw in (
    pathlib.Path(os.environ["V3_TOKEN"]),
    pathlib.Path("/var/lib/workspace-ci/v3/credentials/padataset/controller.env"),
):
    st = raw.stat()
    assert st.st_uid == 0
    assert st.st_gid == grp.getgrnam("ci-gh-padataset").gr_gid
    assert stat.S_IMODE(st.st_mode) == 0o640
print("V3_PADATASET_CREDENTIAL=PASS")
PY
  echo "STOP_V3_PADATASET_CREDENTIAL_ATTEST_FAILED"
  exit 1
fi

# Every legacy scale set must be drained BEFORE generation exclusion.
cat > "$TMP/legacy-scalesets.tsv" <<'EOF'
https://github.com/adamtrott78/workspace-control	lambda-workspace-control
https://github.com/adamtrott78/PADataset	lambda-padataset
https://github.com/adamtrott78/PADataset	lambda-padataset-gpu
https://github.com/adamtrott78/research-engine	lambda-research-engine
https://github.com/adamtrott78/research-engine	lambda-research-engine-gpu
EOF

sudo "$PREFLIGHT_BIN"   --token-file "$V3_TOKEN"   --legacy-scalesets "$TMP/legacy-scalesets.tsv"   --source-head "$SOURCE_HEAD"   --target-name "$TARGET_SCALE_SET"   --target-url "$TARGET_GITHUB_URL"

# Generate exact canary artifacts from the installed source generation.
mkdir -p "$CANARY_OUT"
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3   "$SOURCE_TREE/scripts/lambda_ci_v3_canary.py"   --repo-root "$SOURCE_TREE"   --output "$CANARY_OUT"

CANARY_MANIFEST="$CANARY_OUT/canary-manifest.json"
CANARY_POLICY="$CANARY_OUT/controllers/$TARGET_CLASS.canary.json"
GENERATED_WORKFLOW="$CANARY_OUT/repositories/adamtrott78/PADataset/$WORKFLOW_PATH"

test -f "$CANARY_MANIFEST"
test -f "$CANARY_POLICY"
test -f "$GENERATED_WORKFLOW"

GENERATED_BLOB="$(git hash-object "$GENERATED_WORKFLOW")"
test "$GENERATED_BLOB" = "$EXPECTED_WORKFLOW_BLOB"

MAIN_BLOB="$(gh api   "repos/$REPOSITORY/contents/$WORKFLOW_PATH?ref=main"   --jq '.sha')"
test "$MAIN_BLOB" = "$EXPECTED_WORKFLOW_BLOB"

echo "CANARY_DEFAULT_BRANCH_BLOB=PASS"

readarray -t CANARY_META < <(
  env     CANARY_MANIFEST="$CANARY_MANIFEST"     CANARY_POLICY="$CANARY_POLICY"     TARGET_CLASS="$TARGET_CLASS"     EXPECTED_WORKFLOW_BLOB="$EXPECTED_WORKFLOW_BLOB"     /usr/bin/python3 - <<'PY'
import json
import os
import pathlib

manifest = json.loads(pathlib.Path(os.environ["CANARY_MANIFEST"]).read_text())
policy = json.loads(pathlib.Path(os.environ["CANARY_POLICY"]).read_text())
target = os.environ["TARGET_CLASS"]
entry = manifest["classes"][target]

assert manifest["status"] == "STAGED_NOT_INSTALLED_NOT_AUTHORIZED"
assert entry["authorization_state"] == "REQUIRES_SEPARATE_LIVE_CANARY_AUTHORITY"
assert entry["blockers"] == []
assert entry["workflow_blob_sha"] == os.environ["EXPECTED_WORKFLOW_BLOB"]
assert policy["runner_class_id"] == target
assert policy["controller_policy_sha256"] == entry["controller_policy_sha256"]
assert len(policy["trusted_workflows"]) == 1
assert policy["trusted_workflows"][0]["allowed_events"] == ["workflow_dispatch"]
assert policy["trusted_workflows"][0]["allowed_actor_logins"] == ["adamtrott78"]

print(manifest["canary_generation_sha256"])
print(policy["controller_policy_sha256"])
print(entry["workflow_blob_sha"])
PY
)

CANARY_GENERATION="${CANARY_META[0]}"
CONTROLLER_POLICY_SHA="${CANARY_META[1]}"
WORKFLOW_BLOB="${CANARY_META[2]}"

# Fresh one-shot authority, bound to the exact canary generation.
AUTH_ID="$(python3 - <<'PY'
import uuid
print(uuid.uuid4())
PY
)"

AUTH_PATH="/var/lib/workspace-ci/v3/migration/canary-authority-$AUTH_ID.json"

sudo env   AUTH_PATH="$AUTH_PATH"   AUTH_ID="$AUTH_ID"   SOURCE_HEAD="$SOURCE_HEAD"   CANARY_GENERATION="$CANARY_GENERATION"   TARGET_CLASS="$TARGET_CLASS"   CONTROLLER_POLICY_SHA="$CONTROLLER_POLICY_SHA"   WORKFLOW_BLOB="$WORKFLOW_BLOB"   /usr/bin/python3 - <<'PY'
import json
import os
import pathlib
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
receipt = {
    "schema_version": 1,
    "authority": "workspace-control-operator",
    "operation": "ACTIVATE_ONE_V3_CANARY",
    "authorization_id": os.environ["AUTH_ID"],
    "source_head": os.environ["SOURCE_HEAD"],
    "canary_generation_sha256": os.environ["CANARY_GENERATION"],
    "target_runner_class_id": os.environ["TARGET_CLASS"],
    "controller_policy_sha256": os.environ["CONTROLLER_POLICY_SHA"],
    "workflow_blob_sha": os.environ["WORKFLOW_BLOB"],
    "issued_at": now.isoformat(),
    "expires_at": (now + timedelta(minutes=15)).isoformat(),
}
path = pathlib.Path(os.environ["AUTH_PATH"])
raw = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "wb") as handle:
    handle.write(raw)
    handle.flush()
    os.fsync(handle.fileno())
dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
try:
    os.fsync(dir_fd)
finally:
    os.close(dir_fd)
print("CANARY_AUTHORITY_CREATED=PASS")
PY

echo "GENERATION_EXCLUSION=BEGIN"

APPLY_LOG="$TMP/apply.log"
set +e
sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$TX_HELPER"   --repo-root "$SOURCE_TREE"   --apply-canary   --source-head "$SOURCE_HEAD"   --target-class "$TARGET_CLASS"   --canary-manifest "$CANARY_MANIFEST"   --canary-policy "$CANARY_POLICY"   --authorization-receipt "$AUTH_PATH"   | tee "$APPLY_LOG"
APPLY_RC=${PIPESTATUS[0]}
set -e

TX_RECEIPT="$(
  awk -F= '/^TRANSACTION_RECEIPT=/{print $2}' "$APPLY_LOG" | tail -n 1
)"

if [[ -z "$TX_RECEIPT" ]]; then
  TX_RECEIPT="$(
    sudo env AUTH_ID="$AUTH_ID" /usr/bin/python3 - <<'PY'
import json
import os
import pathlib

root = pathlib.Path("/var/lib/workspace-ci/v3/migration")
matches = []
for path in root.glob("*/transaction.json"):
    try:
        value = json.loads(path.read_text())
    except Exception:
        continue
    if value.get("authorization_id") == os.environ["AUTH_ID"]:
        matches.append(path)
if len(matches) > 1:
    raise SystemExit("multiple matching transaction receipts")
if matches:
    print(matches[0])
PY
  )"
fi

if [[ "$APPLY_RC" -ne 0 ]]; then
  echo "CANARY_TRANSACTION_APPLY=FAILED"
  exit "$APPLY_RC"
fi

test -n "$TX_RECEIPT"
grep -q '^V3_ONE_CLASS_CANARY_ACTIVE=PASS$' "$APPLY_LOG"

echo "TRANSACTION_RECEIPT=$TX_RECEIPT"
echo "GENERATION_EXCLUSION=ACTIVE"

# Dispatch exactly the owner-only workflow now trusted by the canary policy.
BEFORE_RUN_ID="$(
  gh api --method GET \
    "repos/$REPOSITORY/actions/workflows/$CANARY_WORKFLOW_ID/runs" \
    -f event=workflow_dispatch \
    -f branch=main \
    -f per_page=100 \
    --jq '.workflow_runs[0].id // 0'
)"

DISPATCHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "CANARY_DISPATCH=BEGIN workflow_id=$CANARY_WORKFLOW_ID"
if ! gh api --method POST \
  "repos/$REPOSITORY/actions/workflows/$CANARY_WORKFLOW_ID/dispatches" \
  -f ref=main \
  >/dev/null
then
  echo "STOP_CANARY_DISPATCH_FAILED"
  exit 1
fi
echo "CANARY_DISPATCH=PASS"

for _ in $(seq 1 30); do
  RUN_ID="$(
    gh api --method GET \
      "repos/$REPOSITORY/actions/workflows/$CANARY_WORKFLOW_ID/runs" \
      -f event=workflow_dispatch \
      -f branch=main \
      -f per_page=100 \
      --jq ".workflow_runs | map(select(.id != $BEFORE_RUN_ID and .created_at >= \"$DISPATCHED_AT\")) | .[0].id // 0"
  )"
  if [[ "$RUN_ID" != "0" && -n "$RUN_ID" ]]; then
    break
  fi
  RUN_ID=""
  sleep 2
done

if [[ -z "$RUN_ID" ]]; then
  echo "STOP_CANARY_RUN_DISCOVERY_FAILED"
  exit 1
fi
echo "CANARY_RUN_ID=$RUN_ID"

CANARY_RC=124
CANARY_CONCLUSION=""
CANARY_STATUS=""
CANARY_STATUS_QUERY_FAILURES=0
CANARY_STATUS_QUERY_FAILURE_LIMIT=6
CANARY_QUEUED_POLLS=0

emit_canary_controller_diagnostics() {
  local target_unit="workspace-ci-v3-controller@$TARGET_CLASS.service"
  echo "CANARY_CONTROLLER_DIAGNOSTICS=BEGIN"
  systemctl show "$target_unit" \
    -p LoadState \
    -p ActiveState \
    -p SubState \
    -p Result \
    -p ExecMainCode \
    -p ExecMainStatus \
    -p NRestarts \
    --no-pager 2>/dev/null || true
  sudo journalctl \
    -u "$target_unit" \
    -n 80 \
    --no-pager \
    -o short-iso \
    2>/dev/null || true
  echo "CANARY_CONTROLLER_DIAGNOSTICS=END"
}

for poll in $(seq 1 210); do
  set +e
  CANARY_STATE="$(
    gh api --method GET \
      "repos/$REPOSITORY/actions/runs/$RUN_ID" \
      --jq '[.status, (.conclusion // "")] | @tsv'
  )"
  CANARY_STATE_RC=$?
  set -e
  if [[ "$CANARY_STATE_RC" -ne 0 ]]; then
    CANARY_STATUS_QUERY_FAILURES=$((CANARY_STATUS_QUERY_FAILURES + 1))
    echo "CANARY_RUN_STATUS_QUERY_RETRY=PASS rc=$CANARY_STATE_RC run_id=$RUN_ID consecutive_failures=$CANARY_STATUS_QUERY_FAILURES limit=$CANARY_STATUS_QUERY_FAILURE_LIMIT"
    if [[ "$CANARY_STATUS_QUERY_FAILURES" -ge "$CANARY_STATUS_QUERY_FAILURE_LIMIT" ]]; then
      echo "STOP_CANARY_RUN_STATUS_QUERY_RETRY_EXHAUSTED rc=$CANARY_STATE_RC run_id=$RUN_ID"
      CANARY_RC="$CANARY_STATE_RC"
      emit_canary_controller_diagnostics
      cancel_dispatched_canary
      break
    fi
    sleep 3
    continue
  fi

  CANARY_STATUS_QUERY_FAILURES=0
  read -r CANARY_STATUS CANARY_CONCLUSION <<< "$CANARY_STATE"
  echo "CANARY_STATUS_OBSERVED=PASS poll=$poll status=$CANARY_STATUS conclusion=${CANARY_CONCLUSION:-pending}"

  if [[ "$CANARY_STATUS" == "queued" || "$CANARY_STATUS" == "waiting" || "$CANARY_STATUS" == "requested" || "$CANARY_STATUS" == "pending" ]]; then
    CANARY_QUEUED_POLLS=$((CANARY_QUEUED_POLLS + 1))
    if [[ "$CANARY_QUEUED_POLLS" -eq 60 ]]; then
      echo "CANARY_QUEUED_DIAGNOSTIC_THRESHOLD=REACHED polls=$CANARY_QUEUED_POLLS"
      emit_canary_controller_diagnostics
    fi
  else
    CANARY_QUEUED_POLLS=0
  fi

  if [[ "$CANARY_STATUS" == "completed" ]]; then
    if [[ "$CANARY_CONCLUSION" == "success" ]]; then
      CANARY_RC=0
    else
      CANARY_RC=1
    fi
    echo "CANARY_TERMINAL=PASS status=$CANARY_STATUS conclusion=$CANARY_CONCLUSION"
    break
  fi
  sleep 2
done

if [[ "$CANARY_RC" -eq 124 ]]; then
  echo "STOP_CANARY_RUN_TIMEOUT run_id=$RUN_ID last_status=${CANARY_STATUS:-unknown}"
  emit_canary_controller_diagnostics
  cancel_dispatched_canary
fi

# Restore exact v2 prestate after the canary is terminal.
for _ in $(seq 1 60); do
  if sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$TX_HELPER"     --repo-root "$SOURCE_TREE"     --rollback "$TX_RECEIPT"
  then
    ROLLBACK_DONE=1
    TX_RECEIPT=""
    break
  fi
  sleep 2
done

test "$ROLLBACK_DONE" -eq 1
echo "GENERATION_EXCLUSION_ROLLBACK=PASS"

if [[ "$CANARY_RC" -ne 0 ]]; then
  echo "CANARY_RESULT=FAILED"
  exit "$CANARY_RC"
fi

test "$CANARY_CONCLUSION" = "success"

sudo /usr/bin/python3 - <<'PY'
import json
import pathlib
import subprocess

root_policy = json.loads(
    pathlib.Path("/etc/workspace-ci/v3/root-policy.json").read_text()
)

assert subprocess.run(
    ["systemctl", "is-active", "--quiet", "workspace-ci-v3-reconciler.service"]
).returncode == 0
assert subprocess.run(
    ["systemctl", "is-active", "--quiet", "workspace-ci-v3-provisioner.service"]
).returncode == 0

for class_id in root_policy["runner_classes"]:
    assert subprocess.run(
        [
            "systemctl",
            "is-active",
            "--quiet",
            f"workspace-ci-v3-controller@{class_id}.service",
        ]
    ).returncode != 0

assert subprocess.run(
    [
        "systemctl",
        "is-active",
        "--quiet",
        "workspace-ci-controller@research-engine-gpu.service",
    ]
).returncode != 0

print("POST_CANARY_ROOT_SERVICES=ACTIVE")
print("POST_CANARY_V3_CLASS_CONTROLLERS=INACTIVE")
print("RESEARCH_GPU_CONTAINMENT=PRESERVED")
PY

echo "CANARY_RESULT=SUCCESS"
echo "TERMINAL_INPUT_3=PASS"
echo "PADATASET_GPU_CANARY_ACCEPTED=PASS"
echo "PADATASET_GPU_V3_CANARY=COMPLETE"
echo "=== V3 PADATASET GPU CANARY: COMPLETE ==="
