#!/usr/bin/env bash
set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }

EXPECTED_UPGRADE_SHA="${1:-}"
EXPECTED_PAD_SHA="${2:-17e1147614f27702e43565089d618182ff71c5af}"
PAD_ROOT="${PADATASET_CHECKOUT:-$HOME/adamArchives/Adam/varMax/PADataset}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/var/lib/workspace-shell/upgrades/padataset-multirepo-v1-${STAMP}"
SERVICES=(workspace-shell-job-launcher.service workspace-shell-root-broker.service workspace-shell-mcp.service workspace-shell-tunnel.service)

[[ "$EXPECTED_UPGRADE_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "usage: bash upgrade_multirepo_padataset_v1.sh <expected-workspace-control-sha> [expected-padataset-sha]"
[[ "$EXPECTED_PAD_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "expected PADataset SHA must be full lowercase SHA"
[[ -d "$ROOT/.git" || -f "$ROOT/.git" ]] || fail "upgrade script must run from a workspace-control Git checkout"
[[ -d "$PAD_ROOT/.git" || -f "$PAD_ROOT/.git" ]] || fail "PADataset checkout not found at $PAD_ROOT"

UPGRADE_SHA="$(git -C "$ROOT" rev-parse HEAD)"
[[ "$UPGRADE_SHA" == "$EXPECTED_UPGRADE_SHA" ]] || fail "workspace-control HEAD $UPGRADE_SHA != expected $EXPECTED_UPGRADE_SHA"
[[ -z "$(git -C "$ROOT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "workspace-control upgrade checkout must be clean"

PAD_BRANCH="$(git -C "$PAD_ROOT" branch --show-current)"
PAD_SHA="$(git -C "$PAD_ROOT" rev-parse HEAD)"
PAD_STATUS="$(git -C "$PAD_ROOT" status --short)"
[[ "$PAD_SHA" == "$EXPECTED_PAD_SHA" ]] || fail "PADataset HEAD $PAD_SHA != expected $EXPECTED_PAD_SHA; no runtime mutation performed"

echo "PADataset branch: ${PAD_BRANCH:-DETACHED}"
echo "PADataset HEAD: $PAD_SHA"
if [[ -n "$PAD_STATUS" ]]; then
  echo "PADataset tracked/untracked status before snapshot:"
  printf '%s\n' "$PAD_STATUS"
else
  echo "PADataset tracked/untracked status before snapshot: clean"
fi

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

rollback() {
  rc=$?
  if [[ $rc -eq 0 ]]; then return; fi
  echo "Upgrade failed; attempting rollback from $BACKUP" >&2
  sudo systemctl stop "${SERVICES[@]}" >/dev/null 2>&1 || true

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
  exit "$rc"
}
trap rollback EXIT

sudo systemctl stop workspace-shell-tunnel.service workspace-shell-mcp.service workspace-shell-root-broker.service workspace-shell-job-launcher.service

WC_NEXT="/srv/workspace-shell/workspace-control.next.$$"
PAD_NEXT="/srv/workspace-shell/PADataset.next.$$"
sudo rm -rf "$WC_NEXT" "$PAD_NEXT"
sudo mkdir -p "$WC_NEXT" "$PAD_NEXT"
sudo cp -a --reflink=auto "$ROOT/." "$WC_NEXT/"
sudo cp -a --reflink=auto "$PAD_ROOT/." "$PAD_NEXT/"
sudo chown -R root:root "$WC_NEXT" "$PAD_NEXT"
sudo chmod -R go-w "$WC_NEXT" "$PAD_NEXT"

[[ "$(sudo git -c safe.directory="$WC_NEXT" -C "$WC_NEXT" rev-parse HEAD)" == "$EXPECTED_UPGRADE_SHA" ]] || fail "workspace-control snapshot SHA mismatch"
[[ "$(sudo git -c safe.directory="$PAD_NEXT" -C "$PAD_NEXT" rev-parse HEAD)" == "$EXPECTED_PAD_SHA" ]] || fail "PADataset snapshot SHA mismatch"

sudo rm -rf /srv/workspace-shell/workspace-control /srv/workspace-shell/PADataset
sudo mv "$WC_NEXT" /srv/workspace-shell/workspace-control
sudo mv "$PAD_NEXT" /srv/workspace-shell/PADataset

sudo rm -rf /opt/workspace-shell/runtime/plugins/workspace-shell
sudo mkdir -p /opt/workspace-shell/runtime/plugins
sudo cp -a "$ROOT/plugins/workspace-shell" /opt/workspace-shell/runtime/plugins/workspace-shell
sudo chown -R root:root /opt/workspace-shell/runtime/plugins/workspace-shell
sudo chmod -R go-w /opt/workspace-shell/runtime/plugins/workspace-shell
sudo install -o root -g root -m 0644 "$ROOT/plugins/workspace-shell/config/profiles.v1.json" /etc/workspace-shell/profiles.v1.json

sudo python3 - <<'PY'
import json
from pathlib import Path

for raw in ("/etc/workspace-shell/job-launcher.json", "/etc/workspace-shell/broker-verifier.json"):
    p = Path(raw)
    data = json.loads(p.read_text())
    roots = data.setdefault("source_roots", {})
    roots["workspace-control"] = "/srv/workspace-shell/workspace-control"
    roots["PADataset"] = "/srv/workspace-shell/PADataset"
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.chmod(0o600)
    tmp.replace(p)
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
echo "PADataset_SNAPSHOT=$(sudo git -c safe.directory=/srv/workspace-shell/PADataset -C /srv/workspace-shell/PADataset rev-parse HEAD)"
echo "WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS"
echo "Backup retained at: $BACKUP"
trap - EXIT
