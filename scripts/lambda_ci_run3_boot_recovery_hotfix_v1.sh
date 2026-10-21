#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

die() {
  echo "ERROR=$*" >&2
  exit 70
}

[[ "$(id -u)" == "0" ]] || die "ROOT_REQUIRED"
[[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]] || die "RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT"
[[ -n "${WORKSPACE_CI_RUN3_BOOT_RECOVERY_EXPECTED_SHA:-}" ]] || die "EXPECTED_SHA_REQUIRED"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
git_as_invoker() {
  runuser -u "$SUDO_USER" -- env GIT_OPTIONAL_LOCKS=0 git -C "$REPO_ROOT" "$@"
}

HEAD="$(git_as_invoker rev-parse HEAD)" || die "WORKSPACE_CONTROL_HEAD_READ_FAILED"
[[ "$HEAD" == "$WORKSPACE_CI_RUN3_BOOT_RECOVERY_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
STATUS="$(git_as_invoker status --porcelain)" || die "WORKSPACE_CONTROL_STATUS_FAILED"
[[ -z "$STATUS" ]] || die "WORKSPACE_CONTROL_DIRTY"

MANIFEST="$REPO_ROOT/architecture/lambda-ci-run3-boot-recovery-hotfix.v1.json"
python3 - "$REPO_ROOT" "$MANIFEST" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
manifest = json.loads(pathlib.Path(sys.argv[2]).read_text())
if manifest.get("schema_version") != 1 or manifest.get("status") != "VALIDATED_HOTFIX_INPUT":
    raise SystemExit("ERROR=BOOT_RECOVERY_MANIFEST_STATUS")
for item in manifest["source_blobs"]:
    data = (root / item["path"]).read_bytes()
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    actual = h.hexdigest()
    if actual != item["git_blob_sha"]:
        raise SystemExit(
            f"ERROR=BOOT_RECOVERY_SOURCE_BLOB_DRIFT:{item['path']}:{actual}:{item['git_blob_sha']}"
        )
print("RUN3_BOOT_RECOVERY_SOURCE_PREFLIGHT=PASS")
PY

TOKEN=/var/lib/workspace-ci/reconcile-controller/github-token
[[ -f "$TOKEN" ]] || die "RECONCILIATION_TOKEN_MISSING"
[[ "$(stat -c '%U:%G' "$TOKEN")" == "ci-reconciler:workspace-ci-reconciler" ]] || die "RECONCILIATION_TOKEN_OWNER_DRIFT"
[[ "$(stat -c '%a' "$TOKEN")" == "600" ]] || die "RECONCILIATION_TOKEN_MODE_DRIFT"

for identity in ci-controller ci-reconciler ci-research-engine; do
  getent passwd "$identity" >/dev/null || die "MISSING_IDENTITY:$identity"
done
for group in workspace-ci-controller workspace-ci-reconciler; do
  getent group "$group" >/dev/null || die "MISSING_GROUP:$group"
done

if pgrep -u ci-research-engine >/dev/null 2>&1; then
  pgrep -a -u ci-research-engine >&2 || true
  die "ACTIVE_RESEARCH_ENGINE_PROCESS"
fi
if systemctl list-units --type=service --state=running --no-legend 'workspace-ci-research-engine-*.service' | grep -q .; then
  systemctl list-units --type=service --state=running --no-legend 'workspace-ci-research-engine-*.service' >&2 || true
  die "ACTIVE_RESEARCH_ENGINE_TRANSIENT_UNIT"
fi

hash_file() {
  [[ -f "$1" ]] || return 1
  git hash-object "$1"
}

accepted_blob() {
  local path="$1"; shift
  local actual allowed
  actual="$(hash_file "$path")" || die "EXPECTED_INSTALLED_FILE_MISSING:$path"
  for allowed in "$@"; do
    [[ "$actual" == "$allowed" ]] && {
      echo "accepted_installed_blob=$path:$actual"
      return 0
    }
  done
  die "UNEXPECTED_INSTALLED_BLOB:$path:$actual"
}

PROV_PY=/opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py
RECON_PY=/opt/workspace-ci/reconciler/lambda_ci_reconciler.py
POLL_PY=/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py
PROV_UNIT=/etc/systemd/system/workspace-ci-provisioner.service
RECON_UNIT=/etc/systemd/system/workspace-ci-reconciler.service
CTRL_UNIT=/etc/systemd/system/workspace-ci-controller@.service
TMPFILES=/etc/tmpfiles.d/workspace-ci.conf

accepted_blob "$PROV_PY" \
  85a341527fa951ac6a88a4e8e15141d54f728f5a \
  d728c5d26f56694507a23623ccf10d8f71eb05a0
accepted_blob "$RECON_PY" \
  0d189505d7ddb42522e261dff9f2c1e5193fa882 \
  360d6b25599b09ccb727e4aacf23374d3529c787
accepted_blob "$POLL_PY" \
  8469569ea0864e24d1c219fc3fea438367a8efc8
accepted_blob "$PROV_UNIT" \
  baf99b17026a2b2090bdbe52ea0c5566d44efe28 \
  acdadf5ce6f152d7f1d04e5308657d35e0585d4f
accepted_blob "$RECON_UNIT" \
  b4a5808b8bbf4629c6c14d2280b2bb002e92a03e \
  a81b758dd2f735fbe72085e3ae3c7529e10152a1
accepted_blob "$CTRL_UNIT" \
  0124023c22575ebb94c79a71f4589af6e562db96 \
  03ee9278bfcc8d9a455ecdacefd7bee5bd4a50b7

if [[ -e "$TMPFILES" ]]; then
  accepted_blob "$TMPFILES" eb6ddec43bdeead39c7af91f052c3f1a2602ebf2
fi

echo "RUN3_BOOT_RECOVERY_INSTALLED_STATE_PREFLIGHT=PASS"

BACKUP="$(mktemp -d /var/lib/workspace-ci/reconciler/run3-boot-recovery.XXXXXX)"
mkdir -p "$BACKUP/files"
: > "$BACKUP/index.tsv"

backup_target() {
  local target="$1" key prior
  key="$(printf '%s' "$target" | sha256sum | awk '{print $1}')"
  if [[ -e "$target" || -L "$target" ]]; then
    prior=PRESENT
    cp -a -- "$target" "$BACKUP/files/$key"
  else
    prior=ABSENT
  fi
  printf '%s\t%s\t%s\n' "$key" "$target" "$prior" >> "$BACKUP/index.tsv"
}

for target in \
  "$PROV_PY" \
  "$RECON_PY" \
  "$PROV_UNIT" \
  "$RECON_UNIT" \
  "$CTRL_UNIT" \
  "$TMPFILES"
do
  backup_target "$target"
done

PARENT_WAS_PRESENT=NO
[[ -e /run/workspace-ci ]] && PARENT_WAS_PRESENT=YES

rollback_needed=0
rollback() {
  local rc="$?"
  trap - EXIT
  echo "RUN3_BOOT_RECOVERY_ROLLBACK=BEGIN" >&2

  systemctl disable --now workspace-ci-reconcile-controller.service 2>/dev/null || true
  systemctl disable --now workspace-ci-controller@research-engine-cpu.service 2>/dev/null || true
  systemctl disable --now workspace-ci-controller@research-engine-gpu.service 2>/dev/null || true
  systemctl disable --now workspace-ci-provisioner.service 2>/dev/null || true
  systemctl disable --now workspace-ci-reconciler.service 2>/dev/null || true

  while IFS=$'\t' read -r key target prior; do
    [[ -n "$target" ]] || continue
    if [[ "$prior" == "PRESENT" ]]; then
      install -d -o root -g root -m 0755 "$(dirname "$target")"
      rm -rf -- "$target"
      cp -a -- "$BACKUP/files/$key" "$target"
    else
      rm -rf -- "$target"
    fi
  done < "$BACKUP/index.tsv"

  systemctl daemon-reload 2>/dev/null || true
  if [[ "$PARENT_WAS_PRESENT" == "NO" ]]; then
    rm -rf /run/workspace-ci 2>/dev/null || true
  fi
  rm -rf -- "$BACKUP"
  echo "RUN3_BOOT_RECOVERY_ROLLBACK=COMPLETE_SERVICES_LEFT_DISABLED" >&2
  exit "$rc"
}
trap rollback EXIT

systemctl stop \
  workspace-ci-reconcile-controller.service \
  workspace-ci-controller@research-engine-cpu.service \
  workspace-ci-controller@research-engine-gpu.service \
  workspace-ci-provisioner.service \
  workspace-ci-reconciler.service \
  2>/dev/null || true

install -d -o root -g root -m 0755 /etc/tmpfiles.d
install -o root -g root -m 0644 \
  "$REPO_ROOT/systemd/workspace-ci-tmpfiles.conf" \
  "$TMPFILES"
install -o root -g root -m 0755 \
  "$REPO_ROOT/scripts/lambda_ci_provisioner_service.py" \
  "$PROV_PY"
install -o root -g root -m 0755 \
  "$REPO_ROOT/scripts/lambda_ci_reconciler.py" \
  "$RECON_PY"
install -o root -g root -m 0644 \
  "$REPO_ROOT/templates/lambda-ci/workspace-ci-provisioner-multirepo.service.in" \
  "$PROV_UNIT"
install -o root -g root -m 0644 \
  "$REPO_ROOT/systemd/workspace-ci-reconciler.service" \
  "$RECON_UNIT"
install -o root -g root -m 0644 \
  "$REPO_ROOT/templates/lambda-ci/workspace-ci-controller@.service.in" \
  "$CTRL_UNIT"

systemd-analyze verify "$PROV_UNIT" "$RECON_UNIT" "$CTRL_UNIT"
systemd-tmpfiles --create "$TMPFILES"

[[ -d /run/workspace-ci ]] || die "SOCKET_PARENT_MISSING_AFTER_TMPFILES"
[[ "$(stat -c '%U:%G' /run/workspace-ci)" == "root:root" ]] || die "SOCKET_PARENT_OWNER_DRIFT"
[[ "$(stat -c '%a' /run/workspace-ci)" == "711" ]] || die "SOCKET_PARENT_MODE_DRIFT"

systemctl daemon-reload

systemctl enable \
  workspace-ci-provisioner.service \
  workspace-ci-reconciler.service \
  workspace-ci-controller@research-engine-cpu.service \
  workspace-ci-controller@research-engine-gpu.service

for service in \
  workspace-ci-provisioner.service \
  workspace-ci-reconciler.service \
  workspace-ci-controller@research-engine-cpu.service \
  workspace-ci-controller@research-engine-gpu.service
do
  systemctl is-enabled --quiet "$service" || die "SERVICE_NOT_BOOT_ENABLED:$service"
done

systemctl restart workspace-ci-provisioner.service
systemctl restart workspace-ci-reconciler.service

for _ in $(seq 1 40); do
  if systemctl is-active --quiet workspace-ci-provisioner.service \
    && systemctl is-active --quiet workspace-ci-reconciler.service \
    && [[ -S /run/workspace-ci/provisioner.sock ]] \
    && [[ -S /run/workspace-ci/reconciler.sock ]]; then
    break
  fi
  sleep 0.25
done

systemctl is-active --quiet workspace-ci-provisioner.service || die "PROVISIONER_NOT_ACTIVE"
systemctl is-active --quiet workspace-ci-reconciler.service || die "RECONCILER_NOT_ACTIVE"
[[ -S /run/workspace-ci/provisioner.sock ]] || die "PROVISIONER_SOCKET_MISSING"
[[ -S /run/workspace-ci/reconciler.sock ]] || die "RECONCILER_SOCKET_MISSING"
[[ "$(stat -c '%U:%G' /run/workspace-ci/provisioner.sock)" == "root:workspace-ci-controller" ]] || die "PROVISIONER_SOCKET_OWNER_DRIFT"
[[ "$(stat -c '%a' /run/workspace-ci/provisioner.sock)" == "660" ]] || die "PROVISIONER_SOCKET_MODE_DRIFT"
[[ "$(stat -c '%U:%G' /run/workspace-ci/reconciler.sock)" == "root:workspace-ci-reconciler" ]] || die "RECONCILER_SOCKET_OWNER_DRIFT"
[[ "$(stat -c '%a' /run/workspace-ci/reconciler.sock)" == "660" ]] || die "RECONCILER_SOCKET_MODE_DRIFT"

runuser -u ci-controller -- test -x /run/workspace-ci || die "CONTROLLER_SOCKET_PARENT_NOT_TRAVERSABLE"
runuser -u ci-reconciler -- test -x /run/workspace-ci || die "RECONCILER_SOCKET_PARENT_NOT_TRAVERSABLE"
runuser -u ci-controller -- test -w /run/workspace-ci/provisioner.sock || die "CONTROLLER_CANNOT_WRITE_PROVISIONER_SOCKET"
runuser -u ci-reconciler -- test -w /run/workspace-ci/reconciler.sock || die "RECONCILER_CANNOT_WRITE_RECONCILER_SOCKET"
if runuser -u ci-reconciler -- test -w /run/workspace-ci/provisioner.sock; then
  die "RECONCILER_CAN_WRITE_PROVISIONER_SOCKET"
fi
if runuser -u ci-controller -- test -w /run/workspace-ci/reconciler.sock; then
  die "CONTROLLER_CAN_WRITE_RECONCILER_SOCKET"
fi

echo "RUN3_BOOT_SOCKET_ISOLATION=PASS"

systemctl restart workspace-ci-controller@research-engine-cpu.service
systemctl restart workspace-ci-controller@research-engine-gpu.service

systemctl is-active --quiet workspace-ci-controller@research-engine-cpu.service || die "CPU_CONTROLLER_NOT_ACTIVE"
systemctl is-active --quiet workspace-ci-controller@research-engine-gpu.service || die "GPU_CONTROLLER_NOT_ACTIVE"

SUCCESS=/var/lib/workspace-ci/reconcile-controller/last-success.json
REJECTED=/var/lib/workspace-ci/reconcile-controller/last-rejected.json
BEFORE_SUCCESS_MTIME=0
if [[ -f "$SUCCESS" ]]; then
  BEFORE_SUCCESS_MTIME="$(stat -c '%Y' "$SUCCESS")"
fi

systemctl enable workspace-ci-reconcile-controller.service
systemctl restart workspace-ci-reconcile-controller.service

for _ in $(seq 1 60); do
  if [[ -f "$SUCCESS" ]] && python3 - "$SUCCESS" "$BEFORE_SUCCESS_MTIME" <<'PY'
import json
import os
import sys

path = sys.argv[1]
before = int(sys.argv[2])
p = json.load(open(path))
mtime = int(os.stat(path).st_mtime)
fresh = before == 0 or mtime > before
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

[[ ! -f "$REJECTED" ]] || echo "NOTICE=LAST_REJECTED_PRESENT"

getent passwd ci-padataset >/dev/null && die "PADATASET_USER_PREMATURELY_CREATED"
[[ ! -e /srv/workspace-ci/padataset ]] || die "PADATASET_ROOT_PREMATURELY_CREATED"
[[ ! -e /etc/workspace-ci/controllers/padataset-cpu.env ]] || die "PADATASET_CPU_CONTROLLER_PREMATURELY_CREATED"
[[ ! -e /etc/workspace-ci/controllers/padataset-gpu.env ]] || die "PADATASET_GPU_CONTROLLER_PREMATURELY_CREATED"

declare -A BEFORE
for service in \
  workspace-ci-provisioner.service \
  workspace-ci-reconciler.service \
  workspace-ci-controller@research-engine-cpu.service \
  workspace-ci-controller@research-engine-gpu.service \
  workspace-ci-reconcile-controller.service
do
  systemctl is-active --quiet "$service" || die "SERVICE_NOT_ACTIVE_AFTER_RECOVERY:$service"
  BEFORE["$service"]="$(systemctl show "$service" -p NRestarts --value)"
done

sleep 6

for service in \
  workspace-ci-provisioner.service \
  workspace-ci-reconciler.service \
  workspace-ci-controller@research-engine-cpu.service \
  workspace-ci-controller@research-engine-gpu.service \
  workspace-ci-reconcile-controller.service
do
  systemctl is-active --quiet "$service" || die "SERVICE_NOT_STABLE:$service"
  after="$(systemctl show "$service" -p NRestarts --value)"
  [[ "$after" == "${BEFORE[$service]}" ]] || die "SERVICE_RESTARTED_AFTER_RECOVERY:$service:${BEFORE[$service]}:$after"
done

systemd-tmpfiles --create "$TMPFILES"
[[ "$(stat -c '%U:%G' /run/workspace-ci)" == "root:root" ]] || die "SOCKET_PARENT_OWNER_DRIFT_AFTER_RECREATE"
[[ "$(stat -c '%a' /run/workspace-ci)" == "711" ]] || die "SOCKET_PARENT_MODE_DRIFT_AFTER_RECREATE"

[[ "$(git hash-object "$PROV_PY")" == "$(git hash-object "$REPO_ROOT/scripts/lambda_ci_provisioner_service.py")" ]] || die "INSTALLED_PROVISIONER_SERVICE_BLOB_DRIFT"
[[ "$(git hash-object "$RECON_PY")" == "$(git hash-object "$REPO_ROOT/scripts/lambda_ci_reconciler.py")" ]] || die "INSTALLED_RECONCILER_BLOB_DRIFT"
[[ "$(git hash-object "$PROV_UNIT")" == "$(git hash-object "$REPO_ROOT/templates/lambda-ci/workspace-ci-provisioner-multirepo.service.in")" ]] || die "INSTALLED_PROVISIONER_UNIT_BLOB_DRIFT"
[[ "$(git hash-object "$RECON_UNIT")" == "$(git hash-object "$REPO_ROOT/systemd/workspace-ci-reconciler.service")" ]] || die "INSTALLED_RECONCILER_UNIT_BLOB_DRIFT"
[[ "$(git hash-object "$CTRL_UNIT")" == "$(git hash-object "$REPO_ROOT/templates/lambda-ci/workspace-ci-controller@.service.in")" ]] || die "INSTALLED_CONTROLLER_UNIT_BLOB_DRIFT"
[[ "$(git hash-object "$TMPFILES")" == "$(git hash-object "$REPO_ROOT/systemd/workspace-ci-tmpfiles.conf")" ]] || die "INSTALLED_TMPFILES_BLOB_DRIFT"

rollback_needed=0
trap - EXIT
rm -rf -- "$BACKUP"

echo "RUN3_BOOT_RECOVERY=PASS"
echo "RUN3_RECONCILIATION_PLANE=PASS"
echo "NEXT=Checkpoint accepted reconciliation plane, then execute research-engine CPU, gpu-small, and accepted model-eval regressions."
