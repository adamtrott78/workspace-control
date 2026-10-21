#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

die() {
  echo "ERROR=$*" >&2
  exit 70
}

[[ "$(id -u)" == "0" ]] || die "ROOT_REQUIRED"
[[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]] || die "RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT"
[[ -n "${WORKSPACE_CI_RECONCILE_SOCKET_HOTFIX_EXPECTED_SHA:-}" ]] || die "EXPECTED_SHA_REQUIRED"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
git_as_invoker() {
  runuser -u "$SUDO_USER" -- env GIT_OPTIONAL_LOCKS=0 git -C "$REPO_ROOT" "$@"
}

HEAD="$(git_as_invoker rev-parse HEAD)" || die "WORKSPACE_CONTROL_HEAD_READ_FAILED"
[[ "$HEAD" == "$WORKSPACE_CI_RECONCILE_SOCKET_HOTFIX_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
STATUS="$(git_as_invoker status --porcelain)" || die "WORKSPACE_CONTROL_STATUS_FAILED"
[[ -z "$STATUS" ]] || die "WORKSPACE_CONTROL_DIRTY"

MANIFEST="$REPO_ROOT/architecture/lambda-ci-reconciliation-socket-hotfix.v1.json"
python3 - "$REPO_ROOT" "$MANIFEST" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
manifest = json.loads(pathlib.Path(sys.argv[2]).read_text())
if manifest.get("status") != "VALIDATED_HOTFIX_INPUT":
    raise SystemExit("ERROR=HOTFIX_MANIFEST_STATUS")

for item in manifest["source_blobs"]:
    data = (root / item["path"]).read_bytes()
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    actual = h.hexdigest()
    if actual != item["git_blob_sha"]:
        raise SystemExit(
            f"ERROR=HOTFIX_SOURCE_BLOB_DRIFT:{item['path']}:{actual}:{item['git_blob_sha']}"
        )
print("RECONCILIATION_SOCKET_HOTFIX_SOURCE_PREFLIGHT=PASS")
PY

TOKEN=/var/lib/workspace-ci/reconcile-controller/github-token
[[ -f "$TOKEN" ]] || die "RECONCILIATION_TOKEN_MISSING"
[[ "$(stat -c '%U:%G' "$TOKEN")" == "ci-reconciler:workspace-ci-reconciler" ]] || die "RECONCILIATION_TOKEN_OWNER_DRIFT"
[[ "$(stat -c '%a' "$TOKEN")" == "600" ]] || die "RECONCILIATION_TOKEN_MODE_DRIFT"

for service in \
  workspace-ci-provisioner.service \
  workspace-ci-reconciler.service \
  workspace-ci-controller@research-engine-cpu.service \
  workspace-ci-controller@research-engine-gpu.service
do
  systemctl is-active --quiet "$service" || die "REQUIRED_SERVICE_NOT_ACTIVE:$service"
done

PARENT=/run/workspace-ci
RECON_TARGET=/opt/workspace-ci/reconciler/lambda_ci_reconciler.py
PROV_TARGET=/opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py
CONTROLLER_TARGET=/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py
EXPECTED_CONTROLLER_BLOB=8469569ea0864e24d1c219fc3fea438367a8efc8

[[ "$(git hash-object "$CONTROLLER_TARGET")" == "$EXPECTED_CONTROLLER_BLOB" ]] || die "RECONCILE_CONTROLLER_BLOB_DRIFT"

OLD_PARENT_OWNER="$(stat -c '%U' "$PARENT")"
OLD_PARENT_GROUP="$(stat -c '%G' "$PARENT")"
OLD_PARENT_MODE="$(stat -c '%a' "$PARENT")"

BACKUP="$(mktemp -d /var/lib/workspace-ci/reconciler/run3-socket-hotfix.XXXXXX)"
cp -a -- "$RECON_TARGET" "$BACKUP/lambda_ci_reconciler.py"
cp -a -- "$PROV_TARGET" "$BACKUP/lambda_ci_provisioner_service.py"

rollback_needed=0
cleanup() {
  rc=$?
  if [[ "$rc" -ne 0 && "$rollback_needed" -eq 1 ]]; then
    trap - EXIT
    cp -a -- "$BACKUP/lambda_ci_reconciler.py" "$RECON_TARGET" 2>/dev/null || true
    cp -a -- "$BACKUP/lambda_ci_provisioner_service.py" "$PROV_TARGET" 2>/dev/null || true
    chown "$OLD_PARENT_OWNER:$OLD_PARENT_GROUP" "$PARENT" 2>/dev/null || true
    chmod "$OLD_PARENT_MODE" "$PARENT" 2>/dev/null || true
    systemctl restart workspace-ci-reconciler.service 2>/dev/null || true
    systemctl stop workspace-ci-reconcile-controller.service 2>/dev/null || true
    rm -rf -- "$BACKUP"
    echo "RECONCILIATION_SOCKET_HOTFIX_ROLLBACK=COMPLETE" >&2
    exit "$rc"
  fi
  rm -rf -- "$BACKUP"
}
trap cleanup EXIT
rollback_needed=1

install -d -o root -g root -m 0711 "$PARENT"
install -o root -g root -m 0755 \
  "$REPO_ROOT/scripts/lambda_ci_reconciler.py" \
  "$RECON_TARGET"
install -o root -g root -m 0755 \
  "$REPO_ROOT/scripts/lambda_ci_provisioner_service.py" \
  "$PROV_TARGET"

[[ "$(stat -c '%U:%G' "$PARENT")" == "root:root" ]] || die "SOCKET_PARENT_OWNER_DRIFT"
[[ "$(stat -c '%a' "$PARENT")" == "711" ]] || die "SOCKET_PARENT_MODE_DRIFT"

systemctl restart workspace-ci-reconciler.service
systemctl is-active --quiet workspace-ci-reconciler.service || die "ROOT_RECONCILER_NOT_ACTIVE"

for _ in $(seq 1 20); do
  [[ -S /run/workspace-ci/reconciler.sock ]] && break
  sleep 0.25
done

[[ -S /run/workspace-ci/reconciler.sock ]] || die "RECONCILER_SOCKET_MISSING"
[[ -S /run/workspace-ci/provisioner.sock ]] || die "PROVISIONER_SOCKET_MISSING"
[[ "$(stat -c '%U:%G' /run/workspace-ci/reconciler.sock)" == "root:workspace-ci-reconciler" ]] || die "RECONCILER_SOCKET_OWNER_DRIFT"
[[ "$(stat -c '%a' /run/workspace-ci/reconciler.sock)" == "660" ]] || die "RECONCILER_SOCKET_MODE_DRIFT"
[[ "$(stat -c '%U:%G' /run/workspace-ci/provisioner.sock)" == "root:workspace-ci-controller" ]] || die "PROVISIONER_SOCKET_OWNER_DRIFT"
[[ "$(stat -c '%a' /run/workspace-ci/provisioner.sock)" == "660" ]] || die "PROVISIONER_SOCKET_MODE_DRIFT"

runuser -u ci-reconciler -- test -x "$PARENT" || die "RECONCILER_SOCKET_PARENT_NOT_TRAVERSABLE"
runuser -u ci-controller -- test -x "$PARENT" || die "CONTROLLER_SOCKET_PARENT_NOT_TRAVERSABLE"
runuser -u ci-reconciler -- test -w /run/workspace-ci/reconciler.sock || die "RECONCILER_SOCKET_NOT_WRITABLE_BY_RECONCILER"
runuser -u ci-controller -- test -w /run/workspace-ci/provisioner.sock || die "PROVISIONER_SOCKET_NOT_WRITABLE_BY_CONTROLLER"
if runuser -u ci-reconciler -- test -w /run/workspace-ci/provisioner.sock; then
  die "RECONCILER_CAN_WRITE_PROVISIONER_SOCKET"
fi
if runuser -u ci-controller -- test -w /run/workspace-ci/reconciler.sock; then
  die "CONTROLLER_CAN_WRITE_RECONCILER_SOCKET"
fi

echo "SOCKET_PARENT_AND_GROUP_ISOLATION=PASS"

SUCCESS=/var/lib/workspace-ci/reconcile-controller/last-success.json
REJECTED=/var/lib/workspace-ci/reconcile-controller/last-rejected.json
BEFORE_SUCCESS_MTIME=0
if [[ -f "$SUCCESS" ]]; then
  BEFORE_SUCCESS_MTIME="$(stat -c '%Y' "$SUCCESS")"
fi

systemctl restart workspace-ci-reconcile-controller.service

for _ in $(seq 1 60); do
  if [[ -f "$SUCCESS" ]] && python3 - "$SUCCESS" "$BEFORE_SUCCESS_MTIME" <<'PY'
import json
import os
import sys

path = sys.argv[1]
before = int(sys.argv[2])
p = json.load(open(path))
fresh = int(os.stat(path).st_mtime) >= before
ok = (
    fresh
    and p.get("response", {}).get("status") == "PASS"
    and p.get("policy_equivalent_to_observed_main") is True
    and isinstance(p.get("approved_policy_sha"), str)
    and isinstance(p.get("observed_main_sha"), str)
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
import json
import sys

p = json.load(open(sys.argv[1]))
if p.get("response", {}).get("status") != "PASS":
    raise SystemExit("ERROR=ROOT_RECONCILIATION_NOT_PASS")
if p.get("policy_equivalent_to_observed_main") is not True:
    raise SystemExit("ERROR=POLICY_EQUIVALENCE_NOT_PROVEN")
receipt = p.get("response", {}).get("receipt", {})
plan = receipt.get("plan", {})
if plan.get("active_projects") != ["research-engine"]:
    raise SystemExit("ERROR=ACTIVE_PROJECT_SET_DRIFT")
if plan.get("planned_projects_skipped") != ["padataset"]:
    raise SystemExit("ERROR=PADATASET_SKIP_NOT_PROVEN")
if receipt.get("mutation_performed") is not True:
    raise SystemExit("ERROR=RECONCILIATION_APPLY_NOT_PROVEN")
print(json.dumps({
    "approved_policy_sha": p.get("approved_policy_sha"),
    "observed_main_sha": p.get("observed_main_sha"),
    "policy_equivalent_to_observed_main": p.get("policy_equivalent_to_observed_main"),
    "root_receipt_status": receipt.get("status"),
    "mutation_performed": receipt.get("mutation_performed"),
    "active_projects": plan.get("active_projects"),
    "planned_projects_skipped": plan.get("planned_projects_skipped"),
}, indent=2, sort_keys=True))
PY

[[ ! -f "$REJECTED" ]] || echo "NOTICE=LAST_REJECTED_PRESENT_FROM_PRIOR_ATTEMPT"

getent passwd ci-padataset >/dev/null && die "PADATASET_USER_PREMATURELY_CREATED"
[[ ! -e /srv/workspace-ci/padataset ]] || die "PADATASET_ROOT_PREMATURELY_CREATED"
[[ ! -e /etc/workspace-ci/controllers/padataset-cpu.env ]] || die "PADATASET_CONTROLLER_PREMATURELY_CREATED"

RESTARTS_BEFORE="$(systemctl show workspace-ci-reconcile-controller.service -p NRestarts --value)"
sleep 6
systemctl is-active --quiet workspace-ci-reconcile-controller.service || die "RECONCILE_CONTROLLER_NOT_STABLE"
RESTARTS_AFTER="$(systemctl show workspace-ci-reconcile-controller.service -p NRestarts --value)"
[[ "$RESTARTS_AFTER" == "$RESTARTS_BEFORE" ]] || die "RECONCILE_CONTROLLER_RESTARTED_AFTER_PASS"

[[ "$(git hash-object "$RECON_TARGET")" == "$(git hash-object "$REPO_ROOT/scripts/lambda_ci_reconciler.py")" ]] || die "INSTALLED_RECONCILER_BLOB_DRIFT"
[[ "$(git hash-object "$PROV_TARGET")" == "$(git hash-object "$REPO_ROOT/scripts/lambda_ci_provisioner_service.py")" ]] || die "INSTALLED_PROVISIONER_SERVICE_BLOB_DRIFT"

rollback_needed=0
echo "RUN3_RECONCILIATION_SOCKET_HOTFIX=PASS"
echo "RUN3_RECONCILIATION_PLANE=PASS"
echo "NEXT=Checkpoint reconciliation acceptance, then execute research-engine CPU, gpu-small, and accepted model-eval regressions."
