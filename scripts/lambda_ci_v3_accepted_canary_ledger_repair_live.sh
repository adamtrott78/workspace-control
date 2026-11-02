#!/usr/bin/env bash
# One-time fail-closed repair for the accepted workspace-control v3 canary ledger.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPAIR_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
PRODUCTION_SOURCE_HEAD="dd91ab09db74948354afcc538224490f0fa95a13"
REPO="adamtrott78/workspace-control"
RUN_ID="41264356722"
JOB_ID="124723948506"
JOB_NAME="v3-class-canary"
HELPER="$ROOT/scripts/lambda_ci_v3_accepted_canary_ledger_repair.py"

test -z "$(git -C "$ROOT" status --porcelain --untracked-files=no)"

echo "=== V3 ACCEPTED CANARY LEDGER REPAIR: BEGIN ==="
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

PR_HEAD="$(gh api --method GET "repos/$REPO/pulls/572" --jq '.head.sha')"
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

gh api --method GET "repos/$REPO/actions/runs/$RUN_ID" > "$TMP/run.json"
gh api --method GET "repos/$REPO/actions/jobs/$JOB_ID" > "$TMP/job.json"

env   RUN="$TMP/run.json"   JOB="$TMP/job.json"   OUT="$TMP/github-terminal-proof.json"   REPO="$REPO"   RUN_ID="$RUN_ID"   JOB_ID="$JOB_ID"   JOB_NAME="$JOB_NAME"   python3 - <<'PY'
import json, os, pathlib
run=json.loads(pathlib.Path(os.environ["RUN"]).read_text())
job=json.loads(pathlib.Path(os.environ["JOB"]).read_text())
run_id=int(os.environ["RUN_ID"])
job_id=int(os.environ["JOB_ID"])
job_name=os.environ["JOB_NAME"]
repo=os.environ["REPO"]
assert run["id"] == run_id
assert run["status"] == "completed"
assert run["conclusion"] == "success"
assert job["id"] == job_id
assert job["run_id"] == run_id
assert job["name"] == job_name
assert job["status"] == "completed"
assert job["conclusion"] == "success"
payload={
  "schema_version":1,
  "repository":repo,
  "workflow_run_id":run_id,
  "workflow_run_status":run["status"],
  "workflow_run_conclusion":run["conclusion"],
  "github_job_id":job_id,
  "github_job_name":job["name"],
  "github_job_status":job["status"],
  "github_job_conclusion":job["conclusion"],
}
pathlib.Path(os.environ["OUT"]).write_text(
    json.dumps(payload,indent=2,sort_keys=True)+"\n"
)
PY
echo "GITHUB_TERMINAL_PROOF=PASS run=$RUN_ID job=$JOB_ID"

sudo env PYTHONDONTWRITEBYTECODE=1   /usr/bin/python3 "$HELPER"   --repo-root "$ROOT"   --expected-source-head "$REPAIR_HEAD"   --github-proof "$TMP/github-terminal-proof.json"

echo "=== V3 ACCEPTED CANARY LEDGER REPAIR: PASS ==="
echo "NEXT_PRODUCTION_SOURCE_HEAD=$PRODUCTION_SOURCE_HEAD"
