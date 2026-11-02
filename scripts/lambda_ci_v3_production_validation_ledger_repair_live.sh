#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPAIR_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
PRODUCTION_HEAD="e44a797667ebad1d1046c83c427340fce5938828"
HELPER="$ROOT/scripts/lambda_ci_v3_production_validation_ledger_repair.py"

test -z "$(git -C "$ROOT" status --porcelain --untracked-files=no)"

echo "=== V3 PRODUCTION VALIDATION LEDGER REPAIR: BEGIN ==="
echo "REPAIR_HEAD=$REPAIR_HEAD"
echo "PRODUCTION_HEAD=$PRODUCTION_HEAD"

sudo -v
command -v gh >/dev/null
gh auth status >/dev/null

PR_HEAD="$(gh api --method GET repos/adamtrott78/workspace-control/pulls/572 --jq '.head.sha')"
if [ "$PR_HEAD" != "$PRODUCTION_HEAD" ]; then
  echo "STOP_PRODUCTION_PR_HEAD_DRIFT actual=$PR_HEAD expected=$PRODUCTION_HEAD"
  exit 1
fi
echo "PRODUCTION_PR_HEAD_BINDING=PASS"

TMP="$(mktemp -d /tmp/workspace-ci-v3-prod-ledger-repair.XXXXXX)"
trap 'rm -rf "$TMP" >/dev/null 2>&1 || true' EXIT

fetch_pair() {
  run_id="$1"
  job_id="$2"
  prefix="$3"
  gh api --method GET "repos/adamtrott78/workspace-control/actions/runs/$run_id" > "$TMP/$prefix-run.json"
  gh api --method GET "repos/adamtrott78/workspace-control/actions/jobs/$job_id" > "$TMP/$prefix-job.json"
}

fetch_pair 41466656949 125349219134 attempt1
fetch_pair 41487908880 125422978205 attempt2

env TMP="$TMP" OUT="$TMP/github-terminal-proof.json" python3 - <<'PY'
import json, os, pathlib
root=pathlib.Path(os.environ["TMP"])
specs=[
    ("attempt1",41466656949,125349219134,"cancelled"),
    ("attempt2",41487908880,125422978205,"failure"),
]
jobs=[]
for prefix,run_id,job_id,conclusion in specs:
    run=json.loads((root/f"{prefix}-run.json").read_text())
    job=json.loads((root/f"{prefix}-job.json").read_text())
    assert run["id"] == run_id
    assert run["status"] == "completed"
    assert run["conclusion"] == conclusion
    assert job["id"] == job_id
    assert job["run_id"] == run_id
    assert job["status"] == "completed"
    assert job["conclusion"] == conclusion
    jobs.append({
        "repository":"adamtrott78/workspace-control",
        "workflow_run_id":run_id,
        "workflow_run_status":run["status"],
        "workflow_run_conclusion":run["conclusion"],
        "github_job_id":job_id,
        "github_job_status":job["status"],
        "github_job_conclusion":job["conclusion"],
    })
pathlib.Path(os.environ["OUT"]).write_text(
    json.dumps({"schema_version":1,"jobs":jobs},indent=2,sort_keys=True)+"\n"
)
PY
echo "GITHUB_PRODUCTION_TERMINAL_PROOFS=PASS jobs=2"

sudo env PYTHONDONTWRITEBYTECODE=1   /usr/bin/python3 "$HELPER"   --repo-root "$ROOT"   --expected-source-head "$REPAIR_HEAD"   --github-proof "$TMP/github-terminal-proof.json"

echo "=== V3 PRODUCTION VALIDATION LEDGER REPAIR: PASS ==="
echo "NEXT_PRODUCTION_HEAD=$PRODUCTION_HEAD"
