#!/usr/bin/env bash
set -euo pipefail

SOURCE_HEAD="09c46818252991f6a55aaeedbcf046c554e2ffee"
TARGET_CLASS="workspace-control-control-small-v1"
TARGET_SCALE_SET="lambda-workspace-control-control-small"
WORKFLOW_PATH=".github/workflows/workspace-ci-v3-migration-canary-workspace-control-control-small-v1.yml"
EXPECTED_WORKFLOW_BLOB="c7471bdd5e35a7f8be27c3153f615a382845e195"
REPOSITORY="adamtrott78/workspace-control"

INSTALLED_TX="/opt/workspace-ci/v3/reconciler/lambda_ci_v3_migration_transaction.py"
LEGACY_TOKEN="/var/lib/workspace-ci/controller/github-token"
V3_CREDENTIAL_DIR="/var/lib/workspace-ci/v3/credentials/workspace-control"
V3_TOKEN="$V3_CREDENTIAL_DIR/github-token"
V3_ENV="$V3_CREDENTIAL_DIR/controller.env"

ROOT="$(git rev-parse --show-toplevel)"
TMP="$(mktemp -d /tmp/workspace-ci-v3-first-canary.XXXXXX)"
SOURCE_TREE="$TMP/source"
CANARY_OUT="$TMP/canary"
PREFLIGHT_BIN="$TMP/v3-canary-preflight"
TX_RECEIPT=""
RUN_ID=""
ROLLBACK_DONE=0

cleanup_files() {
  git -C "$ROOT" worktree remove --force "$SOURCE_TREE" >/dev/null 2>&1 || true
  rm -rf "$TMP" >/dev/null 2>&1 || sudo -n rm -rf "$TMP" >/dev/null 2>&1 || true
}

rollback_transaction() {
  if [[ -z "$TX_RECEIPT" || "$ROLLBACK_DONE" -eq 1 ]]; then
    return 0
  fi

  echo "RECOVERY_ROLLBACK=BEGIN"

  if [[ -n "$RUN_ID" ]]; then
    gh run cancel "$RUN_ID" --repo "$REPOSITORY" >/dev/null 2>&1 || true
  fi

  for _ in $(seq 1 60); do
    if sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$INSTALLED_TX"       --repo-root "$SOURCE_TREE"       --rollback "$TX_RECEIPT"
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

echo "=== V3 FIRST CANARY: BEGIN ==="
echo "SOURCE_HEAD=$SOURCE_HEAD"
echo "TARGET_CLASS=$TARGET_CLASS"

sudo -v
command -v gh >/dev/null
gh auth status >/dev/null

test -x "$INSTALLED_TX"
test -f "$LEGACY_TOKEN"

# Root services from Input #2 must remain active; every class stays inactive.
systemctl is-active --quiet workspace-ci-v3-reconciler.service
systemctl is-active --quiet workspace-ci-v3-provisioner.service
! systemctl is-active --quiet workspace-ci-controller@research-engine-gpu.service

for class_id in   workspace-control-control-small-v1   padataset-cpu-public-v1   padataset-gpu-single-public-v1   research-cpu-public-v1   research-gpu-single-public-v1   research-gpu-single-runtime-v1   research-model-single-offline-v1   research-model-dual-offline-v1   research-model-dual-public-v1
do
  ! systemctl is-active --quiet "workspace-ci-v3-controller@${class_id}.service"
done

echo "LIVE_PREFLIGHT_ROOT_AND_CLASS_STATE=PASS"

# Exact installed generation must still be the Input #1 generation.
sudo env EXPECTED_HEAD="$SOURCE_HEAD" /usr/bin/python3 - <<'PY'
import json
import os
import pathlib

manifest = json.loads(
    pathlib.Path("/etc/workspace-ci/v3/install-manifest.json").read_text()
)
assert manifest["source_head"] == os.environ["EXPECTED_HEAD"]
assert manifest["controller_state"] == "INACTIVE"
assert manifest["route_state"] == "DISABLED"
print("INSTALLED_GENERATION_BINDING=PASS")
PY

# Create an immutable worktree for the exact live generation.
git -C "$ROOT" cat-file -e "$SOURCE_HEAD^{commit}"
git -C "$ROOT" worktree add --detach "$SOURCE_TREE" "$SOURCE_HEAD" >/dev/null
test "$(git -C "$SOURCE_TREE" rev-parse HEAD)" = "$SOURCE_HEAD"
test -z "$(git -C "$SOURCE_TREE" status --porcelain --untracked-files=no)"

# Exact Go 1.26.3 toolchain for the reviewed scale-set preflight helper.
GO_ARCHIVE="$TMP/go1.26.3.linux-amd64.tar.gz"
GO_SHA256="2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556"
curl -fsSL --retry 3   -o "$GO_ARCHIVE"   "https://go.dev/dl/go1.26.3.linux-amd64.tar.gz"
printf '%s  %s\n' "$GO_SHA256" "$GO_ARCHIVE" | sha256sum -c -
tar -C "$TMP" -xzf "$GO_ARCHIVE"
GO_BIN="$TMP/go/bin/go"
test "$("$GO_BIN" env GOVERSION)" = "go1.26.3"

GOTOOLCHAIN=local GOMODCACHE="$TMP/gomodcache" GOCACHE="$TMP/gocache" "$GO_BIN" -C "$ROOT/controller/lambda-ci-controller"   build -mod=readonly -trimpath   -o "$PREFLIGHT_BIN"   ./cmd/v3-canary-preflight

# Stage the existing repository credential into the new repository-scoped group.
sudo install -o root -g ci-gh-workspace-control -m 0640   "$LEGACY_TOKEN" "$V3_TOKEN"

printf 'WORKSPACE_CI_PAT_FILE=%s\n' "$V3_TOKEN" > "$TMP/controller.env"
sudo install -o root -g ci-gh-workspace-control -m 0640   "$TMP/controller.env" "$V3_ENV"

sudo env V3_TOKEN="$V3_TOKEN" /usr/bin/python3 - <<'PY'
import grp
import os
import pathlib
import stat

for raw in (
    pathlib.Path(os.environ["V3_TOKEN"]),
    pathlib.Path("/var/lib/workspace-ci/v3/credentials/workspace-control/controller.env"),
):
    st = raw.stat()
    assert st.st_uid == 0
    assert st.st_gid == grp.getgrnam("ci-gh-workspace-control").gr_gid
    assert stat.S_IMODE(st.st_mode) == 0o640
print("V3_WORKSPACE_CONTROL_CREDENTIAL=PASS")
PY

# Every legacy scale set must be drained BEFORE generation exclusion.
cat > "$TMP/legacy-scalesets.tsv" <<'EOF'
https://github.com/adamtrott78/workspace-control	lambda-workspace-control
https://github.com/adamtrott78/PADataset	lambda-padataset
https://github.com/adamtrott78/PADataset	lambda-padataset-gpu
https://github.com/adamtrott78/research-engine	lambda-research-engine
https://github.com/adamtrott78/research-engine	lambda-research-engine-gpu
EOF

sudo "$PREFLIGHT_BIN"   --token-file "$LEGACY_TOKEN"   --legacy-scalesets "$TMP/legacy-scalesets.tsv"   --source-head "$SOURCE_HEAD"   --target-name "$TARGET_SCALE_SET"

# Generate exact canary artifacts from the installed source generation.
mkdir -p "$CANARY_OUT"
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3   "$SOURCE_TREE/scripts/lambda_ci_v3_canary.py"   --repo-root "$SOURCE_TREE"   --output "$CANARY_OUT"

CANARY_MANIFEST="$CANARY_OUT/canary-manifest.json"
CANARY_POLICY="$CANARY_OUT/controllers/$TARGET_CLASS.canary.json"
GENERATED_WORKFLOW="$CANARY_OUT/repositories/adamtrott78/workspace-control/$WORKFLOW_PATH"

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
sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$INSTALLED_TX"   --repo-root "$SOURCE_TREE"   --apply-canary   --source-head "$SOURCE_HEAD"   --target-class "$TARGET_CLASS"   --canary-manifest "$CANARY_MANIFEST"   --canary-policy "$CANARY_POLICY"   --authorization-receipt "$AUTH_PATH"   | tee "$APPLY_LOG"
APPLY_RC=${PIPESTATUS[0]}
set -e

if [[ "$APPLY_RC" -ne 0 ]]; then
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
  echo "CANARY_TRANSACTION_APPLY=FAILED"
  exit "$APPLY_RC"
fi

grep -q '^V3_ONE_CLASS_CANARY_ACTIVE=PASS$' "$APPLY_LOG"
TX_RECEIPT="$(
  awk -F= '/^TRANSACTION_RECEIPT=/{print $2}' "$APPLY_LOG"
)"
test -n "$TX_RECEIPT"

echo "TRANSACTION_RECEIPT=$TX_RECEIPT"
echo "GENERATION_EXCLUSION=ACTIVE"

# Dispatch exactly the owner-only workflow now trusted by the canary policy.
BEFORE_RUN_ID="$(
  gh run list     --repo "$REPOSITORY"     --workflow "$WORKFLOW_PATH"     --event workflow_dispatch     --branch main     --limit 1     --json databaseId     --jq '.[0].databaseId // 0'
)"

DISPATCHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
gh workflow run "$WORKFLOW_PATH"   --repo "$REPOSITORY"   --ref main

for _ in $(seq 1 30); do
  RUN_ID="$(
    gh run list       --repo "$REPOSITORY"       --workflow "$WORKFLOW_PATH"       --event workflow_dispatch       --branch main       --limit 10       --json databaseId,createdAt       --jq "map(select(.databaseId != $BEFORE_RUN_ID and .createdAt >= \"$DISPATCHED_AT\")) | .[0].databaseId // 0"
  )"
  if [[ "$RUN_ID" != "0" && -n "$RUN_ID" ]]; then
    break
  fi
  RUN_ID=""
  sleep 2
done

test -n "$RUN_ID"
echo "CANARY_RUN_ID=$RUN_ID"

CANARY_RC=0
gh run watch "$RUN_ID" --repo "$REPOSITORY" --exit-status || CANARY_RC=$?

# Restore exact v2 prestate after the canary is terminal.
for _ in $(seq 1 60); do
  if sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$INSTALLED_TX"     --repo-root "$SOURCE_TREE"     --rollback "$TX_RECEIPT"
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

CONCLUSION="$(
  gh run view "$RUN_ID"     --repo "$REPOSITORY"     --json conclusion     --jq '.conclusion'
)"
test "$CONCLUSION" = "success"

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
echo "INITIAL_V3_LIVE_PROOF=COMPLETE"
echo "=== V3 FIRST CANARY: COMPLETE ==="
