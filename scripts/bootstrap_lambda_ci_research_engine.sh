#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

die() {
  echo "ERROR=$*" >&2
  exit 70
}

[[ "${EUID}" -eq 0 ]] || die "ROOT_REQUIRED"
[[ "${WORKSPACE_CI_P2_AUTHORIZED:-}" == "YES" ]] || die "P2_AUTHORIZATION_REQUIRED"
[[ -n "${WORKSPACE_CI_P2_EXPECTED_SHA:-}" ]] || die "EXPECTED_SHA_REQUIRED"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
GIT=(git -c "safe.directory=$REPO_ROOT" -C "$REPO_ROOT")

HEAD="$("${GIT[@]}" rev-parse HEAD)"
[[ "$HEAD" == "$WORKSPACE_CI_P2_EXPECTED_SHA" ]] || die "UNEXPECTED_WORKSPACE_CONTROL_SHA:$HEAD"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "WORKSPACE_CONTROL_DIRTY"

INVOKER="${SUDO_USER:-}"
[[ -n "$INVOKER" && "$INVOKER" != "root" ]] || die "RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT"
INVOKER_HOME="$(getent passwd "$INVOKER" | awk -F: '{print $6}')"
[[ -d "$INVOKER_HOME" ]] || die "INVOKER_HOME_NOT_FOUND"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$INVOKER_HOME/adamArchives/Adam/workspace-control-tmp/lambda-ci-p2-bootstrap-$STAMP"
mkdir -p "$OUT"
chmod 0700 "$OUT"

RUNNER_VERSION="2.337.0"
RUNNER_ASSET="actions-runner-linux-x64-2.337.0.tar.gz"
RUNNER_SHA256="70920811a4f8ad4328818682bca5c6469c1c942fab52448868071d0063816613"
RUNNER_URL="https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/$RUNNER_ASSET"
RUNNER_BASE="/opt/workspace-ci/actions-runner/$RUNNER_VERSION"
PROJECT_ROOT="/srv/workspace-ci/research-engine"
CONTROLLER_ROOT="/var/lib/workspace-ci/controller"

PRIMARY_DEV="$(ip -4 route get 1.1.1.1 | awk '{for (i=1;i<=NF;i++) if ($i=="dev") {print $(i+1); exit}}')"
PRIMARY_IP="$(ip -4 route get 1.1.1.1 | awk '{for (i=1;i<=NF;i++) if ($i=="src") {print $(i+1); exit}}')"
LOCAL_SUBNET="$(ip -4 route show dev "$PRIMARY_DEV" proto kernel scope link | awk '$1 ~ /^[0-9]+\./ && $1 ~ /\// {print $1; exit}')"
TAILSCALE_IP="$(ip -4 -br addr show tailscale0 2>/dev/null | awk '{split($3,a,"/"); print a[1]}' || true)"

[[ -n "$PRIMARY_DEV" && -n "$PRIMARY_IP" && -n "$LOCAL_SUBNET" ]] || die "NETWORK_TOPOLOGY_UNRESOLVED"

echo "=== P2 ROOT FIREWALL SNAPSHOT ===" | tee "$OUT/preflight.txt"
(nft list ruleset >"$OUT/nft-ruleset.txt" 2>"$OUT/nft-ruleset.err" || true)
(iptables-save >"$OUT/iptables-save.txt" 2>"$OUT/iptables-save.err" || true)
(ufw status verbose >"$OUT/ufw-status.txt" 2>"$OUT/ufw-status.err" || true)

echo "PRIMARY_DEV=$PRIMARY_DEV" | tee -a "$OUT/preflight.txt"
echo "PRIMARY_IP=$PRIMARY_IP" | tee -a "$OUT/preflight.txt"
echo "LOCAL_SUBNET=$LOCAL_SUBNET" | tee -a "$OUT/preflight.txt"
echo "TAILSCALE_IP=${TAILSCALE_IP:-<none>}" | tee -a "$OUT/preflight.txt"

UNIT_SUFFIX="$RANDOM-$$"

echo "=== P2 PROCESS/FILESYSTEM SANDBOX PROBE ===" | tee -a "$OUT/preflight.txt"
systemd-run --quiet --wait --collect --pipe   --unit="workspace-ci-p2-process-$UNIT_SUFFIX"   -p NoNewPrivileges=yes   -p CapabilityBoundingSet=   -p AmbientCapabilities=   -p RestrictSUIDSGID=yes   -p PrivateTmp=yes   -p ProtectSystem=strict   -p ProtectHome=yes   -p ProtectKernelTunables=yes   -p ProtectKernelModules=yes   -p ProtectKernelLogs=yes   -p ProtectControlGroups=yes   -p ProtectClock=yes   -p ProtectHostname=yes   -p RestrictRealtime=yes   -p LockPersonality=yes   -p ProtectProc=invisible   -p ProcSubset=pid   /bin/bash -ceu '
    test ! -r /home/atrott
    test ! -w /etc
    test ! -w /usr
    test ! -r /home/atrott/.ssh
    echo PROCESS_FILESYSTEM_SANDBOX=PASS
  ' | tee -a "$OUT/preflight.txt"

echo "=== P2 NETWORK SANDBOX PROBE ===" | tee -a "$OUT/preflight.txt"
NETWORK_PROPS=(
  -p "IPAddressAllow=127.0.0.53/32"
  -p "IPAddressDeny=127.0.0.0/8"
  -p "IPAddressDeny=::1/128"
  -p "IPAddressDeny=10.0.0.0/8"
  -p "IPAddressDeny=172.16.0.0/12"
  -p "IPAddressDeny=192.168.0.0/16"
  -p "IPAddressDeny=100.64.0.0/10"
  -p "IPAddressDeny=169.254.0.0/16"
  -p "IPAddressDeny=fe80::/10"
  -p "IPAddressDeny=fc00::/7"
  -p "IPAddressDeny=$LOCAL_SUBNET"
)
systemd-run --quiet --wait --collect --pipe   --unit="workspace-ci-p2-network-$UNIT_SUFFIX"   "${NETWORK_PROPS[@]}"   /bin/bash -ceu '
    host_ip="$1"
    tailscale_ip="$2"

    getent ahostsv4 github.com >/dev/null
    curl -fsS --max-time 15 https://api.github.com/meta >/dev/null

    if timeout 2 bash -c "</dev/tcp/127.0.0.1/5432" 2>/dev/null; then
      echo "LOCALHOST_POSTGRES_REACHABLE" >&2
      exit 41
    fi

    if timeout 2 bash -c "</dev/tcp/$host_ip/5432" 2>/dev/null; then
      echo "HOST_SUBNET_POSTGRES_REACHABLE" >&2
      exit 42
    fi

    if [[ -n "$tailscale_ip" ]] && timeout 2 bash -c "</dev/tcp/$tailscale_ip/443" 2>/dev/null; then
      echo "TAILSCALE_ENDPOINT_REACHABLE" >&2
      exit 43
    fi

    echo NETWORK_SANDBOX=PASS
  ' bash "$PRIMARY_IP" "$TAILSCALE_IP" | tee -a "$OUT/preflight.txt"

echo "=== P2 DEVICE DENY PROBE ===" | tee -a "$OUT/preflight.txt"
if systemd-run --quiet --wait --collect --pipe   --unit="workspace-ci-p2-device-deny-$UNIT_SUFFIX"   -p DevicePolicy=closed   /usr/bin/nvidia-smi -L >"$OUT/device-deny.out" 2>"$OUT/device-deny.err"
then
  die "DEVICE_POLICY_DID_NOT_BLOCK_NVIDIA"
fi
echo "DEVICE_DENY=PASS" | tee -a "$OUT/preflight.txt"

echo "=== P2 GPU0 NARROW ALLOW DIAGNOSTIC ===" | tee -a "$OUT/preflight.txt"
systemd-run --quiet --wait --collect --pipe   --unit="workspace-ci-p2-device-allow-$UNIT_SUFFIX"   -p DevicePolicy=closed   -p "DeviceAllow=/dev/nvidiactl rw"   -p "DeviceAllow=/dev/nvidia0 rw"   /usr/bin/nvidia-smi -i 0 --query-gpu=index,uuid,name --format=csv,noheader   | tee "$OUT/device-allow.out"
grep -q '^0,' "$OUT/device-allow.out" || die "GPU0_NARROW_ALLOW_FAILED"
echo "DEVICE_ALLOW_GPU0=PASS" | tee -a "$OUT/preflight.txt"

echo "P2_TRANSIENT_PREFLIGHT=PASS" | tee -a "$OUT/preflight.txt"

# Persistent mutation starts only after every transient isolation probe above passed.
getent group workspace-ci-controller >/dev/null || groupadd --system workspace-ci-controller
getent passwd ci-controller >/dev/null ||   useradd --system --gid workspace-ci-controller --home-dir "$CONTROLLER_ROOT"     --create-home --shell /usr/sbin/nologin ci-controller

getent group ci-research-engine >/dev/null || groupadd --system ci-research-engine
getent passwd ci-research-engine >/dev/null ||   useradd --system --gid ci-research-engine --home-dir "$PROJECT_ROOT/home"     --no-create-home --shell /usr/sbin/nologin ci-research-engine

CONTROLLER_GROUPS="$(id -nG ci-controller)"
PROJECT_GROUPS="$(id -nG ci-research-engine)"
[[ "$CONTROLLER_GROUPS" == "workspace-ci-controller" ]] || die "CONTROLLER_SUPPLEMENTARY_GROUPS:$CONTROLLER_GROUPS"
[[ "$PROJECT_GROUPS" == "ci-research-engine" ]] || die "PROJECT_SUPPLEMENTARY_GROUPS:$PROJECT_GROUPS"

install -d -o root -g root -m 0755 /opt/workspace-ci /opt/workspace-ci/actions-runner
install -d -o root -g workspace-ci-controller -m 0750 /run/workspace-ci
install -d -o ci-controller -g workspace-ci-controller -m 0700 "$CONTROLLER_ROOT"

install -d -o root -g ci-research-engine -m 0750 "$PROJECT_ROOT"
install -d -o ci-research-engine -g ci-research-engine -m 0700   "$PROJECT_ROOT/jobs" "$PROJECT_ROOT/staging-cache" "$PROJECT_ROOT/home"
install -d -o root -g root -m 0755 "$PROJECT_ROOT/trusted-cache"
install -d -o root -g ci-research-engine -m 0750 "$PROJECT_ROOT/logs"

TMP_ARCHIVE="$(mktemp)"
trap 'rm -f "$TMP_ARCHIVE"' EXIT
curl -fL --retry 3 --retry-delay 2 "$RUNNER_URL" -o "$TMP_ARCHIVE"
echo "$RUNNER_SHA256  $TMP_ARCHIVE" | sha256sum -c -

if [[ ! -x "$RUNNER_BASE/run.sh" ]]; then
  rm -rf "$RUNNER_BASE"
  install -d -o root -g root -m 0755 "$RUNNER_BASE"
  tar -xzf "$TMP_ARCHIVE" -C "$RUNNER_BASE"
  chown -R root:root "$RUNNER_BASE"
  chmod -R go-w "$RUNNER_BASE"
fi

[[ -x "$RUNNER_BASE/run.sh" ]] || die "RUNNER_BASE_INSTALL_FAILED"

install -o root -g root -m 0750 "$SCRIPT_DIR/lambda_ci_kill_switch.sh" /usr/local/sbin/workspace-ci-kill

runuser -u ci-research-engine -- /bin/bash -ceu '
  test ! -r /home/atrott
  test ! -w /etc
  test ! -r /home/atrott/adamArchives/Adam/workspace-control
  test ! -r /home/atrott/adamArchives/Adam/PADataset
  test -w /srv/workspace-ci/research-engine/jobs
  test -w /srv/workspace-ci/research-engine/staging-cache
  test ! -w /srv/workspace-ci/research-engine/trusted-cache
  if command -v sudo >/dev/null 2>&1; then
    ! sudo -n true >/dev/null 2>&1
  fi
  if [[ -e /var/run/docker.sock ]]; then
    test ! -r /var/run/docker.sock
    test ! -w /var/run/docker.sock
  fi
  echo PROJECT_IDENTITY_ISOLATION=PASS
' | tee -a "$OUT/preflight.txt"

GO_VERSION="$(go version 2>/dev/null || true)"
RUNNER_FILE_SHA="$(sha256sum "$TMP_ARCHIVE" | awk '{print $1}')"

python3 - "$OUT/lambda-ci-p2-bootstrap.json"   "$HEAD" "$PRIMARY_DEV" "$PRIMARY_IP" "$LOCAL_SUBNET" "$TAILSCALE_IP"   "$GO_VERSION" "$RUNNER_VERSION" "$RUNNER_FILE_SHA" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone

(
    report_path,
    head,
    primary_dev,
    primary_ip,
    local_subnet,
    tailscale_ip,
    go_version,
    runner_version,
    runner_sha,
) = sys.argv[1:]

payload = {
    "schema_version": 1,
    "phase": "P2-A",
    "decision": "PASS",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "workspace_control_sha": head,
    "transient_process_filesystem_probe": "PASS",
    "transient_network_probe": "PASS",
    "device_deny_probe": "PASS",
    "gpu0_narrow_allow_diagnostic": "PASS",
    "network": {
        "primary_device": primary_dev,
        "primary_ip": primary_ip,
        "local_subnet": local_subnet,
        "tailscale_ip": tailscale_ip or None,
    },
    "identities": {
        "controller": "ci-controller",
        "project": "ci-research-engine",
        "project_isolation": "PASS",
    },
    "runner_base": {
        "version": runner_version,
        "archive_sha256": runner_sha,
        "path": f"/opt/workspace-ci/actions-runner/{runner_version}",
    },
    "go_version": go_version,
    "runner_registered": False,
    "controller_service_installed": False,
    "production_services_modified": False,
    "firewall_rules_modified": False,
    "next_gate": "P2-B JIT one-job no-op runner",
}
pathlib.Path(report_path).write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, indent=2, sort_keys=True))
PY

chown -R "$INVOKER":"$(id -gn "$INVOKER")" "$OUT"

echo
echo "P2_A_BOOTSTRAP=PASS"
echo "REPORT=$OUT/lambda-ci-p2-bootstrap.json"
echo "NEXT=P2-B JIT one-job no-op runner; no runner has been registered yet."
