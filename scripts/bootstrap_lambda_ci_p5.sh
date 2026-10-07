#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

die() {
  echo "ERROR=$*" >&2
  exit 70
}

[[ "${EUID}" -eq 0 ]] || die "ROOT_REQUIRED"
[[ "${WORKSPACE_CI_P5_INSTALL_AUTHORIZED:-}" == "YES" ]] || die "P5_INSTALL_AUTHORIZATION_REQUIRED"
[[ -n "${WORKSPACE_CI_P5_EXPECTED_SHA:-}" ]] || die "EXPECTED_SHA_REQUIRED"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
GIT=(git -c "safe.directory=$REPO_ROOT" -C "$REPO_ROOT")
HEAD="$("${GIT[@]}" rev-parse HEAD)"
[[ "$HEAD" == "$WORKSPACE_CI_P5_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "WORKSPACE_CONTROL_DIRTY"

INVOKER="${SUDO_USER:-}"
[[ -n "$INVOKER" && "$INVOKER" != "root" ]] || die "RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT"
INVOKER_HOME="$(getent passwd "$INVOKER" | awk -F: '{print $6}')"
[[ -d "$INVOKER_HOME" ]] || die "INVOKER_HOME_NOT_FOUND"

for identity in ci-controller ci-research-engine; do
  getent passwd "$identity" >/dev/null || die "MISSING_IDENTITY:$identity"
done
getent group workspace-ci-controller >/dev/null || die "MISSING_GROUP:workspace-ci-controller"
[[ "$(id -nG ci-controller)" == "workspace-ci-controller" ]] || die "CONTROLLER_GROUP_DRIFT"
[[ "$(id -nG ci-research-engine)" == "ci-research-engine" ]] || die "PROJECT_GROUP_DRIFT"

GO_BIN=/opt/workspace-ci/go/1.26.3/bin/go
[[ -x "$GO_BIN" ]] || die "ISOLATED_GO_TOOLCHAIN_REQUIRED:/opt/workspace-ci/go/1.26.3"
GO_VERSION="$("$GO_BIN" env GOVERSION 2>/dev/null || true)"
[[ "$GO_VERSION" == "go1.26.3" ]] || die "ISOLATED_GO_VERSION_DRIFT:$GO_VERSION"

PRIMARY_DEV="$(ip -4 route get 1.1.1.1 | awk '{for (i=1;i<=NF;i++) if ($i=="dev") {print $(i+1); exit}}')"
LOCAL_SUBNET="$(ip -4 route show dev "$PRIMARY_DEV" proto kernel scope link | awk '$1 ~ /^[0-9]+\./ && $1 ~ /\// {print $1; exit}')"
[[ -n "$PRIMARY_DEV" && -n "$LOCAL_SUBNET" ]] || die "NETWORK_TOPOLOGY_UNRESOLVED"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$INVOKER_HOME/adamArchives/Adam/workspace-control-tmp/lambda-ci-p5-install-$STAMP"
mkdir -p "$OUT"
chmod 0700 "$OUT"
BACKUP="$OUT/rollback"
mkdir -p "$BACKUP"

TARGETS=(
  /opt/workspace-ci/controller/lambda-ci-controller
  /opt/workspace-ci/controller/stage-pat
  /opt/workspace-ci/provisioner/lambda_ci_admission.py
  /opt/workspace-ci/provisioner/lambda_ci_provisioner.py
  /opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py
  /opt/workspace-ci/provisioner/lambda_ci_runtime.py
  /opt/workspace-ci/cache-manager/lambda_ci_trusted_cache.py
  /etc/workspace-ci/projects/research-engine.json
  /etc/workspace-ci/lambda-ci-systemd-profiles.v1.json
  /etc/workspace-ci/lambda-ci-upstream-pins.v1.json
  /etc/workspace-ci/lambda-ci-workload-policy.v1.json
  /etc/systemd/system/workspace-ci-provisioner.service
  /etc/systemd/system/workspace-ci-controller.service
  /etc/systemd/system/workspace-ci-controller.service.d/network.conf
  /etc/systemd/system/workspace-ci-controller-gpu.service
  /etc/systemd/system/workspace-ci-controller-gpu.service.d/network.conf
)

backup_target() {
  local target="$1"
  local key
  key="$(printf '%s' "$target" | sha256sum | awk '{print $1}')"
  if [[ -e "$target" ]]; then
    cp -a -- "$target" "$BACKUP/$key"
    printf '%s\t%s\tPRESENT\n' "$key" "$target" >> "$BACKUP/index.tsv"
  else
    printf '%s\t%s\tABSENT\n' "$key" "$target" >> "$BACKUP/index.tsv"
  fi
}

rollback() {
  local rc=$?
  trap - ERR
  systemctl stop workspace-ci-controller-gpu.service 2>/dev/null || true
  systemctl stop workspace-ci-controller.service 2>/dev/null || true
  systemctl stop workspace-ci-provisioner.service 2>/dev/null || true
  if [[ -f "$BACKUP/index.tsv" ]]; then
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
  fi
  systemctl daemon-reload 2>/dev/null || true
  echo "P5_INSTALL_ROLLBACK=COMPLETE" >&2
  exit "$rc"
}
trap rollback ERR

: > "$BACKUP/index.tsv"
for target in "${TARGETS[@]}"; do
  backup_target "$target"
done

install -d -o root -g root -m 0755 /opt/workspace-ci/controller /opt/workspace-ci/provisioner /opt/workspace-ci/cache-manager
install -d -o root -g root -m 0700 /var/lib/workspace-ci/cache-manager /var/lib/workspace-ci/cache-manager/research-engine
install -d -o root -g root -m 0755 /srv/workspace-ci/research-engine/trusted-cache
install -d -o root -g root -m 0755 /etc/workspace-ci /etc/workspace-ci/projects
install -d -o root -g root -m 0700 /var/lib/workspace-ci/provisioner
install -d -o root -g workspace-ci-controller -m 0750 /run/workspace-ci
install -d -o ci-controller -g workspace-ci-controller -m 0700 /var/lib/workspace-ci/controller

BUILD_ROOT="$(mktemp -d)"
trap 'rm -rf "$BUILD_ROOT"' EXIT
cp -a "$REPO_ROOT/controller/lambda-ci-controller/." "$BUILD_ROOT/"
chown -R ci-controller:workspace-ci-controller "$BUILD_ROOT"

runuser -u ci-controller -- env \
  HOME=/var/lib/workspace-ci/controller \
  GOCACHE="$BUILD_ROOT/.gocache" \
  GOMODCACHE="$BUILD_ROOT/.gomodcache" \
  "$GO_BIN" -C "$BUILD_ROOT" build -mod=mod -trimpath -o "$BUILD_ROOT/lambda-ci-controller" .

install -o root -g root -m 0755 "$BUILD_ROOT/lambda-ci-controller" /opt/workspace-ci/controller/lambda-ci-controller
install -o root -g root -m 0755 "$REPO_ROOT/scripts/stage_lambda_ci_controller_pat.sh" /opt/workspace-ci/controller/stage-pat
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_admission.py" /opt/workspace-ci/provisioner/lambda_ci_admission.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_provisioner.py" /opt/workspace-ci/provisioner/lambda_ci_provisioner.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_provisioner_service.py" /opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_runtime.py" /opt/workspace-ci/provisioner/lambda_ci_runtime.py
install -o root -g root -m 0755 "$REPO_ROOT/scripts/lambda_ci_trusted_cache.py" /opt/workspace-ci/cache-manager/lambda_ci_trusted_cache.py

install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-project-research-engine.v1.json" /etc/workspace-ci/projects/research-engine.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-systemd-profiles.v1.json" /etc/workspace-ci/lambda-ci-systemd-profiles.v1.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-upstream-pins.v1.json" /etc/workspace-ci/lambda-ci-upstream-pins.v1.json
install -o root -g root -m 0644 "$REPO_ROOT/architecture/lambda-ci-workload-policy.v1.json" /etc/workspace-ci/lambda-ci-workload-policy.v1.json

install -o root -g root -m 0644 "$REPO_ROOT/systemd/workspace-ci-provisioner.service" /etc/systemd/system/workspace-ci-provisioner.service
install -o root -g root -m 0644 "$REPO_ROOT/systemd/workspace-ci-controller.service" /etc/systemd/system/workspace-ci-controller.service
install -o root -g root -m 0644 "$REPO_ROOT/systemd/workspace-ci-controller-gpu.service" /etc/systemd/system/workspace-ci-controller-gpu.service
install -d -o root -g root -m 0755 /etc/systemd/system/workspace-ci-controller.service.d
install -d -o root -g root -m 0755 /etc/systemd/system/workspace-ci-controller-gpu.service.d
cat > /etc/systemd/system/workspace-ci-controller.service.d/network.conf <<EOF
[Service]
IPAddressDeny=$LOCAL_SUBNET
EOF
chmod 0644 /etc/systemd/system/workspace-ci-controller.service.d/network.conf
chown root:root /etc/systemd/system/workspace-ci-controller.service.d/network.conf

cat > /etc/systemd/system/workspace-ci-controller-gpu.service.d/network.conf <<EOF
[Service]
IPAddressDeny=$LOCAL_SUBNET
EOF
chmod 0644 /etc/systemd/system/workspace-ci-controller-gpu.service.d/network.conf
chown root:root /etc/systemd/system/workspace-ci-controller-gpu.service.d/network.conf

systemd-analyze verify \
  /etc/systemd/system/workspace-ci-provisioner.service \
  /etc/systemd/system/workspace-ci-controller.service \
  /etc/systemd/system/workspace-ci-controller-gpu.service

if [[ -e /var/lib/workspace-ci/controller/github-token ]]; then
  TOKEN_OWNER="$(stat -c '%U:%G' /var/lib/workspace-ci/controller/github-token)"
  TOKEN_MODE="$(stat -c '%a' /var/lib/workspace-ci/controller/github-token)"
  [[ "$TOKEN_OWNER" == "ci-controller:workspace-ci-controller" ]] || die "CONTROLLER_TOKEN_OWNER:$TOKEN_OWNER"
  [[ "$TOKEN_MODE" == "600" ]] || die "CONTROLLER_TOKEN_MODE:$TOKEN_MODE"
  CREDENTIAL_READY=true
else
  CREDENTIAL_READY=false
fi

systemctl daemon-reload
systemctl enable workspace-ci-provisioner.service
systemctl restart workspace-ci-provisioner.service
systemctl is-active --quiet workspace-ci-provisioner.service || die "PROVISIONER_NOT_ACTIVE"

SOCKET=""
for _ in $(seq 1 50); do
  [[ -S /run/workspace-ci/provisioner.sock ]] && { SOCKET=/run/workspace-ci/provisioner.sock; break; }
  sleep 0.1
done
[[ "$SOCKET" == "/run/workspace-ci/provisioner.sock" ]] || die "PROVISIONER_SOCKET_NOT_READY"
[[ "$(stat -c '%U:%G' "$SOCKET")" == "root:workspace-ci-controller" ]] || die "SOCKET_OWNER_DRIFT"
[[ "$(stat -c '%a' "$SOCKET")" == "660" ]] || die "SOCKET_MODE_DRIFT"

if [[ "${WORKSPACE_CI_P5_ACTIVATE_CONTROLLER:-NO}" == "YES" ]]; then
  [[ "$CREDENTIAL_READY" == "true" ]] || die "CONTROLLER_CREDENTIAL_NOT_READY"
  systemctl enable workspace-ci-controller.service workspace-ci-controller-gpu.service
  systemctl restart workspace-ci-controller.service
  systemctl restart workspace-ci-controller-gpu.service
  systemctl is-active --quiet workspace-ci-controller.service || die "CONTROLLER_NOT_ACTIVE"
  systemctl is-active --quiet workspace-ci-controller-gpu.service || die "GPU_CONTROLLER_NOT_ACTIVE"
  CONTROLLER_STATE=ACTIVE
  GPU_CONTROLLER_STATE=ACTIVE
else
  systemctl disable --now workspace-ci-controller.service 2>/dev/null || true
  systemctl disable --now workspace-ci-controller-gpu.service 2>/dev/null || true
  CONTROLLER_STATE=INSTALLED_INACTIVE
  GPU_CONTROLLER_STATE=INSTALLED_INACTIVE
fi

python3 - "$OUT/lambda-ci-p5-install.json" "$HEAD" "$GO_VERSION" "$LOCAL_SUBNET" "$CREDENTIAL_READY" "$CONTROLLER_STATE" "$GPU_CONTROLLER_STATE" <<'PY'
import json, pathlib, sys
from datetime import datetime, timezone
path, head, go_version, subnet, credential_ready, controller_state, gpu_controller_state = sys.argv[1:]
payload = {
    "schema_version": 1,
    "phase": "P5-install",
    "decision": "PASS",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "workspace_control_sha": head,
    "go_version": go_version,
    "controller_binary": "/opt/workspace-ci/controller/lambda-ci-controller",
    "provisioner_service": "active",
    "controller_state": controller_state,
    "gpu_controller_state": gpu_controller_state,
    "cpu_scale_set": "lambda-research-engine",
    "gpu_scale_set": "lambda-research-engine-gpu",
    "controller_credential_ready": credential_ready == "true",
    "provisioner_socket": "/run/workspace-ci/provisioner.sock",
    "provisioner_socket_owner": "root:workspace-ci-controller",
    "provisioner_socket_mode": "0660",
    "controller_local_subnet_denied": subnet,
    "github_credential_handled_by_bootstrap": False,
    "production_services_modified": False,
}
pathlib.Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, indent=2, sort_keys=True))
PY

chown -R "$INVOKER":"$(id -gn "$INVOKER")" "$OUT"
trap - ERR
rm -rf "$BUILD_ROOT"

echo "P5_INSTALL=PASS"
echo "REPORT=$OUT/lambda-ci-p5-install.json"
if [[ "$CONTROLLER_STATE" == "INSTALLED_INACTIVE" ]]; then
  echo "NEXT=Run sudo -u ci-controller /opt/workspace-ci/controller/stage-pat, then rerun this bootstrap with WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES."
else
  echo "NEXT=Run autonomous scale-set acceptance; no manual runner launch is required."
fi
