from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
NS = runpy.run_path(
    str(ROOT / "scripts" / "lambda_ci_chat_protocol.py"),
    run_name="lambda_ci_chat_protocol_test",
)

correlate_run = NS["correlate_run"]
correlate_job = NS["correlate_job"]
expected_job_name = NS["expected_job_name"]
next_action = NS["next_action"]
verify_receipt = NS["verify_receipt"]


def request():
    return {
        "schema_version": 1,
        "repository": "adamtrott78/research-engine",
        "pr_number": 106,
        "pr_title": "Admission-v2 live acceptance marker",
        "candidate_sha": "a" * 40,
        "workflow_path": ".github/workflows/lambda-ci-p5-gpu-autonomous.yml",
        "workflow_name": "Lambda CI P5 Autonomous GPU Acceptance",
        "actor": "adamtrott78",
        "trigger_comment_id": 12345,
        "trigger_comment_created_at": "2026-10-06T03:23:50Z",
        "baseline_run_number": 4,
        "job_identity": {
            "workload": "gpu-small",
            "trigger_command": "/lambda-ci-p5-gpu",
        },
        "receipt_artifact": "lambda-ci-p5-gpu-autonomous-receipt",
    }


def run(run_id, run_number, *, title=None, status="queued", conclusion=None):
    return {
        "id": run_id,
        "path": ".github/workflows/lambda-ci-p5-gpu-autonomous.yml",
        "event": "issue_comment",
        "triggering_actor": {"login": "adamtrott78"},
        "run_number": run_number,
        "created_at": "2026-10-06T03:23:53Z",
        "display_title": (
            title
            if title is not None
            else "Admission-v2 live acceptance marker"
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
        run(11, 6, title="Lambda GPU PR #106 comment:12345"),
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
    assert result["correlation"] == "PROVISIONAL_TRIGGER_WINDOW"
    assert result["run_id"] == 10


def test_multiple_compatible_runs_fail_closed_instead_of_picking_newest():
    result = correlate_run(request(), [run(10, 5), run(11, 6)])
    assert result["decision"] == "AMBIGUOUS"
    assert result["correlation"] == "MULTIPLE_TRIGGER_WINDOW_CANDIDATES"
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
        "pr_number": 106,
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
        "pr_number": 106,
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

def job(job_id, *, name=None):
    req = request()
    return {
        "id": job_id,
        "name": name if name is not None else expected_job_name(req),
        "status": "queued",
        "conclusion": None,
    }


def test_unique_trigger_window_does_not_depend_on_pr_display_title():
    row = run(10, 5, title="A display title that is not the PR title")
    result = correlate_run(request(), [row])
    assert result["decision"] == "BOUND_RUN"
    assert result["correlation"] == "PROVISIONAL_TRIGGER_WINDOW"


def test_exact_p5_job_identity_confirms_workload_pr_and_request_sha():
    result = correlate_job(request(), [job(100)])
    assert result["decision"] == "BOUND_JOB"
    assert result["correlation"] == "EXACT_REQUEST_IDENTITY"
    assert result["job_id"] == 100


def test_wrong_sha_or_workload_job_identity_is_not_accepted():
    req = request()
    wrong_sha = expected_job_name(req).replace(req["candidate_sha"], "b" * 40)
    wrong_workload = expected_job_name(req).replace("workload=gpu-small", "workload=cpu-test")
    result = correlate_job(req, [job(100, name=wrong_sha), job(101, name=wrong_workload)])
    assert result["decision"] == "WAIT_FOR_JOB"
    assert result["correlation"] == "NO_EXACT_REQUEST_IDENTITY"


def test_duplicate_exact_job_identities_fail_closed():
    result = correlate_job(request(), [job(100), job(101)])
    assert result["decision"] == "AMBIGUOUS"
    assert result["correlation"] == "MULTIPLE_EXACT_REQUEST_IDENTITIES"
    assert result["candidate_job_ids"] == [100, 101]

