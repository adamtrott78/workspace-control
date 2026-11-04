#!/usr/bin/env bash
set -Eeuo pipefail

# Transactional boot-persistence update for the already accepted live
# Workspace Shell recovery plane. This changes only:
# - /etc/tmpfiles.d/workspace-shell.conf
# - /opt/workspace-shell/bin/workspace-shell-disable
# - boot enablement of the four existing Workspace Shell units
#
# It does not change MCP schema, runtime code, TLS/tunnel identities, helper
# authority, trusted issuers, credentials, GitRunner state, or v3 services.

ACCEPTED_OBSERVABILITY_HEAD="98ce61aad8addd604f93e7a04876eaefd0989589"
TMPFILES_BLOB="7d873c16bb1be1776a41db0ddcb88dad97abc6ff"
DISABLE_BLOB="a71be010885e5144fdff99e33ddcbaf4b4f56c5b"
OLD_DISABLE_SHA256="d7ff9174ddaec5bc17cdb3a85f3a7ae09db0fff489875e5436d1ac2387c8fb00"
NEW_DISABLE_SHA256="19d19fdb22450b46f568be472731df461b8b3b39ddf252dfb3efbb3c3a0090e6"

EXPECTED_HEAD="${1:-}"
CONFIRM="${WORKSPACE_SHELL_BOOT_RECOVERY_CONFIRM:-}"
ROOT="$(git rev-parse --show-toplevel)"

TMPFILES_SRC="$ROOT/plugins/workspace-shell/install/tmpfiles.conf"
TMPFILES_DST="/etc/tmpfiles.d/workspace-shell.conf"
DISABLE_SRC="$ROOT/plugins/workspace-shell/install/workspace-shell-disable.sh"
DISABLE_DST="/opt/workspace-shell/bin/workspace-shell-disable"
UPDATE_ROOT="/var/lib/workspace-shell/updates/${EXPECTED_HEAD}/boot-recovery"

SERVICES=(
  workspace-shell-job-launcher.service
  workspace-shell-root-broker.service
  workspace-shell-mcp.service
  workspace-shell-tunnel.service
)

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

require_sha() {
  [[ "$1" =~ ^[0-9a-f]{40}$ ]] || fail "$2 must be a full lowercase Git SHA"
}

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

git_blob_file() {
  git hash-object "$1"
}

service_active() {
  [ "$(systemctl is-active "$1" 2>/dev/null || true)" = "active" ]
}

service_disabled() {
  [ "$(systemctl is-enabled "$1" 2>/dev/null || true)" != "enabled" ]
}

service_enabled() {
  [ "$(systemctl is-enabled "$1" 2>/dev/null || true)" = "enabled" ]
}

[ "$(id -u)" -eq 0 ] || fail "must run as root"
[ -n "$EXPECTED_HEAD" ] || fail "usage: $0 <exact-validated-head>"
require_sha "$EXPECTED_HEAD" expected_head
[ "$CONFIRM" = "ENABLE_BOOT_RECOVERY_V1" ] \
  || fail "set WORKSPACE_SHELL_BOOT_RECOVERY_CONFIRM=ENABLE_BOOT_RECOVERY_V1"

cd "$ROOT"
[ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
  || fail "operator checkout HEAD does not match expected head"
[ -z "$(git status --porcelain=v1 --untracked-files=normal)" ] \
  || fail "operator checkout is dirty"
git merge-base --is-ancestor "$ACCEPTED_OBSERVABILITY_HEAD" "$EXPECTED_HEAD" \
  || fail "candidate does not descend from accepted observability head"

[ "$(git_blob_file "$TMPFILES_SRC")" = "$TMPFILES_BLOB" ] \
  || fail "candidate tmpfiles blob mismatch"
[ "$(git_blob_file "$DISABLE_SRC")" = "$DISABLE_BLOB" ] \
  || fail "candidate emergency-disable blob mismatch"

for svc in "${SERVICES[@]}"; do
  service_active "$svc" || fail "$svc is not active before boot-persistence update"
  service_disabled "$svc" || fail "$svc is already boot-enabled"
done

[ "$(stat -c '%U:%G:%a' /run/workspace-shell-control)" = "root:workspace-shell-mcp:750" ] \
  || fail "runtime control root metadata does not match accepted live state"
[ ! -e "$TMPFILES_DST" ] || fail "persistent Workspace Shell tmpfiles rule already exists"
[ -f "$DISABLE_DST" ] && [ ! -L "$DISABLE_DST" ] \
  || fail "installed emergency-disable helper is missing or symlinked"
[ "$(sha256_file "$DISABLE_DST")" = "$OLD_DISABLE_SHA256" ] \
  || fail "installed emergency-disable helper does not match reviewed boot-disabled prestate"

[ ! -e "$UPDATE_ROOT" ] || fail "update receipt directory already exists"
install -d -o root -g root -m 0700 "$UPDATE_ROOT"
install -d -o root -g root -m 0700 "$UPDATE_ROOT/backup"
cp -a "$DISABLE_DST" "$UPDATE_ROOT/backup/workspace-shell-disable"
chmod 0755 "$UPDATE_ROOT/backup/workspace-shell-disable"

MUTATION_STARTED=0
COMMITTED=0

rollback() {
  local rc="$?"
  trap - EXIT
  if [ "$MUTATION_STARTED" = "1" ] && [ "$COMMITTED" != "1" ]; then
    echo "=== WORKSPACE SHELL BOOT RECOVERY UPDATE: ROLLBACK ===" >&2
    for svc in "${SERVICES[@]}"; do
      systemctl disable "$svc" >/dev/null 2>&1 || true
    done
    rm -f "$TMPFILES_DST"
    install -o root -g root -m 0755 \
      "$UPDATE_ROOT/backup/workspace-shell-disable" "$DISABLE_DST" || true
    python3 - "$UPDATE_ROOT/rollback-receipt.json" "$EXPECTED_HEAD" "$rc" <<'PY'
import json, sys
from datetime import datetime, timezone
path, head, rc = sys.argv[1:]
payload = {
    "schema": "workspace-shell-boot-recovery-update-rollback.v1",
    "status": "ROLLED_BACK",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "expected_head": head,
    "failed_exit_code": int(rc),
}
open(path, "w", encoding="utf-8").write(
    json.dumps(payload, indent=2, sort_keys=True) + "\n"
)
PY
  fi
  exit "$rc"
}
trap rollback EXIT

echo "=== WORKSPACE SHELL BOOT RECOVERY UPDATE: APPLY ==="
MUTATION_STARTED=1

install -o root -g root -m 0644 "$TMPFILES_SRC" "$TMPFILES_DST"
systemd-tmpfiles --create "$TMPFILES_DST"
[ "$(stat -c '%U:%G:%a' /run/workspace-shell-control)" = "root:workspace-shell-mcp:750" ] \
  || fail "persistent tmpfiles rule produced wrong runtime-control metadata"

install -o root -g root -m 0755 "$DISABLE_SRC" "$DISABLE_DST"
[ "$(sha256_file "$DISABLE_DST")" = "$NEW_DISABLE_SHA256" ] \
  || fail "emergency-disable helper install mismatch"

systemctl enable "${SERVICES[@]}" >/dev/null
for svc in "${SERVICES[@]}"; do
  service_active "$svc" || fail "$svc stopped during boot-persistence update"
  service_enabled "$svc" || fail "$svc was not enabled at boot"
done

sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 3 \
  --cacert /etc/workspace-shell/tunnel/ca.crt \
  --cert /etc/workspace-shell/tunnel/client.crt \
  --key /etc/workspace-shell/tunnel/client.key \
  https://127.0.0.1:8797/healthz >/dev/null \
  || fail "local Workspace Shell mTLS health failed after boot enablement"

HEALTH_URL="$(cat /var/lib/workspace-shell/tunnel/health.url 2>/dev/null || true)"
[ -n "$HEALTH_URL" ] || fail "tunnel health URL is missing"
curl -fsS --max-time 3 "$HEALTH_URL/readyz" >/dev/null \
  || fail "Workspace Shell tunnel is not ready after boot enablement"

python3 - "$UPDATE_ROOT/receipt.json" "$EXPECTED_HEAD" "$HEALTH_URL" <<'PY'
import json, sys
from datetime import datetime, timezone
path, head, health = sys.argv[1:]
payload = {
    "schema": "workspace-shell-boot-recovery-update.v1",
    "status": "PASS",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "validated_head": head,
    "persistent_tmpfiles": "/etc/tmpfiles.d/workspace-shell.conf",
    "runtime_control_root": "/run/workspace-shell-control",
    "services": [
        "workspace-shell-job-launcher.service",
        "workspace-shell-root-broker.service",
        "workspace-shell-mcp.service",
        "workspace-shell-tunnel.service",
    ],
    "boot_enabled": True,
    "runtime_services_restarted": False,
    "helper_authority_changed": False,
    "mcp_schema_changed": False,
    "tunnel_health_url": health,
}
open(path, "w", encoding="utf-8").write(
    json.dumps(payload, indent=2, sort_keys=True) + "\n"
)
PY

COMMITTED=1
trap - EXIT
echo "WORKSPACE_SHELL_BOOT_RECOVERY_UPDATE=PASS"
echo "VALIDATED_HEAD=$EXPECTED_HEAD"
echo "TMPFILES_RULE=$TMPFILES_DST"
echo "UPDATE_RECEIPT=$UPDATE_ROOT/receipt.json"
echo "SERVICES_ACTIVE_BOOT_ENABLED=PASS"
