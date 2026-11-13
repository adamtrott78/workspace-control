#!/usr/bin/env bash
set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }

EXPECTED_OLD_AUTHORITY_SHA="${1:-}"
EXPECTED_NEW_AUTHORITY_SHA="${2:-}"
EXPECTED_OLD_PAD_SHA="${3:-}"
EXPECTED_NEW_PAD_SHA="${4:-}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AUTHORITY_ROOT="/etc/workspace-shell/authority"
PAD_ROOT="/srv/workspace-shell/PADataset"
TASK_REL="tasks/active/mth602-final-multisurrogate-dqnguard-v1.json"
TASK_MD_REL="tasks/active/mth602-final-multisurrogate-dqnguard-v1.md"
PAD_REPO_URL="https://github.com/adamtrott78/PADataset.git"
PAD_BRANCH="mth602-final-multisurrogate-dqnguard-v1"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/var/lib/workspace-shell/upgrades/padataset-checkpoint-${STAMP}"
SERVICES=(
  workspace-shell-job-launcher.service
  workspace-shell-root-broker.service
  workspace-shell-mcp.service
  workspace-shell-tunnel.service
)

for value in "$EXPECTED_OLD_AUTHORITY_SHA" "$EXPECTED_NEW_AUTHORITY_SHA" "$EXPECTED_OLD_PAD_SHA" "$EXPECTED_NEW_PAD_SHA"; do
  [[ "$value" =~ ^[0-9a-f]{40}$ ]] || fail "all four arguments must be full lowercase Git SHAs"
done
[[ "$EXPECTED_OLD_AUTHORITY_SHA" != "$EXPECTED_NEW_AUTHORITY_SHA" ]] || fail "authority SHA must advance"
[[ "$EXPECTED_OLD_PAD_SHA" != "$EXPECTED_NEW_PAD_SHA" ]] || fail "PADataset SHA must advance"
[[ -d "$ROOT/.git" || -f "$ROOT/.git" ]] || fail "operator must run from a workspace-control Git checkout"
command -v git >/dev/null || fail "git is required"
command -v python3 >/dev/null || fail "python3 is required"

NEW_AUTHORITY_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
[[ "$NEW_AUTHORITY_HEAD" == "$EXPECTED_NEW_AUTHORITY_SHA" ]] || fail "operator checkout HEAD mismatch"
[[ -z "$(git -C "$ROOT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "operator checkout must be clean"
git -C "$ROOT" merge-base --is-ancestor "$EXPECTED_OLD_AUTHORITY_SHA" "$EXPECTED_NEW_AUTHORITY_SHA"   || fail "new authority state is not descended from installed authority state"

python3 - "$ROOT/$TASK_REL" "$EXPECTED_NEW_PAD_SHA" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
expected = sys.argv[2]
data = json.loads(path.read_text(encoding="utf-8"))
if data.get("task_id") != "mth602-final-multisurrogate-dqnguard-v1":
    raise SystemExit("candidate task_id mismatch")
if data.get("status") != "IN_PROGRESS":
    raise SystemExit("candidate task is not IN_PROGRESS")
repos = [r for r in data.get("repositories", []) if r.get("name") == "PADataset"]
if len(repos) != 1:
    raise SystemExit("candidate PADataset repository binding must be unique")
actual = (repos[0].get("remote") or {}).get("checkpoint_sha")
if actual != expected:
    raise SystemExit(f"candidate checkpoint {actual} != expected {expected}")
print("CANDIDATE_TASK_BINDING=PASS")
PY

LIVE_AUTHORITY_HEAD="$(sudo git -c safe.directory="$AUTHORITY_ROOT" -C "$AUTHORITY_ROOT" rev-parse HEAD)"
[[ "$LIVE_AUTHORITY_HEAD" == "$EXPECTED_OLD_AUTHORITY_SHA" ]]   || fail "live authority HEAD $LIVE_AUTHORITY_HEAD != expected old authority $EXPECTED_OLD_AUTHORITY_SHA"
[[ -z "$(sudo git -c safe.directory="$AUTHORITY_ROOT" -C "$AUTHORITY_ROOT" status --porcelain=v1 --untracked-files=normal)" ]]   || fail "live authority snapshot is dirty"

sudo python3 - "$AUTHORITY_ROOT/$TASK_REL" "$EXPECTED_OLD_PAD_SHA" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
expected = sys.argv[2]
data = json.loads(path.read_text(encoding="utf-8"))
repos = [r for r in data.get("repositories", []) if r.get("name") == "PADataset"]
if len(repos) != 1:
    raise SystemExit("live PADataset repository binding must be unique")
actual = (repos[0].get("remote") or {}).get("checkpoint_sha")
if actual != expected:
    raise SystemExit(f"live checkpoint {actual} != expected old {expected}")
print("LIVE_TASK_BINDING=PASS")
PY

LIVE_PAD_HEAD="$(sudo git -c safe.directory="$PAD_ROOT" -C "$PAD_ROOT" rev-parse HEAD)"
[[ "$LIVE_PAD_HEAD" == "$EXPECTED_OLD_PAD_SHA" ]]   || fail "live PADataset HEAD $LIVE_PAD_HEAD != expected old PADataset $EXPECTED_OLD_PAD_SHA"
[[ -z "$(sudo git -c safe.directory="$PAD_ROOT" -C "$PAD_ROOT" status --porcelain=v1 --untracked-files=normal)" ]]   || fail "live PADataset execution snapshot is dirty"

TMP="$(mktemp -d /tmp/workspace-shell-pad-refresh.XXXXXX)"
AUTH_NEXT="$TMP/authority-next"
PAD_FETCH="$TMP/padataset-fetch"
cleanup_tmp() { rm -rf "$TMP" >/dev/null 2>&1 || true; }
trap cleanup_tmp EXIT

git clone --no-hardlinks --no-checkout "$ROOT" "$AUTH_NEXT"
git -C "$AUTH_NEXT" checkout --detach "$EXPECTED_NEW_AUTHORITY_SHA"
[[ "$(git -C "$AUTH_NEXT" rev-parse HEAD)" == "$EXPECTED_NEW_AUTHORITY_SHA" ]] || fail "prepared authority SHA mismatch"
[[ -z "$(git -C "$AUTH_NEXT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "prepared authority snapshot is dirty"

git clone --filter=blob:none --no-checkout "$PAD_REPO_URL" "$PAD_FETCH"
git -C "$PAD_FETCH" fetch origin "$PAD_BRANCH:refs/remotes/origin/$PAD_BRANCH"
REMOTE_PAD_HEAD="$(git -C "$PAD_FETCH" rev-parse "origin/$PAD_BRANCH")"
[[ "$REMOTE_PAD_HEAD" == "$EXPECTED_NEW_PAD_SHA" ]]   || fail "remote PADataset branch head $REMOTE_PAD_HEAD != expected $EXPECTED_NEW_PAD_SHA"
git -C "$PAD_FETCH" checkout --detach "$EXPECTED_NEW_PAD_SHA"
git -C "$PAD_FETCH" merge-base --is-ancestor "$EXPECTED_OLD_PAD_SHA" "$EXPECTED_NEW_PAD_SHA"   || fail "new PADataset candidate is not descended from installed source"
[[ -z "$(git -C "$PAD_FETCH" status --porcelain=v1 --untracked-files=normal)" ]] || fail "prepared PADataset snapshot is dirty"

sudo mkdir -p "$BACKUP"
sudo chmod 0700 "$BACKUP"
sudo cp -a --reflink=auto "$AUTHORITY_ROOT" "$BACKUP/authority"
sudo cp -a --reflink=auto "$PAD_ROOT" "$BACKUP/PADataset"

MUTATION_STARTED=0
rollback() {
  rc="$1"
  if [[ "$rc" -eq 0 ]]; then
    cleanup_tmp
    return
  fi
  if [[ "$MUTATION_STARTED" != "1" ]]; then
    cleanup_tmp
    return
  fi
  echo "Checkpoint refresh failed; rolling back from $BACKUP" >&2
  sudo systemctl stop "${SERVICES[@]}" >/dev/null 2>&1 || true
  sudo rm -rf "$AUTHORITY_ROOT" "$PAD_ROOT"
  sudo cp -a "$BACKUP/authority" "$AUTHORITY_ROOT"
  sudo cp -a "$BACKUP/PADataset" "$PAD_ROOT"
  sudo systemctl start workspace-shell-job-launcher.service workspace-shell-root-broker.service workspace-shell-mcp.service workspace-shell-tunnel.service || true
  cleanup_tmp
  exit "$rc"
}
trap 'rollback "$?"' EXIT

MUTATION_STARTED=1
sudo systemctl stop workspace-shell-tunnel.service workspace-shell-mcp.service workspace-shell-root-broker.service workspace-shell-job-launcher.service

sudo rm -rf "$AUTHORITY_ROOT" "$PAD_ROOT"
sudo cp -a --reflink=auto "$AUTH_NEXT" "$AUTHORITY_ROOT"
sudo cp -a --reflink=auto "$PAD_FETCH" "$PAD_ROOT"
sudo chown -R root:root "$AUTHORITY_ROOT" "$PAD_ROOT"
sudo chmod -R a+rX,go-w "$AUTHORITY_ROOT" "$PAD_ROOT"

[[ "$(sudo git -c safe.directory="$AUTHORITY_ROOT" -C "$AUTHORITY_ROOT" rev-parse HEAD)" == "$EXPECTED_NEW_AUTHORITY_SHA" ]]   || fail "installed authority SHA mismatch after swap"
[[ "$(sudo git -c safe.directory="$PAD_ROOT" -C "$PAD_ROOT" rev-parse HEAD)" == "$EXPECTED_NEW_PAD_SHA" ]]   || fail "installed PADataset SHA mismatch after swap"
[[ -z "$(sudo git -c safe.directory="$AUTHORITY_ROOT" -C "$AUTHORITY_ROOT" status --porcelain=v1 --untracked-files=normal)" ]]   || fail "installed authority snapshot is dirty after swap"
[[ -z "$(sudo git -c safe.directory="$PAD_ROOT" -C "$PAD_ROOT" status --porcelain=v1 --untracked-files=normal)" ]]   || fail "installed PADataset snapshot is dirty after swap"

sudo python3 - "$AUTHORITY_ROOT/$TASK_REL" "$EXPECTED_NEW_PAD_SHA" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = sys.argv[2]
repo = next((r for r in data.get("repositories", []) if r.get("name") == "PADataset"), None)
actual = ((repo or {}).get("remote") or {}).get("checkpoint_sha")
if actual != expected:
    raise SystemExit(f"installed checkpoint {actual} != expected {expected}")
print("INSTALLED_TASK_BINDING=PASS")
PY

sudo systemctl start workspace-shell-job-launcher.service workspace-shell-root-broker.service workspace-shell-mcp.service workspace-shell-tunnel.service
for unit in "${SERVICES[@]}"; do
  [[ "$(sudo systemctl is-active "$unit")" == "active" ]] || fail "$unit is not active after refresh"
done

MUTATION_STARTED=0
trap cleanup_tmp EXIT

echo "OLD_AUTHORITY_SHA=$EXPECTED_OLD_AUTHORITY_SHA"
echo "NEW_AUTHORITY_SHA=$EXPECTED_NEW_AUTHORITY_SHA"
echo "OLD_PAD_SHA=$EXPECTED_OLD_PAD_SHA"
echo "NEW_PAD_SHA=$EXPECTED_NEW_PAD_SHA"
echo "BACKUP=$BACKUP"
echo "PADATASET_CHECKPOINT_REFRESH=PASS"
