#!/usr/bin/env bash
# Restore the Workspace Shell scratch-root traversal contract required by
# write-scratch worker profiles. Changes only /var/lib/workspace-shell/jobs mode.
set -Eeuo pipefail

EXPECTED_SOURCE_SHA="01a95b61410e2f427b9885a19e6a0b9c5ee60a38"
SOURCE="/srv/workspace-shell/workspace-control"
AUTHORITY="/etc/workspace-shell/authority/tasks/active/workspace-shell-mcp-v1.json"
SCRATCH_ROOT="/var/lib/workspace-shell/jobs"
WORKER_USER="workspace-shell-exec"
RECEIPT="/var/lib/workspace-shell/commissioning/worker-scratch-root-repair-receipt.json"

fail() {
  printf 'WORKSPACE_SHELL_WORKER_SCRATCH_ROOT_REPAIR=FAIL reason=%s\n' "$*" >&2
  exit 70
}

echo "=== WORKSPACE SHELL WORKER SCRATCH ROOT REPAIR ==="

[ "$(sudo git -C "$SOURCE" rev-parse HEAD)" = "$EXPECTED_SOURCE_SHA" ] \
  || fail "execution source SHA drift"

sudo /usr/bin/python3 - "$AUTHORITY" "$EXPECTED_SOURCE_SHA" <<'PY'
import json
import pathlib
import sys
p = pathlib.Path(sys.argv[1])
expected = sys.argv[2]
obj = json.loads(p.read_text())
matches = [
    r for r in obj.get("repositories", [])
    if isinstance(r, dict) and r.get("name") == "workspace-control"
]
if len(matches) != 1:
    raise SystemExit("workspace-control authority binding ambiguous")
remote = matches[0].get("remote")
if not isinstance(remote, dict) or remote.get("checkpoint_sha") != expected:
    raise SystemExit("authority checkpoint mismatch")
PY

sudo test -d "$SCRATCH_ROOT" || fail "scratch root missing"
PRE_META="$(sudo stat -Lc '%U:%G:%a' "$SCRATCH_ROOT")"
printf 'SCRATCH_ROOT_PRE_META=%s\n' "$PRE_META"

case "$PRE_META" in
  root:root:700|root:root:711) ;;
  *) fail "unexpected scratch root prestate: $PRE_META" ;;
esac

sudo chown root:root "$SCRATCH_ROOT"
sudo chmod 0711 "$SCRATCH_ROOT"

POST_META="$(sudo stat -Lc '%U:%G:%a' "$SCRATCH_ROOT")"
printf 'SCRATCH_ROOT_POST_META=%s\n' "$POST_META"
[ "$POST_META" = "root:root:711" ] || fail "scratch root metadata repair did not hold"

sudo -u "$WORKER_USER" test -x "$SCRATCH_ROOT" \
  || fail "worker cannot traverse scratch root"
if sudo -u "$WORKER_USER" test -r "$SCRATCH_ROOT"; then
  fail "worker unexpectedly gained directory-listing access"
fi
sudo -u "$WORKER_USER" test ! -w "$SCRATCH_ROOT" \
  || fail "worker unexpectedly gained scratch-root write access"

sudo install -d -o root -g root -m 0700 /var/lib/workspace-shell/commissioning
TMP_RECEIPT="$(mktemp)"
trap 'rm -f "$TMP_RECEIPT"' EXIT
/usr/bin/python3 - "$EXPECTED_SOURCE_SHA" "$PRE_META" "$POST_META" >"$TMP_RECEIPT" <<'PY'
import datetime as dt
import json
import sys
source, pre, post = sys.argv[1:]
print(json.dumps({
    "schema": "workspace-shell-worker-scratch-root-repair.v1",
    "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "execution_source_sha": source,
    "scratch_root": "/var/lib/workspace-shell/jobs",
    "observed_pre_meta": pre,
    "observed_post_meta": post,
    "worker_traverse": True,
    "worker_directory_read": False,
    "worker_root_write": False,
    "boot_state_changed": False,
}, sort_keys=True, indent=2))
PY
sudo install -o root -g root -m 0600 "$TMP_RECEIPT" "$RECEIPT"

echo "WORKER_TRAVERSE_ONLY=PASS"
echo "WORKSPACE_SHELL_WORKER_SCRATCH_ROOT_REPAIR=PASS"
echo "SCRATCH_ROOT_REPAIR_RECEIPT=$RECEIPT"
