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
GIT=(git -c "safe.directory=$REPO_ROOT" -C "$REPO_ROOT")
HEAD="$("${GIT[@]}" rev-parse HEAD)"
[[ "$HEAD" == "$WORKSPACE_CI_MULTIREPO_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "WORKSPACE_CONTROL_DIRTY"

INSTALL_MANIFEST="$REPO_ROOT/architecture/lambda-ci-multirepo-install.v1.json"
[[ -f "$INSTALL_MANIFEST" ]] || die "INSTALL_MANIFEST_MISSING"

python3 - "$REPO_ROOT" "$INSTALL_MANIFEST" <<'PY'
import json, pathlib, subprocess, sys
root=pathlib.Path(sys.argv[1])
manifest=json.loads(pathlib.Path(sys.argv[2]).read_text())
if manifest.get("schema_version") != 1 or manifest.get("status") != "RUN3_VALIDATED_INSTALL_INPUT":
    raise SystemExit("ERROR=INSTALL_MANIFEST_STATUS")
for item in manifest.get("source_blobs", []):
    path=item["path"]
    expected=item["git_blob_sha"]
    actual=subprocess.check_output(
        ["git","-c",f"safe.directory={root}","-C",str(root),"hash-object",path],
        text=True,
    ).strip()
    if actual != expected:
        raise SystemExit(f"ERROR=SOURCE_BLOB_DRIFT:{path}:{actual}:{expected}")
print("SOURCE_BLOB_PREFLIGHT=PASS")
PY

for identity in ci-controller ci-research-engine; do
  getent passwd "$identity" >/dev/null || die "MISSING_IDENTITY:$identity"
done
getent group workspace-ci-controller >/dev/null || die "MISSING_GROUP:workspace-ci-controller"

GO_BIN=/opt/workspace-ci/go/1.26.3/bin/go
[[ -x "$GO_BIN" ]] || die "ISOLATED_GO_TOOLCHAIN_REQUIRED"
[[ "$("$GO_BIN" env GOVERSION 2>/dev/null)" == "go1.26.3" ]] || die "ISOLATED_GO_VERSION_DRIFT"

if pgrep -u ci-research-engine >/dev/null 2>&1; then
  pgrep -a -u ci-research-engine >&2 || true
  die "ACTIVE_RESEARCH_ENGINE_PROCESS"
fi
if systemctl list-units --type=service --state=running --no-legend 'workspace-ci-research-engine-*.service' | grep -q .; then
  systemctl list-units --type=service --state=running --no-legend 'workspace-ci-research-engine-*.service' >&2 || true
  die "ACTIVE_RESEARCH_ENGINE_TRANSIENT_UNIT"
fi
for service in workspace-ci-provisioner.service workspace-ci-controller.service workspace-ci-controller-gpu.service; do
  systemctl is-active --quiet "$service" || die "PREMIGRATION_SERVICE_NOT_ACTIVE:$service"
done

PRIMARY_DEV="$(ip -4 route get 1.1.1.1 | awk '{for (i=1;i<=NF;i++) if ($i=="dev") {print $(i+1); exit}}')"
LOCAL_SUBNET="$(ip -4 route show dev "$PRIMARY_DEV" proto kernel scope link | awk '$1 ~ /^[0-9]+\./ && $1 ~ /\// {print $1; exit}')"
[[ -n "$PRIMARY_DEV" && -n "$LOCAL_SUBNET" ]] || die "NETWORK_TOPOLOGY_UNRESOLVED"

INVOKER="$SUDO_USER"
INVOKER_HOME="$(getent passwd "$INVOKER" | awk -F: '{print $6}')"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$INVOKER_HOME/adamArchives/Adam/workspace-control-tmp/lambda-ci-multirepo-run3-$STAMP"
BACKUP="$OUT/rollback"
mkdir -p "$BACKUP"
chmod 0700 "$OUT" "$BACKUP"

TARGETS=(
  /opt/workspace-ci/controller/lambda-ci-controller
  /opt/workspace-ci/provisioner/lambda_ci_admission.py
  /opt/workspace-ci/provisioner/lambda_ci_multirepo.py
  /opt/workspace-ci/provisioner/lambda_ci_provisioner.py
  /opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py
  /opt/workspace-ci/provisioner/lambda_ci_runtime.py
  /opt/workspace-ci/reconciler/lambda_ci_multirepo.py
  /opt/workspace-ci/reconciler/lambda_ci_reconciler.py
  /opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py
  /opt/workspace-ci/reconcile-controller/stage-pat
  /etc/workspace-ci/lambda-ci-project-registry.v1.json
  /etc/workspace-ci/lambda-ci-execution-contracts.v1.json
  /etc/workspace-ci/lambda-ci-reconciliation-ceiling.v1.json
  /etc/workspace-ci/projects/research-engine.json
  /etc/workspace-ci/projects/padataset.json
  /etc/workspace-ci/controllers/research-engine-cpu.env
  /etc/workspace-ci/controllers/research-engine-gpu.env
  /etc/systemd/system/workspace-ci-provisioner.service
  /etc/systemd/system/workspace-ci-controller@.service
  /etc/systemd/system/workspace-ci-controller@research-engine-cpu.service.d/network.conf
  /etc/systemd/system/workspace-ci-controller@research-engine-gpu.service.d/network.conf
  /etc/systemd/system/workspace-ci-reconciler.service
  /etc/systemd/system/workspace-ci-reconcile-controller.service
  /etc/systemd/system/workspace-ci-reconcile-controller.service.d/network.conf
)

backup_target() {
  local target="$1" key prior
  key="$(printf '%s' "$target" | sha256sum | awk '{print $1}')"
  if [[ -e "$target" || -L "$target" ]]; then
    prior=PRESENT
    cp -a -- "$target" "$BACKUP/$key"
  else
    prior=ABSENT
  fi
  printf '%s\t%s\t%s\n' "$key" "$target" "$prior" >> "$BACKUP/index.tsv"
}

: > "$BACKUP/index.tsv"
for target in "${TARGETS[@]}"; do
  backup_target "$target"
done

OLD_RECON_USER=false
OLD_RECON_GROUP=false
getent passwd ci-reconciler >/dev/null && OLD_RECON_USER=true
getent group workspace-ci-reconciler >/dev/null && OLD_RECON_GROUP=true

for service in workspace-ci-provisioner.service workspace-ci-controller.service workspace-ci-controller-gpu.service; do
  enabled=NO; active=NO
  systemctl is-enabled --quiet "$service" 2>/dev/null && enabled=YES || true
  systemctl is-active --quiet "$service" 2>/dev/null && active=YES || true
  printf '%s\t%s\t%s\n' "$service" "$enabled" "$active" >> "$BACKUP/service-state.tsv"
done

rollback() {
  local rc="$?"
  trap - ERR
  echo "RUN3_ROLLBACK=BEGIN" >&2
  systemctl disable --now workspace-ci-reconcile-controller.service 2>/dev/null || true
  systemctl disable --now workspace-ci-reconciler.service 2>/dev/null || true
  systemctl disable --now workspace-ci-controller@research-engine-cpu.service 2>/dev/null || true
  systemctl disable --now workspace-ci-controller@research-engine-gpu.service 2>/dev/null || true
  systemctl stop workspace-ci-provisioner.service 2>/dev/null || true

  while IFS=$'\t' read -r key target prior; do
    [[ -n "$target" ]] || continue
    if [[ "$prior" == "PRESENT" ]]; then
      install -d -o root -g root -m 0755 "$(dirname "$target")"
      rm -rf -- "$target"
      cp -a -- "$BACKUP/$key" "$target"
    else
      rm -rf -- "$target"
    fi
  done < "$BACKUP/index.tsv"

  systemctl daemon-reload 2>/dev/null || true
  if [[ -f "$BACKUP/service-state.tsv" ]]; then
    while IFS=$'\t' read -r service enabled active; do
      if [[ "$enabled" == "YES" ]]; then systemctl enable "$service" 2>/dev/null || true; fi
      if [[ "$active" == "YES" ]]; then systemctl restart "$service" 2>/dev/null || true; fi
    done < "$BACKUP/service-state.tsv"
  fi

  if [[ "$OLD_RECON_USER" == "false" ]]; then
    userdel ci-reconciler 2>/dev/null || true
  fi
  if [[ "$OLD_RECON_GROUP" == "false" ]]; then
    groupdel workspace-ci-reconciler 2>/dev/null || true
  fi
  rm -rf /var/lib/workspace-ci/reconciler /var/lib/workspace-ci/reconcile-controller 2>/dev/null || true
  echo "RUN3_ROLLBACK=COMPLETE" >&2
  exit "$rc"
}
trap rollback ERR

# Freeze new GitHub job claims before any installed binary/config changes.
systemctl stop workspace-ci-controller.service workspace-ci-controller-gpu.service
if pgrep -u ci-research-engine >/dev/null 2>&1; then
  pgrep -a -u ci-research-engine >&2 || true
  die "RESEARCH_ENGINE_PROCESS_APPEARED_AFTER_CONTROLLER_FREEZE"
fi

if [[ "$OLD_RECON_GROUP" == "false" ]]; then
  groupadd --system workspace-ci-reconciler
fi
if [[ "$OLD_RECON_USER" == "false" ]]; then
  useradd --system --gid workspace-ci-reconciler --home-dir /var/lib/workspace-ci/reconcile-controller --shell /usr/sbin/nologin --no-create-home ci-reconciler
fi
[[ "$(id -nG ci-reconciler)" == "workspace-ci-reconciler" ]] || die "RECONCILER_GROUP_DRIFT"

install -d -o root -g root -m 0755   /opt/workspace-ci/controller   /opt/workspace-ci/provisioner   /opt/workspace-ci/reconciler   /opt/workspace-ci/reconcile-controller   /etc/workspace-ci   /etc/workspace-ci/projects   /etc/workspace-ci/controllers
install -d -o root -g root -m 0700 /var/lib/workspace-ci/reconciler
install -d -o ci-reconciler -g workspace-ci-reconciler -m 0700 /var/lib/workspace-ci/reconcile-controller
install -d -o root -g workspace-ci-controller -m 0750 /run/workspace-ci

BUILD_ROOT="$(mktemp -d)"
cp -a "$REPO_ROOT/controller/lambda-ci-controller/." "$BUILD_ROOT/"
chown -R ci-controller:workspace-ci-controller "$BUILD_ROOT"
runuser -u ci-controller -- env   HOME=/var/lib/workspace-ci/controller   GOCACHE="$BUILD_ROOT/.gocache"   GOMODCACHE="$BUILD_ROOT/.gomodcache"   "$GO_BIN" -C "$BUILD_ROOT" build -mod=mod -trimpath -o "$BUILD_ROOT/lambda-ci-controller" .
install -o root -g root -m 0755 "$BUILD_ROOT/lambda-ci-controller" /opt/workspace-ci/controller/lambda-ci-controller
rm -rf "$BUILD_ROOT"

install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_admission.py" /opt/workspace-ci/provisioner/lambda_ci_admission.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_multirepo.py" /opt/workspace-ci/provisioner/lambda_ci_multirepo.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_provisioner.py" /opt/workspace-ci/provisioner/lambda_ci_provisioner.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_provisioner_service.py" /opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_runtime.py" /opt/workspace-ci/provisioner/lambda_ci_runtime.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_multirepo.py" /opt/workspace-ci/reconciler/lambda_ci_multirepo.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_reconciler.py" /opt/workspace-ci/reconciler/lambda_ci_reconciler.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_reconcile_controller.py" /opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/stage_lambda_ci_reconciler_pat.sh" /opt/workspace-ci/reconcile-controller/stage-pat

install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-project-registry.v1.json" /etc/workspace-ci/lambda-ci-project-registry.v1.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-execution-contracts.v1.json" /etc/workspace-ci/lambda-ci-execution-contracts.v1.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-reconciliation-ceiling.v1.json" /etc/workspace-ci/lambda-ci-reconciliation-ceiling.v1.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-project-research-engine.v2.json" /etc/workspace-ci/projects/research-engine.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-project-padataset.v1.json" /etc/workspace-ci/projects/padataset.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-systemd-profiles.v1.json" /etc/workspace-ci/lambda-ci-systemd-profiles.v1.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-upstream-pins.v1.json" /etc/workspace-ci/lambda-ci-upstream-pins.v1.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-workload-policy.v1.json" /etc/workspace-ci/lambda-ci-workload-policy.v1.json

install -o root -g root -m 0644 "$REPO_ROOT/templates/lambda-ci/workspace-ci-provisioner-multirepo.service.in" /etc/systemd/system/workspace-ci-provisioner.service
install -o root -g root -m 0644 "$REPO_ROOT/templates/lambda-ci/workspace-ci-controller@.service.in" /etc/systemd/system/workspace-ci-controller@.service
install -o root -g root -m 0644 "$REPO_ROOT/systemd/workspace-ci-reconciler.service" /etc/systemd/system/workspace-ci-reconciler.service
install -o root -g root -m 0644 "$REPO_ROOT/systemd/workspace-ci-reconcile-controller.service" /etc/systemd/system/workspace-ci-reconcile-controller.service

PYTHONPATH="$REPO_ROOT/scripts" python3 - "$REPO_ROOT/architecture/lambda-ci-project-research-engine.v2.json" /tmp/research-engine-cpu.env /tmp/research-engine-gpu.env <<'PY'
import json, pathlib, sys
import lambda_ci_reconciler as r
m=json.loads(pathlib.Path(sys.argv[1]).read_text())
pathlib.Path(sys.argv[2]).write_text(r.render_controller_env(m,"cpu"))
pathlib.Path(sys.argv[3]).write_text(r.render_controller_env(m,"gpu"))
PY
install -o root -g root -m 0644 /tmp/research-engine-cpu.env /etc/workspace-ci/controllers/research-engine-cpu.env
install -o root -g root -m 0644 /tmp/research-engine-gpu.env /etc/workspace-ci/controllers/research-engine-gpu.env
rm -f /tmp/research-engine-cpu.env /tmp/research-engine-gpu.env

for lane in cpu gpu; do
  DROPIN="/etc/systemd/system/workspace-ci-controller@research-engine-$lane.service.d"
  install -d -o root -g root -m 0755 "$DROPIN"
  printf '[Service]\nIPAddressDeny=%s\n' "$LOCAL_SUBNET" > "$DROPIN/network.conf"
  chown root:root "$DROPIN/network.conf"
  chmod 0644 "$DROPIN/network.conf"
done
install -d -o root -g root -m 0755 /etc/systemd/system/workspace-ci-reconcile-controller.service.d
printf '[Service]\nIPAddressDeny=%s\n' "$LOCAL_SUBNET" > /etc/systemd/system/workspace-ci-reconcile-controller.service.d/network.conf
chown root:root /etc/systemd/system/workspace-ci-reconcile-controller.service.d/network.conf
chmod 0644 /etc/systemd/system/workspace-ci-reconcile-controller.service.d/network.conf

systemd-analyze verify   /etc/systemd/system/workspace-ci-provisioner.service   /etc/systemd/system/workspace-ci-controller@.service   /etc/systemd/system/workspace-ci-reconciler.service   /etc/systemd/system/workspace-ci-reconcile-controller.service

systemctl disable workspace-ci-controller.service workspace-ci-controller-gpu.service 2>/dev/null || true
systemctl stop workspace-ci-provisioner.service
systemctl daemon-reload

systemctl enable workspace-ci-provisioner.service workspace-ci-reconciler.service
systemctl restart workspace-ci-provisioner.service
systemctl restart workspace-ci-reconciler.service
systemctl enable workspace-ci-controller@research-engine-cpu.service workspace-ci-controller@research-engine-gpu.service
systemctl restart workspace-ci-controller@research-engine-cpu.service
systemctl restart workspace-ci-controller@research-engine-gpu.service

for service in   workspace-ci-provisioner.service   workspace-ci-reconciler.service   workspace-ci-controller@research-engine-cpu.service   workspace-ci-controller@research-engine-gpu.service
do
  systemctl is-active --quiet "$service" || die "POSTMIGRATION_SERVICE_NOT_ACTIVE:$service"
done

[[ -S /run/workspace-ci/provisioner.sock ]] || die "PROVISIONER_SOCKET_MISSING"
[[ "$(stat -c '%U:%G' /run/workspace-ci/provisioner.sock)" == "root:workspace-ci-controller" ]] || die "PROVISIONER_SOCKET_OWNER_DRIFT"
[[ "$(stat -c '%a' /run/workspace-ci/provisioner.sock)" == "660" ]] || die "PROVISIONER_SOCKET_MODE_DRIFT"
[[ -S /run/workspace-ci/reconciler.sock ]] || die "RECONCILER_SOCKET_MISSING"
[[ "$(stat -c '%U:%G' /run/workspace-ci/reconciler.sock)" == "root:workspace-ci-reconciler" ]] || die "RECONCILER_SOCKET_OWNER_DRIFT"
[[ "$(stat -c '%a' /run/workspace-ci/reconciler.sock)" == "660" ]] || die "RECONCILER_SOCKET_MODE_DRIFT"

getent passwd ci-padataset >/dev/null && die "PADATASET_USER_PREMATURELY_CREATED"
getent group ci-padataset >/dev/null && die "PADATASET_GROUP_PREMATURELY_CREATED"
[[ ! -e /srv/workspace-ci/padataset ]] || die "PADATASET_ROOT_PREMATURELY_CREATED"
[[ ! -e /etc/workspace-ci/controllers/padataset-cpu.env ]] || die "PADATASET_CPU_CONTROLLER_PREMATURELY_CREATED"
[[ ! -e /etc/workspace-ci/controllers/padataset-gpu.env ]] || die "PADATASET_GPU_CONTROLLER_PREMATURELY_CREATED"

python3 - "$OUT/lambda-ci-multirepo-run3-install.json" "$HEAD" "$LOCAL_SUBNET" "$INSTALL_MANIFEST" <<'PY'
import hashlib, json, pathlib, subprocess, sys
out=pathlib.Path(sys.argv[1]); head=sys.argv[2]; subnet=sys.argv[3]
install_manifest=json.loads(pathlib.Path(sys.argv[4]).read_text())
installed_paths=[
 "/opt/workspace-ci/controller/lambda-ci-controller",
 "/opt/workspace-ci/provisioner/lambda_ci_admission.py",
 "/opt/workspace-ci/provisioner/lambda_ci_multirepo.py",
 "/opt/workspace-ci/provisioner/lambda_ci_provisioner.py",
 "/opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py",
 "/opt/workspace-ci/provisioner/lambda_ci_runtime.py",
 "/opt/workspace-ci/reconciler/lambda_ci_multirepo.py",
 "/opt/workspace-ci/reconciler/lambda_ci_reconciler.py",
 "/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py",
 "/etc/workspace-ci/lambda-ci-project-registry.v1.json",
 "/etc/workspace-ci/lambda-ci-execution-contracts.v1.json",
 "/etc/workspace-ci/lambda-ci-reconciliation-ceiling.v1.json",
 "/etc/workspace-ci/projects/research-engine.json",
 "/etc/workspace-ci/projects/padataset.json",
]
def sha(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
 return h.hexdigest()
services={}
for name in [
 "workspace-ci-provisioner.service",
 "workspace-ci-reconciler.service",
 "workspace-ci-controller@research-engine-cpu.service",
 "workspace-ci-controller@research-engine-gpu.service",
]:
 p=subprocess.run(["systemctl","show",name,"--property=ActiveState,NRestarts,ExecMainStatus","--no-pager"],text=True,stdout=subprocess.PIPE,check=True)
 services[name]=dict(line.split("=",1) for line in p.stdout.splitlines() if "=" in line)
payload={
 "schema_version":1,
 "phase":"RUN3_MULTIREPO_INSTALL",
 "decision":"PASS",
 "workspace_control_sha":head,
 "source_blobs":install_manifest["source_blobs"],
 "installed_sha256":{p:sha(p) for p in installed_paths},
 "services":services,
 "controller_local_subnet_denied":subnet,
 "research_engine_generic_controllers_active":True,
 "reconciler_root_socket_active":True,
 "reconcile_controller_state":"INSTALLED_INACTIVE_CREDENTIAL_REQUIRED",
 "padataset_identity_created":False,
 "padataset_root_created":False,
 "padataset_controller_created":False,
 "rollback_directory":str(out.parent/"rollback"),
 "production_services_modified":False,
 "scientific_state_materialized":False,
}
out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
print(json.dumps(payload,indent=2,sort_keys=True))
PY

systemctl disable --now workspace-ci-reconcile-controller.service 2>/dev/null || true
chown -R "$INVOKER":"$(id -gn "$INVOKER")" "$OUT"
trap - ERR

echo "RUN3_MULTIREPO_INSTALL=PASS"
echo "RECEIPT=$OUT/lambda-ci-multirepo-run3-install.json"
echo "NEXT=Stage the dedicated workspace-control reconciliation token as ci-reconciler, then run scripts/activate_lambda_ci_reconcile_controller.sh via sudo from this exact checkout."
