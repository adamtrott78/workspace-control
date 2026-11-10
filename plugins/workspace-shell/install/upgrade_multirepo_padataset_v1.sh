#!/usr/bin/env bash
set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }

EXPECTED_UPGRADE_SHA="${1:-}"
EXPECTED_PAD_EXEC_SHA="${2:-17e1147614f27702e43565089d618182ff71c5af}"
PAD_EVIDENCE_ROOT="${PADATASET_CHECKOUT:-$HOME/adamArchives/Adam/varMax/PADataset}"
PAD_EXEC_REPO_URL="https://github.com/adamtrott78/PADataset.git"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/var/lib/workspace-shell/upgrades/padataset-multirepo-v1-${STAMP}"
EVIDENCE_MOUNT="/srv/workspace-shell/PADataset-evidence"
SERVICES=(workspace-shell-job-launcher.service workspace-shell-root-broker.service workspace-shell-mcp.service workspace-shell-tunnel.service)

[[ "$EXPECTED_UPGRADE_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "usage: bash upgrade_multirepo_padataset_v1.sh <expected-workspace-control-sha> [expected-padataset-execution-sha]"
[[ "$EXPECTED_PAD_EXEC_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "expected PADataset execution SHA must be full lowercase SHA"
[[ -d "$ROOT/.git" || -f "$ROOT/.git" ]] || fail "upgrade script must run from a workspace-control Git checkout"
[[ -d "$PAD_EVIDENCE_ROOT/.git" || -f "$PAD_EVIDENCE_ROOT/.git" ]] || fail "historical PADataset checkout not found at $PAD_EVIDENCE_ROOT"
command -v mountpoint >/dev/null || fail "mountpoint is required"
command -v findmnt >/dev/null || fail "findmnt is required"

UPGRADE_SHA="$(git -C "$ROOT" rev-parse HEAD)"
[[ "$UPGRADE_SHA" == "$EXPECTED_UPGRADE_SHA" ]] || fail "workspace-control HEAD $UPGRADE_SHA != expected $EXPECTED_UPGRADE_SHA"
[[ -z "$(git -C "$ROOT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "workspace-control upgrade checkout must be clean"

EVIDENCE_BRANCH="$(git -C "$PAD_EVIDENCE_ROOT" branch --show-current)"
EVIDENCE_SHA="$(git -C "$PAD_EVIDENCE_ROOT" rev-parse HEAD)"
EVIDENCE_STATUS="$(git -C "$PAD_EVIDENCE_ROOT" status --short)"
EVIDENCE_BYTES="$(du -sb "$PAD_EVIDENCE_ROOT" | awk '{print $1}')"

echo "Historical PADataset evidence checkout:"
echo "  path=$PAD_EVIDENCE_ROOT"
echo "  branch=${EVIDENCE_BRANCH:-DETACHED}"
echo "  HEAD=$EVIDENCE_SHA"
echo "  bytes=$EVIDENCE_BYTES"
if [[ -n "$EVIDENCE_STATUS" ]]; then
  echo "  status=DIRTY (preserved; no switch/reset/clean/stash/write)"
  printf '%s\n' "$EVIDENCE_STATUS"
else
  echo "  status=clean"
fi

if sudo mountpoint -q "$EVIDENCE_MOUNT"; then
  fail "$EVIDENCE_MOUNT is already a mountpoint; refusing to replace an unknown evidence mount"
fi

PAD_FETCH="$(mktemp -d /tmp/padataset-exec.XXXXXX)"
cleanup_tmp() {
  rm -rf "$PAD_FETCH" >/dev/null 2>&1 || true
}
trap cleanup_tmp EXIT

echo "Materializing clean PADataset execution source at exact SHA $EXPECTED_PAD_EXEC_SHA"
git clone --filter=blob:none --no-checkout "$PAD_EXEC_REPO_URL" "$PAD_FETCH"
git -C "$PAD_FETCH" checkout --detach "$EXPECTED_PAD_EXEC_SHA"
[[ "$(git -C "$PAD_FETCH" rev-parse HEAD)" == "$EXPECTED_PAD_EXEC_SHA" ]] || fail "clean PADataset execution checkout SHA mismatch"
[[ -z "$(git -C "$PAD_FETCH" status --porcelain=v1 --untracked-files=normal)" ]] || fail "clean PADataset execution checkout unexpectedly dirty"

mkdir -p "$PAD_FETCH/local_artifacts/evidence"
git -C "$PAD_EVIDENCE_ROOT" status --short > "$PAD_FETCH/local_artifacts/evidence_source_status.txt"
git -C "$PAD_EVIDENCE_ROOT" diff --no-ext-diff --binary > "$PAD_FETCH/local_artifacts/evidence_source_tracked.diff"
git -C "$PAD_EVIDENCE_ROOT" diff --cached --no-ext-diff --binary > "$PAD_FETCH/local_artifacts/evidence_source_index.diff"
export EVIDENCE_BRANCH EVIDENCE_SHA EVIDENCE_BYTES PAD_EVIDENCE_ROOT EXPECTED_PAD_EXEC_SHA
python3 - "$PAD_FETCH/local_artifacts/evidence_source.json" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

out = Path(sys.argv[1])
payload = {
    "schema": "workspace-shell-padataset-evidence-source.v1",
    "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    "historical_checkout_path": os.environ["PAD_EVIDENCE_ROOT"],
    "historical_branch": os.environ.get("EVIDENCE_BRANCH") or None,
    "historical_head": os.environ["EVIDENCE_SHA"],
    "historical_checkout_bytes": int(os.environ["EVIDENCE_BYTES"]),
    "execution_source_sha": os.environ["EXPECTED_PAD_EXEC_SHA"],
    "evidence_exposed_read_only": True,
    "historical_checkout_mutated": False,
}
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

# local_artifacts is ignored by PADataset; provenance files and the evidence
# mountpoint must not dirty the clean execution source.
[[ -z "$(git -C "$PAD_FETCH" status --porcelain=v1 --untracked-files=normal)" ]] || fail "ignored evidence metadata unexpectedly dirtied clean PADataset source"

sudo mkdir -p "$BACKUP"
sudo chmod 0700 "$BACKUP"

for p in \
  /srv/workspace-shell/workspace-control \
  /srv/workspace-shell/PADataset \
  /opt/workspace-shell/runtime/plugins/workspace-shell \
  /etc/workspace-shell/profiles.v1.json \
  /etc/workspace-shell/job-launcher.json \
  /etc/workspace-shell/broker-verifier.json; do
  if sudo test -e "$p"; then
    name="$(echo "$p" | sed 's#^/##; s#/#__#g')"
    sudo cp -a --reflink=auto "$p" "$BACKUP/$name"
  fi
done

EVIDENCE_MOUNT_CREATED=0
rollback() {
  rc=$?
  if [[ $rc -eq 0 ]]; then return; fi
  echo "Upgrade failed; attempting rollback from $BACKUP" >&2
  sudo systemctl stop "${SERVICES[@]}" >/dev/null 2>&1 || true

  if [[ "$EVIDENCE_MOUNT_CREATED" == "1" ]] && sudo mountpoint -q "$EVIDENCE_MOUNT"; then
    sudo umount "$EVIDENCE_MOUNT" >/dev/null 2>&1 || true
  fi

  restore() {
    local path="$1"
    local name
    name="$(echo "$path" | sed 's#^/##; s#/#__#g')"
    if sudo test -e "$BACKUP/$name"; then
      sudo rm -rf "$path"
      sudo mkdir -p "$(dirname "$path")"
      sudo cp -a "$BACKUP/$name" "$path"
    fi
  }

  restore /srv/workspace-shell/workspace-control
  restore /srv/workspace-shell/PADataset
  restore /opt/workspace-shell/runtime/plugins/workspace-shell
  restore /etc/workspace-shell/profiles.v1.json
  restore /etc/workspace-shell/job-launcher.json
  restore /etc/workspace-shell/broker-verifier.json

  sudo systemctl daemon-reload || true
  sudo systemctl start workspace-shell-job-launcher.service workspace-shell-root-broker.service workspace-shell-mcp.service workspace-shell-tunnel.service || true
  cleanup_tmp
  exit "$rc"
}
trap rollback EXIT

sudo systemctl stop workspace-shell-tunnel.service workspace-shell-mcp.service workspace-shell-root-broker.service workspace-shell-job-launcher.service

WC_NEXT="/srv/workspace-shell/workspace-control.next.$$"
PAD_NEXT="/srv/workspace-shell/PADataset.next.$$"
sudo rm -rf "$WC_NEXT" "$PAD_NEXT"
sudo mkdir -p "$WC_NEXT" "$PAD_NEXT"
sudo cp -a --reflink=auto "$ROOT/." "$WC_NEXT/"
sudo cp -a --reflink=auto "$PAD_FETCH/." "$PAD_NEXT/"
sudo chown -R root:root "$WC_NEXT" "$PAD_NEXT"
sudo chmod -R go-w "$WC_NEXT" "$PAD_NEXT"

[[ "$(sudo git -c safe.directory="$WC_NEXT" -C "$WC_NEXT" rev-parse HEAD)" == "$EXPECTED_UPGRADE_SHA" ]] || fail "workspace-control snapshot SHA mismatch"
[[ "$(sudo git -c safe.directory="$PAD_NEXT" -C "$PAD_NEXT" rev-parse HEAD)" == "$EXPECTED_PAD_EXEC_SHA" ]] || fail "PADataset execution snapshot SHA mismatch"
[[ -z "$(sudo git -c safe.directory="$PAD_NEXT" -C "$PAD_NEXT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "PADataset execution snapshot is not clean"

sudo rm -rf /srv/workspace-shell/workspace-control /srv/workspace-shell/PADataset
sudo mv "$WC_NEXT" /srv/workspace-shell/workspace-control
sudo mv "$PAD_NEXT" /srv/workspace-shell/PADataset

sudo mkdir -p "$EVIDENCE_MOUNT"
sudo chown root:root "$EVIDENCE_MOUNT"
sudo chmod 0755 "$EVIDENCE_MOUNT"
sudo mount --bind "$PAD_EVIDENCE_ROOT" "$EVIDENCE_MOUNT"
EVIDENCE_MOUNT_CREATED=1
sudo mount -o remount,bind,ro,nosuid,nodev,noexec "$EVIDENCE_MOUNT"
MOUNT_OPTIONS="$(sudo findmnt -n -o OPTIONS --target "$EVIDENCE_MOUNT")"
case ",$MOUNT_OPTIONS," in
  *,ro,*) ;;
  *) fail "PADataset evidence bind is not read-only: $MOUNT_OPTIONS" ;;
esac

sudo rm -rf /opt/workspace-shell/runtime/plugins/workspace-shell
sudo mkdir -p /opt/workspace-shell/runtime/plugins
sudo cp -a "$ROOT/plugins/workspace-shell" /opt/workspace-shell/runtime/plugins/workspace-shell
sudo chown -R root:root /opt/workspace-shell/runtime/plugins/workspace-shell
sudo chmod -R go-w /opt/workspace-shell/runtime/plugins/workspace-shell
sudo install -o root -g root -m 0644 "$ROOT/plugins/workspace-shell/config/profiles.v1.json" /etc/workspace-shell/profiles.v1.json

sudo python3 - <<'PY'
import json
from pathlib import Path

launcher = Path("/etc/workspace-shell/job-launcher.json")
data = json.loads(launcher.read_text())
roots = data.setdefault("source_roots", {})
roots["workspace-control"] = "/srv/workspace-shell/workspace-control"
roots["PADataset"] = "/srv/workspace-shell/PADataset"
evidence = data.setdefault("evidence_roots", {})
evidence["PADataset"] = "/srv/workspace-shell/PADataset-evidence"
tmp = launcher.with_suffix(launcher.suffix + ".tmp")
tmp.write_text(json.dumps(data, indent=2) + "\n")
tmp.chmod(0o600)
tmp.replace(launcher)

verifier = Path("/etc/workspace-shell/broker-verifier.json")
vdata = json.loads(verifier.read_text())
vroots = vdata.setdefault("source_roots", {})
vroots["workspace-control"] = "/srv/workspace-shell/workspace-control"
vroots["PADataset"] = "/srv/workspace-shell/PADataset"
vtmp = verifier.with_suffix(verifier.suffix + ".tmp")
vtmp.write_text(json.dumps(vdata, indent=2) + "\n")
vtmp.chmod(0o600)
vtmp.replace(verifier)
PY

sudo systemctl daemon-reload
sudo systemctl start workspace-shell-job-launcher.service
sudo systemctl start workspace-shell-root-broker.service
sudo systemctl start workspace-shell-mcp.service
sudo systemctl start workspace-shell-tunnel.service

for svc in "${SERVICES[@]}"; do
  sudo systemctl is-active --quiet "$svc" || fail "$svc is not active after upgrade"
done

echo "WORKSPACE_CONTROL_SNAPSHOT=$(sudo git -c safe.directory=/srv/workspace-shell/workspace-control -C /srv/workspace-shell/workspace-control rev-parse HEAD)"
echo "PADataset_EXECUTION_SNAPSHOT=$(sudo git -c safe.directory=/srv/workspace-shell/PADataset -C /srv/workspace-shell/PADataset rev-parse HEAD)"
echo "PADataset_EVIDENCE_BRANCH=${EVIDENCE_BRANCH:-DETACHED}"
echo "PADataset_EVIDENCE_HEAD=$EVIDENCE_SHA"
echo "PADataset_EVIDENCE_MOUNT_OPTIONS=$MOUNT_OPTIONS"
echo "WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS"
echo "Backup retained at: $BACKUP"
trap - EXIT
cleanup_tmp
