#!/usr/bin/env python3
"""GitHub-native exact-head review request and disposition automation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.request

REQ_START = "WORKSPACE_CONTROL_REVIEW_REQUEST_V1"
REQ_END = "END_WORKSPACE_CONTROL_REVIEW_REQUEST_V1"
DISP_START = "WORKSPACE_CONTROL_REVIEW_DISPOSITION_V1"
DISP_END = "END_WORKSPACE_CONTROL_REVIEW_DISPOSITION_V1"
USED_START = "WORKSPACE_CONTROL_REVIEW_CONSUMED_V1"
USED_END = "END_WORKSPACE_CONTROL_REVIEW_CONSUMED_V1"

REQ_KEYS = {
    "task_id", "pr_number", "head_sha", "base_sha", "tree_sha",
    "review_kind", "sensitivity", "bindings_sha256",
    "request_copilot", "request_digest",
}
DISP_KEYS = {
    "request_comment_id", "request_digest", "task_id", "pr_number",
    "head_sha", "review_kind", "sensitivity",
    "reviewer_attestation", "disposition",
}
SENSITIVITIES = {"authority_sensitive", "routine_code"}
DISPOSITIONS = {"NO_BLOCKING_FINDING", "BLOCKING_FINDINGS"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
API = "https://api.github.com"
TIMEOUT = 10
MAX_PAGES = 10
PAGE_SIZE = 100


class ReviewError(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def need_sha40(label, value):
    if not isinstance(value, str) or not SHA40.fullmatch(value):
        raise ReviewError(label + " must be 40 lowercase hex characters")


def need_sha256(label, value):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ReviewError(label + " must be 64 lowercase hex characters")


def git(*args):
    p = subprocess.run(
        ["git", *args], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if p.returncode:
        raise ReviewError("git failed: " + " ".join(args) + ": " + p.stderr.strip())
    return p.stdout.strip()


def changed_bindings(base_sha, head_sha):
    need_sha40("base_sha", base_sha)
    need_sha40("head_sha", head_sha)
    paths = sorted(set(filter(None, git(
        "diff", "--name-only", "--no-renames", base_sha, head_sha
    ).splitlines())))
    rows = []
    for path in paths:
        p = subprocess.run(
            ["git", "cat-file", "-e", head_sha + ":" + path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        blob = "DELETED" if p.returncode else git("rev-parse", head_sha + ":" + path)
        if blob != "DELETED":
            need_sha40("blob", blob)
        rows.append({"path": path, "blob": blob})
    return rows, digest(canonical(rows))


def fields_for_request(task_id, pr_number, head_sha, base_sha, tree_sha,
                       review_kind, sensitivity, bindings_sha256,
                       request_copilot):
    need_sha40("head_sha", head_sha)
    need_sha40("base_sha", base_sha)
    need_sha40("tree_sha", tree_sha)
    need_sha256("bindings_sha256", bindings_sha256)
    if sensitivity not in SENSITIVITIES:
        raise ReviewError("unsupported sensitivity")
    if request_copilot and sensitivity != "routine_code":
        raise ReviewError("Copilot cannot be requested for authority_sensitive review")
    f = {
        "task_id": task_id,
        "pr_number": str(pr_number),
        "head_sha": head_sha,
        "base_sha": base_sha,
        "tree_sha": tree_sha,
        "review_kind": review_kind,
        "sensitivity": sensitivity,
        "bindings_sha256": bindings_sha256,
        "request_copilot": "true" if request_copilot else "false",
    }
    f["request_digest"] = digest(canonical(f))
    return f


def block(start, end, fields):
    return "\n".join([start] + [k + "=" + str(v) for k, v in fields.items()] + [end])


def exact_block(body, start, end, expected):
    lines = body.splitlines()
    starts = [i for i, x in enumerate(lines) if x.strip() == start]
    ends = [i for i, x in enumerate(lines) if x.strip() == end]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise ReviewError("expected exactly one well-ordered machine block")
    out = {}
    for raw in lines[starts[0] + 1:ends[0]]:
        line = raw.strip()
        if not line:
            continue
        if "=" not in line:
            raise ReviewError("malformed machine block line")
        k, v = line.split("=", 1)
        if not k or k in out:
            raise ReviewError("duplicate/empty machine block key")
        out[k] = v
    if set(out) != expected:
        raise ReviewError("machine block key mismatch")
    return out


def validate_request(f):
    for key in ("head_sha", "base_sha", "tree_sha"):
        need_sha40(key, f[key])
    need_sha256("bindings_sha256", f["bindings_sha256"])
    need_sha256("request_digest", f["request_digest"])
    if f["sensitivity"] not in SENSITIVITIES:
        raise ReviewError("invalid sensitivity")
    if f["request_copilot"] not in {"true", "false"}:
        raise ReviewError("invalid request_copilot")
    if f["request_copilot"] == "true" and f["sensitivity"] != "routine_code":
        raise ReviewError("authority_sensitive request cannot request Copilot")
    no_digest = dict(f)
    actual = no_digest.pop("request_digest")
    if actual != digest(canonical(no_digest)):
        raise ReviewError("request_digest mismatch")


def validate_disposition(f, req, request_id):
    if int(f["request_comment_id"]) != request_id:
        raise ReviewError("request_comment_id mismatch")
    for key in ("request_digest", "task_id", "pr_number", "head_sha",
                "review_kind", "sensitivity"):
        if f[key] != req[key]:
            raise ReviewError("disposition " + key + " mismatch")
    if f["disposition"] not in DISPOSITIONS:
        raise ReviewError("invalid disposition")
    if f["sensitivity"] == "authority_sensitive":
        if f["reviewer_attestation"] != "fresh_independent_session":
            raise ReviewError("authority_sensitive requires fresh_independent_session")
    elif f["reviewer_attestation"] not in {
        "fresh_independent_session", "copilot_approval"
    }:
        raise ReviewError("invalid reviewer_attestation")


def render_request(f, rows):
    att = "fresh_independent_session"
    listed = "\n".join("- " + x["path"] + " -> " + x["blob"] for x in rows)
    if not listed:
        listed = "- no changed paths"
    template = block(DISP_START, DISP_END, {
        "request_comment_id": "<ID OF THIS REQUEST COMMENT>",
        "request_digest": f["request_digest"],
        "task_id": f["task_id"],
        "pr_number": f["pr_number"],
        "head_sha": f["head_sha"],
        "review_kind": f["review_kind"],
        "sensitivity": f["sensitivity"],
        "reviewer_attestation": att,
        "disposition": "NO_BLOCKING_FINDING",
    })
    independence = (
        "YOU ARE THE INDEPENDENT REVIEWER. PERFORM THE REVIEW YOURSELF IN THIS "
        "FRESH REVIEW SESSION. DO NOT RETURN ANOTHER HANDOFF OR REVIEWER PROMPT."
        if f["sensitivity"] == "authority_sensitive"
        else "Perform the review against the exact immutable target below."
    )
    return (
        "Automated durable review request for task " + f["task_id"] + ".\n\n"
        + independence + "\n\n"
        + "PR #" + f["pr_number"] + " exact head: " + f["head_sha"] + "\n"
        + "Base: " + f["base_sha"] + "\n"
        + "Tree: " + f["tree_sha"] + "\n"
        + "Review kind: " + f["review_kind"] + "\n"
        + "Sensitivity: " + f["sensitivity"] + "\n\n"
        + "Exact changed-path/blob bindings:\n" + listed + "\n\n"
        + "Return NO_BLOCKING_FINDING only if the exact target is acceptable; "
        + "otherwise return precise actionable blocking findings.\n\n"
        + "Disposition block template:\n\n" + template + "\n\n"
        + block(REQ_START, REQ_END, f) + "\n"
    )


def api_url(repo, suffix):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ReviewError("repo must be owner/name")
    return API + "/repos/" + repo + suffix


def github(method, url, token, payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "workspace-control-review-automation-v1",
    }
    raw = None
    if payload is not None:
        raw = json.dumps(payload, separators=(",", ":")).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=raw, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read(4 * 1024 * 1024 + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ReviewError("GitHub API failed: " + str(exc)) from exc
    if len(data) > 4 * 1024 * 1024:
        raise ReviewError("GitHub API response too large")
    return None if not data else json.loads(data)


def token_from(name):
    value = os.environ.get(name, "")
    if not value:
        raise ReviewError("missing token env " + name)
    return value


def get_pr(repo, number, token):
    value = github("GET", api_url(repo, "/pulls/" + str(number)), token)
    if not isinstance(value, dict):
        raise ReviewError("malformed PR response")
    return value


def get_comment(repo, cid, token):
    value = github("GET", api_url(repo, "/issues/comments/" + str(cid)), token)
    if not isinstance(value, dict):
        raise ReviewError("malformed comment response")
    return value


def list_pages(repo, suffix, token):
    out = []
    for page in range(1, MAX_PAGES + 1):
        sep = "&" if "?" in suffix else "?"
        value = github(
            "GET", api_url(repo, suffix + sep + "per_page=" + str(PAGE_SIZE)
                           + "&page=" + str(page)), token
        )
        if not isinstance(value, list):
            raise ReviewError("malformed paginated response")
        out.extend(x for x in value if isinstance(x, dict))
        if len(value) < PAGE_SIZE:
            return out
    raise ReviewError("bounded page limit exceeded")


def post_comment(repo, pr, token, body):
    value = github("POST", api_url(repo, "/issues/" + str(pr) + "/comments"),
                   token, {"body": body})
    if not isinstance(value, dict) or not isinstance(value.get("id"), int):
        raise ReviewError("malformed comment creation response")
    return value


def login(comment):
    user = comment.get("user")
    return user.get("login", "") if isinstance(user, dict) else ""


def unedited(comment):
    return (
        isinstance(comment.get("created_at"), str)
        and comment.get("created_at") == comment.get("updated_at")
    )


def matching_dispositions(comments, req, request_id, request_author):
    found = []
    for c in comments:
        cid = c.get("id")
        body = c.get("body")
        if not isinstance(cid, int) or cid <= request_id:
            continue
        if not isinstance(body, str) or DISP_START not in body:
            continue
        f = exact_block(body, DISP_START, DISP_END, DISP_KEYS)
        validate_disposition(f, req, request_id)
        if not unedited(c):
            raise ReviewError("matching disposition was edited")
        reviewer = login(c)
        if not reviewer:
            raise ReviewError("matching disposition reviewer missing")
        if reviewer == request_author:
            raise ReviewError("reviewer principal equals request principal")
        found.append((c, f))
    return found


def exact_copilot_approval(reviews, req):
    if req["sensitivity"] != "routine_code":
        return None
    found = []
    for r in reviews:
        user = r.get("user")
        who = user.get("login", "") if isinstance(user, dict) else ""
        if (
            who == "copilot-pull-request-reviewer[bot]"
            and r.get("state") == "APPROVED"
            and r.get("commit_id") == req["head_sha"]
        ):
            found.append(r)
    if len(found) > 1:
        raise ReviewError("ambiguous exact-head Copilot approvals")
    return found[0] if found else None


def command_request(args):
    token = token_from(args.token_env)
    pr = get_pr(args.repo, args.pr_number, token)
    head = pr.get("head", {}).get("sha")
    base = pr.get("base", {}).get("sha")
    need_sha40("PR head", head)
    need_sha40("PR base", base)
    if git("rev-parse", "HEAD") != head:
        raise ReviewError("checked-out HEAD differs from current PR head")
    tree = git("rev-parse", head + "^{tree}")
    rows, bindings = changed_bindings(base, head)
    f = fields_for_request(
        args.task_id, args.pr_number, head, base, tree, args.review_kind,
        args.sensitivity, bindings, args.request_copilot
    )
    body = render_request(f, rows)
    if args.dry_run:
        print(body)
        return 0
    c = post_comment(args.repo, args.pr_number, token, body)
    if args.request_copilot:
        github(
            "POST",
            api_url(args.repo, "/pulls/" + str(args.pr_number)
                    + "/requested_reviewers"),
            token,
            {"reviewers": ["copilot-pull-request-reviewer[bot]"]},
        )
    print(canonical({
        "status": "REVIEW_REQUEST_CREATED",
        "request_comment_id": c["id"],
        "request_digest": f["request_digest"],
        "head_sha": head,
        "bindings_sha256": bindings,
        "copilot_requested": args.request_copilot,
    }))
    return 0


def command_consume(args):
    token = token_from(args.token_env)
    rc = get_comment(args.repo, args.request_comment_id, token)
    if not unedited(rc):
        raise ReviewError("review request was edited")
    request_author = login(rc)
    if request_author not in set(args.trusted_requester):
        raise ReviewError("untrusted review request author")
    req = exact_block(rc.get("body", ""), REQ_START, REQ_END, REQ_KEYS)
    validate_request(req)
    if int(req["pr_number"]) != args.pr_number or req["task_id"] != args.task_id:
        raise ReviewError("consume identity does not match request")
    pr = get_pr(args.repo, args.pr_number, token)
    current = pr.get("head", {}).get("sha")
    if current != req["head_sha"]:
        raise ReviewError("stale review request: PR head moved")

    comments = list_pages(args.repo, "/issues/" + str(args.pr_number) + "/comments",
                          token)
    matches = matching_dispositions(
        comments, req, args.request_comment_id, request_author
    )
    if len(matches) > 1:
        raise ReviewError("ambiguous matching disposition comments")

    backend = None
    disposition_id = None
    disposition = None
    if len(matches) == 1:
        c, f = matches[0]
        if args.disposition_comment_id and c["id"] != args.disposition_comment_id:
            raise ReviewError("triggering comment is not unique matching disposition")
        backend, disposition_id, disposition = "comment", c["id"], f["disposition"]
    elif args.disposition_comment_id:
        raise ReviewError("triggering comment is not a valid matching disposition")

    if disposition is None and req["request_copilot"] == "true":
        reviews = list_pages(
            args.repo, "/pulls/" + str(args.pr_number) + "/reviews", token
        )
        approved = exact_copilot_approval(reviews, req)
        if approved is not None:
            backend = "copilot"
            disposition_id = approved.get("id", "copilot")
            disposition = "NO_BLOCKING_FINDING"

    if disposition is None:
        print(canonical({
            "status": "PENDING",
            "request_comment_id": args.request_comment_id,
            "head_sha": req["head_sha"],
        }))
        return 0

    state = "ACCEPTED" if disposition == "NO_BLOCKING_FINDING" else "BLOCKING"
    used = {
        "request_comment_id": str(args.request_comment_id),
        "request_digest": req["request_digest"],
        "task_id": req["task_id"],
        "pr_number": req["pr_number"],
        "head_sha": req["head_sha"],
        "review_kind": req["review_kind"],
        "sensitivity": req["sensitivity"],
        "backend": backend,
        "disposition_id": str(disposition_id),
        "disposition": disposition,
    }
    if args.post_receipt:
        posted = post_comment(
            args.repo, args.pr_number, token,
            "Automated review disposition consumption receipt.\n\n"
            + block(USED_START, USED_END, used),
        )
        used["consumed_comment_id"] = str(posted["id"])
    print(canonical({"status": state, **used}))
    return 0


def parser():
    p = argparse.ArgumentParser(description="workspace-control review automation")
    s = p.add_subparsers(dest="command", required=True)
    r = s.add_parser("request")
    r.add_argument("--repo", required=True)
    r.add_argument("--pr-number", type=int, required=True)
    r.add_argument("--task-id", required=True)
    r.add_argument("--review-kind", required=True)
    r.add_argument("--sensitivity", choices=sorted(SENSITIVITIES), required=True)
    r.add_argument("--request-copilot", action="store_true")
    r.add_argument("--token-env", default="GITHUB_TOKEN")
    r.add_argument("--dry-run", action="store_true")
    r.set_defaults(func=command_request)

    c = s.add_parser("consume")
    c.add_argument("--repo", required=True)
    c.add_argument("--pr-number", type=int, required=True)
    c.add_argument("--task-id", required=True)
    c.add_argument("--request-comment-id", type=int, required=True)
    c.add_argument("--disposition-comment-id", type=int)
    c.add_argument("--token-env", default="GITHUB_TOKEN")
    c.add_argument(
        "--trusted-requester", action="append", default=["github-actions[bot]"]
    )
    c.add_argument("--post-receipt", action="store_true")
    c.set_defaults(func=command_consume)
    return p


def main():
    try:
        args = parser().parse_args()
        return args.func(args)
    except (ReviewError, ValueError, json.JSONDecodeError) as exc:
        print(canonical({"status": "INVALID", "error": str(exc)}))
        return 30


if __name__ == "__main__":
    raise SystemExit(main())
