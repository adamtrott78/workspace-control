#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


EXIT_READY = 0
EXIT_REVIEW = 10
EXIT_POLICY = 20
EXIT_STATE = 30


def fail(message, code=EXIT_STATE):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run_git(path, *args):
    proc = subprocess.run(
        ["git", "-C", str(path), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def require_git(path, *args):
    rc, out, err = run_git(path, *args)
    if rc != 0:
        fail(
            f"git command failed at {path}: git {' '.join(args)}"
            + (f"\n{err}" if err else "")
        )
    return out


def query_remote_branch(path, branch):
    rc, out, err = run_git(
        path,
        "ls-remote",
        "--exit-code",
        "origin",
        f"refs/heads/{branch}",
    )

    if rc == 0:
        fields = out.split()
        if len(fields) < 2:
            return {
                "status": "ERROR",
                "branch": branch,
                "sha": None,
                "error": "unexpected ls-remote output",
            }

        return {
            "status": "FOUND",
            "branch": branch,
            "sha": fields[0],
            "error": None,
        }

    if rc == 2:
        return {
            "status": "MISSING",
            "branch": branch,
            "sha": None,
            "error": None,
        }

    return {
        "status": "ERROR",
        "branch": branch,
        "sha": None,
        "error": err or f"git ls-remote exited {rc}",
    }


def load_registry():
    control_root = Path(__file__).resolve().parent.parent
    registry_path = control_root / "repos.json"

    try:
        data = json.loads(registry_path.read_text())
    except FileNotFoundError:
        fail(f"registry not found: {registry_path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid registry JSON: {exc}")

    if data.get("schema_version") != 1:
        fail(f"unsupported registry schema: {data.get('schema_version')!r}")

    root = Path(data["workspace_root"]).expanduser().resolve()
    repos = data.get("repositories")

    if not isinstance(repos, dict) or not repos:
        fail("registry contains no repositories")

    return control_root, root, repos


def is_parent(parent, child):
    parent = Path(parent).resolve()
    child = Path(child).resolve()
    try:
        child.relative_to(parent)
        return parent != child
    except ValueError:
        return False


def status_counts(lines):
    counts = {
        "staged": 0,
        "unstaged": 0,
        "untracked": 0,
    }

    for line in lines:
        if not line:
            continue

        code = line[:2]

        if code == "??":
            counts["untracked"] += 1
            continue

        if len(code) >= 1 and code[0] != " ":
            counts["staged"] += 1

        if len(code) >= 2 and code[1] != " ":
            counts["unstaged"] += 1

    return counts


def get_worktrees(path):
    rc, out, _ = run_git(path, "worktree", "list", "--porcelain")
    if rc != 0 or not out:
        return []

    result = []
    current = {}

    for line in out.splitlines() + [""]:
        if not line:
            if current:
                branch = current.get("branch")
                if branch and branch.startswith("refs/heads/"):
                    branch = branch[len("refs/heads/"):]
                current["branch"] = branch
                result.append(current)
                current = {}
            continue

        if " " in line:
            key, value = line.split(" ", 1)
            current[key] = value
        else:
            current[line] = True

    return result


def inspect_checkout(name, cfg, requested_path, workspace_root, all_repos):
    path = Path(requested_path).expanduser().resolve()

    result = {
        "name": name,
        "registered_path": str((workspace_root / cfg["path"]).resolve()),
        "requested_path": str(path),
        "role": cfg.get("role"),
        "writable": bool(cfg.get("writable", False)),
        "canonical_branch": cfg.get("canonical_branch"),
        "context_entry": cfg.get("context_entry"),
        "worktree_policy": cfg.get("worktree_policy"),
        "recursive_mutation_forbidden": bool(
            cfg.get("recursive_mutation_forbidden", False)
        ),
        "registered_remote": cfg.get("remote"),
        "authority": cfg.get("authority"),
        "exists": path.exists(),
    }

    parent_overlaps = []
    for other_name, other_cfg in all_repos.items():
        if other_name == name:
            continue
        other_path = (workspace_root / other_cfg["path"]).resolve()
        if is_parent(other_path, path):
            parent_overlaps.append(
                {
                    "name": other_name,
                    "path": str(other_path),
                    "writable": bool(other_cfg.get("writable", False)),
                    "recursive_mutation_forbidden": bool(
                        other_cfg.get("recursive_mutation_forbidden", False)
                    ),
                }
            )

    result["registered_parent_overlaps"] = parent_overlaps

    if not path.exists():
        result.update(
            {
                "git": False,
                "clean": None,
                "identity_matches": False,
                "worktrees": [],
            }
        )
        return result

    rc, top, _ = run_git(path, "rev-parse", "--show-toplevel")
    if rc != 0:
        result.update(
            {
                "git": False,
                "clean": None,
                "identity_matches": False,
                "worktrees": [],
            }
        )
        return result

    git_root = Path(top).resolve()
    branch = require_git(git_root, "branch", "--show-current")
    head = require_git(git_root, "rev-parse", "HEAD")

    rc, origin, _ = run_git(git_root, "remote", "get-url", "origin")
    if rc != 0:
        origin = None

    rc, status_out, status_err = run_git(
        git_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )
    if rc != 0:
        fail(f"could not inspect status for {git_root}: {status_err}")

    lines = status_out.splitlines() if status_out else []
    counts = status_counts(lines)

    context_entry = cfg.get("context_entry")
    context_exists = (
        (git_root / context_entry).is_file()
        if context_entry
        else None
    )

    result.update(
        {
            "git": True,
            "git_root": str(git_root),
            "branch": branch if branch else None,
            "detached": not bool(branch),
            "head": head,
            "observed_origin": origin,
            "origin_matches": origin == cfg.get("remote"),
            "identity_matches": origin == cfg.get("remote"),
            "status": counts,
            "clean": not bool(lines),
            "context_exists": context_exists,
            "worktrees": get_worktrees(git_root),
        }
    )

    return result


def print_status_human(records):
    print("============================================================")
    print("WORKSPACE STATUS")
    print("============================================================")

    for r in records:
        print()
        print("------------------------------------------------------------")
        print(f"REPOSITORY: {r['name']}")
        print(f"ROLE:       {r.get('role')}")
        print(f"WRITABLE:   {r.get('writable')}")
        print(f"PATH:       {r.get('requested_path')}")

        if not r.get("exists"):
            print("STATE:      MISSING")
            continue

        if not r.get("git"):
            print("STATE:      NOT_GIT")
            continue

        print(f"BRANCH:     {r.get('branch') or '<detached>'}")
        print(f"HEAD:       {r.get('head')}")
        print(f"ORIGIN:     {r.get('observed_origin') or '<none>'}")
        print(f"ORIGIN_OK:  {r.get('origin_matches')}")

        s = r["status"]
        print(
            "STATUS:     "
            f"staged={s['staged']} "
            f"unstaged={s['unstaged']} "
            f"untracked={s['untracked']} "
            f"clean={r['clean']}"
        )

        if r.get("context_entry"):
            print(
                f"CONTEXT:    {r['context_entry']} "
                f"exists={r.get('context_exists')}"
            )

        overlaps = r.get("registered_parent_overlaps", [])
        if overlaps:
            print("PARENTS:")
            for item in overlaps:
                print(
                    "  - "
                    f"{item['name']} "
                    f"(recursive_mutation_forbidden="
                    f"{item['recursive_mutation_forbidden']})"
                )

        worktrees = r.get("worktrees", [])
        print(f"WORKTREES:  {len(worktrees)}")
        for wt in worktrees:
            print(
                "  - "
                f"{wt.get('worktree')} "
                f"branch={wt.get('branch') or '<detached>'} "
                f"HEAD={wt.get('HEAD')}"
            )


def command_status(args):
    _, workspace_root, repos = load_registry()

    records = []

    for name, cfg in repos.items():
        canonical = workspace_root / cfg["path"]
        records.append(
            inspect_checkout(
                name,
                cfg,
                canonical,
                workspace_root,
                repos,
            )
        )

    payload = {
        "schema_version": 1,
        "workspace_root": str(workspace_root),
        "repositories": records,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_status_human(records)

    return EXIT_READY


def preflight_state(record, intent, allow_dirty):
    if not record.get("exists") or not record.get("git"):
        return "BLOCKED_STATE", EXIT_STATE, [
            "requested path is missing or is not a Git checkout"
        ]

    reasons = []

    if not record.get("identity_matches"):
        return "BLOCKED_IDENTITY", EXIT_STATE, [
            "observed origin does not match the registered repository identity"
        ]

    if intent == "mutate":
        if not record.get("writable"):
            return "BLOCKED_POLICY", EXIT_POLICY, [
                "registry marks this logical repository non-writable"
            ]

        if record.get("recursive_mutation_forbidden"):
            return "BLOCKED_POLICY", EXIT_POLICY, [
                "registry forbids mutation from this repository scope"
            ]

        if record.get("context_entry") and not record.get("context_exists"):
            reasons.append("registered context entry is missing")

        if not record.get("clean") and not allow_dirty:
            reasons.append(
                "checkout is dirty; review it or use an isolated worktree"
            )

        if record.get("branch") == record.get("canonical_branch"):
            remote = record.get("canonical_remote")

            if not remote:
                reasons.append(
                    "remote canonical branch state was not checked"
                )
            elif remote.get("status") == "ERROR":
                reasons.append(
                    "remote canonical branch state could not be verified"
                )
            elif remote.get("status") == "MISSING":
                reasons.append(
                    "registered canonical branch is missing on the remote"
                )
            elif remote.get("sha") != record.get("head"):
                reasons.append(
                    "local canonical branch HEAD differs from remote "
                    "canonical branch; synchronize or use an isolated "
                    "task worktree"
                )

        if reasons:
            return "REVIEW_REQUIRED", EXIT_REVIEW, reasons

    return "READY", EXIT_READY, reasons


def print_preflight_human(record, intent, allow_dirty, state, reasons):
    print("============================================================")
    print("REPOSITORY PREFLIGHT")
    print("============================================================")
    print(f"REPOSITORY:  {record['name']}")
    print(f"INTENT:      {intent}")
    print(f"PATH:        {record['requested_path']}")
    print(f"ROLE:        {record.get('role')}")
    print(f"WRITABLE:    {record.get('writable')}")
    print(f"GIT:         {record.get('git')}")

    if record.get("git"):
        print(f"GIT_ROOT:    {record.get('git_root')}")
        print(f"BRANCH:      {record.get('branch') or '<detached>'}")
        print(f"HEAD:        {record.get('head')}")
        print(f"ORIGIN:      {record.get('observed_origin') or '<none>'}")
        print(f"ORIGIN_OK:   {record.get('origin_matches')}")

        s = record["status"]
        print(
            "STATUS:      "
            f"staged={s['staged']} "
            f"unstaged={s['unstaged']} "
            f"untracked={s['untracked']} "
            f"clean={record['clean']}"
        )

        if record.get("context_entry"):
            print(
                f"CONTEXT:     {record['context_entry']} "
                f"exists={record.get('context_exists')}"
            )

    overlaps = record.get("registered_parent_overlaps", [])
    if overlaps:
        print("PARENT_OVERLAPS:")
        for item in overlaps:
            print(
                "  - "
                f"{item['name']} path={item['path']} "
                f"recursive_mutation_forbidden="
                f"{item['recursive_mutation_forbidden']}"
            )

    remote = record.get("canonical_remote")
    if remote:
        print(
            "REMOTE_MAIN:  "
            f"status={remote.get('status')} "
            f"branch={remote.get('branch')} "
            f"sha={remote.get('sha') or '<none>'}"
        )

    print(f"ALLOW_DIRTY: {allow_dirty}")
    print(f"RESULT:      {state}")

    if reasons:
        print("REASONS:")
        for reason in reasons:
            print(f"  - {reason}")


def command_preflight(args):
    _, workspace_root, repos = load_registry()

    if args.repo not in repos:
        fail(
            f"unknown registered repository: {args.repo}",
            EXIT_STATE,
        )

    cfg = repos[args.repo]
    path = (
        Path(args.path).expanduser()
        if args.path
        else workspace_root / cfg["path"]
    )

    record = inspect_checkout(
        args.repo,
        cfg,
        path,
        workspace_root,
        repos,
    )

    if (
        args.intent == "mutate"
        and record.get("git")
        and record.get("identity_matches")
        and record.get("writable")
        and not record.get("recursive_mutation_forbidden")
        and record.get("branch") == record.get("canonical_branch")
    ):
        record["canonical_remote"] = query_remote_branch(
            Path(record["git_root"]),
            record["canonical_branch"],
        )

    state, code, reasons = preflight_state(
        record,
        args.intent,
        args.allow_dirty,
    )

    payload = {
        "schema_version": 1,
        "intent": args.intent,
        "allow_dirty": args.allow_dirty,
        "result": state,
        "reasons": reasons,
        "repository": record,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_preflight_human(
            record,
            args.intent,
            args.allow_dirty,
            state,
            reasons,
        )

    return code



TASK_STATUSES = {
    "PLANNED",
    "IN_PROGRESS",
    "VALIDATING",
    "CHECKPOINTED",
    "BLOCKED_RUNTIME",
    "BLOCKED_EVIDENCE",
    "NEEDS_USER_DECISION",
    "COMPLETE",
}

HANDOFF_STATUSES = {
    "CHECKPOINTED",
    "BLOCKED_RUNTIME",
    "BLOCKED_EVIDENCE",
    "NEEDS_USER_DECISION",
    "COMPLETE",
}

TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def validate_string_array(value, field, errors, min_items=0):
    if not isinstance(value, list):
        errors.append(f"{field}: expected array")
        return

    if len(value) < min_items:
        errors.append(
            f"{field}: expected at least {min_items} item(s)"
        )

    for index, item in enumerate(value):
        if not is_nonempty_string(item):
            errors.append(
                f"{field}[{index}]: expected nonempty string"
            )


def validate_exact_keys(obj, required, allowed, field, errors):
    if not isinstance(obj, dict):
        errors.append(f"{field}: expected object")
        return False

    missing = sorted(required - set(obj))
    extra = sorted(set(obj) - allowed)

    if missing:
        errors.append(
            f"{field}: missing required keys: {', '.join(missing)}"
        )

    if extra:
        errors.append(
            f"{field}: unexpected keys: {', '.join(extra)}"
        )

    return not missing and not extra


def load_task_capsule(file_path):
    path = Path(file_path).expanduser().resolve()

    try:
        text = path.read_text()
    except OSError as exc:
        fail(f"could not read task capsule {path}: {exc}")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"invalid task-capsule JSON in {path}: {exc}")

    return path, data


def validate_task_capsule_data(data, source_path, repos):
    errors = []

    top_required = {
        "schema_version",
        "task_id",
        "title",
        "status",
        "goal",
        "acceptance_criteria",
        "constraints",
        "repositories",
        "decisions",
        "executed_operations",
        "artifacts",
        "validation",
        "blockers",
        "remaining_work",
        "next_safe_action",
    }

    top_allowed = top_required | {
        "last_executor",
        "notes",
    }

    if not validate_exact_keys(
        data,
        top_required,
        top_allowed,
        "task",
        errors,
    ):
        if not isinstance(data, dict):
            return errors

    if data.get("schema_version") != 1:
        errors.append("schema_version: expected integer 1")

    task_id = data.get("task_id")
    if not is_nonempty_string(task_id):
        errors.append("task_id: expected nonempty string")
    elif not TASK_ID_RE.fullmatch(task_id):
        errors.append(
            "task_id: must match ^[a-z0-9][a-z0-9._-]*$"
        )
    elif source_path.stem != task_id:
        errors.append(
            "task_id: must match task-capsule filename"
        )

    for field in ("title", "goal", "next_safe_action"):
        if not is_nonempty_string(data.get(field)):
            errors.append(f"{field}: expected nonempty string")

    if "last_executor" in data:
        if not is_nonempty_string(data.get("last_executor")):
            errors.append(
                "last_executor: expected nonempty string when present"
            )

    if "notes" in data and not isinstance(data.get("notes"), str):
        errors.append("notes: expected string when present")

    status = data.get("status")
    if status not in TASK_STATUSES:
        errors.append(
            "status: unsupported value "
            f"{status!r}"
        )

    validate_string_array(
        data.get("acceptance_criteria"),
        "acceptance_criteria",
        errors,
        min_items=1,
    )

    for field in (
        "constraints",
        "decisions",
        "blockers",
        "remaining_work",
    ):
        validate_string_array(
            data.get(field),
            field,
            errors,
        )

    repositories = data.get("repositories")

    if not isinstance(repositories, list):
        errors.append("repositories: expected array")
        repositories = []
    elif not repositories:
        errors.append(
            "repositories: expected at least one repository"
        )

    repo_required = {
        "name",
        "intent",
        "checkout_path",
        "branch",
        "base_sha",
        "checkpoint_sha",
        "checkpoint_pushed",
        "allowed_mutation_scope",
    }

    seen_repositories = set()

    for index, entry in enumerate(repositories):
        field = f"repositories[{index}]"

        if not validate_exact_keys(
            entry,
            repo_required,
            repo_required,
            field,
            errors,
        ):
            if not isinstance(entry, dict):
                continue

        name = entry.get("name")

        if not is_nonempty_string(name):
            errors.append(f"{field}.name: expected nonempty string")
        else:
            if name in seen_repositories:
                errors.append(
                    f"{field}.name: duplicate logical repository {name}"
                )

            seen_repositories.add(name)

            if name not in repos:
                errors.append(
                    f"{field}.name: unknown registered repository {name}"
                )

        intent = entry.get("intent")
        if intent not in {"read", "mutate"}:
            errors.append(
                f"{field}.intent: expected read or mutate"
            )

        checkout_path = entry.get("checkout_path")
        if not is_nonempty_string(checkout_path):
            errors.append(
                f"{field}.checkout_path: expected nonempty string"
            )
        elif not Path(checkout_path).expanduser().is_absolute():
            errors.append(
                f"{field}.checkout_path: expected absolute path"
            )

        if not is_nonempty_string(entry.get("branch")):
            errors.append(
                f"{field}.branch: expected nonempty string"
            )

        for sha_field in ("base_sha", "checkpoint_sha"):
            value = entry.get(sha_field)

            if not isinstance(value, str) or not SHA_RE.fullmatch(value):
                errors.append(
                    f"{field}.{sha_field}: expected 40 lowercase hex characters"
                )

        if not isinstance(entry.get("checkpoint_pushed"), bool):
            errors.append(
                f"{field}.checkpoint_pushed: expected boolean"
            )

        validate_string_array(
            entry.get("allowed_mutation_scope"),
            f"{field}.allowed_mutation_scope",
            errors,
        )

        if (
            intent == "mutate"
            and isinstance(
                entry.get("allowed_mutation_scope"),
                list,
            )
            and not entry["allowed_mutation_scope"]
        ):
            errors.append(
                f"{field}.allowed_mutation_scope: "
                "mutation intent requires nonempty scope"
            )

        if name in repos and intent == "mutate":
            cfg = repos[name]

            if not cfg.get("writable", False):
                errors.append(
                    f"{field}: registry marks repository non-writable"
                )

            if cfg.get("recursive_mutation_forbidden", False):
                errors.append(
                    f"{field}: registry forbids mutation from repository scope"
                )

    operations = data.get("executed_operations")

    if not isinstance(operations, list):
        errors.append("executed_operations: expected array")
        operations = []

    operation_required = {"summary", "evidence"}

    for index, entry in enumerate(operations):
        field = f"executed_operations[{index}]"

        if not validate_exact_keys(
            entry,
            operation_required,
            operation_required,
            field,
            errors,
        ):
            if not isinstance(entry, dict):
                continue

        if not is_nonempty_string(entry.get("summary")):
            errors.append(
                f"{field}.summary: expected nonempty string"
            )

        validate_string_array(
            entry.get("evidence"),
            f"{field}.evidence",
            errors,
            min_items=1,
        )

    artifacts = data.get("artifacts")

    if not isinstance(artifacts, list):
        errors.append("artifacts: expected array")
        artifacts = []

    artifact_required = {
        "path",
        "state",
        "evidence",
    }

    for index, entry in enumerate(artifacts):
        field = f"artifacts[{index}]"

        if not validate_exact_keys(
            entry,
            artifact_required,
            artifact_required,
            field,
            errors,
        ):
            if not isinstance(entry, dict):
                continue

        if not is_nonempty_string(entry.get("path")):
            errors.append(
                f"{field}.path: expected nonempty string"
            )

        if not is_nonempty_string(entry.get("state")):
            errors.append(
                f"{field}.state: expected nonempty string"
            )

        validate_string_array(
            entry.get("evidence"),
            f"{field}.evidence",
            errors,
            min_items=1,
        )

    validations = data.get("validation")

    if not isinstance(validations, list):
        errors.append("validation: expected array")
        validations = []

    validation_required = {
        "check",
        "result",
        "evidence",
    }

    for index, entry in enumerate(validations):
        field = f"validation[{index}]"

        if not validate_exact_keys(
            entry,
            validation_required,
            validation_required,
            field,
            errors,
        ):
            if not isinstance(entry, dict):
                continue

        if not is_nonempty_string(entry.get("check")):
            errors.append(
                f"{field}.check: expected nonempty string"
            )

        if entry.get("result") not in {
            "PASS",
            "FAIL",
            "NOT_RUN",
        }:
            errors.append(
                f"{field}.result: expected PASS, FAIL, or NOT_RUN"
            )

        validate_string_array(
            entry.get("evidence"),
            f"{field}.evidence",
            errors,
        )

    if status == "COMPLETE":
        if isinstance(data.get("remaining_work"), list):
            if data["remaining_work"]:
                errors.append(
                    "remaining_work: COMPLETE task must have no remaining work"
                )

        if isinstance(data.get("blockers"), list):
            if data["blockers"]:
                errors.append(
                    "blockers: COMPLETE task must have no blockers"
                )

    if status in {
        "BLOCKED_RUNTIME",
        "BLOCKED_EVIDENCE",
        "NEEDS_USER_DECISION",
    }:
        if isinstance(data.get("blockers"), list):
            if not data["blockers"]:
                errors.append(
                    "blockers: blocked/decision state requires at least one blocker"
                )

    return errors


def task_validation_payload(path, data, repos):
    errors = validate_task_capsule_data(
        data,
        path,
        repos,
    )

    return {
        "schema_version": 1,
        "task_file": str(path),
        "task_id": (
            data.get("task_id")
            if isinstance(data, dict)
            else None
        ),
        "valid": not errors,
        "errors": errors,
    }


def print_task_validation_human(payload):
    print("============================================================")
    print("TASK CAPSULE VALIDATION")
    print("============================================================")
    print(f"FILE:    {payload['task_file']}")
    print(f"TASK_ID: {payload.get('task_id')}")
    print(f"VALID:   {payload['valid']}")

    if payload["errors"]:
        print("ERRORS:")
        for error in payload["errors"]:
            print(f"  - {error}")


def command_task_validate(args):
    _, _, repos = load_registry()
    path, data = load_task_capsule(args.file)

    payload = task_validation_payload(
        path,
        data,
        repos,
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_task_validation_human(payload)

    return EXIT_READY if payload["valid"] else EXIT_STATE


def check_commit_exists(path, sha):
    rc, _, _ = run_git(
        path,
        "cat-file",
        "-e",
        f"{sha}^{{commit}}",
    )
    return rc == 0


def check_ancestor(path, base_sha, checkpoint_sha):
    rc, _, _ = run_git(
        path,
        "merge-base",
        "--is-ancestor",
        base_sha,
        checkpoint_sha,
    )
    return rc == 0


def handoff_assessment(path, data, workspace_root, repos):
    validation = task_validation_payload(
        path,
        data,
        repos,
    )

    if not validation["valid"]:
        return {
            "schema_version": 1,
            "task_file": str(path),
            "task_id": validation.get("task_id"),
            "result": "INVALID_CAPSULE",
            "handoff_safe": False,
            "reasons": validation["errors"],
            "repositories": [],
        }, EXIT_STATE

    reasons = []
    repository_results = []

    if data["status"] not in HANDOFF_STATUSES:
        reasons.append(
            "task status is not an explicit handoff-capable state"
        )

    for entry in data["repositories"]:
        name = entry["name"]
        cfg = repos[name]
        checkout = Path(
            entry["checkout_path"]
        ).expanduser().resolve()

        record = inspect_checkout(
            name,
            cfg,
            checkout,
            workspace_root,
            repos,
        )

        repo_reasons = []

        if not record.get("exists"):
            repo_reasons.append(
                "recorded checkout/worktree path is missing"
            )
        elif not record.get("git"):
            repo_reasons.append(
                "recorded path is not a Git checkout"
            )
        else:
            if not record.get("identity_matches"):
                repo_reasons.append(
                    "observed origin does not match registered repository"
                )

            if record.get("branch") != entry["branch"]:
                repo_reasons.append(
                    "current branch differs from recorded task branch"
                )

            if record.get("head") != entry["checkpoint_sha"]:
                repo_reasons.append(
                    "current HEAD differs from recorded checkpoint SHA"
                )

            if not record.get("clean"):
                repo_reasons.append(
                    "checkout is dirty; v1 handoff requires a clean checkpoint"
                )

            if not check_commit_exists(
                Path(record["git_root"]),
                entry["checkpoint_sha"],
            ):
                repo_reasons.append(
                    "recorded checkpoint commit is not present locally"
                )

            if (
                check_commit_exists(
                    Path(record["git_root"]),
                    entry["base_sha"],
                )
                and check_commit_exists(
                    Path(record["git_root"]),
                    entry["checkpoint_sha"],
                )
                and not check_ancestor(
                    Path(record["git_root"]),
                    entry["base_sha"],
                    entry["checkpoint_sha"],
                )
            ):
                repo_reasons.append(
                    "recorded base SHA is not an ancestor of checkpoint SHA"
                )

            if not check_commit_exists(
                Path(record["git_root"]),
                entry["base_sha"],
            ):
                repo_reasons.append(
                    "recorded base commit is not present locally"
                )

            if entry["intent"] == "mutate":
                if not entry["checkpoint_pushed"]:
                    repo_reasons.append(
                        "mutation checkpoint is not recorded as pushed"
                    )
                else:
                    remote = query_remote_branch(
                        Path(record["git_root"]),
                        entry["branch"],
                    )

                    if remote["status"] == "ERROR":
                        repo_reasons.append(
                            "remote task branch state could not be verified"
                        )
                    elif remote["status"] == "MISSING":
                        repo_reasons.append(
                            "recorded task branch is missing on remote"
                        )
                    elif remote["sha"] != entry["checkpoint_sha"]:
                        repo_reasons.append(
                            "remote task branch does not advertise "
                            "recorded checkpoint SHA"
                        )

        repository_results.append(
            {
                "name": name,
                "intent": entry["intent"],
                "checkout_path": str(checkout),
                "branch": entry["branch"],
                "checkpoint_sha": entry["checkpoint_sha"],
                "checkpoint_pushed": entry["checkpoint_pushed"],
                "ready": not repo_reasons,
                "reasons": repo_reasons,
            }
        )

        for reason in repo_reasons:
            reasons.append(f"{name}: {reason}")

    result = (
        "HANDOFF_SAFE"
        if not reasons
        else "NOT_HANDOFF_SAFE"
    )

    return {
        "schema_version": 1,
        "task_file": str(path),
        "task_id": data["task_id"],
        "status": data["status"],
        "result": result,
        "handoff_safe": not reasons,
        "reasons": reasons,
        "repositories": repository_results,
        "next_safe_action": data["next_safe_action"],
    }, (
        EXIT_READY
        if not reasons
        else EXIT_REVIEW
    )


def print_handoff_human(payload):
    print("============================================================")
    print("TASK HANDOFF ASSESSMENT")
    print("============================================================")
    print(f"FILE:      {payload['task_file']}")
    print(f"TASK_ID:   {payload.get('task_id')}")
    print(f"STATUS:    {payload.get('status')}")
    print(f"RESULT:    {payload['result']}")

    if "next_safe_action" in payload:
        print(
            f"NEXT_SAFE_ACTION: {payload['next_safe_action']}"
        )

    repositories = payload.get("repositories", [])

    if repositories:
        print("REPOSITORIES:")
        for repo in repositories:
            print(
                "  - "
                f"{repo['name']} "
                f"intent={repo['intent']} "
                f"branch={repo['branch']} "
                f"ready={repo['ready']}"
            )

            for reason in repo["reasons"]:
                print(f"      reason: {reason}")

    if payload["reasons"]:
        print("REASONS:")
        for reason in payload["reasons"]:
            print(f"  - {reason}")


def command_handoff_check(args):
    _, workspace_root, repos = load_registry()
    path, data = load_task_capsule(args.file)

    payload, code = handoff_assessment(
        path,
        data,
        workspace_root,
        repos,
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_handoff_human(payload)

    return code


def build_parser():
    parser = argparse.ArgumentParser(
        description="Executor-neutral workspace control CLI"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser(
        "status",
        help="observe all registered logical repositories",
    )
    status.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    status.set_defaults(func=command_status)

    preflight = sub.add_parser(
        "preflight",
        help="establish checkout state before a read or mutation",
    )
    preflight.add_argument(
        "--repo",
        required=True,
        help="logical repository name from repos.json",
    )
    preflight.add_argument(
        "--path",
        help="specific checkout/worktree path; defaults to registered path",
    )
    preflight.add_argument(
        "--intent",
        choices=("read", "mutate"),
        default="read",
    )
    preflight.add_argument(
        "--allow-dirty",
        action="store_true",
        help="acknowledge reviewed dirty state for mutation",
    )
    preflight.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    preflight.set_defaults(func=command_preflight)

    task_validate = sub.add_parser(
        "task-validate",
        help="validate a durable task capsule",
    )
    task_validate.add_argument(
        "--file",
        required=True,
        help="path to task-capsule JSON",
    )
    task_validate.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    task_validate.set_defaults(func=command_task_validate)

    handoff = sub.add_parser(
        "handoff-check",
        help="assess whether a task capsule is handoff-safe",
    )
    handoff.add_argument(
        "--file",
        required=True,
        help="path to task-capsule JSON",
    )
    handoff.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    handoff.set_defaults(func=command_handoff_check)

    return parser


def main():
    if sys.version_info < (3, 8):
        fail("Python 3.8 or newer is required")

    parser = build_parser()
    args = parser.parse_args()

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
