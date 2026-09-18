#!/usr/bin/env python3

import argparse
import json
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

    return parser


def main():
    if sys.version_info < (3, 8):
        fail("Python 3.8 or newer is required")

    parser = build_parser()
    args = parser.parse_args()

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
