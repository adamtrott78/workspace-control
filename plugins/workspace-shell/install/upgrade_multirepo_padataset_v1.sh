#!/usr/bin/env bash
set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }

git_retry() {
  local attempt rc
  for attempt in 1 2 3 4 5; do
    if "$@"; then
      return 0
    fi
    rc=$?
    echo "Git operation failed (attempt $attempt/5, rc=$rc); retrying..." >&2
    sleep $((attempt * 2))
  done
  return "$rc"
}

EXPECTED_AUTHORITY_SHA="${1:-}"
EXPECTED_EXEC_SHA="${2:-}"
EXPECTED_PAD_EXEC_SHA="${3:-}"
EXPECTED_SEMANTIC_CAPSULE_SHA="${4:-}"
EXPECTED_SEMANTIC_EXEC_SHA="${5:-}"
SEMANTIC_TASK_ID="workspace-semantic-execution-migration-v1"
SEMANTIC_TASK_REL="tasks/active/${SEMANTIC_TASK_ID}.json"
PAD_EVIDENCE_ROOT="${PADATASET_CHECKOUT:-$HOME/adamArchives/Adam/varMax/PADataset}"
PAD_EXEC_REPO_URL="https://github.com/adamtrott78/PADataset.git"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/var/lib/workspace-shell/upgrades/padataset-multirepo-v1-${STAMP}"
AUTHORITY_ROOT="/etc/workspace-shell/authority"
EVIDENCE_MOUNT="/srv/workspace-shell/PADataset-evidence"
EVALUATOR_SEALED_ROOT="/var/lib/workspace-shell/evaluator-sealed"
EVALUATOR_DENIAL_SENTINEL="$EVALUATOR_SEALED_ROOT/worker-denial-probe"
BASE_SERVICES=(workspace-shell-job-launcher.service workspace-shell-root-broker.service workspace-shell-mcp.service workspace-shell-tunnel.service)
SERVICES=(workspace-shell-candidate-materializer.service "${BASE_SERVICES[@]}")

[[ "$EXPECTED_AUTHORITY_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "usage: bash upgrade_multirepo_padataset_v1.sh <expected-authority-sha> <expected-workspace-control-exec-sha> <expected-padataset-execution-sha>"
[[ "$EXPECTED_EXEC_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "expected workspace-control execution SHA must be full lowercase SHA"
[[ "$EXPECTED_PAD_EXEC_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "expected PADataset execution SHA must be full lowercase SHA"
if [[ -n "$EXPECTED_SEMANTIC_CAPSULE_SHA" || -n "$EXPECTED_SEMANTIC_EXEC_SHA" ]]; then
  [[ -n "$EXPECTED_SEMANTIC_CAPSULE_SHA" && -n "$EXPECTED_SEMANTIC_EXEC_SHA" ]] \
    || fail "semantic authority enrollment requires both capsule SHA and execution SHA"
  [[ "$EXPECTED_SEMANTIC_CAPSULE_SHA" =~ ^[0-9a-f]{40}$ ]] \
    || fail "semantic capsule SHA must be full lowercase SHA"
  [[ "$EXPECTED_SEMANTIC_EXEC_SHA" =~ ^[0-9a-f]{40}$ ]] \
    || fail "semantic execution SHA must be full lowercase SHA"
fi
[[ -d "$ROOT/.git" || -f "$ROOT/.git" ]] || fail "upgrade script must run from a workspace-control Git checkout"
[[ -d "$PAD_EVIDENCE_ROOT/.git" || -f "$PAD_EVIDENCE_ROOT/.git" ]] || fail "historical PADataset checkout not found at $PAD_EVIDENCE_ROOT"
command -v mountpoint >/dev/null || fail "mountpoint is required"
command -v findmnt >/dev/null || fail "findmnt is required"
command -v python3 >/dev/null || fail "python3 is required"

AUTHORITY_SHA="$(git -C "$ROOT" rev-parse HEAD)"
[[ "$AUTHORITY_SHA" == "$EXPECTED_AUTHORITY_SHA" ]] || fail "workspace-control authority HEAD $AUTHORITY_SHA != expected $EXPECTED_AUTHORITY_SHA"
[[ -z "$(git -C "$ROOT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "workspace-control authority checkout must be clean"

LIVE_AUTHORITY_ROOT="$(sudo python3 - <<'PY'
import json
from pathlib import Path
cfg = json.loads(Path("/etc/workspace-shell/frontend.json").read_text(encoding="utf-8"))
value = cfg.get("authority_root")
if not isinstance(value, str) or not value:
    raise SystemExit("frontend authority_root missing")
print(value)
PY
)"
[[ "$LIVE_AUTHORITY_ROOT" == "$AUTHORITY_ROOT" ]] || fail "live frontend authority_root $LIVE_AUTHORITY_ROOT != expected independent authority root $AUTHORITY_ROOT"

python3 - "$ROOT" "$EXPECTED_EXEC_SHA" "$EXPECTED_PAD_EXEC_SHA" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
expected_exec = sys.argv[2]
expected_pad = sys.argv[3]

def load(task_id, allowed_statuses):
    path = root / "tasks" / "active" / f"{task_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("task_id") != task_id:
        raise SystemExit(f"{task_id}: task_id mismatch")
    if data.get("status") not in allowed_statuses:
        raise SystemExit(
            f"{task_id}: status {data.get('status')!r} not in {sorted(allowed_statuses)}"
        )
    return data

def checkpoint(task, repository):
    for entry in task.get("repositories", []):
        if entry.get("name") == repository:
            value = (entry.get("remote") or {}).get("checkpoint_sha")
            if isinstance(value, str):
                return value
    return None

shell = load("workspace-shell-multirepo-research-v1", {"IN_PROGRESS"})
research = load(
    "mth602-final-multisurrogate-dqnguard-v1",
    {"IN_PROGRESS", "CHECKPOINTED"},
)
if checkpoint(shell, "workspace-control") != expected_exec:
    raise SystemExit("workspace-shell task does not bind expected workspace-control execution SHA")
if checkpoint(shell, "PADataset") != expected_pad:
    raise SystemExit("workspace-shell task does not bind expected PADataset execution SHA")
if checkpoint(research, "PADataset") != expected_pad:
    raise SystemExit("MTH602 task does not bind expected PADataset execution SHA")
print("DURABLE_TASK_BINDINGS=PASS")
PY

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

EVIDENCE_MOUNT_PREEXISTING=0
verify_existing_evidence_mount() {
  sudo mountpoint -q "$EVIDENCE_MOUNT" || fail "$EVIDENCE_MOUNT is not a mountpoint"
  local source_identity mount_identity options
  source_identity="$(stat -Lc '%d:%i' "$PAD_EVIDENCE_ROOT")"
  mount_identity="$(sudo stat -Lc '%d:%i' "$EVIDENCE_MOUNT")"
  [[ "$mount_identity" == "$source_identity" ]]     || fail "$EVIDENCE_MOUNT is mounted from an unexpected source"
  options="$(sudo findmnt -n -o OPTIONS --target "$EVIDENCE_MOUNT")"
  case ",$options," in
    *,ro,*) ;;
    *) fail "$EVIDENCE_MOUNT existing bind is not read-only: $options" ;;
  esac
  for required in nosuid nodev noexec; do
    case ",$options," in
      *,"$required",*) ;;
      *) fail "$EVIDENCE_MOUNT existing bind is missing $required: $options" ;;
    esac
  done
  printf '%s\n' "$options"
}

if sudo mountpoint -q "$EVIDENCE_MOUNT"; then
  MOUNT_OPTIONS="$(verify_existing_evidence_mount)"
  EVIDENCE_MOUNT_PREEXISTING=1
  echo "PADataset evidence mount already present and verified safe; reusing it."
fi

WC_FETCH="$(mktemp -d /tmp/workspace-control-exec.XXXXXX)"
PAD_FETCH="$(mktemp -d /tmp/padataset-exec.XXXXXX)"
SEM_AUTH_FETCH="$(mktemp -d /tmp/workspace-control-semantic-authority.XXXXXX)"
SEM_EXEC_FETCH="$(mktemp -d /tmp/workspace-control-semantic-exec.XXXXXX)"
cleanup_tmp() {
  rm -rf "$WC_FETCH" "$PAD_FETCH" "$SEM_AUTH_FETCH" "$SEM_EXEC_FETCH" >/dev/null 2>&1 || true
}
trap cleanup_tmp EXIT

echo "Materializing clean workspace-control execution source at exact SHA $EXPECTED_EXEC_SHA"
rm -rf "$WC_FETCH"
mkdir -p "$WC_FETCH"
git -C "$WC_FETCH" init --quiet
git -C "$WC_FETCH" remote add origin "https://github.com/adamtrott78/workspace-control.git"
git_retry git -C "$WC_FETCH" -c http.version=HTTP/1.1 fetch --quiet --depth=1 --no-tags origin "$EXPECTED_EXEC_SHA" \
  || fail "unable to fetch exact workspace-control execution SHA after bounded retries"
git -C "$WC_FETCH" -c advice.detachedHead=false checkout --quiet --detach FETCH_HEAD
[[ "$(git -C "$WC_FETCH" rev-parse HEAD)" == "$EXPECTED_EXEC_SHA" ]] || fail "workspace-control execution checkout SHA mismatch"
[[ -z "$(git -C "$WC_FETCH" status --porcelain=v1 --untracked-files=normal)" ]] || fail "workspace-control execution checkout unexpectedly dirty"

echo "Materializing clean PADataset execution source at exact SHA $EXPECTED_PAD_EXEC_SHA"
rm -rf "$PAD_FETCH"
mkdir -p "$PAD_FETCH"
git -C "$PAD_FETCH" init --quiet
git -C "$PAD_FETCH" remote add origin "$PAD_EXEC_REPO_URL"
git_retry git -C "$PAD_FETCH" -c http.version=HTTP/1.1 fetch --quiet --depth=1 --no-tags origin "$EXPECTED_PAD_EXEC_SHA" \
  || fail "unable to fetch exact PADataset execution SHA after bounded retries"
git -C "$PAD_FETCH" -c advice.detachedHead=false checkout --quiet --detach FETCH_HEAD
[[ "$(git -C "$PAD_FETCH" rev-parse HEAD)" == "$EXPECTED_PAD_EXEC_SHA" ]] || fail "clean PADataset execution checkout SHA mismatch"
[[ -z "$(git -C "$PAD_FETCH" status --porcelain=v1 --untracked-files=normal)" ]] || fail "clean PADataset execution checkout unexpectedly dirty"

if [[ -n "$EXPECTED_SEMANTIC_CAPSULE_SHA" ]]; then
  echo "Materializing semantic task authority capsule at exact SHA $EXPECTED_SEMANTIC_CAPSULE_SHA"
  rm -rf "$SEM_AUTH_FETCH"
  mkdir -p "$SEM_AUTH_FETCH"
  git -C "$SEM_AUTH_FETCH" init --quiet
  git -C "$SEM_AUTH_FETCH" remote add origin "https://github.com/adamtrott78/workspace-control.git"
  git_retry git -C "$SEM_AUTH_FETCH" -c http.version=HTTP/1.1 fetch --quiet --depth=1 --no-tags origin "$EXPECTED_SEMANTIC_CAPSULE_SHA" \
    || fail "unable to fetch exact semantic authority capsule SHA after bounded retries"
  git -C "$SEM_AUTH_FETCH" -c advice.detachedHead=false checkout --quiet --detach FETCH_HEAD
  [[ "$(git -C "$SEM_AUTH_FETCH" rev-parse HEAD)" == "$EXPECTED_SEMANTIC_CAPSULE_SHA" ]] \
    || fail "semantic authority checkout SHA mismatch"
  python3 - "$SEM_AUTH_FETCH/$SEMANTIC_TASK_REL" "$EXPECTED_SEMANTIC_EXEC_SHA" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_exec = sys.argv[2]
task = json.loads(path.read_text(encoding="utf-8"))
if task.get("task_id") != "workspace-semantic-execution-migration-v1":
    raise SystemExit("semantic task_id mismatch")
if task.get("status") != "IN_PROGRESS":
    raise SystemExit("semantic task must be IN_PROGRESS")
repo = next(
    (item for item in task.get("repositories", []) if item.get("name") == "workspace-control"),
    None,
)
if not isinstance(repo, dict):
    raise SystemExit("semantic task workspace-control repository binding missing")
bound = (repo.get("remote") or {}).get("checkpoint_sha")
if bound != expected_exec:
    raise SystemExit(
        f"semantic task execution binding {bound!r} != expected {expected_exec!r}"
    )
print("SEMANTIC_DURABLE_TASK_BINDING=PASS")
PY

  echo "Materializing semantic execution source at exact SHA $EXPECTED_SEMANTIC_EXEC_SHA"
  rm -rf "$SEM_EXEC_FETCH"
  mkdir -p "$SEM_EXEC_FETCH"
  git -C "$SEM_EXEC_FETCH" init --quiet
  git -C "$SEM_EXEC_FETCH" remote add origin "https://github.com/adamtrott78/workspace-control.git"
  git_retry git -C "$SEM_EXEC_FETCH" -c http.version=HTTP/1.1 fetch --quiet --depth=1 --no-tags origin "$EXPECTED_SEMANTIC_EXEC_SHA" \
    || fail "unable to fetch exact semantic execution SHA after bounded retries"
  git -C "$SEM_EXEC_FETCH" -c advice.detachedHead=false checkout --quiet --detach FETCH_HEAD
  [[ "$(git -C "$SEM_EXEC_FETCH" rev-parse HEAD)" == "$EXPECTED_SEMANTIC_EXEC_SHA" ]] \
    || fail "semantic execution checkout SHA mismatch"
  [[ -z "$(git -C "$SEM_EXEC_FETCH" status --porcelain=v1 --untracked-files=normal)" ]] \
    || fail "semantic execution checkout unexpectedly dirty"
fi

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
  "$AUTHORITY_ROOT" \
  /srv/workspace-shell/workspace-control \
  /srv/workspace-shell/PADataset \
  /opt/workspace-shell/runtime/plugins/workspace-shell \
  /etc/workspace-shell/profiles.v1.json \
  /etc/workspace-shell/frontend.json \
  /etc/workspace-shell/candidate-materializer.json \
  /etc/workspace-shell/job-launcher.json \
  /etc/workspace-shell/broker-verifier.json \
  /etc/systemd/system/workspace-shell-candidate-materializer.service; do
  if sudo test -e "$p"; then
    name="$(echo "$p" | sed 's#^/##; s#/#__#g')"
    sudo cp -a --reflink=auto "$p" "$BACKUP/$name"
  fi
done

EVIDENCE_MOUNT_CREATED=0
EVALUATOR_SEALED_ROOT_CREATED=0
rollback() {
  rc="$1"
  if [[ $rc -eq 0 ]]; then return; fi
  echo "Upgrade failed; attempting rollback from $BACKUP" >&2
  sudo systemctl stop "${SERVICES[@]}" >/dev/null 2>&1 || true

  if [[ "$EVIDENCE_MOUNT_CREATED" == "1" ]] && sudo mountpoint -q "$EVIDENCE_MOUNT"; then
    sudo umount "$EVIDENCE_MOUNT" >/dev/null 2>&1 || true
  fi

  sudo rm -f "$EVALUATOR_DENIAL_SENTINEL" >/dev/null 2>&1 || true
  if [[ "$EVALUATOR_SEALED_ROOT_CREATED" == "1" ]]; then
    sudo rm -rf "$EVALUATOR_SEALED_ROOT" >/dev/null 2>&1 || true
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

  restore "$AUTHORITY_ROOT"
  restore /srv/workspace-shell/workspace-control
  restore /srv/workspace-shell/PADataset
  restore /opt/workspace-shell/runtime/plugins/workspace-shell
  restore /etc/workspace-shell/profiles.v1.json
  restore /etc/workspace-shell/frontend.json
  restore /etc/workspace-shell/candidate-materializer.json
  restore /etc/workspace-shell/job-launcher.json
  restore /etc/workspace-shell/broker-verifier.json
  restore /etc/systemd/system/workspace-shell-candidate-materializer.service
  if [[ ! -e "$BACKUP/etc__workspace-shell__candidate-materializer.json" ]]; then
    sudo rm -f /etc/workspace-shell/candidate-materializer.json
  fi
  if [[ ! -e "$BACKUP/etc__systemd__system__workspace-shell-candidate-materializer.service" ]]; then
    sudo rm -f /etc/systemd/system/workspace-shell-candidate-materializer.service
  fi

  sudo systemctl daemon-reload || true
  if [[ -e "$BACKUP/etc__systemd__system__workspace-shell-candidate-materializer.service" ]]; then
    sudo systemctl start workspace-shell-candidate-materializer.service || true
  fi
  sudo systemctl start "${BASE_SERVICES[@]}" || true
  cleanup_tmp
  exit "$rc"
}
trap 'rollback "$?"' EXIT

sudo systemctl stop workspace-shell-tunnel.service workspace-shell-mcp.service workspace-shell-root-broker.service workspace-shell-job-launcher.service
sudo systemctl stop workspace-shell-candidate-materializer.service >/dev/null 2>&1 || true

AUTH_NEXT="$AUTHORITY_ROOT.next.$$"
WC_NEXT="/srv/workspace-shell/workspace-control.next.$$"
PAD_NEXT="/srv/workspace-shell/PADataset.next.$$"
sudo rm -rf "$AUTH_NEXT" "$WC_NEXT" "$PAD_NEXT"
sudo mkdir -p "$AUTH_NEXT" "$WC_NEXT" "$PAD_NEXT"
sudo cp -a --reflink=auto "$ROOT/." "$AUTH_NEXT/"
sudo cp -a --reflink=auto "$WC_FETCH/." "$WC_NEXT/"
sudo cp -a --reflink=auto "$PAD_FETCH/." "$PAD_NEXT/"
if [[ -n "$EXPECTED_SEMANTIC_CAPSULE_SHA" ]]; then
  sudo install -o root -g root -m 0644 \
    "$SEM_AUTH_FETCH/$SEMANTIC_TASK_REL" \
    "$AUTH_NEXT/$SEMANTIC_TASK_REL"
  SEMANTIC_CAPSULE_SHA256="$(sha256sum "$SEM_AUTH_FETCH/$SEMANTIC_TASK_REL" | awk '{print $1}')"
  INSTALLED_SEMANTIC_CAPSULE_SHA256="$(sudo sha256sum "$AUTH_NEXT/$SEMANTIC_TASK_REL" | awk '{print $1}')"
  [[ "$INSTALLED_SEMANTIC_CAPSULE_SHA256" == "$SEMANTIC_CAPSULE_SHA256" ]] \
    || fail "semantic authority capsule content hash mismatch"
fi
sudo chown -R root:root "$AUTH_NEXT" "$WC_NEXT" "$PAD_NEXT"
# mktemp creates 0700 roots and cp -a preserves those source-directory modes.
# These snapshots are immutable inputs for unprivileged Workspace Shell principals,
# so restore read/traverse while keeping group/other writes forbidden.
sudo chmod -R a+rX,go-w "$AUTH_NEXT" "$WC_NEXT" "$PAD_NEXT"

[[ "$(sudo git -c safe.directory="$AUTH_NEXT" -C "$AUTH_NEXT" rev-parse HEAD)" == "$EXPECTED_AUTHORITY_SHA" ]] || fail "workspace-control authority snapshot SHA mismatch"
if [[ -n "$EXPECTED_SEMANTIC_CAPSULE_SHA" ]]; then
  AUTH_STATUS="$(sudo git -c safe.directory="$AUTH_NEXT" -C "$AUTH_NEXT" status --porcelain=v1 --untracked-files=normal)"
  [[ "$AUTH_STATUS" == "?? $SEMANTIC_TASK_REL" ]] \
    || fail "authority snapshot has unexpected changes after semantic enrollment: $AUTH_STATUS"
fi
[[ "$(sudo git -c safe.directory="$WC_NEXT" -C "$WC_NEXT" rev-parse HEAD)" == "$EXPECTED_EXEC_SHA" ]] || fail "workspace-control execution snapshot SHA mismatch"
[[ "$(sudo git -c safe.directory="$PAD_NEXT" -C "$PAD_NEXT" rev-parse HEAD)" == "$EXPECTED_PAD_EXEC_SHA" ]] || fail "PADataset execution snapshot SHA mismatch"
[[ -z "$(sudo git -c safe.directory="$WC_NEXT" -C "$WC_NEXT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "workspace-control execution snapshot is not clean"
[[ -z "$(sudo git -c safe.directory="$PAD_NEXT" -C "$PAD_NEXT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "PADataset execution snapshot is not clean"

sudo rm -rf "$AUTHORITY_ROOT" /srv/workspace-shell/workspace-control /srv/workspace-shell/PADataset
sudo mv "$AUTH_NEXT" "$AUTHORITY_ROOT"
sudo mv "$WC_NEXT" /srv/workspace-shell/workspace-control
sudo mv "$PAD_NEXT" /srv/workspace-shell/PADataset

if [[ "$EVIDENCE_MOUNT_PREEXISTING" == "0" ]]; then
  sudo mkdir -p "$EVIDENCE_MOUNT"
  sudo chown root:root "$EVIDENCE_MOUNT"
  sudo chmod 0755 "$EVIDENCE_MOUNT"
  sudo mount --bind "$PAD_EVIDENCE_ROOT" "$EVIDENCE_MOUNT"
  EVIDENCE_MOUNT_CREATED=1
  sudo mount -o remount,bind,ro,nosuid,nodev,noexec "$EVIDENCE_MOUNT"
fi
MOUNT_OPTIONS="$(verify_existing_evidence_mount)"

if sudo test -e "$EVALUATOR_SEALED_ROOT"; then
  sudo python3 - "$EVALUATOR_SEALED_ROOT" <<'PY'
import os
import stat
import sys

path = sys.argv[1]
st = os.lstat(path)
if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
    raise SystemExit("evaluator sealed root must be a real directory")
if st.st_uid != 0 or st.st_gid != 0:
    raise SystemExit("evaluator sealed root must be root:root")
if stat.S_IMODE(st.st_mode) != 0o700:
    raise SystemExit("evaluator sealed root mode must be 0700")
PY
else
  sudo install -d -o root -g root -m 0700 "$EVALUATOR_SEALED_ROOT"
  EVALUATOR_SEALED_ROOT_CREATED=1
fi
echo "EVALUATOR_SEALED_ROOT=PASS"

if [[ -n "$EXPECTED_SEMANTIC_EXEC_SHA" ]]; then
  sudo env PYTHONPATH="$SEM_EXEC_FETCH/semantic-execution/src" python3 - "$SEM_EXEC_FETCH" "$EVALUATOR_SEALED_ROOT" <<'PY'
import importlib.util
from pathlib import Path
import sys

source = Path(sys.argv[1])
sealed_root = Path(sys.argv[2])

from workspace_semantic_execution.evaluator import (
    FilesystemEvaluatorSealedStore,
    stage_ephemeral_bundle,
)

generator_path = source / "benchmarks/workspace-semantic-execution/resumable_reasoning_ephemeral_fixture_v1.py"
spec = importlib.util.spec_from_file_location("ws_ephemeral_fixture", generator_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

seed = "a1" * 32
nonce = "b2" * 32
bundle = module.generate_bundle(seed_hex=seed, seal_nonce_hex=nonce)
store = FilesystemEvaluatorSealedStore(sealed_root, owner_uid=0)
staged = stage_ephemeral_bundle(
    store=store,
    bundle=bundle,
    seed_hex=seed,
    seal_nonce_hex=nonce,
)
restored = store.load(staged.record.fixture_id)
if not module.verify_bundle(
    public_fixture=staged.worker_material["public_fixture"],
    evaluator_oracle=restored.evaluator_oracle,
    public_seal=staged.worker_material["public_seal"],
    seal_nonce_hex=restored.seal_nonce_hex,
):
    raise SystemExit("evaluator sealed-store commitment verification failed")
record = sealed_root / f"{staged.record.fixture_id}.sealed.json"
record.unlink()
print("LOCAL_EVALUATOR_CONTROL_READBACK=PASS")
PY
fi

printf '%s\n' 'workspace-shell-evaluator-worker-denial-probe-v1' \
  | sudo tee "$EVALUATOR_DENIAL_SENTINEL" >/dev/null
sudo chown root:root "$EVALUATOR_DENIAL_SENTINEL"
sudo chmod 0600 "$EVALUATOR_DENIAL_SENTINEL"

RUNTIME_PLUGIN="/opt/workspace-shell/runtime/plugins/workspace-shell"
BACKUP_RUNTIME_PLUGIN="$BACKUP/opt__workspace-shell__runtime__plugins__workspace-shell"
BACKUP_NODE_MODULES="$BACKUP_RUNTIME_PLUGIN/node_modules"

for dep in "@modelcontextprotocol/sdk" "@modelcontextprotocol/ext-apps" "zod"; do
  sudo test -e "$BACKUP_NODE_MODULES/$dep" || fail "backup runtime dependency closure is missing $dep"
done

sudo rm -rf "$RUNTIME_PLUGIN"
sudo mkdir -p /opt/workspace-shell/runtime/plugins
sudo cp -a "$WC_FETCH/plugins/workspace-shell" "$RUNTIME_PLUGIN"
sudo cp -a "$BACKUP_NODE_MODULES" "$RUNTIME_PLUGIN/node_modules"
sudo chown -R root:root "$RUNTIME_PLUGIN"
sudo chmod -R go-w "$RUNTIME_PLUGIN"

(
  cd "$RUNTIME_PLUGIN"
  sudo -u workspace-shell-mcp env \
    HOME=/var/lib/workspace-shell \
    OPENSSL_CONF=/opt/workspace-shell/node/ssl/openssl.cnf \
    /opt/workspace-shell/node/bin/node --input-type=module -e \
    "await import('@modelcontextprotocol/ext-apps/server'); await import('@modelcontextprotocol/sdk/server/mcp.js'); await import('zod');"
)
echo "RUNTIME_NODE_DEPENDENCIES=PASS"

sudo install -o root -g root -m 0644 "$WC_FETCH/plugins/workspace-shell/config/profiles.v1.json" /etc/workspace-shell/profiles.v1.json
sudo install -o root -g root -m 0644 \
  "$WC_FETCH/plugins/workspace-shell/install/workspace-shell-candidate-materializer.service.in" \
  /etc/systemd/system/workspace-shell-candidate-materializer.service
sudo mkdir -p /var/lib/workspace-shell/candidates /etc/workspace-shell/candidate-sources
sudo chown root:root /var/lib/workspace-shell/candidates /etc/workspace-shell/candidate-sources
sudo chmod 0711 /var/lib/workspace-shell/candidates
sudo chmod 0700 /etc/workspace-shell/candidate-sources

sudo python3 - <<'PY'
import json
from pathlib import Path

frontend = Path("/etc/workspace-shell/frontend.json")
fdata = json.loads(frontend.read_text())
units = fdata.setdefault("allowed_units", [])
candidate_unit = "workspace-shell-candidate-materializer.service"
if candidate_unit not in units:
    units.append(candidate_unit)
fst = frontend.stat()
ftmp = frontend.with_suffix(frontend.suffix + ".tmp")
ftmp.write_text(json.dumps(fdata, indent=2) + "\n")
ftmp.chmod(fst.st_mode & 0o777)
import os
os.chown(ftmp, fst.st_uid, fst.st_gid)
ftmp.replace(frontend)

launcher = Path("/etc/workspace-shell/job-launcher.json")
data = json.loads(launcher.read_text())
roots = data.setdefault("source_roots", {})
roots["workspace-control"] = "/srv/workspace-shell/workspace-control"
roots["PADataset"] = "/srv/workspace-shell/PADataset"
evidence = data.setdefault("evidence_roots", {})
evidence["PADataset"] = "/srv/workspace-shell/PADataset-evidence"
data["candidate_materializer_socket"] = "/run/workspace-shell-control/candidate-materializer.sock"
data["candidate_store_root"] = "/var/lib/workspace-shell/candidates"
tmp = launcher.with_suffix(launcher.suffix + ".tmp")
tmp.write_text(json.dumps(data, indent=2) + "\n")
tmp.chmod(0o600)
tmp.replace(launcher)

materializer = Path("/etc/workspace-shell/candidate-materializer.json")
if materializer.exists():
    mdata = json.loads(materializer.read_text())
else:
    mdata = {}
mdata["socket_path"] = "/run/workspace-shell-control/candidate-materializer.sock"
mdata["candidate_store_root"] = "/var/lib/workspace-shell/candidates"
sources = mdata.setdefault("sources", {})
sources.setdefault("workspace-control", {
    "repository": "adamtrott78/workspace-control",
    "transport": "public_https",
    "url": "https://github.com/adamtrott78/workspace-control.git",
})
sources.setdefault("PADataset", {
    "repository": "adamtrott78/PADataset",
    "transport": "public_https",
    "url": "https://github.com/adamtrott78/PADataset.git",
})
for target, repository in (
    ("workspace-control", "adamtrott78/workspace-control"),
    ("PADataset", "adamtrott78/PADataset"),
):
    if (sources.get(target) or {}).get("repository") != repository:
        raise SystemExit(f"candidate source repository mismatch for {target}")
mtmp = materializer.with_suffix(materializer.suffix + ".tmp")
mtmp.write_text(json.dumps(mdata, indent=2) + "\n")
mtmp.chmod(0o600)
mtmp.replace(materializer)

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
sudo systemctl start workspace-shell-candidate-materializer.service
sudo systemctl start workspace-shell-job-launcher.service
sudo systemctl start workspace-shell-root-broker.service
sudo systemctl start workspace-shell-mcp.service
sudo systemctl start workspace-shell-tunnel.service

for svc in "${SERVICES[@]}"; do
  sudo systemctl is-active --quiet "$svc" || fail "$svc is not active after upgrade"
done

MCP_INIT="$(mktemp /tmp/workspace-shell-upgrade-init.XXXXXX.json)"
MCP_TOOLS="$(mktemp /tmp/workspace-shell-upgrade-tools.XXXXXX.json)"
MCP_TASK_PRIMARY="$(mktemp /tmp/workspace-shell-upgrade-task-primary.XXXXXX.json)"
MCP_TASK_DEPENDENT="$(mktemp /tmp/workspace-shell-upgrade-task-dependent.XXXXXX.json)"
MCP_TASK_SEMANTIC="$(mktemp /tmp/workspace-shell-upgrade-task-semantic.XXXXXX.json)"
MCP_EVALUATOR_DENIAL="$(mktemp /tmp/workspace-shell-upgrade-evaluator-denial.XXXXXX.json)"
trap 'rc=$?; rm -f "$MCP_INIT" "$MCP_TOOLS" "$MCP_TASK_PRIMARY" "$MCP_TASK_DEPENDENT" "$MCP_TASK_SEMANTIC" "$MCP_EVALUATOR_DENIAL"; rollback "$rc"' EXIT

MCP_READY=0
for attempt in $(seq 1 20); do
  if sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 2 \
    --cacert /etc/workspace-shell/tunnel/ca.crt \
    --cert /etc/workspace-shell/tunnel/client.crt \
    --key /etc/workspace-shell/tunnel/client.key \
    -H 'content-type: application/json' \
    -H 'accept: application/json, text/event-stream' \
    --data-binary '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"workspace-shell-upgrade","version":"0.1.0"}}}' \
    https://127.0.0.1:8797/mcp >"$MCP_INIT"; then
    MCP_READY=1
    break
  fi
  sleep 1
done
[[ "$MCP_READY" == "1" ]] || fail "workspace-shell MCP did not become ready on 127.0.0.1:8797 after bounded startup wait"
echo "LOCAL_MCP_READY=PASS"

sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 5 \
  --cacert /etc/workspace-shell/tunnel/ca.crt \
  --cert /etc/workspace-shell/tunnel/client.crt \
  --key /etc/workspace-shell/tunnel/client.key \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  --data-binary '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  https://127.0.0.1:8797/mcp >"$MCP_TOOLS"

python3 - "$MCP_INIT" "$MCP_TOOLS" <<'PY'
import json, pathlib, sys
init=json.loads(pathlib.Path(sys.argv[1]).read_text())
tools=json.loads(pathlib.Path(sys.argv[2]).read_text())
if init.get("result", {}).get("serverInfo", {}).get("name") != "workspace-shell":
    raise SystemExit("MCP initialize response invalid")
result=tools.get("result")
if not isinstance(result, dict) or not isinstance(result.get("tools"), list):
    raise SystemExit(f"MCP tools/list response invalid: {tools}")
names={t.get("name") for t in result["tools"] if isinstance(t, dict)}
expected={"workspace_shell_inspect","workspace_shell_exec","workspace_shell_run_reviewed_helper","workspace_shell_receipt"}
if names != expected:
    raise SystemExit(f"MCP tools/list names mismatch: {sorted(names)}")
exec_tool=next(t for t in result["tools"] if t.get("name")=="workspace_shell_exec")
schema=exec_tool.get("inputSchema", {})
target=((schema.get("properties") or {}).get("target") or {}).get("enum") or []
profile=((schema.get("properties") or {}).get("profile") or {}).get("enum") or []
for value in ("workspace-control","PADataset"):
    if value not in target:
        raise SystemExit(f"workspace_shell_exec target missing {value}")
for value in ("file-list","file-read","file-hash","research-bounded","candidate-pytest","evaluator-denial-probe"):
    if value not in profile:
        raise SystemExit(f"workspace_shell_exec profile missing {value}")
print("LOCAL_MCP_DISCOVERY=PASS")
PY

sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 5 \
  --cacert /etc/workspace-shell/tunnel/ca.crt \
  --cert /etc/workspace-shell/tunnel/client.crt \
  --key /etc/workspace-shell/tunnel/client.key \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  --data-binary '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"workspace_shell_inspect","arguments":{"task_id":"workspace-shell-multirepo-research-v1","target":"workspace-shell","operation":"runtime_inventory"}}}' \
  https://127.0.0.1:8797/mcp >"$MCP_TASK_PRIMARY"

sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 5 \
  --cacert /etc/workspace-shell/tunnel/ca.crt \
  --cert /etc/workspace-shell/tunnel/client.crt \
  --key /etc/workspace-shell/tunnel/client.key \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  --data-binary '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"workspace_shell_inspect","arguments":{"task_id":"mth602-final-multisurrogate-dqnguard-v1","target":"workspace-shell","operation":"runtime_inventory"}}}' \
  https://127.0.0.1:8797/mcp >"$MCP_TASK_DEPENDENT"

if [[ -n "$EXPECTED_SEMANTIC_CAPSULE_SHA" ]]; then
  SEMANTIC_ACCEPTANCE_STARTED="$(date +%s)"
  sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 60 \
    --cacert /etc/workspace-shell/tunnel/ca.crt \
    --cert /etc/workspace-shell/tunnel/client.crt \
    --key /etc/workspace-shell/tunnel/client.key \
    -H 'content-type: application/json' \
    -H 'accept: application/json, text/event-stream' \
    --data-binary '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"workspace_shell_exec","arguments":{"task_id":"workspace-semantic-execution-migration-v1","target":"workspace-control","expected_sha":"'"$EXPECTED_SEMANTIC_EXEC_SHA"'","profile":"git-read","argv":["rev-parse","HEAD"],"cwd":".","timeout_ms":50000}}}' \
    https://127.0.0.1:8797/mcp >"$MCP_TASK_SEMANTIC"

  EVALUATOR_DENIAL_STARTED="$(date +%s)"
  sudo -u workspace-shell-tunnel /usr/bin/curl -fsS --max-time 60 \
    --cacert /etc/workspace-shell/tunnel/ca.crt \
    --cert /etc/workspace-shell/tunnel/client.crt \
    --key /etc/workspace-shell/tunnel/client.key \
    -H 'content-type: application/json' \
    -H 'accept: application/json, text/event-stream' \
    --data-binary '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"workspace_shell_exec","arguments":{"task_id":"workspace-semantic-execution-migration-v1","target":"workspace-control","expected_sha":"'"$EXPECTED_SEMANTIC_EXEC_SHA"'","profile":"evaluator-denial-probe","argv":["sealed-store-v1"],"cwd":".","timeout_ms":30000}}}' \
    https://127.0.0.1:8797/mcp >"$MCP_EVALUATOR_DENIAL"
fi

python3 - "$MCP_TASK_PRIMARY" "$MCP_TASK_DEPENDENT" "$MCP_TASK_SEMANTIC" "$MCP_EVALUATOR_DENIAL" "$EXPECTED_SEMANTIC_EXEC_SHA" <<'PY'
import json
import pathlib
import sys

def accepted(path, label):
    payload = json.loads(pathlib.Path(path).read_text())
    if payload.get("error") is not None:
        raise SystemExit(f"{label} MCP error: {payload['error']}")
    result = payload.get("result")
    if not isinstance(result, dict) or result.get("isError") is True:
        raise SystemExit(f"{label} tools/call failed: {payload}")
    serialized = json.dumps(payload, sort_keys=True)
    for marker in ("TASK_NOT_FOUND", "TASK_ID_MISMATCH", "AUTHORITY_READ_FAILED"):
        if marker in serialized:
            raise SystemExit(f"{label} authority gate failed with {marker}")
    structured = result.get("structuredContent")
    if isinstance(structured, dict) and structured.get("ok") is True:
        return
    for item in result.get("content", []):
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        try:
            value = json.loads(item.get("text", ""))
        except Exception:
            continue
        if isinstance(value, dict) and value.get("ok") is True:
            return
    raise SystemExit(f"{label} did not return an ok=true tool result: {payload}")

accepted(sys.argv[1], "workspace-shell-multirepo-research-v1")
accepted(sys.argv[2], "mth602-final-multisurrogate-dqnguard-v1")
expected_semantic = sys.argv[5]
if expected_semantic:
    accepted(sys.argv[3], "workspace-semantic-execution-migration-v1")
    accepted(sys.argv[4], "workspace-semantic-execution-evaluator-denial")
    print("LOCAL_SEMANTIC_TASK_MCP=PASS")
    print("LOCAL_EVALUATOR_WORKER_DENIAL_MCP=PASS")
print("LOCAL_TASK_AUTHORITY=PASS")
PY

if [[ -n "$EXPECTED_SEMANTIC_CAPSULE_SHA" ]]; then
  SEMANTIC_RECEIPT_ROOT="$(sudo python3 - <<'PY'
import json
from pathlib import Path
cfg = json.loads(Path("/etc/workspace-shell/frontend.json").read_text(encoding="utf-8"))
value = cfg.get("receipt_root")
if not isinstance(value, str) or not value:
    raise SystemExit("frontend receipt_root missing")
print(value)
PY
)"
  sudo python3 - "$SEMANTIC_RECEIPT_ROOT" "$MCP_TASK_SEMANTIC" "$EXPECTED_SEMANTIC_EXEC_SHA" <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
mcp_payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
expected = sys.argv[3]
structured = ((mcp_payload.get("result") or {}).get("structuredContent") or {})
launcher_result = structured.get("result") or {}
receipt_id = launcher_result.get("receipt_id")
if not isinstance(receipt_id, str) or re.fullmatch(
    r"job-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    receipt_id,
) is None:
    raise SystemExit("semantic MCP response did not contain an exact job receipt_id")
path = root / f"{receipt_id}.json"
if not path.is_file():
    raise SystemExit(f"semantic MCP receipt file missing: {path.name}")
receipt = json.loads(path.read_text(encoding="utf-8"))
checks = {
    "receipt_id": receipt.get("receipt_id") == receipt_id,
    "task_id": receipt.get("task_id") == "workspace-semantic-execution-migration-v1",
    "argv_profile": receipt.get("argv_profile") == "git-read",
    "authorization_decision": receipt.get("authorization_decision") in (None, "ALLOW"),
    "exit_code": receipt.get("exit_code") == 0,
    "privileged": receipt.get("privileged") is False,
    "expected_git_sha": receipt.get("expected_git_sha") == expected,
    "observed_git_sha": receipt.get("observed_git_sha") == expected,
    "task_checkpoint_sha": receipt.get("task_checkpoint_sha") == expected,
    "source_mode": receipt.get("source_mode") == "task",
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit(
        "semantic acceptance receipt failed checks "
        + ",".join(failed)
        + ": "
        + json.dumps(receipt, sort_keys=True)
    )
print("LOCAL_SEMANTIC_TASK_RECEIPT=PASS")
print("LOCAL_SEMANTIC_TASK_AUTHORITY=PASS")
print("SEMANTIC_ACCEPTANCE_RECEIPT=" + path.name)
PY

  sudo python3 - "$SEMANTIC_RECEIPT_ROOT" "$MCP_EVALUATOR_DENIAL" "$EXPECTED_SEMANTIC_EXEC_SHA" <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
mcp_payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
expected = sys.argv[3]
structured = ((mcp_payload.get("result") or {}).get("structuredContent") or {})
launcher_result = structured.get("result") or {}
receipt_id = launcher_result.get("receipt_id")
if not isinstance(receipt_id, str) or re.fullmatch(
    r"job-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    receipt_id,
) is None:
    raise SystemExit("evaluator MCP response did not contain an exact job receipt_id")
path = root / f"{receipt_id}.json"
if not path.is_file():
    raise SystemExit(f"evaluator MCP receipt file missing: {path.name}")
receipt = json.loads(path.read_text(encoding="utf-8"))
checks = {
    "receipt_id": receipt.get("receipt_id") == receipt_id,
    "task_id": receipt.get("task_id") == "workspace-semantic-execution-migration-v1",
    "authorization_decision": receipt.get("authorization_decision") == "ALLOW",
    "exit_code": receipt.get("exit_code") == 0,
    "privileged": receipt.get("privileged") is False,
    "expected_git_sha": receipt.get("expected_git_sha") == expected,
    "observed_git_sha": receipt.get("observed_git_sha") == expected,
    "task_checkpoint_sha": receipt.get("task_checkpoint_sha") == expected,
    "source_mode": receipt.get("source_mode") == "task",
    "argv_profile": receipt.get("argv_profile") == "evaluator-denial-probe",
    "redacted_argv": receipt.get("redacted_argv") == ["sealed-store-v1"],
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit(
        "evaluator worker-denial receipt failed checks "
        + ",".join(failed)
        + ": "
        + json.dumps(receipt, sort_keys=True)
    )
print("LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS")
print("LOCAL_EVALUATOR_ISOLATION=PASS")
print("EVALUATOR_DENIAL_RECEIPT=" + path.name)
PY
  sudo rm -f "$EVALUATOR_DENIAL_SENTINEL"
fi

rm -f "$MCP_INIT" "$MCP_TOOLS" "$MCP_TASK_PRIMARY" "$MCP_TASK_DEPENDENT" "$MCP_TASK_SEMANTIC" "$MCP_EVALUATOR_DENIAL"
trap 'rollback "$?"' EXIT

echo "WORKSPACE_CONTROL_AUTHORITY_SNAPSHOT=$(sudo git -c safe.directory="$AUTHORITY_ROOT" -C "$AUTHORITY_ROOT" rev-parse HEAD)"
if [[ -n "$EXPECTED_SEMANTIC_CAPSULE_SHA" ]]; then
  echo "SEMANTIC_AUTHORITY_CAPSULE_SOURCE=$EXPECTED_SEMANTIC_CAPSULE_SHA"
  echo "SEMANTIC_AUTHORITY_CAPSULE_SHA256=$SEMANTIC_CAPSULE_SHA256"
  echo "SEMANTIC_EXECUTION_BINDING=$EXPECTED_SEMANTIC_EXEC_SHA"
fi
echo "WORKSPACE_CONTROL_SNAPSHOT=$(sudo git -c safe.directory=/srv/workspace-shell/workspace-control -C /srv/workspace-shell/workspace-control rev-parse HEAD)"
echo "PADataset_EXECUTION_SNAPSHOT=$(sudo git -c safe.directory=/srv/workspace-shell/PADataset -C /srv/workspace-shell/PADataset rev-parse HEAD)"
echo "PADataset_EVIDENCE_BRANCH=${EVIDENCE_BRANCH:-DETACHED}"
echo "PADataset_EVIDENCE_HEAD=$EVIDENCE_SHA"
echo "PADataset_EVIDENCE_MOUNT_OPTIONS=$MOUNT_OPTIONS"
if [[ -n "$EXPECTED_SEMANTIC_EXEC_SHA" ]]; then
  echo "EVALUATOR_SEALED_ROOT_PATH=$EVALUATOR_SEALED_ROOT"
  echo "EVALUATOR_ISOLATION_ACCEPTANCE=PASS"
fi
echo "WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS"
echo "Backup retained at: $BACKUP"
trap - EXIT
cleanup_tmp
