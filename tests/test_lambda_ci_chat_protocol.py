from pathlib import Path
import json
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
NS = runpy.run_path(
    str(ROOT / "scripts" / "lambda_ci_chat_protocol.py"),
    run_name="lambda_ci_chat_protocol_test",
)

correlate_run = NS["correlate_run"]
next_action = NS["next_action"]
verify_receipt = NS["verify_receipt"]


def request():
    return {
        "schema_version": 1,
        "repository": "adamtrott78/research-engine",
        "pr_number": 95,
        "pr_title": "Define mostly-local EXTRACT redesign contract",
        "candidate_sha": "a" * 40,
        "workflow_path": ".github/workflows/lambda-ci-p3-cpu.yml",
        "workflow_name": "Lambda CI P3 CPU Validation",
        "actor": "adamtrott78",
        "trigger_comment_id": 12345,
        "trigger_comment_created_at": "2026-10-06T03:23:50Z",
        "baseline_run_number": 4,
        "receipt_artifact": "lambda-ci-p3-receipt",
    }


def run(run_id, run_number, *, title=None, status="queued", conclusion=None):
    return {
        "id": run_id,
        "path": ".github/workflows/lambda-ci-p3-cpu.yml",
        "event": "issue_comment",
        "triggering_actor": {"login": "adamtrott78"},
        "run_number": run_number,
        "created_at": "2026-10-06T03:23:53Z",
        "display_title": (
            title
            if title is not None
            else "Define mostly-local EXTRACT redesign contract"
        ),
        "status": status,
        "conclusion": conclusion,
        # issue_comment runs may expose default-branch SHA; correlation must not
        # mistake this for the candidate SHA.
        "head_sha": "b" * 40,
    }


def test_exact_comment_id_metadata_wins_over_compatibility_candidates():
    req = request()
    rows = [
        run(10, 5),
        run(11, 6, title="Lambda CPU PR #95 comment:12345"),
    ]
    result = correlate_run(req, rows)
    assert result == {
        "decision": "BOUND_RUN",
        "correlation": "EXACT_COMMENT_ID",
        "run_id": 11,
        "run_number": 6,
    }


def test_current_workflow_can_bind_provisionally_when_candidate_is_unique():
    result = correlate_run(request(), [run(10, 5)])
    assert result["decision"] == "BOUND_RUN"
    assert result["correlation"] == "PROVISIONAL_COMPAT"
    assert result["run_id"] == 10


def test_multiple_compatible_runs_fail_closed_instead_of_picking_newest():
    result = correlate_run(request(), [run(10, 5), run(11, 6)])
    assert result["decision"] == "AMBIGUOUS"
    assert result["correlation"] == "MULTIPLE_COMPAT_CANDIDATES"
    assert result["candidate_run_ids"] == [10, 11]


def test_old_or_wrong_actor_runs_are_ignored():
    req = request()
    old = run(9, 4)
    wrong = run(10, 5)
    wrong["triggering_actor"] = {"login": "someone-else"}
    result = correlate_run(req, [old, wrong])
    assert result == {"decision": "WAIT_FOR_RUN", "correlation": "NONE_YET"}


def test_default_branch_head_sha_is_not_used_for_issue_comment_correlation():
    req = request()
    row = run(10, 5)
    assert row["head_sha"] != req["candidate_sha"]
    result = correlate_run(req, [row])
    assert result["decision"] == "BOUND_RUN"


def test_queued_and_active_runs_do_not_request_logs():
    req = request()
    queued = next_action(req, run(10, 5, status="queued"))
    active = next_action(req, run(10, 5, status="in_progress"))

    assert queued == {
        "action": "WAIT_EXTERNAL",
        "dependency": "RUNNER_ALLOCATION",
        "fetch_logs": False,
    }
    assert active == {
        "action": "WAIT_EXTERNAL",
        "dependency": "ACTIVE_COMPUTE",
        "fetch_logs": False,
    }


def test_success_fetches_compact_artifact_before_acceptance():
    req = request()
    completed = run(10, 5, status="completed", conclusion="success")
    result = next_action(req, completed)
    assert result == {
        "action": "FETCH_ARTIFACTS",
        "expected_artifact": "lambda-ci-p3-receipt",
    }


def test_receipt_identity_mismatch_is_rejected():
    req = request()
    receipt = {
        "decision": "PASS",
        "pr_number": 95,
        "expected_sha": req["candidate_sha"],
        "actual_sha": "c" * 40,
    }
    verdict = verify_receipt(req, receipt)
    assert verdict == {"verified": False, "reason": "ACTUAL_SHA_MISMATCH"}

    completed = run(10, 5, status="completed", conclusion="success")
    result = next_action(req, completed, receipt)
    assert result["action"] == "REJECT_EVIDENCE"


def test_matching_terminal_receipt_continues_immediately():
    req = request()
    receipt = {
        "decision": "PASS",
        "pr_number": 95,
        "expected_sha": req["candidate_sha"],
        "actual_sha": req["candidate_sha"],
    }
    completed = run(10, 5, status="completed", conclusion="success")
    result = next_action(req, completed, receipt)
    assert result["action"] == "ACCEPT_AND_CONTINUE"
    assert result["receipt"]["verified"] is True


def test_failed_run_requests_narrow_failure_evidence_ladder():
    req = request()
    completed = run(10, 5, status="completed", conclusion="failure")
    result = next_action(req, completed)
    assert result["action"] == "FETCH_FAILURE_EVIDENCE"
    assert result["order"] == [
        "jobs",
        "failing-step-summary",
        "failing-job-log",
        "receipt",
    ]


def test_run_handle_schema_regexes_decode_to_intended_patterns():
    schema = json.loads(
        (ROOT / "architecture" / "lambda-ci-chat-run.v1.schema.json").read_text()
    )
    repository_pattern = schema["properties"]["repository"]["pattern"]
    workflow_pattern = schema["properties"]["workflow_path"]["pattern"]

    assert repository_pattern == r"^[^/\s]+/[^/\s]+$"
    assert re.fullmatch(repository_pattern, "adamtrott78/research-engine")
    assert not re.fullmatch(repository_pattern, "bad owner/research-engine")

    assert workflow_pattern == r"^\.github/workflows/[^/]+\.ya?ml$"
    assert re.fullmatch(workflow_pattern, ".github/workflows/lambda-ci-p3-cpu.yml")
    assert re.fullmatch(workflow_pattern, ".github/workflows/lambda-ci-p4-gpu.yaml")
    assert not re.fullmatch(workflow_pattern, "xgithub/workflows/lambda-ci-p3-cpu.yml")
