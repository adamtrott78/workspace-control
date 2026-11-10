#!/usr/bin/env bash
set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }

EXPECTED_AUTHORITY_SHA="${1:-}"
EXPECTED_EXEC_SHA="${2:-}"
EXPECTED_PAD_EXEC_SHA="${3:-17e1147614f27702e43565089d618182ff71c5af}"
PAD_EVIDENCE_ROOT="${PADATASET_CHECKOUT:-$HOME/adamArchives/Adam/varMax/PADataset}"
PAD_EXEC_REPO_URL="https://github.com/adamtrott78/PADataset.git"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/var/lib/workspace-shell/upgrades/padataset-multirepo-v1-${STAMP}"
AUTHORITY_ROOT="/etc/workspace-shell/authority"
EVIDENCE_MOUNT="/srv/workspace-shell/PADataset-evidence"
SERVICES=(workspace-shell-job-launcher.service workspace-shell-root-broker.service workspace-shell-mcp.service workspace-shell-tunnel.service)

[[ "$EXPECTED_AUTHORITY_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "usage: bash upgrade_multirepo_padataset_v1.sh <expected-authority-sha> <expected-workspace-control-exec-sha> [expected-padataset-execution-sha]"
[[ "$EXPECTED_EXEC_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "expected workspace-control execution SHA must be full lowercase SHA"
[[ "$EXPECTED_PAD_EXEC_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "expected PADataset execution SHA must be full lowercase SHA"
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

def load(task_id):
    path = root / "tasks" / "active" / f"{task_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("task_id") != task_id:
        raise SystemExit(f"{task_id}: task_id mismatch")
    if data.get("status") != "IN_PROGRESS":
        raise SystemExit(f"{task_id}: status must be IN_PROGRESS")
    return data

def checkpoint(task, repository):
    for entry in task.get("repositories", []):
        if entry.get("name") == repository:
            value = (entry.get("remote") or {}).get("checkpoint_sha")
            if isinstance(value, str):
                return value
    return None

shell = load("workspace-shell-multirepo-research-v1")
research = load("mth602-final-multisurrogate-dqnguard-v1")
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
cleanup_tmp() {
  rm -rf "$WC_FETCH" "$PAD_FETCH" >/dev/null 2>&1 || true
}
trap cleanup_tmp EXIT

echo "Materializing clean workspace-control execution source at exact SHA $EXPECTED_EXEC_SHA"
git clone --no-checkout "$ROOT" "$WC_FETCH"
git -C "$WC_FETCH" checkout --detach "$EXPECTED_EXEC_SHA"
git -C "$WC_FETCH" remote remove origin >/dev/null 2>&1 || true
[[ "$(git -C "$WC_FETCH" rev-parse HEAD)" == "$EXPECTED_EXEC_SHA" ]] || fail "workspace-control execution checkout SHA mismatch"
[[ -z "$(git -C "$WC_FETCH" status --porcelain=v1 --untracked-files=normal)" ]] || fail "workspace-control execution checkout unexpectedly dirty"

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
  "$AUTHORITY_ROOT" \
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
  rc="$1"
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

  restore "$AUTHORITY_ROOT"
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
trap 'rollback "$?"' EXIT

sudo systemctl stop workspace-shell-tunnel.service workspace-shell-mcp.service workspace-shell-root-broker.service workspace-shell-job-launcher.service

AUTH_NEXT="$AUTHORITY_ROOT.next.$$"
WC_NEXT="/srv/workspace-shell/workspace-control.next.$$"
PAD_NEXT="/srv/workspace-shell/PADataset.next.$$"
sudo rm -rf "$AUTH_NEXT" "$WC_NEXT" "$PAD_NEXT"
sudo mkdir -p "$AUTH_NEXT" "$WC_NEXT" "$PAD_NEXT"
sudo cp -a --reflink=auto "$ROOT/." "$AUTH_NEXT/"
sudo cp -a --reflink=auto "$WC_FETCH/." "$WC_NEXT/"
sudo cp -a --reflink=auto "$PAD_FETCH/." "$PAD_NEXT/"
sudo chown -R root:root "$AUTH_NEXT" "$WC_NEXT" "$PAD_NEXT"
# mktemp creates 0700 roots and cp -a preserves those source-directory modes.
# These snapshots are immutable inputs for unprivileged Workspace Shell principals,
# so restore read/traverse while keeping group/other writes forbidden.
sudo chmod -R a+rX,go-w "$AUTH_NEXT" "$WC_NEXT" "$PAD_NEXT"

[[ "$(sudo git -c safe.directory="$AUTH_NEXT" -C "$AUTH_NEXT" rev-parse HEAD)" == "$EXPECTED_AUTHORITY_SHA" ]] || fail "workspace-control authority snapshot SHA mismatch"
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

MCP_INIT="$(mktemp /tmp/workspace-shell-upgrade-init.XXXXXX.json)"
MCP_TOOLS="$(mktemp /tmp/workspace-shell-upgrade-tools.XXXXXX.json)"
MCP_TASK_PRIMARY="$(mktemp /tmp/workspace-shell-upgrade-task-primary.XXXXXX.json)"
MCP_TASK_DEPENDENT="$(mktemp /tmp/workspace-shell-upgrade-task-dependent.XXXXXX.json)"
trap 'rc=$?; rm -f "$MCP_INIT" "$MCP_TOOLS" "$MCP_TASK_PRIMARY" "$MCP_TASK_DEPENDENT"; rollback "$rc"' EXIT

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
for value in ("file-list","file-read","file-hash","research-bounded"):
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

python3 - "$MCP_TASK_PRIMARY" "$MCP_TASK_DEPENDENT" <<'PY'
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
print("LOCAL_TASK_AUTHORITY=PASS")
PY

rm -f "$MCP_INIT" "$MCP_TOOLS" "$MCP_TASK_PRIMARY" "$MCP_TASK_DEPENDENT"
trap 'rollback "$?"' EXIT

echo "WORKSPACE_CONTROL_AUTHORITY_SNAPSHOT=$(sudo git -c safe.directory="$AUTHORITY_ROOT" -C "$AUTHORITY_ROOT" rev-parse HEAD)"
echo "WORKSPACE_CONTROL_SNAPSHOT=$(sudo git -c safe.directory=/srv/workspace-shell/workspace-control -C /srv/workspace-shell/workspace-control rev-parse HEAD)"
echo "PADataset_EXECUTION_SNAPSHOT=$(sudo git -c safe.directory=/srv/workspace-shell/PADataset -C /srv/workspace-shell/PADataset rev-parse HEAD)"
echo "PADataset_EVIDENCE_BRANCH=${EVIDENCE_BRANCH:-DETACHED}"
echo "PADataset_EVIDENCE_HEAD=$EVIDENCE_SHA"
echo "PADataset_EVIDENCE_MOUNT_OPTIONS=$MOUNT_OPTIONS"
echo "WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS"
echo "Backup retained at: $BACKUP"
trap - EXIT
cleanup_tmp
