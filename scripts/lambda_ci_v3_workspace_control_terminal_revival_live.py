#!/usr/bin/env python3
"""Source-bound live V3 workspace-control terminal-record revival transaction.

This operator never writes a scheduler ledger and never dispatches, cancels, or
reruns a GitHub workflow. It installs a class-specific controller executable
override for workspace-control-control-small-v1, restarts only that exact v3
controller, and then observes the controller-owned durable ledger for a fresh
REST-attested attempt.

Execution authority is external: an accepted, automatically-consumed
authority-sensitive GitHub review request for the exact transaction head.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import pathlib
import pwd
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

REPOSITORY = "adamtrott78/workspace-control"
TASK_ID = "workspace-github-actions-selfhosted-control-plane-v1"

# Previously accepted code/state-machine review that this live transaction may
# install. The live transaction must not accept any controller source drift.
CODE_REVIEW_PR = 602
CODE_REVIEW_REQUEST_COMMENT = 6801484654
CODE_REVIEW_DISPOSITION_COMMENT = 6801586149
CODE_REVIEW_CONSUMED_COMMENT = 6801591386
REVIEWED_CONTROLLER_HEAD = "4196934cad14ddf3238c4637da4229b8d5e0fc60"
REVIEWED_CONTROLLER_GO_BLOB = "5823ffbf922ebc367c973a921f28963ea726ffa1"
REVIEWED_CONTROLLER_TEST_BLOB = "8404791b6ffdde9a63fb70978b3403e350478bf6"

LIVE_REVIEW_KIND = "workspace_control_v3_rest_terminal_revival_live_transaction_20261111"

TARGET_CLASS = "workspace-control-control-small-v1"
TARGET_SERVICE = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
TARGET_USER = "ci-ctl-wc-control"
TARGET_GROUP = "ci-gh-workspace-control"
TARGET_SCALE_SET = "lambda-workspace-control-control-small"
TARGET_RUNNER_PREFIX = "lambda-workspace-control-control-small-"

LEGACY_V2_SERVICE = "workspace-ci-controller@workspace-control-cpu.service"
PROVISIONER_SERVICE = "workspace-ci-v3-provisioner.service"
RECONCILER_SERVICE = "workspace-ci-v3-reconciler.service"

WORKFLOW_RUN_ID = 42881495845
GITHUB_JOB_ID = 130058639814
WORKFLOW_RUN_NUMBER = 389
WORKFLOW_PATH = ".github/workflows/lambda-ci-workspace-control-validation.yml"
WORKFLOW_BLOB = "7e361db3a8ead667c047e9dc3fe12908c10eb96a"
WORKFLOW_HEAD_SHA = "3bee43a810d739cb199c5091024b8d91115aa5d6"
WORKFLOW_EVENT = "issue_comment"
OWNER_ACTOR = "adamtrott78"

STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/controller/state")
LEDGER_PATH = STATE_ROOT / TARGET_CLASS / f"scheduler-{GITHUB_JOB_ID}.json"
EXPECTED_LEDGER_SHA256 = "39c5ed5b4b3337433fc8608a82f7d2a767ebd575ab0aa507cf3bbaa70a5fb5b9"
EXPECTED_OLD_REQUEST_ID = "a5ea4df1-284f-5566-bc64-f8bb1867f69a"
EXPECTED_OLD_RUNNER_NAME = "lambda-workspace-control-control-small-369d468744b1"

POLICY_PATH = pathlib.Path(f"/etc/workspace-ci/v3/controllers/{TARGET_CLASS}.json")
ROOT_POLICY_PATH = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")

OVERRIDE_ROOT = pathlib.Path("/opt/workspace-ci/v3/controller-overrides") / TARGET_CLASS
OVERRIDE_BINARY = OVERRIDE_ROOT / "lambda-ci-controller-v3"
DROPIN_DIR = pathlib.Path(f"/etc/systemd/system/{TARGET_SERVICE}.d")
DROPIN_PATH = DROPIN_DIR / "99-terminal-revival-reviewed.conf"
RECEIPT_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/workspace-control-terminal-revival")

REVIEW_BINDING_PATHS = (
    "scripts/lambda_ci_v3_workspace_control_terminal_revival_live.py",
    "scripts/lambda_ci_v3_workspace_control_terminal_revival_live.sh",
    "tests/test_lambda_ci_v3_workspace_control_terminal_revival_live.py",
    "architecture/lambda-ci-v3-workspace-control-terminal-revival-live.v1.md",
)

REQUEST_START = "WORKSPACE_CONTROL_REVIEW_REQUEST_V1"
REQUEST_END = "END_WORKSPACE_CONTROL_REVIEW_REQUEST_V1"
DISP_START = "WORKSPACE_CONTROL_REVIEW_DISPOSITION_V1"
DISP_END = "END_WORKSPACE_CONTROL_REVIEW_DISPOSITION_V1"
CONSUMED_START = "WORKSPACE_CONTROL_REVIEW_CONSUMED_V1"
CONSUMED_END = "END_WORKSPACE_CONTROL_REVIEW_CONSUMED_V1"

REQUEST_KEYS = frozenset({
    "task_id", "pr_number", "head_sha", "base_sha", "tree_sha",
    "review_kind", "sensitivity", "bindings_sha256",
    "request_copilot", "request_digest",
})
DISPOSITION_KEYS = frozenset({
    "request_comment_id", "request_digest", "task_id", "pr_number",
    "head_sha", "review_kind", "sensitivity",
    "reviewer_attestation", "disposition",
})
CONSUMPTION_KEYS = frozenset({
    "request_comment_id", "request_digest", "task_id", "pr_number",
    "head_sha", "review_kind", "sensitivity", "backend",
    "disposition_id", "disposition",
})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class LiveRevivalError(RuntimeError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveRevivalError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise LiveRevivalError(f"expected JSON object: {path}")
    return value


def canonical(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: pathlib.Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with tmp.open("wb") as handle:
        os.chmod(tmp, mode)
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def exact_block(body: str, start: str, end: str) -> dict[str, str]:
    source = body.splitlines()
    starts = [i for i, line in enumerate(source) if line.strip() == start]
    ends = [i for i, line in enumerate(source) if line.strip() == end]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise LiveRevivalError(f"review block multiplicity/order invalid: {start}")
    lines = [line.strip() for line in source[starts[0] + 1 : ends[0]] if line.strip()]
    result: dict[str, str] = {}
    for line in lines:
        if "=" not in line:
            raise LiveRevivalError(f"review block line invalid: {line}")
        key, value = line.split("=", 1)
        if not key or key in result:
            raise LiveRevivalError(f"review block key invalid/duplicate: {key}")
        result[key] = value
    return result


def git(repo_root: pathlib.Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_root), *args],
        text=True,
    ).strip()


def git_blob(repo_root: pathlib.Path, head: str, path: str) -> str:
    return git(repo_root, "rev-parse", f"{head}:{path}")


def assert_source(repo_root: pathlib.Path) -> str:
    head = git(repo_root, "rev-parse", "HEAD")
    if git(repo_root, "status", "--porcelain", "--untracked-files=all"):
        raise LiveRevivalError("source tree is not completely clean, including untracked files")
    attached = subprocess.run(
        ["git", "-C", str(repo_root), "symbolic-ref", "-q", "HEAD"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    if attached:
        raise LiveRevivalError("live transaction requires detached HEAD")

    if git_blob(repo_root, head, "controller/lambda-ci-controller/v3/controller.go") != REVIEWED_CONTROLLER_GO_BLOB:
        raise LiveRevivalError("reviewed controller.go blob drift")
    if git_blob(repo_root, head, "controller/lambda-ci-controller/v3/controller_test.go") != REVIEWED_CONTROLLER_TEST_BLOB:
        raise LiveRevivalError("reviewed controller_test.go blob drift")
    return head


def read_token(path: pathlib.Path) -> str:
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) & 0o077:
        raise LiveRevivalError("GitHub token file must be a private regular file")
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise LiveRevivalError("GitHub token file is empty")
    return token


def github_get(token: str, api_path: str) -> Any:
    url = f"https://api.github.com{api_path}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "workspace-control-v3-terminal-revival-live",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            value = json.load(response)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise LiveRevivalError(f"GitHub GET failed: {api_path}") from exc
    return value


def issue_comment(token: str, comment_id: int) -> dict[str, Any]:
    value = github_get(token, f"/repos/{REPOSITORY}/issues/comments/{comment_id}")
    if not isinstance(value, dict) or int(value.get("id", 0)) != comment_id:
        raise LiveRevivalError(f"GitHub comment identity mismatch: {comment_id}")
    return value


def issue_comments(token: str, pr_number: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    page = 1
    while True:
        value = github_get(
            token,
            f"/repos/{REPOSITORY}/issues/{pr_number}/comments?per_page=100&page={page}",
        )
        if not isinstance(value, list):
            raise LiveRevivalError("GitHub issue comments response invalid")
        result.extend(item for item in value if isinstance(item, dict))
        if len(value) < 100:
            return result
        page += 1


def require_exact_keys(fields: dict[str, str], expected: frozenset[str], label: str) -> None:
    if set(fields) != set(expected):
        missing = sorted(set(expected) - set(fields))
        extra = sorted(set(fields) - set(expected))
        raise LiveRevivalError(f"{label} keys mismatch: missing={missing} extra={extra}")


def compact_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verified_request_digest(fields: dict[str, str]) -> str:
    require_exact_keys(fields, REQUEST_KEYS, "review request")
    supplied = fields["request_digest"]
    if SHA256_RE.fullmatch(supplied) is None:
        raise LiveRevivalError("review request digest format invalid")
    unsigned = {key: value for key, value in fields.items() if key != "request_digest"}
    computed = sha256(compact_json(unsigned))
    if supplied != computed:
        raise LiveRevivalError("review request digest mismatch")
    return supplied


def validate_bound_review_state(
    *,
    request_fields: dict[str, str],
    request_comment_id: int,
    expected_common: dict[str, str],
    dispositions: list[tuple[int, dict[str, str], str]],
    consumptions: list[tuple[int, dict[str, str], str]],
) -> dict[str, Any]:
    request_digest = verified_request_digest(request_fields)
    for key, value in expected_common.items():
        if request_fields.get(key) != value:
            raise LiveRevivalError(f"review request mismatch: {key}")

    if len(dispositions) != 1:
        raise LiveRevivalError(
            f"review request must have exactly one bound disposition, found {len(dispositions)}"
        )
    disposition_id, disposition, disposition_user = dispositions[0]
    require_exact_keys(disposition, DISPOSITION_KEYS, "review disposition")
    expected_disposition = {
        "request_comment_id": str(request_comment_id),
        "request_digest": request_digest,
        "task_id": expected_common["task_id"],
        "pr_number": expected_common["pr_number"],
        "head_sha": expected_common["head_sha"],
        "review_kind": expected_common["review_kind"],
        "sensitivity": expected_common["sensitivity"],
        "reviewer_attestation": "fresh_independent_session",
        "disposition": "NO_BLOCKING_FINDING",
    }
    if disposition != expected_disposition:
        raise LiveRevivalError("review disposition fields do not exactly match request authority")
    if disposition_user == "github-actions[bot]":
        raise LiveRevivalError("independent review disposition cannot be automation-authored")

    if len(consumptions) != 1:
        raise LiveRevivalError(
            f"review request must have exactly one bound consumption, found {len(consumptions)}"
        )
    consumption_id, consumption, consumption_user = consumptions[0]
    require_exact_keys(consumption, CONSUMPTION_KEYS, "review consumption")
    expected_consumption = {
        "request_comment_id": str(request_comment_id),
        "request_digest": request_digest,
        "task_id": expected_common["task_id"],
        "pr_number": expected_common["pr_number"],
        "head_sha": expected_common["head_sha"],
        "review_kind": expected_common["review_kind"],
        "sensitivity": expected_common["sensitivity"],
        "backend": "comment",
        "disposition_id": str(disposition_id),
        "disposition": "NO_BLOCKING_FINDING",
    }
    if consumption != expected_consumption:
        raise LiveRevivalError("review consumption fields do not exactly match accepted disposition")
    if consumption_user != "github-actions[bot]":
        raise LiveRevivalError("review consumption is not automation-authored")

    return {
        "review_request_comment_id": request_comment_id,
        "review_request_digest": request_digest,
        "review_disposition_comment_id": disposition_id,
        "review_consumption_comment_id": consumption_id,
    }


def verify_code_review_acceptance(token: str) -> None:
    request = issue_comment(token, CODE_REVIEW_REQUEST_COMMENT)
    if request.get("user", {}).get("login") != "github-actions[bot]":
        raise LiveRevivalError("accepted controller review request is not automation-authored")
    request_fields = exact_block(str(request.get("body", "")), REQUEST_START, REQUEST_END)
    require_exact_keys(request_fields, REQUEST_KEYS, "accepted controller review request")
    verified_request_digest(request_fields)

    expected_common = {
        "task_id": TASK_ID,
        "pr_number": str(CODE_REVIEW_PR),
        "head_sha": REVIEWED_CONTROLLER_HEAD,
        "review_kind": "workspace_control_v3_rest_terminal_revival_bf2_corrected_20261111",
        "sensitivity": "authority_sensitive",
    }
    for key, value in {**expected_common, "request_copilot": "false"}.items():
        if request_fields.get(key) != value:
            raise LiveRevivalError(f"accepted controller review request mismatch: {key}")

    dispositions: list[tuple[int, dict[str, str], str]] = []
    consumptions: list[tuple[int, dict[str, str], str]] = []
    for comment in issue_comments(token, CODE_REVIEW_PR):
        body = str(comment.get("body", ""))
        cid = int(comment.get("id", 0))
        user = str(comment.get("user", {}).get("login") or "")
        if DISP_START in body:
            value = exact_block(body, DISP_START, DISP_END)
            if value.get("request_comment_id") == str(CODE_REVIEW_REQUEST_COMMENT):
                dispositions.append((cid, value, user))
        if CONSUMED_START in body:
            value = exact_block(body, CONSUMED_START, CONSUMED_END)
            if value.get("request_comment_id") == str(CODE_REVIEW_REQUEST_COMMENT):
                consumptions.append((cid, value, user))

    accepted = validate_bound_review_state(
        request_fields=request_fields,
        request_comment_id=CODE_REVIEW_REQUEST_COMMENT,
        expected_common=expected_common,
        dispositions=dispositions,
        consumptions=consumptions,
    )
    if accepted["review_disposition_comment_id"] != CODE_REVIEW_DISPOSITION_COMMENT:
        raise LiveRevivalError("accepted controller disposition comment identity drift")
    if accepted["review_consumption_comment_id"] != CODE_REVIEW_CONSUMED_COMMENT:
        raise LiveRevivalError("accepted controller consumption comment identity drift")

def request_bindings(body: str) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for path, blob in re.findall(r"^-\s+([^\n]+?)\s+->\s+([0-9a-f]{40})\s*$", body, re.MULTILINE):
        bindings[path.strip()] = blob
    return bindings


def verify_live_review(
    token: str,
    repo_root: pathlib.Path,
    *,
    pr_number: int,
    request_comment_id: int,
    head: str,
) -> dict[str, Any]:
    pr = github_get(token, f"/repos/{REPOSITORY}/pulls/{pr_number}")
    if (
        not isinstance(pr, dict)
        or pr.get("state") != "open"
        or pr.get("head", {}).get("repo", {}).get("full_name") != REPOSITORY
        or pr.get("head", {}).get("sha") != head
    ):
        raise LiveRevivalError("live transaction PR/head binding mismatch")

    request = issue_comment(token, request_comment_id)
    if request.get("user", {}).get("login") != "github-actions[bot]":
        raise LiveRevivalError("live review request is not automation-authored")
    body = str(request.get("body", ""))
    fields = exact_block(body, REQUEST_START, REQUEST_END)
    require_exact_keys(fields, REQUEST_KEYS, "live review request")

    base_sha = str(pr.get("base", {}).get("sha") or "")
    tree_sha = git(repo_root, "rev-parse", f"{head}^{{tree}}")
    bindings = request_bindings(body)
    if set(bindings) != set(REVIEW_BINDING_PATHS):
        raise LiveRevivalError("live review changed-path binding set mismatch")
    rows = [
        {"path": path, "blob": bindings[path]}
        for path in sorted(bindings)
    ]
    expected_bindings_digest = sha256(compact_json(rows))
    expected_request = {
        "task_id": TASK_ID,
        "pr_number": str(pr_number),
        "head_sha": head,
        "base_sha": base_sha,
        "tree_sha": tree_sha,
        "review_kind": LIVE_REVIEW_KIND,
        "sensitivity": "authority_sensitive",
        "bindings_sha256": expected_bindings_digest,
        "request_copilot": "false",
    }
    for key, value in expected_request.items():
        if fields.get(key) != value:
            raise LiveRevivalError(f"live review request mismatch: {key}")
    verified_request_digest(fields)

    for path in REVIEW_BINDING_PATHS:
        actual = git_blob(repo_root, head, path)
        if bindings[path] != actual:
            raise LiveRevivalError(f"live review binding mismatch: {path}")

    dispositions: list[tuple[int, dict[str, str], str]] = []
    consumptions: list[tuple[int, dict[str, str], str]] = []
    for comment in issue_comments(token, pr_number):
        comment_body = str(comment.get("body", ""))
        cid = int(comment.get("id", 0))
        user = str(comment.get("user", {}).get("login") or "")
        if DISP_START in comment_body:
            value = exact_block(comment_body, DISP_START, DISP_END)
            if value.get("request_comment_id") == str(request_comment_id):
                dispositions.append((cid, value, user))
        if CONSUMED_START in comment_body:
            value = exact_block(comment_body, CONSUMED_START, CONSUMED_END)
            if value.get("request_comment_id") == str(request_comment_id):
                consumptions.append((cid, value, user))

    return validate_bound_review_state(
        request_fields=fields,
        request_comment_id=request_comment_id,
        expected_common={
            "task_id": TASK_ID,
            "pr_number": str(pr_number),
            "head_sha": head,
            "review_kind": LIVE_REVIEW_KIND,
            "sensitivity": "authority_sensitive",
        },
        dispositions=dispositions,
        consumptions=consumptions,
    )

def verify_scheduler(token: str) -> dict[str, Any]:
    run = github_get(token, f"/repos/{REPOSITORY}/actions/runs/{WORKFLOW_RUN_ID}")
    if not isinstance(run, dict):
        raise LiveRevivalError("scheduler run response invalid")
    expected_run = {
        "id": WORKFLOW_RUN_ID,
        "run_number": WORKFLOW_RUN_NUMBER,
        "event": WORKFLOW_EVENT,
        "status": "queued",
        "conclusion": None,
        "path": WORKFLOW_PATH,
        "head_sha": WORKFLOW_HEAD_SHA,
    }
    for key, value in expected_run.items():
        if run.get(key) != value:
            raise LiveRevivalError(f"scheduler run precondition mismatch: {key}")
    if run.get("actor", {}).get("login") != OWNER_ACTOR or run.get("triggering_actor", {}).get("login") != OWNER_ACTOR:
        raise LiveRevivalError("scheduler actor binding mismatch")

    jobs = github_get(token, f"/repos/{REPOSITORY}/actions/runs/{WORKFLOW_RUN_ID}/jobs?filter=latest&per_page=100")
    if not isinstance(jobs, dict) or not isinstance(jobs.get("jobs"), list):
        raise LiveRevivalError("scheduler jobs response invalid")
    matches = [job for job in jobs["jobs"] if isinstance(job, dict) and job.get("id") == GITHUB_JOB_ID]
    if len(matches) != 1:
        raise LiveRevivalError("exact scheduler job missing/ambiguous")
    job = matches[0]
    if job.get("status") != "queued" or job.get("conclusion") is not None:
        raise LiveRevivalError("scheduler job is no longer queued")
    if job.get("runner_id") not in (0, None) or str(job.get("runner_name") or "").strip():
        raise LiveRevivalError("scheduler job is already runner-bound")
    labels = job.get("labels")
    if not isinstance(labels, list) or TARGET_SCALE_SET not in labels:
        raise LiveRevivalError("scheduler target scale-set label missing")
    if job.get("run_id") != WORKFLOW_RUN_ID or job.get("head_sha") != WORKFLOW_HEAD_SHA:
        raise LiveRevivalError("scheduler job/run binding mismatch")
    return {
        "run_id": WORKFLOW_RUN_ID,
        "job_id": GITHUB_JOB_ID,
        "run_status": run.get("status"),
        "job_status": job.get("status"),
        "labels": labels,
        "runner_id": job.get("runner_id"),
        "runner_name": job.get("runner_name"),
    }


def scheduler_snapshot(token: str) -> dict[str, Any]:
    run = github_get(token, f"/repos/{REPOSITORY}/actions/runs/{WORKFLOW_RUN_ID}")
    jobs = github_get(token, f"/repos/{REPOSITORY}/actions/runs/{WORKFLOW_RUN_ID}/jobs?filter=latest&per_page=100")
    values = jobs.get("jobs") if isinstance(jobs, dict) else None
    if not isinstance(run, dict) or not isinstance(values, list):
        raise LiveRevivalError("scheduler post-revival evidence invalid")
    matches = [job for job in values if isinstance(job, dict) and job.get("id") == GITHUB_JOB_ID]
    if len(matches) != 1:
        raise LiveRevivalError("scheduler post-revival job missing/ambiguous")
    job = matches[0]
    return {
        "run_status": run.get("status"),
        "run_conclusion": run.get("conclusion"),
        "job_status": job.get("status"),
        "job_conclusion": job.get("conclusion"),
        "runner_id": job.get("runner_id"),
        "runner_name": job.get("runner_name"),
        "labels": job.get("labels"),
    }


def systemctl_show(unit: str) -> dict[str, str]:
    props = (
        "Id", "LoadState", "ActiveState", "SubState", "MainPID", "NRestarts",
        "InvocationID", "User", "Group", "Type", "RemainAfterExit",
        "Result", "ExecMainStatus",
    )
    raw = subprocess.check_output(
        ["systemctl", "show", unit, "--no-pager", *[f"--property={p}" for p in props]],
        text=True,
    )
    result: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def require_running_service(unit: str) -> dict[str, str]:
    value = systemctl_show(unit)
    if (
        value.get("LoadState") != "loaded"
        or value.get("ActiveState") != "active"
        or value.get("SubState") != "running"
        or int(value.get("MainPID") or 0) <= 0
    ):
        raise LiveRevivalError(f"required long-running service is not healthy: {unit}")
    return value


def require_verified_oneshot_service(unit: str) -> dict[str, str]:
    value = systemctl_show(unit)
    if value.get("LoadState") != "loaded":
        raise LiveRevivalError(f"required oneshot verifier is not loaded: {unit}")
    if value.get("Type") != "oneshot" or value.get("RemainAfterExit") != "yes":
        raise LiveRevivalError(f"required reconciler unit semantics drifted: {unit}")
    if (
        value.get("ActiveState") != "active"
        or value.get("SubState") != "exited"
        or int(value.get("MainPID") or 0) != 0
        or value.get("Result") != "success"
        or value.get("ExecMainStatus") != "0"
    ):
        raise LiveRevivalError(f"required oneshot verifier is not healthy/verified: {unit}")
    return value


def class_ids() -> list[str]:
    root = load_json(ROOT_POLICY_PATH)
    classes = root.get("runner_classes")
    if not isinstance(classes, dict) or TARGET_CLASS not in classes:
        raise LiveRevivalError("installed root policy class set invalid")
    return sorted(str(key) for key in classes)


def snapshot_services() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for class_id in class_ids():
        unit = f"workspace-ci-v3-controller@{class_id}.service"
        result[unit] = systemctl_show(unit)
    return result


def verify_service_boundary() -> dict[str, dict[str, str]]:
    provisioner = require_running_service(PROVISIONER_SERVICE)
    if provisioner.get("Type") not in ("", "simple"):
        raise LiveRevivalError("V3 provisioner unit type drift")
    if provisioner.get("User") != "root" or provisioner.get("Group") != "root":
        raise LiveRevivalError("V3 provisioner service identity mismatch")

    reconciler = require_verified_oneshot_service(RECONCILER_SERVICE)
    if reconciler.get("User") != "root" or reconciler.get("Group") != "root":
        raise LiveRevivalError("V3 reconciler service identity mismatch")

    target = require_running_service(TARGET_SERVICE)
    if target.get("User") != TARGET_USER or target.get("Group") != TARGET_GROUP:
        raise LiveRevivalError("target controller service identity mismatch")
    legacy = systemctl_show(LEGACY_V2_SERVICE)
    if legacy.get("ActiveState") == "active":
        raise LiveRevivalError("retired v2 workspace-control controller is active")
    return snapshot_services()


def verify_policy() -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    expected = {
        "runner_class_id": TARGET_CLASS,
        "repository": REPOSITORY,
        "scale_set_name": TARGET_SCALE_SET,
        "runner_prefix": TARGET_RUNNER_PREFIX,
        "max_runners": 1,
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            raise LiveRevivalError(f"production controller policy mismatch: {key}")
    workflows = policy.get("trusted_workflows")
    if not isinstance(workflows, list) or len(workflows) != 1:
        raise LiveRevivalError("production controller workflow set invalid")
    workflow = workflows[0]
    if (
        workflow.get("path") != WORKFLOW_PATH
        or workflow.get("blob_sha") != WORKFLOW_BLOB
        or workflow.get("allowed_events") != [WORKFLOW_EVENT]
        or workflow.get("allowed_actor_logins") != [OWNER_ACTOR]
    ):
        raise LiveRevivalError("production trusted workflow binding mismatch")
    return policy


def verify_ledger(policy: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    if LEDGER_PATH.is_symlink() or not LEDGER_PATH.is_file():
        raise LiveRevivalError("target ledger is not a regular file")
    st = LEDGER_PATH.stat()
    if stat.S_IMODE(st.st_mode) != 0o600:
        raise LiveRevivalError("target ledger mode mismatch")
    expected_uid = pwd.getpwnam(TARGET_USER).pw_uid
    if st.st_uid != expected_uid:
        raise LiveRevivalError("target ledger owner mismatch")
    raw = LEDGER_PATH.read_bytes()
    if sha256(raw) != EXPECTED_LEDGER_SHA256:
        raise LiveRevivalError("target ledger byte digest changed; fresh review required")
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LiveRevivalError("target ledger JSON invalid") from exc
    expected = {
        "runner_request_id": GITHUB_JOB_ID,
        "github_job_id": GITHUB_JOB_ID,
        "authority_source": "REST_ACTIVE_JOB_SET",
        "workflow_run_id": WORKFLOW_RUN_ID,
        "workflow_path": WORKFLOW_PATH,
        "workflow_blob_sha": WORKFLOW_BLOB,
        "request_id": EXPECTED_OLD_REQUEST_ID,
        "runner_name": EXPECTED_OLD_RUNNER_NAME,
        "state": "COMPLETED",
        "scheduler_state": "COMPLETED",
        "last_root_status": "COMPLETED",
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise LiveRevivalError(f"target ledger precondition mismatch: {key}")
    if record.get("controller_policy_sha256") != policy.get("controller_policy_sha256"):
        raise LiveRevivalError("ledger/controller-policy binding mismatch")
    if not isinstance(record.get("provision_attempt"), int) or record["provision_attempt"] < 0:
        raise LiveRevivalError("target ledger provision_attempt invalid")
    return raw, record


def materialize_reviewed_controller_source(
    repo_root: pathlib.Path,
    destination: pathlib.Path,
) -> pathlib.Path:
    destination.mkdir(parents=True, exist_ok=False)
    archive = subprocess.check_output(
        [
            "git", "-C", str(repo_root), "archive", "--format=tar",
            REVIEWED_CONTROLLER_HEAD, "controller/lambda-ci-controller",
        ]
    )
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as handle:
        members = handle.getmembers()
        for member in members:
            parts = pathlib.PurePosixPath(member.name).parts
            if member.name.startswith("/") or ".." in parts:
                raise LiveRevivalError("reviewed Git archive contains unsafe path")
        handle.extractall(destination)
    source = destination / "controller/lambda-ci-controller"
    if not (source / "go.mod").is_file() or not (source / "v3").is_dir():
        raise LiveRevivalError("reviewed controller Git archive is incomplete")
    return source


def build_controller(repo_root: pathlib.Path, go_bin: str, output: pathlib.Path) -> str:
    version = subprocess.check_output([go_bin, "env", "GOVERSION"], text=True).strip()
    if version != "go1.26.3":
        raise LiveRevivalError(f"Go version mismatch: {version}")

    source_root = output.parent / "reviewed-controller-source"
    source = materialize_reviewed_controller_source(repo_root, source_root)
    build_env = os.environ.copy()
    build_env["GOWORK"] = "off"
    build_env["GOENV"] = "off"
    build_env["GOFLAGS"] = ""
    subprocess.run(
        [go_bin, "build", "-mod=readonly", "-trimpath", "-o", str(output), "./v3"],
        cwd=source,
        env=build_env,
        check=True,
    )
    raw = output.read_bytes()
    if not raw:
        raise LiveRevivalError("built controller is empty")
    return sha256(raw)

def dropin_bytes() -> bytes:
    return (
        "[Service]\n"
        "ExecStart=\n"
        f"ExecStart={OVERRIDE_BINARY}\n"
    ).encode("utf-8")


def assert_no_existing_override() -> None:
    if OVERRIDE_BINARY.exists() or OVERRIDE_BINARY.is_symlink():
        raise LiveRevivalError("target class executable override already exists")
    if DROPIN_PATH.exists() or DROPIN_PATH.is_symlink():
        raise LiveRevivalError("target class systemd override already exists")


def write_receipt(path: pathlib.Path, value: dict[str, Any]) -> None:
    value["updated_at_unix"] = time.time()
    atomic_write(path, canonical(value), 0o600)


def verify_siblings_unchanged(
    before: dict[str, dict[str, str]],
    after: dict[str, dict[str, str]],
) -> None:
    for unit, old in before.items():
        if unit == TARGET_SERVICE:
            continue
        if after.get(unit) != old:
            raise LiveRevivalError(f"sibling v3 controller changed: {unit}")


def wait_target_active() -> dict[str, str]:
    last: dict[str, str] = {}
    for _ in range(40):
        last = systemctl_show(TARGET_SERVICE)
        if last.get("ActiveState") == "active" and last.get("SubState") == "running" and int(last.get("MainPID") or 0) > 0:
            return last
        time.sleep(0.25)
    raise LiveRevivalError(f"target controller did not become active/running: {last}")


def wait_target_stopped() -> dict[str, str]:
    last: dict[str, str] = {}
    for _ in range(40):
        last = systemctl_show(TARGET_SERVICE)
        if (
            last.get("ActiveState") == "inactive"
            and last.get("SubState") == "dead"
            and int(last.get("MainPID") or 0) == 0
        ):
            return last
        time.sleep(0.25)
    raise LiveRevivalError(f"target controller did not become fully stopped: {last}")


def observe_first_revival(old_raw: bytes, old_record: dict[str, Any]) -> dict[str, Any]:
    for _ in range(120):
        raw = LEDGER_PATH.read_bytes()
        if raw != old_raw:
            try:
                current = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise LiveRevivalError("revived ledger JSON invalid") from exc
            immutable = (
                "runner_request_id",
                "github_job_id",
                "authority_source",
                "workflow_run_id",
                "workflow_path",
                "workflow_blob_sha",
                "controller_policy_sha256",
            )
            for key in immutable:
                if current.get(key) != old_record.get(key):
                    raise LiveRevivalError(f"revived ledger provenance changed: {key}")
            if current.get("provision_attempt") != old_record["provision_attempt"] + 1:
                raise LiveRevivalError("first revival did not increment provision_attempt exactly once")
            if current.get("request_id") == old_record.get("request_id"):
                raise LiveRevivalError("revival reused old request_id")
            if current.get("runner_name") == old_record.get("runner_name"):
                raise LiveRevivalError("revival reused old runner_name")
            if current.get("scheduler_state") != "REST_ATTESTED_QUEUED_RETRY":
                raise LiveRevivalError("revival scheduler_state mismatch")
            return {
                "ledger_sha256": sha256(raw),
                "provision_attempt": current.get("provision_attempt"),
                "request_id": current.get("request_id"),
                "runner_name": current.get("runner_name"),
                "state": current.get("state"),
                "scheduler_state": current.get("scheduler_state"),
                "last_root_status": current.get("last_root_status"),
            }
        time.sleep(0.25)
    raise LiveRevivalError("controller did not produce a fresh ledger attempt")


def rollback_before_revival(
    receipt: dict[str, Any],
    receipt_path: pathlib.Path,
    old_raw: bytes,
) -> None:
    # Quiesce the accepted controller before deciding whether scheduler
    # authority has been crossed. Once fully stopped, it cannot race a later
    # ledger write against removal of the accepted executable override.
    try:
        subprocess.run(["systemctl", "stop", TARGET_SERVICE], check=True)
        stopped = wait_target_stopped()
        receipt["rollback_target_quiesced"] = stopped
        write_receipt(receipt_path, receipt)
    except Exception as exc:
        receipt["phase"] = "ROLLBACK_QUIESCE_FAILED_OVERRIDE_RETAINED"
        write_receipt(receipt_path, receipt)
        raise LiveRevivalError("could not quiesce accepted controller for rollback") from exc

    try:
        current_raw = LEDGER_PATH.read_bytes()
    except Exception as exc:
        receipt["phase"] = "ROLLBACK_LEDGER_REATTEST_FAILED_OVERRIDE_RETAINED"
        write_receipt(receipt_path, receipt)
        raise LiveRevivalError("could not re-attest ledger after target quiescence") from exc

    if current_raw != old_raw:
        receipt["phase"] = "POST_REVIVAL_FAIL_CLOSED_NO_ROLLBACK"
        receipt["ledger_after_quiesce_sha256"] = sha256(current_raw)
        receipt["accepted_override_retained"] = True
        receipt["target_controller_left_quiesced"] = True
        write_receipt(receipt_path, receipt)
        raise LiveRevivalError(
            "ledger changed before rollback decision; accepted override retained and target left quiesced"
        )

    try:
        if DROPIN_PATH.exists():
            DROPIN_PATH.unlink()
        if OVERRIDE_BINARY.exists():
            OVERRIDE_BINARY.unlink()
        try:
            OVERRIDE_ROOT.rmdir()
        except OSError:
            pass
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "start", TARGET_SERVICE], check=True)
        restored = wait_target_active()
        receipt["phase"] = "ROLLED_BACK_BEFORE_REVIVAL"
        receipt["restored_target_service"] = restored
        write_receipt(receipt_path, receipt)
    except Exception as exc:
        receipt["phase"] = "ROLLBACK_FAILED"
        write_receipt(receipt_path, receipt)
        raise LiveRevivalError("pre-revival rollback failed") from exc

def preflight(
    token: str,
    repo_root: pathlib.Path,
    *,
    pr_number: int,
    request_comment_id: int,
) -> dict[str, Any]:
    if os.geteuid() != 0:
        raise LiveRevivalError("live transaction preflight requires root")
    head = assert_source(repo_root)
    verify_code_review_acceptance(token)
    review = verify_live_review(
        token,
        repo_root,
        pr_number=pr_number,
        request_comment_id=request_comment_id,
        head=head,
    )
    scheduler = verify_scheduler(token)
    services = verify_service_boundary()
    policy = verify_policy()
    ledger_raw, ledger = verify_ledger(policy)
    assert_no_existing_override()
    return {
        "head": head,
        "review": review,
        "scheduler": scheduler,
        "services": services,
        "policy": policy,
        "ledger_raw": ledger_raw,
        "ledger": ledger,
    }


def apply(
    token: str,
    repo_root: pathlib.Path,
    *,
    pr_number: int,
    request_comment_id: int,
    go_bin: str,
) -> pathlib.Path:
    evidence = preflight(
        token,
        repo_root,
        pr_number=pr_number,
        request_comment_id=request_comment_id,
    )

    # Re-attest scheduler immediately before the mutation boundary.
    verify_scheduler(token)

    with tempfile.TemporaryDirectory(prefix="workspace-ci-v3-wc-terminal-revival-") as raw:
        candidate = pathlib.Path(raw) / "lambda-ci-controller-v3"
        candidate_sha = build_controller(repo_root, go_bin, candidate)

        # Re-attest both external scheduler truth and exact durable bytes after
        # build time but before any host mutation.
        verify_scheduler(token)
        policy = verify_policy()
        latest_raw, latest_record = verify_ledger(policy)
        if latest_raw != evidence["ledger_raw"]:
            raise LiveRevivalError("ledger changed during staging; refusing mutation")

        RECEIPT_ROOT.mkdir(parents=True, exist_ok=True)
        os.chmod(RECEIPT_ROOT, 0o700)
        tx_id = str(uuid.uuid4())
        tx_dir = RECEIPT_ROOT / tx_id
        tx_dir.mkdir(mode=0o700)
        ledger_backup = tx_dir / "ledger-before.json"
        atomic_write(ledger_backup, latest_raw, 0o600)
        receipt_path = tx_dir / "receipt.json"

        receipt: dict[str, Any] = {
            "schema_version": 1,
            "mode": "V3_WORKSPACE_CONTROL_TERMINAL_REST_REVIVAL",
            "transaction_id": tx_id,
            "phase": "PREPARED",
            "source_head": evidence["head"],
            "accepted_controller_head": REVIEWED_CONTROLLER_HEAD,
            "target_class": TARGET_CLASS,
            "target_service": TARGET_SERVICE,
            "workflow_run_id": WORKFLOW_RUN_ID,
            "github_job_id": GITHUB_JOB_ID,
            "ledger_path": str(LEDGER_PATH),
            "ledger_before_sha256": sha256(latest_raw),
            "ledger_backup_path": str(ledger_backup),
            "controller_candidate_sha256": candidate_sha,
            "review": evidence["review"],
            "scheduler_precondition": evidence["scheduler"],
            "target_service_before": evidence["services"][TARGET_SERVICE],
            "sibling_services_before": {
                key: value
                for key, value in evidence["services"].items()
                if key != TARGET_SERVICE
            },
            "script_mutates_scheduler_ledger": False,
            "workflow_dispatched": False,
            "workflow_cancelled": False,
            "workflow_rerun": False,
            "legacy_v2_mutated": False,
        }
        write_receipt(receipt_path, receipt)

        try:
            OVERRIDE_ROOT.mkdir(parents=True, exist_ok=False)
            os.chmod(OVERRIDE_ROOT, 0o755)
            atomic_write(OVERRIDE_BINARY, candidate.read_bytes(), 0o755)
            DROPIN_DIR.mkdir(parents=True, exist_ok=True)
            atomic_write(DROPIN_PATH, dropin_bytes(), 0o644)
            receipt["phase"] = "OVERRIDE_MATERIALIZED"
            write_receipt(receipt_path, receipt)

            subprocess.run(["systemctl", "daemon-reload"], check=True)
            receipt["phase"] = "DAEMON_RELOAD_COMPLETE"
            write_receipt(receipt_path, receipt)

            # One and only one controller restart is permitted by this operator.
            subprocess.run(["systemctl", "restart", TARGET_SERVICE], check=True)
            target_after = wait_target_active()
            service_after = snapshot_services()
            verify_siblings_unchanged(evidence["services"], service_after)
            legacy = systemctl_show(LEGACY_V2_SERVICE)
            if legacy.get("ActiveState") == "active":
                raise LiveRevivalError("retired v2 controller activated during transaction")

            receipt["phase"] = "TARGET_RESTARTED"
            receipt["target_service_after"] = target_after
            write_receipt(receipt_path, receipt)

            revival = observe_first_revival(latest_raw, latest_record)
            receipt["phase"] = "REVIVAL_OBSERVED"
            receipt["revival"] = revival
            receipt["scheduler_after_revival"] = scheduler_snapshot(token)
            write_receipt(receipt_path, receipt)
            return receipt_path
        except Exception:
            rollback_before_revival(receipt, receipt_path, latest_raw)
            raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, required=True)
    parser.add_argument("--github-token-file", type=pathlib.Path, required=True)
    parser.add_argument("--live-pr-number", type=int, required=True)
    parser.add_argument("--review-request-comment-id", type=int, required=True)
    parser.add_argument("--go-bin", default="go")
    parser.add_argument("--verify-preflight", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.verify_preflight == args.apply:
        raise LiveRevivalError("choose exactly one of --verify-preflight or --apply")
    repo_root = args.repo_root.resolve()
    token = read_token(args.github_token_file)

    if args.verify_preflight:
        value = preflight(
            token,
            repo_root,
            pr_number=args.live_pr_number,
            request_comment_id=args.review_request_comment_id,
        )
        print("V3_WORKSPACE_CONTROL_TERMINAL_REVIVAL_PREFLIGHT=PASS")
        print(f"SOURCE_HEAD={value['head']}")
        print(f"LEDGER_SHA256={sha256(value['ledger_raw'])}")
        return 0

    receipt = apply(
        token,
        repo_root,
        pr_number=args.live_pr_number,
        request_comment_id=args.review_request_comment_id,
        go_bin=args.go_bin,
    )
    print("V3_WORKSPACE_CONTROL_TERMINAL_REVIVAL=PASS")
    print(f"TRANSACTION_RECEIPT={receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
