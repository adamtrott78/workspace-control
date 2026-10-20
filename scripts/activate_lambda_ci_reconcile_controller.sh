#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

die() {
  echo "ERROR=$*" >&2
  exit 70
}

[[ "$(id -u)" == "0" ]] || die "ROOT_REQUIRED"
[[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]] || die "RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT"
[[ -n "${WORKSPACE_CI_MULTIREPO_EXPECTED_SHA:-}" ]] || die "EXPECTED_SHA_REQUIRED"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
HEAD="$(git -c "safe.directory=$REPO_ROOT" -C "$REPO_ROOT" rev-parse HEAD)"
[[ "$HEAD" == "$WORKSPACE_CI_MULTIREPO_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
[[ -z "$(git -c "safe.directory=$REPO_ROOT" -C "$REPO_ROOT" status --porcelain)" ]] || die "WORKSPACE_CONTROL_DIRTY"

TOKEN=/var/lib/workspace-ci/reconcile-controller/github-token
[[ -f "$TOKEN" ]] || die "RECONCILIATION_TOKEN_MISSING"
[[ "$(stat -c '%U:%G' "$TOKEN")" == "ci-reconciler:workspace-ci-reconciler" ]] || die "RECONCILIATION_TOKEN_OWNER_DRIFT"
[[ "$(stat -c '%a' "$TOKEN")" == "600" ]] || die "RECONCILIATION_TOKEN_MODE_DRIFT"

for service in   workspace-ci-provisioner.service   workspace-ci-reconciler.service   workspace-ci-controller@research-engine-cpu.service   workspace-ci-controller@research-engine-gpu.service
do
  systemctl is-active --quiet "$service" || die "REQUIRED_SERVICE_NOT_ACTIVE:$service"
done

systemctl enable workspace-ci-reconcile-controller.service
systemctl restart workspace-ci-reconcile-controller.service
systemctl is-active --quiet workspace-ci-reconcile-controller.service || die "RECONCILE_CONTROLLER_NOT_ACTIVE"

SUCCESS=/var/lib/workspace-ci/reconcile-controller/last-success.json
for _ in $(seq 1 60); do
  if [[ -f "$SUCCESS" ]] && python3 - "$SUCCESS" "$HEAD" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
raise SystemExit(0 if p.get("commit_sha")==sys.argv[2] and p.get("response",{}).get("status")=="PASS" else 1)
PY
  then
    break
  fi
  sleep 2
done

[[ -f "$SUCCESS" ]] || die "RECONCILIATION_SUCCESS_RECEIPT_MISSING"
python3 - "$SUCCESS" "$HEAD" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
if p.get("commit_sha") != sys.argv[2]:
    raise SystemExit("ERROR=RECONCILIATION_COMMIT_MISMATCH")
response=p.get("response",{})
if response.get("status") != "PASS":
    raise SystemExit("ERROR=ROOT_RECONCILIATION_NOT_PASS")
receipt=response.get("receipt",{})
if receipt.get("status") not in {"COMPLETED","DRY_RUN"}:
    raise SystemExit("ERROR=ROOT_RECONCILIATION_RECEIPT_NOT_TERMINAL")
plan=receipt.get("plan",{})
if plan.get("active_projects") != ["research-engine"]:
    raise SystemExit("ERROR=ACTIVE_PROJECT_SET_DRIFT")
if plan.get("planned_projects_skipped") != ["padataset"]:
    raise SystemExit("ERROR=PADATASET_SKIP_NOT_PROVEN")
if receipt.get("mutation_performed") is not True:
    raise SystemExit("ERROR=RECONCILIATION_APPLY_NOT_PROVEN")
print(json.dumps(p,indent=2,sort_keys=True))
PY

getent passwd ci-padataset >/dev/null && die "PADATASET_USER_PREMATURELY_CREATED"
[[ ! -e /srv/workspace-ci/padataset ]] || die "PADATASET_ROOT_PREMATURELY_CREATED"
[[ ! -e /etc/workspace-ci/controllers/padataset-cpu.env ]] || die "PADATASET_CONTROLLER_PREMATURELY_CREATED"

echo "RUN3_RECONCILIATION_PLANE=PASS"
echo "NEXT=Execute research-engine CPU, gpu-small, and accepted model-eval regression through the generic installed path."
