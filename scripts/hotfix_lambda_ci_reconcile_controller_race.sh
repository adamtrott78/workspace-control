#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

die() { echo "ERROR=$*" >&2; exit 70; }

[[ "$(id -u)" == "0" ]] || die "ROOT_REQUIRED"
[[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]] || die "RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT"
[[ -n "${WORKSPACE_CI_RECONCILE_HOTFIX_EXPECTED_SHA:-}" ]] || die "EXPECTED_SHA_REQUIRED"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
git_as_invoker() {
  runuser -u "$SUDO_USER" -- env GIT_OPTIONAL_LOCKS=0 git -C "$REPO_ROOT" "$@"
}
HEAD="$(git_as_invoker rev-parse HEAD)" || die "WORKSPACE_CONTROL_HEAD_READ_FAILED"
[[ "$HEAD" == "$WORKSPACE_CI_RECONCILE_HOTFIX_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
STATUS="$(git_as_invoker status --porcelain)" || die "WORKSPACE_CONTROL_STATUS_FAILED"
[[ -z "$STATUS" ]] || die "WORKSPACE_CONTROL_DIRTY"

MANIFEST="$REPO_ROOT/architecture/lambda-ci-reconcile-controller-hotfix.v1.json"
python3 - "$REPO_ROOT" "$MANIFEST" <<'PY'
import json,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]); manifest=json.loads(pathlib.Path(sys.argv[2]).read_text())
if manifest.get("status")!="VALIDATED_HOTFIX_INPUT":
    raise SystemExit("ERROR=HOTFIX_MANIFEST_STATUS")
for item in manifest["source_blobs"]:
    actual=subprocess.check_output(
        ["git","-c",f"safe.directory={root}","-C",str(root),"hash-object",item["path"]],
        text=True,
    ).strip()
    if actual != item["git_blob_sha"]:
        raise SystemExit(f"ERROR=HOTFIX_SOURCE_BLOB_DRIFT:{item['path']}:{actual}:{item['git_blob_sha']}")
print("HOTFIX_SOURCE_BLOB_PREFLIGHT=PASS")
PY

TOKEN=/var/lib/workspace-ci/reconcile-controller/github-token
[[ -f "$TOKEN" ]] || die "RECONCILIATION_TOKEN_MISSING"
[[ "$(stat -c '%U:%G' "$TOKEN")" == "ci-reconciler:workspace-ci-reconciler" ]] || die "RECONCILIATION_TOKEN_OWNER_DRIFT"
[[ "$(stat -c '%a' "$TOKEN")" == "600" ]] || die "RECONCILIATION_TOKEN_MODE_DRIFT"

for service in   workspace-ci-provisioner.service   workspace-ci-reconciler.service   workspace-ci-controller@research-engine-cpu.service   workspace-ci-controller@research-engine-gpu.service
do
  systemctl is-active --quiet "$service" || die "REQUIRED_SERVICE_NOT_ACTIVE:$service"
done

TARGET=/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py
BACKUP="${TARGET}.pre-unrelated-main-race-hotfix"
cp -a -- "$TARGET" "$BACKUP"
rollback() {
  local rc="$?"
  trap - ERR
  cp -a -- "$BACKUP" "$TARGET" 2>/dev/null || true
  systemctl restart workspace-ci-reconcile-controller.service 2>/dev/null || true
  echo "RECONCILE_CONTROLLER_HOTFIX_ROLLBACK=COMPLETE" >&2
  exit "$rc"
}
trap rollback ERR

install -o root -g root -m 0755   "$REPO_ROOT/scripts/lambda_ci_reconcile_controller.py"   "$TARGET"

systemctl restart workspace-ci-reconcile-controller.service
systemctl is-active --quiet workspace-ci-reconcile-controller.service || die "RECONCILE_CONTROLLER_NOT_ACTIVE"

SUCCESS=/var/lib/workspace-ci/reconcile-controller/last-success.json
for _ in $(seq 1 60); do
  if [[ -f "$SUCCESS" ]] && python3 - "$SUCCESS" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
ok=(
    p.get("response",{}).get("status")=="PASS"
    and p.get("policy_equivalent_to_observed_main") is True
    and isinstance(p.get("approved_policy_sha"),str)
    and isinstance(p.get("observed_main_sha"),str)
)
raise SystemExit(0 if ok else 1)
PY
  then
    break
  fi
  sleep 2
done

[[ -f "$SUCCESS" ]] || die "RECONCILIATION_SUCCESS_RECEIPT_MISSING"
python3 - "$SUCCESS" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
if p.get("response",{}).get("status")!="PASS":
    raise SystemExit("ERROR=ROOT_RECONCILIATION_NOT_PASS")
if p.get("policy_equivalent_to_observed_main") is not True:
    raise SystemExit("ERROR=POLICY_EQUIVALENCE_NOT_PROVEN")
receipt=p.get("response",{}).get("receipt",{})
plan=receipt.get("plan",{})
if plan.get("active_projects") != ["research-engine"]:
    raise SystemExit("ERROR=ACTIVE_PROJECT_SET_DRIFT")
if plan.get("planned_projects_skipped") != ["padataset"]:
    raise SystemExit("ERROR=PADATASET_SKIP_NOT_PROVEN")
if receipt.get("mutation_performed") is not True:
    raise SystemExit("ERROR=RECONCILIATION_APPLY_NOT_PROVEN")
print(json.dumps({
    "approved_policy_sha":p.get("approved_policy_sha"),
    "observed_main_sha":p.get("observed_main_sha"),
    "policy_equivalent_to_observed_main":p.get("policy_equivalent_to_observed_main"),
    "root_receipt_status":receipt.get("status"),
    "active_projects":plan.get("active_projects"),
    "planned_projects_skipped":plan.get("planned_projects_skipped"),
},indent=2,sort_keys=True))
PY

getent passwd ci-padataset >/dev/null && die "PADATASET_USER_PREMATURELY_CREATED"
[[ ! -e /srv/workspace-ci/padataset ]] || die "PADATASET_ROOT_PREMATURELY_CREATED"
[[ ! -e /etc/workspace-ci/controllers/padataset-cpu.env ]] || die "PADATASET_CONTROLLER_PREMATURELY_CREATED"

rm -f -- "$BACKUP"
trap - ERR
echo "RUN3_RECONCILIATION_PLANE=PASS"
echo "NEXT=Execute research-engine CPU, gpu-small, and accepted model-eval regression through the generic installed path."
