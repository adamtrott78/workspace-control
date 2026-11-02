#!/usr/bin/env bash
# One-time fail-closed repair for orphaned terminal v3 migration-canary ledgers.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPAIR_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
PRODUCTION_SOURCE_HEAD="dd91ab09db74948354afcc538224490f0fa95a13"
HELPER="$ROOT/scripts/lambda_ci_v3_accepted_canary_ledger_repair.py"

test -z "$(git -C "$ROOT" status --porcelain --untracked-files=no)"
echo "REPAIR_OPERATOR_BINDING=PASS head=$REPAIR_HEAD"

echo "=== V3 MIGRATION CANARY LEDGER REPAIR: BEGIN ==="
echo "REPAIR_HEAD=$REPAIR_HEAD"
echo "PRODUCTION_SOURCE_HEAD=$PRODUCTION_SOURCE_HEAD"

sudo -v
command -v gh >/dev/null
gh auth status >/dev/null
LOGIN="$(gh api --method GET user --jq '.login')"
if [ "$LOGIN" != "adamtrott78" ]; then
  echo "STOP_GITHUB_OPERATOR_IDENTITY actual=$LOGIN"
  exit 1
fi

PR_HEAD="$(gh api --method GET "repos/adamtrott78/workspace-control/pulls/572" --jq '.head.sha')"
if [ "$PR_HEAD" != "$PRODUCTION_SOURCE_HEAD" ]; then
  echo "STOP_PRODUCTION_PR_HEAD_DRIFT actual=$PR_HEAD expected=$PRODUCTION_SOURCE_HEAD"
  exit 1
fi
echo "PRODUCTION_PR_HEAD_BINDING=PASS"

TMP="$(mktemp -d /tmp/workspace-ci-v3-ledger-repair.XXXXXX)"
cleanup() {
  rm -rf "$TMP" >/dev/null 2>&1 || true
}
trap cleanup EXIT

fetch_pair() {
  repo="$1"
  run_id="$2"
  job_id="$3"
  prefix="$4"
  gh api --method GET "repos/$repo/actions/runs/$run_id" > "$TMP/$prefix-run.json"
  gh api --method GET "repos/$repo/actions/jobs/$job_id" > "$TMP/$prefix-job.json"
}

fetch_pair "adamtrott78/workspace-control" 41264356722 124723948506 wc
fetch_pair "adamtrott78/PADataset" 41418580438 125188348656 cpu
fetch_pair "adamtrott78/PADataset" 41420426352 125194478681 gpu1
fetch_pair "adamtrott78/PADataset" 41425633192 125211444476 gpu2

env TMP="$TMP" OUT="$TMP/github-terminal-proof.json" python3 - <<'PY'
import json, os, pathlib
root=pathlib.Path(os.environ["TMP"])
specs=[
    ("wc","adamtrott78/workspace-control",41264356722,124723948506,"v3-class-canary","success"),
    ("cpu","adamtrott78/PADataset",41418580438,125188348656,"v3-class-canary","success"),
    ("gpu1","adamtrott78/PADataset",41420426352,125194478681,"v3-class-canary","failure"),
    ("gpu2","adamtrott78/PADataset",41425633192,125211444476,"v3-class-canary","success"),
]
jobs=[]
for prefix,repo,run_id,job_id,job_name,conclusion in specs:
    run=json.loads((root/f"{prefix}-run.json").read_text())
    job=json.loads((root/f"{prefix}-job.json").read_text())
    assert run["id"] == run_id
    assert run["status"] == "completed"
    assert run["conclusion"] == conclusion
    assert job["id"] == job_id
    assert job["run_id"] == run_id
    assert job["name"] == job_name
    assert job["status"] == "completed"
    assert job["conclusion"] == conclusion
    jobs.append({
        "repository":repo,
        "workflow_run_id":run_id,
        "workflow_run_status":run["status"],
        "workflow_run_conclusion":run["conclusion"],
        "github_job_id":job_id,
        "github_job_name":job["name"],
        "github_job_status":job["status"],
        "github_job_conclusion":job["conclusion"],
    })
pathlib.Path(os.environ["OUT"]).write_text(
    json.dumps({"schema_version":1,"jobs":jobs},indent=2,sort_keys=True)+"\n"
)
PY
echo "GITHUB_TERMINAL_PROOFS=PASS jobs=4"

sudo env PYTHONDONTWRITEBYTECODE=1   /usr/bin/python3 "$HELPER"   --repo-root "$ROOT"   --expected-source-head "$REPAIR_HEAD"   --github-proof "$TMP/github-terminal-proof.json"

echo "=== V3 MIGRATION CANARY LEDGER REPAIR: PASS ==="
echo "NEXT_PRODUCTION_SOURCE_HEAD=$PRODUCTION_SOURCE_HEAD"
