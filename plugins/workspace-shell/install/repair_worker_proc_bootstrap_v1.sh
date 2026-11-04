#!/usr/bin/env bash
# Incident-specific runtime hotfix for workspace-shell worker Bubblewrap bootstrap.
# Changes only the installed job_launcher.py implementation and restarts only
# workspace-shell-job-launcher.service. Source checkout, task authority, MCP,
# tunnel, runtime key, and boot enablement are not modified.
set -Eeuo pipefail

EXPECTED_SOURCE_SHA="01a95b61410e2f427b9885a19e6a0b9c5ee60a38"
EXPECTED_OLD_BLOB="4030561a764ff47ab5bfb5cbbc345d993c2eacf7"
EXPECTED_NEW_BLOB="f013957705d59b1442ee90a2a375afe631895099"
INSTALLED="/opt/workspace-shell/runtime/plugins/workspace-shell/root/job_launcher.py"
SOURCE="/srv/workspace-shell/workspace-control"
AUTHORITY="/etc/workspace-shell/authority/tasks/active/workspace-shell-mcp-v1.json"
SERVICE="workspace-shell-job-launcher.service"
SOCKET="/run/workspace-shell-control/job-launcher.sock"
RECEIPT="/var/lib/workspace-shell/commissioning/worker-proc-bootstrap-hotfix-receipt.json"

fail() {
  printf 'WORKSPACE_SHELL_WORKER_PROC_HOTFIX=FAIL reason=%s\n' "$*" >&2
  exit 70
}

[ "$#" -eq 1 ] || fail "usage: repair_worker_proc_bootstrap_v1.sh <candidate-job_launcher.py>"
CANDIDATE="$1"
[ -f "$CANDIDATE" ] || fail "candidate launcher missing"

echo "=== WORKSPACE SHELL WORKER PROC BOOTSTRAP HOTFIX ==="

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

CANDIDATE_BLOB="$(git hash-object "$CANDIDATE")"
printf 'CANDIDATE_LAUNCHER_BLOB=%s\n' "$CANDIDATE_BLOB"
[ "$CANDIDATE_BLOB" = "$EXPECTED_NEW_BLOB" ] || fail "candidate launcher blob mismatch"

/usr/bin/python3 -m py_compile "$CANDIDATE" || fail "candidate launcher does not compile"

INSTALLED_BLOB="$(sudo git hash-object "$INSTALLED")"
printf 'INSTALLED_LAUNCHER_PRE_BLOB=%s\n' "$INSTALLED_BLOB"
case "$INSTALLED_BLOB" in
  "$EXPECTED_OLD_BLOB"|"$EXPECTED_NEW_BLOB") ;;
  *) fail "installed launcher is neither expected prestate nor expected candidate" ;;
esac

BACKUP="$(mktemp /tmp/workspace-shell-job-launcher.prehotfix.XXXXXX.py)"
trap 'rm -f "$BACKUP"' EXIT
# Keep the temporary rollback copy caller-owned so EXIT cleanup cannot leave
# a root-owned file behind in /tmp. Rollback reinstalls fixed root metadata.
sudo cat "$INSTALLED" >"$BACKUP"
chmod 0600 "$BACKUP"

rollback() {
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "=== WORKSPACE SHELL WORKER PROC HOTFIX ROLLBACK ===" >&2
    sudo install -o root -g root -m 0644 "$BACKUP" "$INSTALLED" || true
    sudo systemctl reset-failed "$SERVICE" >/dev/null 2>&1 || true
    sudo systemctl restart "$SERVICE" >/dev/null 2>&1 || true
  fi
  exit "$rc"
}
trap rollback ERR

if [ "$INSTALLED_BLOB" != "$EXPECTED_NEW_BLOB" ]; then
  sudo install -o root -g root -m 0644 "$CANDIDATE" "$INSTALLED"
fi

POST_BLOB="$(sudo git hash-object "$INSTALLED")"
printf 'INSTALLED_LAUNCHER_POST_BLOB=%s\n' "$POST_BLOB"
[ "$POST_BLOB" = "$EXPECTED_NEW_BLOB" ] || fail "installed launcher candidate did not hold"

sudo systemctl reset-failed "$SERVICE" >/dev/null 2>&1 || true
sudo systemctl restart "$SERVICE"

READY=0
for _ in $(seq 1 30); do
  if sudo systemctl is-active --quiet "$SERVICE" && sudo test -S "$SOCKET"; then
    READY=1
    break
  fi
  sleep 0.2
done
[ "$READY" = 1 ] || {
  echo "=== JOB LAUNCHER HOTFIX DIAGNOSTICS: BEGIN ===" >&2
  sudo systemctl show "$SERVICE" --no-pager \
    --property=Id,LoadState,ActiveState,SubState,Result,MainPID,ExecMainPID,ExecMainCode,ExecMainStatus,NRestarts,User,Group,FragmentPath >&2 || true
  sudo journalctl -u "$SERVICE" -n 120 --no-pager --output=short-iso 2>&1 | tail -n 120 >&2 || true
  echo "=== JOB LAUNCHER HOTFIX DIAGNOSTICS: END ===" >&2
  fail "job launcher did not become ready"
}

ENABLED="$(sudo systemctl is-enabled "$SERVICE" 2>/dev/null || true)"
[ "$ENABLED" = "disabled" ] || fail "job launcher boot state changed: $ENABLED"

sudo install -d -o root -g root -m 0700 /var/lib/workspace-shell/commissioning
TMP_RECEIPT="$(mktemp)"
/usr/bin/python3 - "$EXPECTED_SOURCE_SHA" "$EXPECTED_OLD_BLOB" "$EXPECTED_NEW_BLOB" "$INSTALLED_BLOB" "$POST_BLOB" "$ENABLED" >"$TMP_RECEIPT" <<'PY'
import datetime as dt
import json
import sys
source, expected_old, expected_new, pre, post, enabled = sys.argv[1:]
print(json.dumps({
    "schema": "workspace-shell-worker-proc-bootstrap-hotfix.v1",
    "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "execution_source_sha": source,
    "expected_old_launcher_blob": expected_old,
    "expected_new_launcher_blob": expected_new,
    "observed_pre_launcher_blob": pre,
    "observed_post_launcher_blob": post,
    "service": "workspace-shell-job-launcher.service",
    "service_active": True,
    "boot_state": enabled,
    "mutation_scope": [
        "/opt/workspace-shell/runtime/plugins/workspace-shell/root/job_launcher.py",
        "workspace-shell-job-launcher.service",
    ],
}, sort_keys=True, indent=2))
PY
sudo install -o root -g root -m 0600 "$TMP_RECEIPT" "$RECEIPT"
rm -f "$TMP_RECEIPT"

trap - ERR
echo "JOB_LAUNCHER_ACTIVE_BOOT_DISABLED=PASS"
echo "WORKSPACE_SHELL_WORKER_PROC_HOTFIX=PASS"
echo "HOTFIX_RECEIPT=$RECEIPT"
