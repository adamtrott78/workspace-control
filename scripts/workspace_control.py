#!/usr/bin/env python3

import argparse
import fnmatch
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


def query_remote_branch_url(remote, branch):
    proc = subprocess.run(
        [
            "git",
            "ls-remote",
            "--exit-code",
            remote,
            f"refs/heads/{branch}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out = proc.stdout.strip()
    err = proc.stderr.strip()

    if proc.returncode == 0:
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

    if proc.returncode == 2:
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
        "error": err or f"git ls-remote exited {proc.returncode}",
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


def inspect_remote(name, cfg, branch):
    remote = cfg.get("remote")
    result = {
        "name": name,
        "topology": "remote",
        "role": cfg.get("role"),
        "writable": bool(cfg.get("writable", False)),
        "canonical_branch": cfg.get("canonical_branch"),
        "branch": branch,
        "registered_remote": remote,
        "authority": cfg.get("authority"),
        "recursive_mutation_forbidden": bool(
            cfg.get("recursive_mutation_forbidden", False)
        ),
    }

    if not remote:
        result["advertised"] = {
            "status": "ERROR",
            "branch": branch,
            "sha": None,
            "error": "registered remote is missing",
        }
    else:
        result["advertised"] = query_remote_branch_url(remote, branch)

    return result


def mutation_path_allowed(path, allowed_scope):
    return any(
        fnmatch.fnmatchcase(path, pattern)
        for pattern in allowed_scope
    )


def remote_preflight_state(
    record,
    intent,
    expected_parent,
    surface_write_ready,
    consequence,
    allowed_scope,
    mutation_paths,
):
    advertised = record.get("advertised") or {}

    if advertised.get("status") == "ERROR":
        return "BLOCKED_STATE", EXIT_STATE, [
            "remote branch state could not be established"
        ]

    if advertised.get("status") == "MISSING":
        return "BLOCKED_STATE", EXIT_STATE, [
            "requested remote branch is missing"
        ]

    reasons = []

    if expected_parent and advertised.get("sha") != expected_parent:
        reasons.append(
            "advertised remote branch SHA differs from the expected parent"
        )

    if intent == "mutate":
        if not record.get("writable"):
            return "BLOCKED_POLICY", EXIT_POLICY, [
                "registry marks this logical repository non-writable"
            ]

        if record.get("recursive_mutation_forbidden"):
            return "BLOCKED_POLICY", EXIT_POLICY, [
                "registry forbids mutation from this repository scope"
            ]

        if not expected_parent:
            reasons.append(
                "remote mutation requires an explicit expected parent"
            )

        if not surface_write_ready:
            reasons.append(
                "remote mutation requires explicit confirmation that the "
                "selected operation surface has write capability and access"
            )

        if consequence is None:
            reasons.append(
                "remote mutation requires an explicit consequence class"
            )
        elif consequence == "read_only":
            reasons.append(
                "read_only consequence is incompatible with mutate intent"
            )
        elif consequence in {"destructive", "external"}:
            reasons.append(
                "higher-consequence remote mutation requires additional "
                "authority or human-gate validation outside preflight"
            )

        if mutation_paths:
            if not allowed_scope:
                reasons.append(
                    "mutation paths were supplied without an allowed "
                    "mutation scope"
                )
            else:
                outside = [
                    path
                    for path in mutation_paths
                    if not mutation_path_allowed(path, allowed_scope)
                ]
                if outside:
                    return "BLOCKED_POLICY", EXIT_POLICY, [
                        "proposed mutation path is outside the allowed scope: "
                        + path
                        for path in outside
                    ]

    if reasons:
        return "REVIEW_REQUIRED", EXIT_REVIEW, reasons

    return "READY", EXIT_READY, []


def print_remote_preflight_human(
    record,
    intent,
    expected_parent,
    surface_write_ready,
    consequence,
    allowed_scope,
    mutation_paths,
    state,
    reasons,
):
    print("============================================================")
    print("REMOTE REPOSITORY PREFLIGHT")
    print("============================================================")
    print(f"REPOSITORY:   {record['name']}")
    print("TOPOLOGY:     remote")
    print(f"INTENT:       {intent}")
    print(f"ROLE:         {record.get('role')}")
    print(f"WRITABLE:     {record.get('writable')}")
    print(f"REMOTE:       {record.get('registered_remote') or '<none>'}")
    print(f"BRANCH:       {record.get('branch')}")

    advertised = record.get("advertised") or {}
    print(
        "ADVERTISED:   "
        f"status={advertised.get('status')} "
        f"sha={advertised.get('sha') or '<none>'}"
    )
    print(f"EXPECTED:     {expected_parent or '<none>'}")
    print(f"WRITE_READY:  {surface_write_ready}")
    print(f"CONSEQUENCE:  {consequence or '<none>'}")

    if allowed_scope:
        print("ALLOWED_SCOPE:")
        for pattern in allowed_scope:
            print(f"  - {pattern}")

    if mutation_paths:
        print("MUTATION_PATHS:")
        for path in mutation_paths:
            print(f"  - {path}")

    print(f"RESULT:       {state}")

    if reasons:
        print("REASONS:")
        for reason in reasons:
            print(f"  - {reason}")


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

    if args.topology == "remote":
        if args.path:
            fail("--path is only valid for local preflight", 2)
        if args.allow_dirty:
            fail("--allow-dirty is only valid for local preflight", 2)

        branch = args.branch or cfg.get("canonical_branch")
        if not branch:
            fail(
                "remote preflight requires --branch when no canonical "
                "branch is registered",
                2,
            )

        if args.expected_parent and not re.fullmatch(
            r"[0-9a-f]{40}",
            args.expected_parent,
        ):
            fail("--expected-parent must be a 40-character Git SHA", 2)

        for value in args.allowed_path + args.mutation_path:
            path = Path(value)
            if (
                not value
                or path.is_absolute()
                or ".." in path.parts
            ):
                fail(
                    "remote mutation scope/path values must be "
                    "repository-relative",
                    2,
                )

        consequence = args.consequence
        if args.intent == "read" and consequence is None:
            consequence = "read_only"

        record = inspect_remote(args.repo, cfg, branch)
        state, code, reasons = remote_preflight_state(
            record,
            args.intent,
            args.expected_parent,
            args.surface_write_ready,
            consequence,
            args.allowed_path,
            args.mutation_path,
        )

        payload = {
            "schema_version": 2,
            "topology": "remote",
            "intent": args.intent,
            "expected_parent": args.expected_parent,
            "surface_write_ready": args.surface_write_ready,
            "consequence": consequence,
            "allowed_scope": args.allowed_path,
            "mutation_paths": args.mutation_path,
            "result": state,
            "reasons": reasons,
            "repository": record,
        }

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print_remote_preflight_human(
                record,
                args.intent,
                args.expected_parent,
                args.surface_write_ready,
                consequence,
                args.allowed_path,
                args.mutation_path,
                state,
                reasons,
            )

        return code

    remote_only_values = (
        args.branch,
        args.expected_parent,
        args.surface_write_ready,
        args.consequence,
        args.allowed_path,
        args.mutation_path,
    )
    if any(remote_only_values):
        fail(
            "remote-only preflight options require --topology remote",
            2,
        )

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

TASK_STATUSES_V2 = TASK_STATUSES | {"SUSPENDED"}

STAGE_STATUSES_V2 = {
    "PLANNED",
    "IN_PROGRESS",
    "VALIDATED",
    "SUSPENDED",
    "FAILED",
    "SKIPPED",
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


def validate_task_capsule_v1_data(data, source_path, repos):
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



def validate_validation_entries(value, field, errors):
    if not isinstance(value, list):
        errors.append(f"{field}: expected array")
        return

    required = {"check", "result", "evidence"}

    for index, entry in enumerate(value):
        item_field = f"{field}[{index}]"

        if not validate_exact_keys(
            entry,
            required,
            required,
            item_field,
            errors,
        ):
            if not isinstance(entry, dict):
                continue

        if not is_nonempty_string(entry.get("check")):
            errors.append(
                f"{item_field}.check: expected nonempty string"
            )

        if entry.get("result") not in {"PASS", "FAIL", "NOT_RUN"}:
            errors.append(
                f"{item_field}.result: expected PASS, FAIL, or NOT_RUN"
            )

        validate_string_array(
            entry.get("evidence"),
            f"{item_field}.evidence",
            errors,
        )


def validate_task_capsule_v2_data(data, source_path, repos):
    errors = []

    top_required = {
        "schema_version",
        "task_id",
        "title",
        "status",
        "goal",
        "execution_topology",
        "acceptance_criteria",
        "constraints",
        "repositories",
        "stages",
        "checkpoints",
        "artifacts",
        "validation",
        "blockers",
        "remaining_work",
        "next_safe_action",
    }

    top_allowed = top_required | {
        "workflow",
        "parent_execution_owner",
        "current_stage",
        "last_executor",
        "last_surface",
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

    if data.get("schema_version") != 2:
        errors.append("schema_version: expected integer 2")

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

    for field in ("last_executor", "last_surface"):
        if field in data and not is_nonempty_string(data.get(field)):
            errors.append(
                f"{field}: expected nonempty string when present"
            )

    if "notes" in data and not isinstance(data.get("notes"), str):
        errors.append("notes: expected string when present")

    status = data.get("status")
    if status not in TASK_STATUSES_V2:
        errors.append(f"status: unsupported value {status!r}")

    topology = data.get("execution_topology")
    if topology not in {"remote_only", "local", "composed"}:
        errors.append(
            "execution_topology: expected remote_only, local, or composed"
        )

    validate_string_array(
        data.get("acceptance_criteria"),
        "acceptance_criteria",
        errors,
        min_items=1,
    )

    for field in ("constraints", "blockers", "remaining_work"):
        validate_string_array(data.get(field), field, errors)

    workflow = data.get("workflow")
    if workflow is not None:
        workflow_required = {
            "repository",
            "path",
            "checkpoint_sha",
        }
        workflow_allowed = workflow_required | {"content_sha"}

        if validate_exact_keys(
            workflow,
            workflow_required,
            workflow_allowed,
            "workflow",
            errors,
        ):
            if not is_nonempty_string(workflow.get("repository")):
                errors.append(
                    "workflow.repository: expected nonempty string"
                )
            elif workflow["repository"] not in repos:
                errors.append(
                    "workflow.repository: unknown registered repository "
                    f"{workflow['repository']}"
                )

            if not is_nonempty_string(workflow.get("path")):
                errors.append("workflow.path: expected nonempty string")

            workflow_sha = workflow.get("checkpoint_sha")
            if (
                not isinstance(workflow_sha, str)
                or not SHA_RE.fullmatch(workflow_sha)
            ):
                errors.append(
                    "workflow.checkpoint_sha: "
                    "expected 40 lowercase hex characters"
                )

            if "content_sha" in workflow:
                if not is_nonempty_string(workflow.get("content_sha")):
                    errors.append(
                        "workflow.content_sha: "
                        "expected nonempty string when present"
                    )

    parent_owner = data.get("parent_execution_owner")
    if parent_owner is not None and not is_nonempty_string(parent_owner):
        errors.append(
            "parent_execution_owner: expected string or null"
        )

    repositories = data.get("repositories")
    if not isinstance(repositories, list):
        errors.append("repositories: expected array")
        repositories = []
    elif not repositories:
        errors.append(
            "repositories: expected at least one repository"
        )

    repo_required = {"name", "intent", "allowed_mutation_scope"}
    repo_allowed = repo_required | {"base_sha", "remote", "local"}
    seen_repositories = set()
    has_remote = False
    has_local = False

    for index, entry in enumerate(repositories):
        field = f"repositories[{index}]"

        if not validate_exact_keys(
            entry,
            repo_required,
            repo_allowed,
            field,
            errors,
        ):
            if not isinstance(entry, dict):
                continue

        name = entry.get("name")
        if not is_nonempty_string(name):
            errors.append(
                f"{field}.name: expected nonempty string"
            )
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

        base_sha = entry.get("base_sha")
        if base_sha is not None:
            if (
                not isinstance(base_sha, str)
                or not SHA_RE.fullmatch(base_sha)
            ):
                errors.append(
                    f"{field}.base_sha: expected 40 lowercase "
                    "hex characters or null"
                )

        remote = entry.get("remote")
        if remote is not None:
            has_remote = True
            remote_required = {
                "branch",
                "checkpoint_sha",
                "verified",
            }

            if validate_exact_keys(
                remote,
                remote_required,
                remote_required,
                f"{field}.remote",
                errors,
            ):
                if not is_nonempty_string(remote.get("branch")):
                    errors.append(
                        f"{field}.remote.branch: expected nonempty string"
                    )

                remote_sha = remote.get("checkpoint_sha")
                if (
                    not isinstance(remote_sha, str)
                    or not SHA_RE.fullmatch(remote_sha)
                ):
                    errors.append(
                        f"{field}.remote.checkpoint_sha: expected "
                        "40 lowercase hex characters"
                    )

                if not isinstance(remote.get("verified"), bool):
                    errors.append(
                        f"{field}.remote.verified: expected boolean"
                    )

        local = entry.get("local")
        if local is not None:
            has_local = True
            local_required = {
                "checkout_path",
                "branch",
                "head_sha",
                "clean",
            }

            if validate_exact_keys(
                local,
                local_required,
                local_required,
                f"{field}.local",
                errors,
            ):
                checkout_path = local.get("checkout_path")
                if not is_nonempty_string(checkout_path):
                    errors.append(
                        f"{field}.local.checkout_path: "
                        "expected nonempty string"
                    )
                elif not Path(
                    checkout_path
                ).expanduser().is_absolute():
                    errors.append(
                        f"{field}.local.checkout_path: "
                        "expected absolute path"
                    )

                if not is_nonempty_string(local.get("branch")):
                    errors.append(
                        f"{field}.local.branch: expected nonempty string"
                    )

                head_sha = local.get("head_sha")
                if (
                    not isinstance(head_sha, str)
                    or not SHA_RE.fullmatch(head_sha)
                ):
                    errors.append(
                        f"{field}.local.head_sha: expected "
                        "40 lowercase hex characters"
                    )

                if not isinstance(local.get("clean"), bool):
                    errors.append(
                        f"{field}.local.clean: expected boolean"
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

    if topology == "remote_only":
        if not has_remote:
            errors.append(
                "execution_topology: remote_only requires remote "
                "repository state"
            )
        if has_local:
            errors.append(
                "execution_topology: remote_only must not require "
                "local repository state"
            )
    elif topology == "local":
        if not has_local:
            errors.append(
                "execution_topology: local requires local repository state"
            )
    elif topology == "composed":
        if not has_remote or not has_local:
            errors.append(
                "execution_topology: composed requires both remote "
                "and local state"
            )

    stages = data.get("stages")
    if not isinstance(stages, list):
        errors.append("stages: expected array")
        stages = []

    stage_required = {
        "id",
        "status",
        "execution_owner",
        "validation",
    }
    stage_allowed = stage_required | {
        "selected_executor",
        "selected_surface",
        "inputs",
        "outputs",
        "resume_condition",
    }
    stage_ids = set()
    stage_status = {}

    for index, entry in enumerate(stages):
        field = f"stages[{index}]"

        if not validate_exact_keys(
            entry,
            stage_required,
            stage_allowed,
            field,
            errors,
        ):
            if not isinstance(entry, dict):
                continue

        stage_id = entry.get("id")
        if not is_nonempty_string(stage_id):
            errors.append(
                f"{field}.id: expected nonempty string"
            )
        elif not TASK_ID_RE.fullmatch(stage_id):
            errors.append(
                f"{field}.id: must match ^[a-z0-9][a-z0-9._-]*$"
            )
        else:
            if stage_id in stage_ids:
                errors.append(
                    f"{field}.id: duplicate stage id {stage_id}"
                )
            stage_ids.add(stage_id)
            stage_status[stage_id] = entry.get("status")

        if entry.get("status") not in STAGE_STATUSES_V2:
            errors.append(
                f"{field}.status: unsupported value "
                f"{entry.get('status')!r}"
            )

        if not is_nonempty_string(entry.get("execution_owner")):
            errors.append(
                f"{field}.execution_owner: expected nonempty string"
            )

        for optional_string in (
            "selected_executor",
            "selected_surface",
        ):
            value = entry.get(optional_string)
            if (
                value is not None
                and not is_nonempty_string(value)
            ):
                errors.append(
                    f"{field}.{optional_string}: expected string or null"
                )

        for string_array in ("inputs", "outputs"):
            if string_array in entry:
                validate_string_array(
                    entry.get(string_array),
                    f"{field}.{string_array}",
                    errors,
                )

        validate_validation_entries(
            entry.get("validation"),
            f"{field}.validation",
            errors,
        )

        resume_condition = entry.get("resume_condition")
        if (
            resume_condition is not None
            and not is_nonempty_string(resume_condition)
        ):
            errors.append(
                f"{field}.resume_condition: expected string or null"
            )

    current_stage = data.get("current_stage")
    if current_stage is not None:
        if not is_nonempty_string(current_stage):
            errors.append(
                "current_stage: expected string or null"
            )
        elif current_stage not in stage_ids:
            errors.append(
                "current_stage: must identify a declared stage"
            )

    checkpoints = data.get("checkpoints")
    if not isinstance(checkpoints, list):
        errors.append("checkpoints: expected array")
        checkpoints = []

    checkpoint_required = {
        "id",
        "kind",
        "identity",
        "required_for_resume",
    }
    checkpoint_allowed = checkpoint_required | {"evidence"}
    checkpoint_ids = set()
    required_resume_checkpoints = 0

    for index, entry in enumerate(checkpoints):
        field = f"checkpoints[{index}]"

        if not validate_exact_keys(
            entry,
            checkpoint_required,
            checkpoint_allowed,
            field,
            errors,
        ):
            if not isinstance(entry, dict):
                continue

        checkpoint_id = entry.get("id")
        if not is_nonempty_string(checkpoint_id):
            errors.append(
                f"{field}.id: expected nonempty string"
            )
        elif checkpoint_id in checkpoint_ids:
            errors.append(
                f"{field}.id: duplicate checkpoint id {checkpoint_id}"
            )
        else:
            checkpoint_ids.add(checkpoint_id)

        for string_field in ("kind", "identity"):
            if not is_nonempty_string(entry.get(string_field)):
                errors.append(
                    f"{field}.{string_field}: expected nonempty string"
                )

        if not isinstance(
            entry.get("required_for_resume"),
            bool,
        ):
            errors.append(
                f"{field}.required_for_resume: expected boolean"
            )
        elif entry["required_for_resume"]:
            required_resume_checkpoints += 1

        if "evidence" in entry:
            validate_string_array(
                entry.get("evidence"),
                f"{field}.evidence",
                errors,
            )

    if status in {"CHECKPOINTED", "SUSPENDED", "COMPLETE"}:
        if required_resume_checkpoints < 1:
            errors.append(
                "checkpoints: handoff/suspended/complete state "
                "requires at least one required_for_resume checkpoint"
            )

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts: expected array")
        artifacts = []

    artifact_required = {"path", "state", "evidence"}
    artifact_allowed = artifact_required | {
        "role",
        "origin",
        "persistence",
        "regeneration",
        "review_requirement",
    }

    for index, entry in enumerate(artifacts):
        field = f"artifacts[{index}]"

        if not validate_exact_keys(
            entry,
            artifact_required,
            artifact_allowed,
            field,
            errors,
        ):
            if not isinstance(entry, dict):
                continue

        for string_field in ("path", "state"):
            if not is_nonempty_string(entry.get(string_field)):
                errors.append(
                    f"{field}.{string_field}: expected nonempty string"
                )

        for optional_string in (
            "role",
            "origin",
            "persistence",
            "regeneration",
            "review_requirement",
        ):
            value = entry.get(optional_string)
            if (
                value is not None
                and not is_nonempty_string(value)
            ):
                errors.append(
                    f"{field}.{optional_string}: expected string or null"
                )

        validate_string_array(
            entry.get("evidence"),
            f"{field}.evidence",
            errors,
        )

    validate_validation_entries(
        data.get("validation"),
        "validation",
        errors,
    )

    if status == "COMPLETE":
        if isinstance(data.get("remaining_work"), list):
            if data["remaining_work"]:
                errors.append(
                    "remaining_work: COMPLETE task must have no "
                    "remaining work"
                )

        if isinstance(data.get("blockers"), list):
            if data["blockers"]:
                errors.append(
                    "blockers: COMPLETE task must have no blockers"
                )

    if status == "SUSPENDED":
        if isinstance(data.get("blockers"), list):
            if not data["blockers"]:
                errors.append(
                    "blockers: SUSPENDED task requires a recorded "
                    "gate/blocker"
                )

        if (
            is_nonempty_string(current_stage)
            and stage_status.get(current_stage) != "SUSPENDED"
        ):
            errors.append(
                "current_stage: SUSPENDED task must identify "
                "a suspended stage"
            )

    if status in {
        "BLOCKED_RUNTIME",
        "BLOCKED_EVIDENCE",
        "NEEDS_USER_DECISION",
    }:
        if isinstance(data.get("blockers"), list):
            if not data["blockers"]:
                errors.append(
                    "blockers: blocked/decision state requires "
                    "at least one blocker"
                )

    return errors


def validate_task_capsule_data(data, source_path, repos):
    if not isinstance(data, dict):
        return ["task: expected object"]

    version = data.get("schema_version")

    if version == 1:
        return validate_task_capsule_v1_data(
            data,
            source_path,
            repos,
        )

    if version == 2:
        return validate_task_capsule_v2_data(
            data,
            source_path,
            repos,
        )

    return [
        "schema_version: unsupported value "
        f"{version!r}; expected 1 or 2"
    ]


DERIVED_HANDOFF_MARKER = (
    "<!-- workspace-control:derived-task-handoff -->"
)


def task_reference(path, control_root):
    try:
        return str(path.relative_to(control_root))
    except ValueError:
        return path.name


def render_task_handoff(path, data, control_root):
    ref = task_reference(path, control_root)
    lines = [
        DERIVED_HANDOFF_MARKER,
        "# Workspace Control Task Handoff",
        "",
        "Derived human-readable view.",
        "",
        f"Authoritative capsule: {ref}",
        "",
        "If this view disagrees with the JSON capsule or verified "
        "Git/runtime evidence, trust the capsule plus verified evidence.",
        "",
        "## Task",
        "",
        f"- ID: {data.get('task_id')}",
        f"- Title: {data.get('title')}",
        f"- Status: {data.get('status')}",
        f"- Capsule schema: v{data.get('schema_version')}",
        "",
        "## Goal",
        "",
        str(data.get("goal", "")),
        "",
    ]

    workflow = data.get("workflow")
    if isinstance(workflow, dict):
        lines.extend([
            "## Workflow",
            "",
            f"- Repository: {workflow.get('repository')}",
            f"- Path: {workflow.get('path')}",
            f"- Checkpoint: {workflow.get('checkpoint_sha')}",
            "",
        ])

    lines.extend(["## Repositories", ""])

    for entry in data.get("repositories", []):
        lines.extend([
            f"### {entry.get('name')}",
            "",
            f"- Intent: {entry.get('intent')}",
        ])

        if data.get("schema_version") == 1:
            lines.extend([
                f"- Branch: {entry.get('branch')}",
                f"- Checkpoint: {entry.get('checkpoint_sha')}",
                f"- Pushed: {entry.get('checkpoint_pushed')}",
            ])
        else:
            remote = entry.get("remote")
            if isinstance(remote, dict):
                lines.extend([
                    f"- Remote branch: {remote.get('branch')}",
                    f"- Remote checkpoint: {remote.get('checkpoint_sha')}",
                    f"- Remote verified: {remote.get('verified')}",
                ])

            local = entry.get("local")
            if isinstance(local, dict):
                lines.extend([
                    f"- Local path: {local.get('checkout_path')}",
                    f"- Local branch: {local.get('branch')}",
                    f"- Local HEAD: {local.get('head_sha')}",
                    f"- Local clean: {local.get('clean')}",
                ])

        lines.append("")

    lines.extend([
        "## Next safe action",
        "",
        str(data.get("next_safe_action", "")),
        "",
        "## Remaining work",
        "",
    ])

    remaining = data.get("remaining_work", [])
    if remaining:
        for item in remaining:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")

    lines.extend([
        "",
        "## Blockers / gates",
        "",
    ])

    blockers = data.get("blockers", [])
    if blockers:
        for item in blockers:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")

    lines.extend([
        "",
        "## Fresh-chat initialization",
        "",
        "@GitHub",
        "",
        "Continue the durable workspace-control task defined by:",
        f"Task capsule: {ref}",
        "",
        "Start from the normal workspace-control root route.",
        "Treat the task capsule, exact durable Git/runtime state, and "
        "referenced owning context/evidence as the handoff.",
        "Do not rely on previous conversation state.",
        "Follow the capsule's next_safe_action.",
        "",
    ])

    return "\n".join(lines)


def command_task_render(args):
    control_root, _, repos = load_registry()
    path, data = load_task_capsule(args.file)

    payload = task_validation_payload(
        path,
        data,
        repos,
    )

    if not payload["valid"]:
        print_task_validation_human(payload)
        return EXIT_STATE

    rendered = render_task_handoff(
        path,
        data,
        control_root,
    )

    if not args.output:
        print(rendered, end="")
        return EXIT_READY

    output = Path(args.output).expanduser().resolve()

    if not output.parent.exists():
        fail(
            f"task-render output parent does not exist: "
            f"{output.parent}"
        )

    if output.exists():
        try:
            existing = output.read_text()
        except OSError as exc:
            fail(
                f"could not read task-render output {output}: {exc}"
            )

        if DERIVED_HANDOFF_MARKER not in existing[:256]:
            fail(
                "refusing to overwrite non-derived "
                f"task-render output: {output}"
            )

    try:
        output.write_text(rendered)
    except OSError as exc:
        fail(
            f"could not write task-render output {output}: {exc}"
        )

    print(str(output))
    return EXIT_READY


def task_validation_payload(path, data, repos):
    errors = validate_task_capsule_data(
        data,
        path,
        repos,
    )

    return {
        "schema_version": (
            data.get("schema_version")
            if isinstance(data, dict)
            else None
        ),
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
            "schema_version": (
                data.get("schema_version")
                if isinstance(data, dict)
                else None
            ),
            "task_file": str(path),
            "task_id": validation.get("task_id"),
            "result": "INVALID_CAPSULE",
            "handoff_safe": False,
            "reasons": validation["errors"],
            "repositories": [],
        }, EXIT_STATE

    if data.get("schema_version") != 1:
        return {
            "schema_version": data.get("schema_version"),
            "task_file": str(path),
            "task_id": data.get("task_id"),
            "status": data.get("status"),
            "result": "NOT_HANDOFF_SAFE",
            "handoff_safe": False,
            "reasons": [
                "v2 topology-aware handoff assessment is not "
                "implemented until the dedicated handoff phase"
            ],
            "repositories": [],
            "next_safe_action": data.get("next_safe_action"),
        }, EXIT_REVIEW

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
        help="establish repository state before a read or mutation",
    )
    preflight.add_argument(
        "--repo",
        required=True,
        help="logical repository name from repos.json",
    )
    preflight.add_argument(
        "--topology",
        choices=("local", "remote"),
        default="local",
        help="state surface to inspect; existing calls default to local",
    )
    preflight.add_argument(
        "--path",
        help="specific checkout/worktree path; local topology only",
    )
    preflight.add_argument(
        "--branch",
        help="remote branch to inspect; defaults to registered canonical branch",
    )
    preflight.add_argument(
        "--expected-parent",
        help="expected advertised SHA before a ref-dependent remote mutation",
    )
    preflight.add_argument(
        "--surface-write-ready",
        action="store_true",
        help=(
            "confirm the selected remote operation surface has write "
            "capability/access; this does not itself grant mutation authority"
        ),
    )
    preflight.add_argument(
        "--consequence",
        choices=("read_only", "reversible", "destructive", "external"),
        help="declared consequence class for remote preflight",
    )
    preflight.add_argument(
        "--allowed-path",
        action="append",
        default=[],
        help=(
            "authoritative allowed mutation path/pattern for remote "
            "preflight; repeat as needed"
        ),
    )
    preflight.add_argument(
        "--mutation-path",
        action="append",
        default=[],
        help=(
            "proposed repository-relative mutation path for remote "
            "scope checking; repeat as needed"
        ),
    )
    preflight.add_argument(
        "--intent",
        choices=("read", "mutate"),
        default="read",
    )
    preflight.add_argument(
        "--allow-dirty",
        action="store_true",
        help="acknowledge reviewed dirty state for local mutation",
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

    task_render = sub.add_parser(
        "task-render",
        help="render a derived human-readable task handoff",
    )
    task_render.add_argument(
        "--file",
        required=True,
        help="path to task-capsule JSON",
    )
    task_render.add_argument(
        "--output",
        help="optional Markdown/text output path",
    )
    task_render.set_defaults(func=command_task_render)

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
