#!/usr/bin/env bash
# Single controlled Lambda CI v3 production-generation cutover.
#
# This operator is intentionally fail-closed.  It does not create authority
# until every repository, host, scale-set, credential, workflow, and verifier
# preflight has passed.  Once v2 is quiesced, any error restores the exact old
# workflow blobs and invokes the root transaction rollback.  If workflow
# restoration is incomplete, rollback still isolates v3 before refusing to
# restore v2.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
OPERATOR_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
export OPERATOR_HEAD
test -z "$(git -C "$ROOT" status --porcelain --untracked-files=no)"

EXPECTED_RECONCILER_SOURCE_HEAD="559c6186b44f17d4b83cb9267d554b355cda2ef7"
EXPECTED_RECONCILER_SHA256="c8ef68bb99626a64a7783ec09b4e6383f6875c0193c5d9a771d52a218251e749"
EXPECTED_RUNTIME_SOURCE_HEAD="e1a2d44bf24a3a7bf53d77baf0fc6170e4af0f15"
EXPECTED_RUNTIME_SHA256="86a7c8e33d689b11ece5cd1456ff3af9e841ed6b62a84356e8727d9cd8e1b9da"

WC_REPO="adamtrott78/workspace-control"
PAD_REPO="adamtrott78/PADataset"
WC_PR="572"

WC_WORKFLOW=".github/workflows/lambda-ci-workspace-control-validation.yml"
PAD_CPU_WORKFLOW=".github/workflows/lambda-ci-cpu.yml"
PAD_GPU_WORKFLOW=".github/workflows/lambda-ci-gpu.yml"

WC_OLD_BLOB="524e01916e1a826efd1edb4792023973d7b3c73c"
PAD_CPU_OLD_BLOB="5e6a1d4a47ecdfa8b40d3bea23fa8739cc12cd9e"
PAD_GPU_OLD_BLOB="3e0c79dc1b8bed7b1480cc745c478c190a3c7da4"

WC_TARGET_CLASS="workspace-control-control-small-v1"
PAD_CPU_TARGET_CLASS="padataset-cpu-public-v1"
PAD_GPU_TARGET_CLASS="padataset-gpu-single-public-v1"

WC_TARGET_SCALE_SET="lambda-workspace-control-control-small"
PAD_CPU_TARGET_SCALE_SET="lambda-padataset-cpu-public"
PAD_GPU_TARGET_SCALE_SET="lambda-padataset-gpu-single-public"

WC_TOKEN="/var/lib/workspace-ci/v3/credentials/workspace-control/github-token"
WC_ENV="/var/lib/workspace-ci/v3/credentials/workspace-control/controller.env"
PAD_TOKEN="/var/lib/workspace-ci/v3/credentials/padataset/github-token"
PAD_ENV="/var/lib/workspace-ci/v3/credentials/padataset/controller.env"

PROD_HELPER="$ROOT/scripts/lambda_ci_v3_production_cutover.py"
CONTROLLER_REFRESH_OPERATOR="$ROOT/scripts/lambda_ci_v3_controller_refresh_live.sh"
INSTALLED_RECONCILER="/opt/workspace-ci/v3/reconciler/lambda_ci_v3_reconciler.py"
INSTALLED_CONTROLLER="/opt/workspace-ci/v3/controller/lambda-ci-controller-v3"
BASE_MANIFEST="/etc/workspace-ci/v3/install-manifest.json"

TMP="$(mktemp -d /tmp/workspace-ci-v3-production-cutover.XXXXXX)"
GENERATION="$TMP/generation"
PREFLIGHT_BIN="$TMP/v3-canary-preflight"
VALIDATION_RUNS="$TMP/validation-runs.tsv"
VALIDATION_ROWS="$TMP/validation.tsv"
: > "$VALIDATION_RUNS"
: > "$VALIDATION_ROWS"

AUTH_ID=""
AUTH_FILE=""
TX_RECEIPT=""
PAD_VALIDATION_BRANCH=""
PAD_VALIDATION_PR=""
PAD_VALIDATION_SHA=""
CUTOVER_COMMITTED=0
ROLLBACK_DONE=0
CREDENTIALS_STAGED=0
WC_COMMIT_SHA=""
PAD_CPU_COMMIT_SHA=""
PAD_GPU_COMMIT_SHA=""

require_active() {
  unit="$1"
  if ! systemctl is-active --quiet "$unit"; then
    echo "STOP_EXPECTED_ACTIVE_UNIT=$unit"
    systemctl status --no-pager --full "$unit" || true
    return 1
  fi
  echo "PREFLIGHT_ACTIVE=PASS $unit"
}

require_inactive() {
  unit="$1"
  active_state="$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || true)"
  sub_state="$(systemctl show "$unit" -p SubState --value 2>/dev/null || true)"
  if systemctl is-active --quiet "$unit" || [ "$active_state" = "activating" ] || [ "$sub_state" = "auto-restart" ]; then
    echo "STOP_EXPECTED_INACTIVE_UNIT=$unit active_state=$active_state sub_state=$sub_state"
    systemctl status --no-pager --full "$unit" || true
    return 1
  fi
  echo "PREFLIGHT_INACTIVE=PASS $unit active_state=$active_state sub_state=$sub_state"
}

require_not_enabled() {
  unit="$1"
  state="$(systemctl is-enabled "$unit" 2>/dev/null || true)"
  if systemctl is-enabled --quiet "$unit"; then
    echo "STOP_EXPECTED_NOT_BOOT_ENABLED_UNIT=$unit state=$state"
    return 1
  fi
  echo "PREFLIGHT_NOT_BOOT_ENABLED=PASS $unit state=$state"
}

workflow_blob() {
  repo="$1"
  path="$2"
  gh api --method GET "repos/$repo/contents/$path?ref=main" --jq '.sha'
}

workflow_id() {
  repo="$1"
  path="$2"
  gh api --paginate "repos/$repo/actions/workflows?per_page=100" \
    --jq ".workflows[] | select(.path == \"$path\") | .id" | head -n 1
}

require_no_active_workflow_runs() {
  repo="$1"
  path="$2"
  wid="$(workflow_id "$repo" "$path")"
  if [ -z "$wid" ]; then
    echo "STOP_WORKFLOW_ID_NOT_FOUND repo=$repo path=$path"
    return 1
  fi
  active_count="$(
    gh api --method GET "repos/$repo/actions/workflows/$wid/runs" \
      -f per_page=100 \
      --jq '[.workflow_runs[] | select(.status != "completed")] | length'
  )"
  if [ "$active_count" -ne 0 ]; then
    echo "STOP_ACTIVE_WORKFLOW_RUNS repo=$repo path=$path count=$active_count"
    return 1
  fi
  echo "PREFLIGHT_NO_ACTIVE_WORKFLOW_RUN=PASS repo=$repo path=$path"
}

install_project_credential() {
  project="$1"
  group="$2"
  token_path="$3"
  env_path="$4"

  if sudo test -e "$token_path" || sudo test -e "$env_path"; then
    echo "STOP_V3_CREDENTIAL_PRESTATE_NOT_EMPTY project=$project"
    return 1
  fi
  printf '%s\n' "$OPERATOR_TOKEN" > "$TMP/$project-token"
  printf 'WORKSPACE_CI_PAT_FILE=%s\n' "$token_path" > "$TMP/$project-controller.env"
  sudo install -o root -g "$group" -m 0640 "$TMP/$project-token" "$token_path"
  sudo install -o root -g "$group" -m 0640 "$TMP/$project-controller.env" "$env_path"
  rm -f "$TMP/$project-token" "$TMP/$project-controller.env"
  echo "V3_PRODUCTION_CREDENTIAL=PASS project=$project"
}

remove_staged_credentials() {
  if [ "$CREDENTIALS_STAGED" -eq 1 ]; then
    sudo -n rm -f "$WC_TOKEN" "$WC_ENV" "$PAD_TOKEN" "$PAD_ENV" >/dev/null 2>&1 || true
    CREDENTIALS_STAGED=0
  fi
}

create_padataset_validation_pr() {
  pad_main="$(gh api --method GET "repos/$PAD_REPO/git/ref/heads/main" --jq '.object.sha')"
  suffix="$(python3 -c 'import uuid; print(uuid.uuid4().hex[:10])')"
  PAD_VALIDATION_BRANCH="workspace-ci-v3-production-validation-$suffix"

  gh api --method POST "repos/$PAD_REPO/git/refs" \
    -f ref="refs/heads/$PAD_VALIDATION_BRANCH" \
    -f sha="$pad_main" >/dev/null

  marker="production validation candidate for $OPERATOR_HEAD"
  marker_b64="$(printf '%s\n' "$marker" | base64 -w0)"
  response="$TMP/pad-validation-marker.json"
  gh api --method PUT \
    "repos/$PAD_REPO/contents/.workspace-ci-v3-production-validation" \
    -f message="chore: stage v3 production validation candidate" \
    -f content="$marker_b64" \
    -f branch="$PAD_VALIDATION_BRANCH" > "$response"

  PAD_VALIDATION_SHA="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["commit"]["sha"])' "$response")"
  PAD_VALIDATION_PR="$(
    gh api --method POST "repos/$PAD_REPO/pulls" \
      -f title="Temporary v3 production validation" \
      -f head="$PAD_VALIDATION_BRANCH" \
      -f base=main \
      -f body="Ephemeral validation PR for the controlled Lambda CI v3 production cutover. Do not merge." \
      -F draft=true \
      --jq '.number'
  )"
  echo "PADATASET_VALIDATION_PR=PASS pr=$PAD_VALIDATION_PR head=$PAD_VALIDATION_SHA"
}

cleanup_padataset_validation_pr() {
  if [ -n "$PAD_VALIDATION_PR" ]; then
    gh api --method PATCH "repos/$PAD_REPO/pulls/$PAD_VALIDATION_PR" \
      -f state=closed >/dev/null 2>&1 || true
  fi
  if [ -n "$PAD_VALIDATION_BRANCH" ]; then
    gh api --method DELETE \
      "repos/$PAD_REPO/git/refs/heads/$PAD_VALIDATION_BRANCH" \
      >/dev/null 2>&1 || true
  fi
}

update_workflow() {
  repo="$1"
  path="$2"
  old_blob="$3"
  new_blob="$4"
  new_file="$5"
  response_file="$6"

  current="$(workflow_blob "$repo" "$path")"
  if [ "$current" != "$old_blob" ]; then
    echo "STOP_WORKFLOW_OLD_BLOB_DRIFT repo=$repo path=$path actual=$current expected=$old_blob"
    return 1
  fi
  encoded="$(base64 -w0 < "$new_file")"
  gh api --method PUT "repos/$repo/contents/$path" \
    -f message="ci: route production workflow to Lambda CI v3" \
    -f content="$encoded" \
    -f sha="$old_blob" \
    -f branch=main > "$response_file"

  got_blob="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["content"]["sha"])' "$response_file")"
  if [ "$got_blob" != "$new_blob" ]; then
    echo "STOP_WORKFLOW_NEW_BLOB_MISMATCH repo=$repo path=$path actual=$got_blob expected=$new_blob"
    return 1
  fi
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["commit"]["sha"])' "$response_file"
}

restore_workflow() {
  repo="$1"
  path="$2"
  old_blob="$3"
  new_blob="$4"
  old_file="$5"

  current="$(workflow_blob "$repo" "$path" 2>/dev/null || true)"
  if [ "$current" = "$old_blob" ]; then
    echo "RECOVERY_WORKFLOW_ALREADY_OLD=PASS repo=$repo path=$path"
    return 0
  fi
  if [ "$current" != "$new_blob" ]; then
    echo "RECOVERY_WORKFLOW_UNKNOWN_BLOB repo=$repo path=$path actual=$current old=$old_blob new=$new_blob"
    return 1
  fi
  encoded="$(base64 -w0 < "$old_file")"
  response="$TMP/restore-$(printf '%s-%s' "$repo" "$path" | tr '/.' '__').json"
  if ! gh api --method PUT "repos/$repo/contents/$path" \
    -f message="ci: rollback Lambda CI v3 production route" \
    -f content="$encoded" \
    -f sha="$current" \
    -f branch=main > "$response"
  then
    echo "RECOVERY_WORKFLOW_RESTORE_FAILED repo=$repo path=$path"
    return 1
  fi
  got="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["content"]["sha"])' "$response")"
  if [ "$got" != "$old_blob" ]; then
    echo "RECOVERY_WORKFLOW_RESTORE_BLOB_MISMATCH repo=$repo path=$path actual=$got expected=$old_blob"
    return 1
  fi
  echo "RECOVERY_WORKFLOW_RESTORE=PASS repo=$repo path=$path"
}

cancel_validation_runs() {
  if [ ! -s "$VALIDATION_RUNS" ]; then
    return 0
  fi
  while IFS=$'\t' read -r repo run_id; do
    [ -n "$repo" ] || continue
    gh api --method POST "repos/$repo/actions/runs/$run_id/cancel" >/dev/null 2>&1 || true
  done < "$VALIDATION_RUNS"
}

write_rollback_confirmation() {
  out="$TMP/workflow-rollback-confirmation.json"
  env \
    MANIFEST="$GENERATION/manifest.json" \
    OUT="$out" \
    WC_BLOB="$(workflow_blob "$WC_REPO" "$WC_WORKFLOW" 2>/dev/null || true)" \
    CPU_BLOB="$(workflow_blob "$PAD_REPO" "$PAD_CPU_WORKFLOW" 2>/dev/null || true)" \
    GPU_BLOB="$(workflow_blob "$PAD_REPO" "$PAD_GPU_WORKFLOW" 2>/dev/null || true)" \
    WC_COMMIT="$(gh api --method GET "repos/$WC_REPO/commits/main" --jq '.sha' 2>/dev/null || true)" \
    PAD_COMMIT="$(gh api --method GET "repos/$PAD_REPO/commits/main" --jq '.sha' 2>/dev/null || true)" \
    python3 - <<'PY'
import json, os, pathlib
m=json.loads(pathlib.Path(os.environ["MANIFEST"]).read_text())
rows={
 "workspace-control:control-validation": {
   "repository":"adamtrott78/workspace-control",
   "path":".github/workflows/lambda-ci-workspace-control-validation.yml",
   "blob_sha":os.environ["WC_BLOB"],
   "commit_sha":os.environ["WC_COMMIT"],
 },
 "padataset:cpu-ci": {
   "repository":"adamtrott78/PADataset",
   "path":".github/workflows/lambda-ci-cpu.yml",
   "blob_sha":os.environ["CPU_BLOB"],
   "commit_sha":os.environ["PAD_COMMIT"],
 },
 "padataset:gpu-ci": {
   "repository":"adamtrott78/PADataset",
   "path":".github/workflows/lambda-ci-gpu.yml",
   "blob_sha":os.environ["GPU_BLOB"],
   "commit_sha":os.environ["PAD_COMMIT"],
 },
}
payload={
 "schema_version":1,
 "mode":"V3_PRODUCTION_WORKFLOW_ROLLBACK_CONFIRMED",
 "production_generation_sha256":m["production_generation_sha256"],
 "workflow_bindings":rows,
}
pathlib.Path(os.environ["OUT"]).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PY
  sudo install -o root -g root -m 0600 "$out" "$TMP/root-workflow-rollback-confirmation.json"
  printf '%s\n' "$TMP/root-workflow-rollback-confirmation.json"
}

recover_transaction_receipt() {
  if [ -n "$TX_RECEIPT" ] || [ -z "$AUTH_ID" ]; then
    return 0
  fi
  TX_RECEIPT="$(
    sudo env AUTH_ID="$AUTH_ID" /usr/bin/python3 - <<'PY'
import json, os, pathlib
root=pathlib.Path("/var/lib/workspace-ci/v3/migration")
auth=os.environ["AUTH_ID"]
matches=[]
for path in root.glob("*/transaction.json"):
    try:
        value=json.loads(path.read_text())
    except Exception:
        continue
    if value.get("authorization_id")==auth:
        matches.append(path)
if matches:
    print(sorted(matches,key=lambda p:p.stat().st_mtime_ns)[-1])
PY
  )"
}

rollback_transaction() {
  if [ -z "$TX_RECEIPT" ] || [ "$ROLLBACK_DONE" -eq 1 ]; then
    return 0
  fi

  echo "=== V3 PRODUCTION RECOVERY: BEGIN ==="
  cancel_validation_runs

  manifest="$GENERATION/manifest.json"
  WC_NEW_BLOB="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["workflow_bindings"]["workspace-control:control-validation"]["new_blob_sha"])' "$manifest")"
  CPU_NEW_BLOB="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["workflow_bindings"]["padataset:cpu-ci"]["new_blob_sha"])' "$manifest")"
  GPU_NEW_BLOB="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["workflow_bindings"]["padataset:gpu-ci"]["new_blob_sha"])' "$manifest")"

  restore_ok=1
  restore_workflow "$WC_REPO" "$WC_WORKFLOW" "$WC_OLD_BLOB" "$WC_NEW_BLOB" "$TMP/wc-old.yml" || restore_ok=0
  restore_workflow "$PAD_REPO" "$PAD_CPU_WORKFLOW" "$PAD_CPU_OLD_BLOB" "$CPU_NEW_BLOB" "$TMP/pad-cpu-old.yml" || restore_ok=0
  restore_workflow "$PAD_REPO" "$PAD_GPU_WORKFLOW" "$PAD_GPU_OLD_BLOB" "$GPU_NEW_BLOB" "$TMP/pad-gpu-old.yml" || restore_ok=0

  confirm="$(write_rollback_confirmation)"
  root_rc=1
  for _ in $(seq 1 90); do
    set +e
    sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$PROD_HELPER" \
      --repo-root "$ROOT" \
      --source-head "$OPERATOR_HEAD" \
      --rollback \
      --receipt "$TX_RECEIPT" \
      --workflow-rollback-confirmation "$confirm"
    root_rc=$?
    set -e
    if [ "$root_rc" -eq 0 ]; then
      break
    fi
    sleep 2
  done

  if [ "$restore_ok" -eq 1 ] && [ "$root_rc" -eq 0 ]; then
    ROLLBACK_DONE=1
    remove_staged_credentials
    echo "V3_PRODUCTION_ROLLBACK=PASS"
    echo "=== V3 PRODUCTION RECOVERY: END ==="
    return 0
  fi

  phase="$(
    sudo env RECEIPT="$TX_RECEIPT" /usr/bin/python3 - <<'PY'
import json, os, pathlib
try:
    print(json.loads(pathlib.Path(os.environ["RECEIPT"]).read_text()).get("phase","UNKNOWN"))
except Exception:
    print("UNKNOWN")
PY
  )"
  echo "RECOVERY_FAIL_CLOSED phase=$phase workflow_restore_ok=$restore_ok root_rollback_rc=$root_rc"
  echo "=== V3 PRODUCTION RECOVERY: END ==="
  return 1
}

on_exit() {
  rc=$?
  if [ "$rc" -ne 0 ] && [ "$CUTOVER_COMMITTED" -eq 0 ]; then
    recover_transaction_receipt || true
    rollback_transaction || true
  fi
  cleanup_padataset_validation_pr
  if [ "$CUTOVER_COMMITTED" -eq 0 ]; then
    if [ "$ROLLBACK_DONE" -eq 1 ] || [ -z "$TX_RECEIPT" ]; then
      remove_staged_credentials
    fi
  fi
  rm -rf "$TMP" >/dev/null 2>&1 || sudo -n rm -rf "$TMP" >/dev/null 2>&1 || true
  exit "$rc"
}
trap on_exit EXIT

echo "=== V3 PRODUCTION GENERATION CUTOVER: BEGIN ==="
echo "OPERATOR_HEAD=$OPERATOR_HEAD"

sudo -v
command -v gh >/dev/null
command -v curl >/dev/null
command -v sha256sum >/dev/null
command -v base64 >/dev/null
gh auth status >/dev/null
LOGIN="$(gh api --method GET user --jq '.login')"
if [ "$LOGIN" != "adamtrott78" ]; then
  echo "STOP_GITHUB_OPERATOR_IDENTITY actual=$LOGIN"
  exit 1
fi

PR_HEAD="$(gh api --method GET "repos/$WC_REPO/pulls/$WC_PR" --jq '.head.sha')"
if [ "$PR_HEAD" != "$OPERATOR_HEAD" ]; then
  echo "STOP_WORKSPACE_CONTROL_PR_HEAD_DRIFT actual=$PR_HEAD expected=$OPERATOR_HEAD"
  exit 1
fi

EXACT_HEAD_CI_JSON="$TMP/exact-head-ci.json"
gh api --method GET \
  "repos/$WC_REPO/actions/workflows/workspace-control-validation.yml/runs" \
  -f head_sha="$OPERATOR_HEAD" \
  -f event="pull_request" \
  -f per_page=20 > "$EXACT_HEAD_CI_JSON"
EXACT_HEAD_CI_RUN="$(
  env CI_JSON="$EXACT_HEAD_CI_JSON" python3 - <<'PY'
import json, os
runs=json.load(open(os.environ["CI_JSON"])).get("workflow_runs", [])
good=[
    r for r in runs
    if r.get("head_sha") == os.environ.get("OPERATOR_HEAD", "")
    and r.get("status") == "completed"
    and r.get("conclusion") == "success"
    and r.get("path") == ".github/workflows/workspace-control-validation.yml"
]
if not good:
    raise SystemExit(1)
good.sort(key=lambda r: r["id"], reverse=True)
print(good[0]["id"])
PY
)" || {
  echo "STOP_EXACT_HEAD_WORKSPACE_CONTROL_CI_NOT_GREEN head=$OPERATOR_HEAD"
  exit 1
}
echo "PRODUCTION_EXACT_HEAD_CI=PASS run_id=$EXACT_HEAD_CI_RUN head=$OPERATOR_HEAD"

for repo in "$WC_REPO" "$PAD_REPO"; do
  default_branch="$(gh api --method GET "repos/$repo" --jq '.default_branch')"
  if [ "$default_branch" != "main" ]; then
    echo "STOP_DEFAULT_BRANCH_DRIFT repo=$repo actual=$default_branch"
    exit 1
  fi
done

require_active workspace-ci-v3-reconciler.service
require_active workspace-ci-v3-provisioner.service
require_not_enabled workspace-ci-v3-reconciler.service
require_not_enabled workspace-ci-v3-provisioner.service
require_inactive workspace-ci-controller@research-engine-gpu.service
require_not_enabled workspace-ci-controller@research-engine-gpu.service

for class_id in \
  workspace-control-control-small-v1 \
  padataset-cpu-public-v1 \
  padataset-gpu-single-public-v1 \
  research-cpu-public-v1 \
  research-gpu-single-public-v1 \
  research-gpu-single-runtime-v1 \
  research-model-single-offline-v1 \
  research-model-dual-offline-v1 \
  research-model-dual-public-v1
do
  require_inactive "workspace-ci-v3-controller@$class_id.service"
  require_not_enabled "workspace-ci-v3-controller@$class_id.service"
done
echo "LIVE_PREFLIGHT_ROOT_AND_CLASS_STATE=PASS"

CONTROLLER_BOUND_HEAD="$(
  sudo /usr/bin/python3 - <<'PY' 2>/dev/null || true
import json, pathlib
path=pathlib.Path("/var/lib/workspace-ci/v3/controller-refresh/active.json")
try:
    value=json.loads(path.read_text())
    print(value.get("controller_source_head",""))
except Exception:
    pass
PY
)"
if [ "$CONTROLLER_BOUND_HEAD" != "$OPERATOR_HEAD" ]; then
  echo "PRODUCTION_CONTROLLER_REFRESH_REQUIRED current=${CONTROLLER_BOUND_HEAD:-missing} expected=$OPERATOR_HEAD"
  bash "$CONTROLLER_REFRESH_OPERATOR"
  echo "PRODUCTION_CONTROLLER_REFRESH=PASS"
else
  echo "PRODUCTION_CONTROLLER_REFRESH=SKIP exact_head=$OPERATOR_HEAD"
fi

sudo env \
  EXPECTED_HEAD="$EXPECTED_RECONCILER_SOURCE_HEAD" \
  EXPECTED_SHA="$EXPECTED_RECONCILER_SHA256" \
  INSTALLED="$INSTALLED_RECONCILER" \
  /usr/bin/python3 - <<'PY'
import hashlib, json, os, pathlib, stat
installed=pathlib.Path(os.environ["INSTALLED"])
active=pathlib.Path("/var/lib/workspace-ci/v3/reconciler-refresh/active.json")
raw=installed.read_bytes()
assert hashlib.sha256(raw).hexdigest()==os.environ["EXPECTED_SHA"]
r=json.loads(active.read_text())
assert r["schema_version"]==1
assert r["mode"]=="V3_RECONCILER_OVERRIDE"
assert r["phase"]=="ACTIVE"
assert r["reconciler_source_head"]==os.environ["EXPECTED_HEAD"]
assert r["reconciler_sha256"]==os.environ["EXPECTED_SHA"]
assert r["non_reconciler_generation_equivalent"] is True
st=active.stat()
assert st.st_uid==0 and st.st_gid==0 and stat.S_IMODE(st.st_mode)==0o600
print("PRODUCTION_RECONCILER_BINDING=PASS")
PY

sudo env \
  EXPECTED_HEAD="$OPERATOR_HEAD" \
  INSTALLED="$INSTALLED_CONTROLLER" \
  /usr/bin/python3 - <<'PY'
import hashlib, json, os, pathlib, stat
installed=pathlib.Path(os.environ["INSTALLED"])
active=pathlib.Path("/var/lib/workspace-ci/v3/controller-refresh/active.json")
actual=hashlib.sha256(installed.read_bytes()).hexdigest()
r=json.loads(active.read_text())
assert r["schema_version"]==1
assert r["mode"]=="V3_INACTIVE_CONTROLLER_BINARY_OVERRIDE"
assert r["phase"]=="ACTIVE"
assert r["controller_source_head"]==os.environ["EXPECTED_HEAD"]
assert r["controller_binary_sha256"]==actual
assert r["non_controller_generation_equivalent"] is True
st=active.stat()
assert st.st_uid==0 and st.st_gid==0 and stat.S_IMODE(st.st_mode)==0o600
print("PRODUCTION_CONTROLLER_BINDING=PASS")
PY

sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$INSTALLED_RECONCILER" \
  --verify-installed --manifest "$BASE_MANIFEST"
echo "LIVE_EFFECTIVE_GENERATION_VERIFY=PASS"

sudo env \
  EXPECTED_SOURCE="$EXPECTED_RUNTIME_SOURCE_HEAD" \
  EXPECTED_SHA="$EXPECTED_RUNTIME_SHA256" \
  /usr/bin/python3 - <<'PY'
import hashlib, json, os, pathlib, stat
runtime=pathlib.Path("/opt/workspace-ci/v3/provisioner/lambda_ci_runtime.py")
active=pathlib.Path("/var/lib/workspace-ci/v3/runtime-refresh/active.json")
r=json.loads(active.read_text())
assert r["schema_version"]==1
assert r["mode"]=="V3_RUNTIME_OVERRIDE"
assert r["phase"]=="ACTIVE"
assert r["runtime_source_head"]==os.environ["EXPECTED_SOURCE"]
assert r["runtime_sha256"]==os.environ["EXPECTED_SHA"]
assert r["non_runtime_generation_equivalent"] is True
assert hashlib.sha256(runtime.read_bytes()).hexdigest()==os.environ["EXPECTED_SHA"]
st=active.stat()
assert st.st_uid==0 and st.st_gid==0 and stat.S_IMODE(st.st_mode)==0o600
print("PRODUCTION_RUNTIME_REFRESH_BINDING=PASS")
PY

for spec in \
  "$WC_REPO|$WC_WORKFLOW|$WC_OLD_BLOB" \
  "$PAD_REPO|$PAD_CPU_WORKFLOW|$PAD_CPU_OLD_BLOB" \
  "$PAD_REPO|$PAD_GPU_WORKFLOW|$PAD_GPU_OLD_BLOB"
do
  IFS='|' read -r repo path expected <<EOF
$spec
EOF
  actual="$(workflow_blob "$repo" "$path")"
  if [ "$actual" != "$expected" ]; then
    echo "STOP_PRODUCTION_WORKFLOW_BLOB_DRIFT repo=$repo path=$path actual=$actual expected=$expected"
    exit 1
  fi
  echo "PRODUCTION_WORKFLOW_OLD_BLOB=PASS repo=$repo path=$path blob=$actual"
done

for spec in \
  "$WC_REPO|.github/workflows/workspace-ci-v3-migration-canary-workspace-control-control-small-v1.yml" \
  "$PAD_REPO|.github/workflows/workspace-ci-v3-migration-canary-padataset-cpu-public-v1.yml" \
  "$PAD_REPO|.github/workflows/workspace-ci-v3-migration-canary-padataset-gpu-single-public-v1.yml" \
  "$WC_REPO|$WC_WORKFLOW" \
  "$PAD_REPO|$PAD_CPU_WORKFLOW" \
  "$PAD_REPO|$PAD_GPU_WORKFLOW"
do
  IFS='|' read -r repo path <<EOF
$spec
EOF
  require_no_active_workflow_runs "$repo" "$path"
done

fetch_workflow_file() {
  repo="$1"
  path="$2"
  out="$3"
  gh api --method GET "repos/$repo/contents/$path?ref=main" --jq '.content' \
    | tr -d '\n' | base64 -d > "$out"
}
fetch_workflow_file "$WC_REPO" "$WC_WORKFLOW" "$TMP/wc-old.yml"
fetch_workflow_file "$PAD_REPO" "$PAD_CPU_WORKFLOW" "$TMP/pad-cpu-old.yml"
fetch_workflow_file "$PAD_REPO" "$PAD_GPU_WORKFLOW" "$TMP/pad-gpu-old.yml"
test "$(git hash-object "$TMP/wc-old.yml")" = "$WC_OLD_BLOB"
test "$(git hash-object "$TMP/pad-cpu-old.yml")" = "$PAD_CPU_OLD_BLOB"
test "$(git hash-object "$TMP/pad-gpu-old.yml")" = "$PAD_GPU_OLD_BLOB"

sudo cat /etc/workspace-ci/v3/deployment-overlay.json > "$TMP/live-overlay.json"
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$PROD_HELPER" \
  --repo-root "$ROOT" \
  --render-generation \
  --source-head "$OPERATOR_HEAD" \
  --workspace-control-workflow "$TMP/wc-old.yml" \
  --padataset-cpu-workflow "$TMP/pad-cpu-old.yml" \
  --padataset-gpu-workflow "$TMP/pad-gpu-old.yml" \
  --live-overlay "$TMP/live-overlay.json" \
  --output "$GENERATION"

MANIFEST="$GENERATION/manifest.json"
GENERATION_SHA="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["production_generation_sha256"])' "$MANIFEST")"
WC_NEW_BLOB="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["workflow_bindings"]["workspace-control:control-validation"]["new_blob_sha"])' "$MANIFEST")"
PAD_CPU_NEW_BLOB="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["workflow_bindings"]["padataset:cpu-ci"]["new_blob_sha"])' "$MANIFEST")"
PAD_GPU_NEW_BLOB="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["workflow_bindings"]["padataset:gpu-ci"]["new_blob_sha"])' "$MANIFEST")"
echo "PRODUCTION_GENERATION_FREEZE=PASS sha256=$GENERATION_SHA"

GO_ARCHIVE="$TMP/go1.26.3.linux-amd64.tar.gz"
GO_SHA256="2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556"
curl -fsSL --retry 3 -o "$GO_ARCHIVE" "https://go.dev/dl/go1.26.3.linux-amd64.tar.gz"
printf '%s  %s\n' "$GO_SHA256" "$GO_ARCHIVE" | sha256sum -c -
tar -C "$TMP" -xzf "$GO_ARCHIVE"
GO_BIN="$TMP/go/bin/go"
test "$("$GO_BIN" env GOVERSION)" = "go1.26.3"
GOTOOLCHAIN=local GOMODCACHE="$TMP/gomodcache" GOCACHE="$TMP/gocache" \
  "$GO_BIN" -C "$ROOT/controller/lambda-ci-controller" \
  build -mod=readonly -trimpath -o "$PREFLIGHT_BIN" ./cmd/v3-canary-preflight
test -x "$PREFLIGHT_BIN"
echo "V3_PRODUCTION_PREFLIGHT_BUILD=PASS"

umask 077
OPERATOR_TOKEN="$(gh auth token)"
if [ -z "$OPERATOR_TOKEN" ]; then
  echo "STOP_EMPTY_OPERATOR_TOKEN"
  exit 1
fi

install_project_credential workspace-control ci-gh-workspace-control "$WC_TOKEN" "$WC_ENV"
install_project_credential padataset ci-gh-padataset "$PAD_TOKEN" "$PAD_ENV"
CREDENTIALS_STAGED=1

cat > "$TMP/legacy-scalesets.tsv" <<'EOF'
https://github.com/adamtrott78/workspace-control	lambda-workspace-control
https://github.com/adamtrott78/PADataset	lambda-padataset
https://github.com/adamtrott78/PADataset	lambda-padataset-gpu
https://github.com/adamtrott78/research-engine	lambda-research-engine
https://github.com/adamtrott78/research-engine	lambda-research-engine-gpu
EOF

sudo "$PREFLIGHT_BIN" \
  --token-file "$WC_TOKEN" \
  --legacy-scalesets "$TMP/legacy-scalesets.tsv" \
  --source-head "$OPERATOR_HEAD" \
  --target-name "$WC_TARGET_SCALE_SET" \
  --target-url "https://github.com/$WC_REPO"
sudo "$PREFLIGHT_BIN" \
  --token-file "$PAD_TOKEN" \
  --legacy-scalesets "$TMP/legacy-scalesets.tsv" \
  --source-head "$OPERATOR_HEAD" \
  --target-name "$PAD_CPU_TARGET_SCALE_SET" \
  --target-url "https://github.com/$PAD_REPO"
sudo "$PREFLIGHT_BIN" \
  --token-file "$PAD_TOKEN" \
  --legacy-scalesets "$TMP/legacy-scalesets.tsv" \
  --source-head "$OPERATOR_HEAD" \
  --target-name "$PAD_GPU_TARGET_SCALE_SET" \
  --target-url "https://github.com/$PAD_REPO"
echo "PRODUCTION_SCALE_SET_PREFLIGHT=PASS"

create_padataset_validation_pr

AUTH_ID="$(python3 -c 'import uuid; print(uuid.uuid4())')"
AUTH_FILE="/var/lib/workspace-ci/v3/migration/root-production-cutover-authority-$AUTH_ID.json"
env MANIFEST="$MANIFEST" AUTH_ID="$AUTH_ID" OUT="$TMP/authority.json" python3 - <<'PY'
from datetime import datetime, timedelta, timezone
import json, os, pathlib
m=json.loads(pathlib.Path(os.environ["MANIFEST"]).read_text())
now=datetime.now(timezone.utc)
payload={
 "schema_version":1,
 "authority":"workspace-control-operator",
 "operation":"CUTOVER_V3_PRODUCTION_GENERATION",
 "authorization_id":os.environ["AUTH_ID"],
 "source_head":m["source_head"],
 "production_generation_sha256":m["production_generation_sha256"],
 "root_policy_sha256":m["root_policy_sha256"],
 "accepted_runner_class_ids":m["accepted_runner_class_ids"],
 "workflow_blob_shas":{
   key:value["new_blob_sha"]
   for key,value in m["workflow_bindings"].items()
 },
 "controller_policy_sha256":m["controller_policy_sha256"],
 "issued_at":now.isoformat(),
 "expires_at":(now+timedelta(minutes=20)).isoformat(),
}
pathlib.Path(os.environ["OUT"]).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PY
sudo install -o root -g root -m 0600 "$TMP/authority.json" "$AUTH_FILE"
echo "PRODUCTION_AUTHORITY_CREATED=PASS id=$AUTH_ID"

set +e
PREPARE_OUT="$(
  sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$PROD_HELPER" \
    --repo-root "$ROOT" \
    --source-head "$OPERATOR_HEAD" \
    --prepare \
    --generation-dir "$GENERATION" \
    --authorization-receipt "$AUTH_FILE" 2>&1
)"
PREPARE_RC=$?
set -e
printf '%s\n' "$PREPARE_OUT"
TX_RECEIPT="$(printf '%s\n' "$PREPARE_OUT" | sed -n 's/^TRANSACTION_RECEIPT=//p' | tail -n 1)"
if [ "$PREPARE_RC" -ne 0 ]; then
  recover_transaction_receipt
  exit "$PREPARE_RC"
fi
if [ -z "$TX_RECEIPT" ]; then
  recover_transaction_receipt
fi
if [ -z "$TX_RECEIPT" ]; then
  echo "STOP_PRODUCTION_TRANSACTION_RECEIPT_MISSING"
  exit 1
fi
echo "PRODUCTION_GENERATION_EXCLUSION=ACTIVE receipt=$TX_RECEIPT"

WC_NEW_FILE="$GENERATION/repositories/adamtrott78/workspace-control/$WC_WORKFLOW"
PAD_CPU_NEW_FILE="$GENERATION/repositories/adamtrott78/PADataset/$PAD_CPU_WORKFLOW"
PAD_GPU_NEW_FILE="$GENERATION/repositories/adamtrott78/PADataset/$PAD_GPU_WORKFLOW"

WC_COMMIT_SHA="$(update_workflow "$WC_REPO" "$WC_WORKFLOW" "$WC_OLD_BLOB" "$WC_NEW_BLOB" "$WC_NEW_FILE" "$TMP/wc-update.json")"
PAD_CPU_COMMIT_SHA="$(update_workflow "$PAD_REPO" "$PAD_CPU_WORKFLOW" "$PAD_CPU_OLD_BLOB" "$PAD_CPU_NEW_BLOB" "$PAD_CPU_NEW_FILE" "$TMP/pad-cpu-update.json")"
PAD_GPU_COMMIT_SHA="$(update_workflow "$PAD_REPO" "$PAD_GPU_WORKFLOW" "$PAD_GPU_OLD_BLOB" "$PAD_GPU_NEW_BLOB" "$PAD_GPU_NEW_FILE" "$TMP/pad-gpu-update.json")"

test "$(workflow_blob "$WC_REPO" "$WC_WORKFLOW")" = "$WC_NEW_BLOB"
test "$(workflow_blob "$PAD_REPO" "$PAD_CPU_WORKFLOW")" = "$PAD_CPU_NEW_BLOB"
test "$(workflow_blob "$PAD_REPO" "$PAD_GPU_WORKFLOW")" = "$PAD_GPU_NEW_BLOB"
echo "PRODUCTION_WORKFLOW_RETARGET=PASS"

env \
  MANIFEST="$MANIFEST" \
  OUT="$TMP/workflow-confirmation.json" \
  WC_COMMIT="$WC_COMMIT_SHA" \
  CPU_COMMIT="$PAD_CPU_COMMIT_SHA" \
  GPU_COMMIT="$PAD_GPU_COMMIT_SHA" \
  python3 - <<'PY'
import json, os, pathlib
m=json.loads(pathlib.Path(os.environ["MANIFEST"]).read_text())
rows={}
commits={
 "workspace-control:control-validation":os.environ["WC_COMMIT"],
 "padataset:cpu-ci":os.environ["CPU_COMMIT"],
 "padataset:gpu-ci":os.environ["GPU_COMMIT"],
}
for key,b in m["workflow_bindings"].items():
    rows[key]={
      "repository":b["repository"],
      "path":b["path"],
      "blob_sha":b["new_blob_sha"],
      "commit_sha":commits[key],
    }
payload={
 "schema_version":1,
 "mode":"V3_PRODUCTION_WORKFLOW_CUTOVER_CONFIRMED",
 "production_generation_sha256":m["production_generation_sha256"],
 "workflow_bindings":rows,
}
pathlib.Path(os.environ["OUT"]).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PY
sudo install -o root -g root -m 0600 \
  "$TMP/workflow-confirmation.json" "$TMP/root-workflow-confirmation.json"

sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$PROD_HELPER" \
  --repo-root "$ROOT" \
  --source-head "$OPERATOR_HEAD" \
  --activate \
  --receipt "$TX_RECEIPT" \
  --workflow-confirmation "$TMP/root-workflow-confirmation.json"
echo "PRODUCTION_V3_ACTIVATION=PASS"

wait_controller_terminal_ledger() {
  class_id="$1"
  job_id="$2"
  conclusion="$3"

  case "$conclusion" in
    success) wanted="COMPLETED" ;;
    failure) wanted="FAILED" ;;
    cancelled) wanted="CANCELED" ;;
    *)
      echo "STOP_UNSUPPORTED_GITHUB_JOB_CONCLUSION job_id=$job_id conclusion=$conclusion"
      return 1
      ;;
  esac

  for _ in $(seq 1 60); do
    if sudo env CLASS_ID="$class_id" JOB_ID="$job_id" WANTED="$wanted" \
      /usr/bin/python3 - <<'PY'
import json, os, pathlib, sys
root=pathlib.Path("/var/lib/workspace-ci/v3/controller/state") / os.environ["CLASS_ID"]
job_id=int(os.environ["JOB_ID"])
wanted=os.environ["WANTED"]
if not root.is_dir():
    raise SystemExit(1)
for path in root.glob("*.json"):
    try:
        value=json.loads(path.read_text())
    except Exception:
        continue
    if value.get("runner_request_id") != job_id:
        continue
    state=value.get("state")
    if state == wanted:
        print(state)
        raise SystemExit(0)
    if state in {"COMPLETED","FAILED","CANCELED"}:
        print(f"unexpected-terminal:{state}", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(1)
raise SystemExit(1)
PY
    then
      echo "PRODUCTION_CONTROLLER_LEDGER_TERMINAL=PASS class=$class_id job_id=$job_id state=$wanted"
      return 0
    fi
    sleep 2
  done
  echo "STOP_PRODUCTION_CONTROLLER_LEDGER_NOT_TERMINAL class=$class_id job_id=$job_id expected=$wanted"
  return 1
}

run_validation() {
  repo="$1"
  path="$2"
  pr="$3"
  command_body="$4"
  route_key="$5"
  class_id="$6"
  scale_set="$7"
  expected_blob="$8"

  current_blob="$(workflow_blob "$repo" "$path")"
  if [ "$current_blob" != "$expected_blob" ]; then
    echo "STOP_VALIDATION_WORKFLOW_BLOB_DRIFT repo=$repo path=$path"
    return 1
  fi
  wid="$(workflow_id "$repo" "$path")"
  before="$(
    gh api --method GET "repos/$repo/actions/workflows/$wid/runs" \
      -f event=issue_comment -f per_page=20 \
      --jq '.workflow_runs[0].id // 0'
  )"
  dispatched_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  gh api --method POST "repos/$repo/issues/$pr/comments" \
    -f body="$command_body" >/dev/null

  run_id=""
  for _ in $(seq 1 90); do
    run_id="$(
      gh api --method GET "repos/$repo/actions/workflows/$wid/runs" \
        -f event=issue_comment -f per_page=50 \
        --jq ".workflow_runs[] | select(.id != $before and .created_at >= \"$dispatched_at\") | .id" \
        | head -n 1
    )"
    if [ -n "$run_id" ]; then
      break
    fi
    sleep 2
  done
  if [ -z "$run_id" ]; then
    echo "STOP_PRODUCTION_VALIDATION_RUN_NOT_FOUND route=$route_key"
    return 1
  fi
  printf '%s\t%s\n' "$repo" "$run_id" >> "$VALIDATION_RUNS"
  echo "PRODUCTION_VALIDATION_RUN_ID route=$route_key run_id=$run_id"

  conclusion=""
  for _ in $(seq 1 150); do
    read -r status conclusion <<EOF
$(gh api --method GET "repos/$repo/actions/runs/$run_id" --jq '[.status, (.conclusion // "pending")] | @tsv')
EOF
    echo "PRODUCTION_VALIDATION_STATUS route=$route_key status=$status conclusion=$conclusion"
    if [ "$status" = "completed" ]; then
      break
    fi
    sleep 5
  done
  if [ "$status" != "completed" ]; then
    echo "STOP_PRODUCTION_VALIDATION_FAILED route=$route_key status=$status conclusion=$conclusion"
    return 1
  fi

  jobs_file="$TMP/jobs-$run_id.json"
  gh api --method GET "repos/$repo/actions/runs/$run_id/jobs" -f per_page=100 > "$jobs_file"
  read -r job_id runner_name job_conclusion <<EOF
$(env JOBS="$jobs_file" SCALE_SET="$scale_set" python3 - <<'PY'
import json, os
j=json.load(open(os.environ["JOBS"]))["jobs"]
assert len(j)==1, f"expected one job, got {len(j)}"
job=j[0]
runner=job.get("runner_name") or ""
assert runner.startswith(os.environ["SCALE_SET"]+"-"), runner
print(job["id"], runner, job.get("conclusion") or "pending")
PY
)
EOF
  if [ -z "$job_id" ] || [ -z "$runner_name" ] || [ "$job_conclusion" = "pending" ]; then
    echo "STOP_PRODUCTION_VALIDATION_JOB_IDENTITY route=$route_key"
    return 1
  fi
  if [ "$job_conclusion" != "$conclusion" ]; then
    echo "STOP_PRODUCTION_VALIDATION_CONCLUSION_MISMATCH route=$route_key run=$conclusion job=$job_conclusion"
    return 1
  fi

  wait_controller_terminal_ledger "$class_id" "$job_id" "$job_conclusion"

  if [ "$conclusion" != "success" ]; then
    echo "STOP_PRODUCTION_VALIDATION_FAILED route=$route_key status=$status conclusion=$conclusion"
    return 1
  fi

  if [ "$(workflow_blob "$repo" "$path")" != "$expected_blob" ]; then
    echo "STOP_VALIDATION_WORKFLOW_CHANGED_DURING_RUN route=$route_key"
    return 1
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$route_key" "$run_id" "$job_id" "$runner_name" \
    "$class_id" "$scale_set" "$expected_blob" >> "$VALIDATION_ROWS"
  echo "PRODUCTION_VALIDATION=PASS route=$route_key run_id=$run_id job_id=$job_id runner=$runner_name"
}

run_validation \
  "$WC_REPO" "$WC_WORKFLOW" "$WC_PR" \
  "/workspace-control-validate $OPERATOR_HEAD" \
  "workspace-control:control-validation" \
  "$WC_TARGET_CLASS" "$WC_TARGET_SCALE_SET" "$WC_NEW_BLOB"

run_validation \
  "$PAD_REPO" "$PAD_CPU_WORKFLOW" "$PAD_VALIDATION_PR" \
  "/lambda-ci-cpu $PAD_VALIDATION_SHA" \
  "padataset:cpu-ci" \
  "$PAD_CPU_TARGET_CLASS" "$PAD_CPU_TARGET_SCALE_SET" "$PAD_CPU_NEW_BLOB"

run_validation \
  "$PAD_REPO" "$PAD_GPU_WORKFLOW" "$PAD_VALIDATION_PR" \
  "/lambda-ci-gpu $PAD_VALIDATION_SHA" \
  "padataset:gpu-ci" \
  "$PAD_GPU_TARGET_CLASS" "$PAD_GPU_TARGET_SCALE_SET" "$PAD_GPU_NEW_BLOB"

env MANIFEST="$MANIFEST" ROWS="$VALIDATION_ROWS" OUT="$TMP/validation-confirmation.json" python3 - <<'PY'
import json, os, pathlib
m=json.loads(pathlib.Path(os.environ["MANIFEST"]).read_text())
routes={}
for line in pathlib.Path(os.environ["ROWS"]).read_text().splitlines():
    if not line:
        continue
    key,run_id,job_id,runner_name,class_id,scale_set,blob=line.split("\t")
    routes[key]={
      "conclusion":"success",
      "run_id":int(run_id),
      "job_id":int(job_id),
      "workflow_blob_sha":blob,
      "runner_class_id":class_id,
      "scale_set_name":scale_set,
      "runner_name":runner_name,
    }
assert set(routes)==set(m["workflow_bindings"])
payload={
 "schema_version":1,
 "mode":"V3_PRODUCTION_VALIDATION_CONFIRMED",
 "production_generation_sha256":m["production_generation_sha256"],
 "routes":routes,
}
pathlib.Path(os.environ["OUT"]).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PY
sudo install -o root -g root -m 0600 \
  "$TMP/validation-confirmation.json" "$TMP/root-validation-confirmation.json"

echo "POST_VALIDATION_RESOURCE_DRAIN=BEGIN"
clean=0
for _ in $(seq 1 90); do
  set +e
  sudo env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/scripts" /usr/bin/python3 - <<'PY'
import pathlib
import lambda_ci_policy_compiler as compiler
import lambda_ci_v3_migration_transaction as migration
import lambda_ci_v3_production_cutover as production
root=production._load(pathlib.Path("/etc/workspace-ci/v3/root-policy.json"))
registry=compiler.load_inputs(production.ROOT)["registry"]
migration._assert_generation_drained(
    production.RealSystemd(),
    registry=registry,
    root_policy=root,
    require_legacy_empty=True,
    require_v3_empty=True,
    state_root=pathlib.Path("/var/lib/workspace-ci/v3/provisioner"),
)
PY
  rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    clean=1
    break
  fi
  sleep 2
done
if [ "$clean" -ne 1 ]; then
  echo "STOP_POST_VALIDATION_RESOURCE_DRAIN_FAILED"
  exit 1
fi
echo "POST_VALIDATION_RESOURCE_DRAIN=PASS"

sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$PROD_HELPER" \
  --repo-root "$ROOT" \
  --source-head "$OPERATOR_HEAD" \
  --commit \
  --receipt "$TX_RECEIPT" \
  --validation-confirmation "$TMP/root-validation-confirmation.json"
echo "PRODUCTION_V3_COMMIT=PASS"

sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 "$INSTALLED_RECONCILER" \
  --verify-installed --manifest "$BASE_MANIFEST"
echo "POST_COMMIT_EFFECTIVE_GENERATION_VERIFY=PASS"

for unit in workspace-ci-v3-reconciler.service workspace-ci-v3-provisioner.service; do
  require_active "$unit"
  if ! systemctl is-enabled --quiet "$unit"; then
    echo "STOP_POST_COMMIT_ROOT_NOT_ENABLED unit=$unit"
    exit 1
  fi
  echo "POST_COMMIT_ROOT_ENABLED=PASS unit=$unit"
done

for class_id in "$WC_TARGET_CLASS" "$PAD_CPU_TARGET_CLASS" "$PAD_GPU_TARGET_CLASS"; do
  unit="workspace-ci-v3-controller@$class_id.service"
  require_active "$unit"
  if ! systemctl is-enabled --quiet "$unit"; then
    echo "STOP_POST_COMMIT_ACCEPTED_CLASS_NOT_ENABLED unit=$unit"
    exit 1
  fi
  echo "POST_COMMIT_ACCEPTED_CLASS_ENABLED=PASS unit=$unit"
done

for class_id in \
  research-cpu-public-v1 \
  research-gpu-single-public-v1 \
  research-gpu-single-runtime-v1 \
  research-model-single-offline-v1 \
  research-model-dual-offline-v1 \
  research-model-dual-public-v1
do
  require_inactive "workspace-ci-v3-controller@$class_id.service"
  require_not_enabled "workspace-ci-v3-controller@$class_id.service"
done

for unit in \
  workspace-ci-controller@workspace-control-cpu.service \
  workspace-ci-controller@padataset-cpu.service \
  workspace-ci-controller@padataset-gpu.service \
  workspace-ci-controller@research-engine-cpu.service \
  workspace-ci-controller@research-engine-gpu.service
do
  require_inactive "$unit"
  require_not_enabled "$unit"
done
echo "POST_COMMIT_V2_CONTROLLERS_RETIRED_OR_GATED=PASS"

test "$(workflow_blob "$WC_REPO" "$WC_WORKFLOW")" = "$WC_NEW_BLOB"
test "$(workflow_blob "$PAD_REPO" "$PAD_CPU_WORKFLOW")" = "$PAD_CPU_NEW_BLOB"
test "$(workflow_blob "$PAD_REPO" "$PAD_GPU_WORKFLOW")" = "$PAD_GPU_NEW_BLOB"
echo "POST_COMMIT_WORKFLOW_BINDING=PASS"

CUTOVER_COMMITTED=1
cleanup_padataset_validation_pr
PAD_VALIDATION_PR=""
PAD_VALIDATION_BRANCH=""

echo "V3_PRODUCTION_GENERATION_SHA256=$GENERATION_SHA"
echo "V3_PRODUCTION_TRANSACTION_RECEIPT=$TX_RECEIPT"
echo "V3_PRODUCTION_CUTOVER_ACCEPTED=PASS"
echo "=== V3 PRODUCTION GENERATION CUTOVER: COMPLETE ==="
