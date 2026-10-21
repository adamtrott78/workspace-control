#!/usr/bin/env python3
"""Unprivileged GitHub-facing controller for reviewed project reconciliation.

This process has GitHub read authority for workspace-control and local write
authority only to the dedicated reconciler Unix socket and its own state dir.
It never executes repository-provided commands.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any

SOURCE_REPOSITORY = "adamtrott78/workspace-control"
SOURCE_BRANCH = "main"
WORKFLOW_PATH = ".github/workflows/lambda-ci-project-reconcile.yml"
WORKFLOW_ID = "lambda-ci-project-reconcile.yml"
API_ROOT = "https://api.github.com"
USER_AGENT = "workspace-control-lambda-ci-reconcile-controller/1"
UUID_NAMESPACE = uuid.UUID("ab97f0b3-3a35-5a48-8c95-119d9f48e7d1")
ROOT_RESPONSE_TIMEOUT_SECONDS = 120


class ReconcileControllerError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class GitHubClient:
    def __init__(self, token: str):
        if not token:
            raise ReconcileControllerError("GitHub token is empty")
        self.token = token

    def get_json(self, path: str) -> Any:
        request = urllib.request.Request(
            API_ROOT + path,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "User-Agent": USER_AGENT,
                "X-GitHub-Api-Version": "2022-11-28",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read(2048).decode("utf-8", errors="replace")
            raise ReconcileControllerError(
                f"GitHub API HTTP {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ReconcileControllerError(f"GitHub API unavailable: {exc}") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ReconcileControllerError("GitHub API returned invalid JSON") from exc

    def content_at(self, path: str, sha: str) -> tuple[bytes, str]:
        encoded_path = urllib.parse.quote(path, safe="/")
        encoded_sha = urllib.parse.quote(sha, safe="")
        value = self.get_json(
            f"/repos/{SOURCE_REPOSITORY}/contents/{encoded_path}?ref={encoded_sha}"
        )
        if not isinstance(value, dict) or value.get("type") != "file":
            raise ReconcileControllerError(f"GitHub content is not a file: {path}")
        blob_sha = value.get("sha")
        if not isinstance(blob_sha, str) or len(blob_sha) != 40:
            raise ReconcileControllerError(f"GitHub content blob SHA invalid: {path}")
        content = value.get("content")
        encoding = value.get("encoding")
        if not isinstance(content, str) or encoding != "base64":
            raise ReconcileControllerError(f"GitHub content encoding invalid: {path}")
        try:
            raw = base64.b64decode(content, validate=False)
        except Exception as exc:
            raise ReconcileControllerError(f"GitHub content base64 invalid: {path}") from exc
        return raw, blob_sha


def _load_token(path: pathlib.Path) -> str:
    st = path.stat()
    if st.st_mode & 0o077:
        raise ReconcileControllerError("reconciliation token permissions are too broad")
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise ReconcileControllerError("reconciliation token is empty")
    return token


def _current_main_sha(client: GitHubClient) -> str:
    branch = client.get_json(
        f"/repos/{SOURCE_REPOSITORY}/branches/{SOURCE_BRANCH}"
    )
    current_sha = branch.get("commit", {}).get("sha") if isinstance(branch, dict) else None
    if not isinstance(current_sha, str) or len(current_sha) != 40:
        raise ReconcileControllerError("unable to resolve current workspace-control main")
    return current_sha


def _is_ancestor(client: GitHubClient, base_sha: str, head_sha: str) -> bool:
    if base_sha == head_sha:
        return True
    compare = client.get_json(
        f"/repos/{SOURCE_REPOSITORY}/compare/{base_sha}...{head_sha}"
    )
    if not isinstance(compare, dict):
        raise ReconcileControllerError("GitHub compare response is invalid")
    return compare.get("status") == "ahead"


def _reconciliation_input_blobs(
    client: GitHubClient,
    sha: str,
) -> dict[str, str]:
    paths = [
        WORKFLOW_PATH,
        "architecture/lambda-ci-project-registry.v1.json",
        "architecture/lambda-ci-execution-contracts.v1.json",
    ]
    result: dict[str, str] = {}
    registry_raw: bytes | None = None
    for path in paths:
        raw, blob_sha = client.content_at(path, sha)
        result[path] = blob_sha
        if path == "architecture/lambda-ci-project-registry.v1.json":
            registry_raw = raw
    if registry_raw is None:
        raise ReconcileControllerError("project registry input is unavailable")
    try:
        registry = json.loads(registry_raw)
    except json.JSONDecodeError as exc:
        raise ReconcileControllerError("project registry input is invalid JSON") from exc
    if not isinstance(registry, dict):
        raise ReconcileControllerError("project registry input must be object")
    projects = registry.get("projects")
    if not isinstance(projects, dict):
        raise ReconcileControllerError("project registry projects are invalid")
    for project_id, entry in sorted(projects.items()):
        if not isinstance(entry, dict):
            raise ReconcileControllerError(f"registry project invalid: {project_id}")
        path = entry.get("manifest_source_path")
        if not isinstance(path, str):
            raise ReconcileControllerError(f"manifest path missing: {project_id}")
        _, blob_sha = client.content_at(path, sha)
        result[path] = blob_sha
    return result


def _reconciliation_inputs_equivalent(
    client: GitHubClient,
    approved_sha: str,
    current_sha: str,
) -> bool:
    return _reconciliation_input_blobs(
        client, approved_sha
    ) == _reconciliation_input_blobs(client, current_sha)


def _select_current_successful_run(
    client: GitHubClient,
    allowed_actors: set[str],
) -> dict[str, Any] | None:
    current_sha = _current_main_sha(client)
    workflow_id = urllib.parse.quote(WORKFLOW_ID, safe="")
    runs = client.get_json(
        f"/repos/{SOURCE_REPOSITORY}/actions/workflows/{workflow_id}/runs"
        f"?branch={SOURCE_BRANCH}&status=success&per_page=20"
    )
    values = runs.get("workflow_runs") if isinstance(runs, dict) else None
    if not isinstance(values, list):
        raise ReconcileControllerError("workflow run list is invalid")
    for run in values:
        if not isinstance(run, dict):
            continue
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        if run.get("head_branch") != SOURCE_BRANCH:
            continue
        approved_sha = run.get("head_sha")
        if not isinstance(approved_sha, str) or len(approved_sha) != 40:
            continue
        if run.get("event") not in {"push", "workflow_dispatch"}:
            continue
        actor = run.get("actor", {}).get("login")
        triggering = run.get("triggering_actor", {}).get("login", actor)
        if actor not in allowed_actors or triggering not in allowed_actors:
            continue
        if not _is_ancestor(client, approved_sha, current_sha):
            continue
        if not _reconciliation_inputs_equivalent(
            client, approved_sha, current_sha
        ):
            continue
        selected = dict(run)
        selected["_observed_main_sha"] = current_sha
        selected["_policy_equivalent_to_main"] = True
        return selected
    return None


def _document_at(
    client: GitHubClient,
    path: str,
    sha: str,
) -> tuple[dict[str, Any], str]:
    raw, blob_sha = client.content_at(path, sha)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReconcileControllerError(f"reviewed JSON is invalid: {path}") from exc
    if not isinstance(value, dict):
        raise ReconcileControllerError(f"reviewed JSON must be object: {path}")
    return value, blob_sha


def build_request(
    client: GitHubClient,
    *,
    run: dict[str, Any],
    allowed_actors: set[str],
) -> dict[str, Any]:
    head_sha = run["head_sha"]
    workflow_raw, workflow_blob = client.content_at(WORKFLOW_PATH, head_sha)
    if not workflow_raw:
        raise ReconcileControllerError("trusted workflow file is empty")

    registry, _ = _document_at(
        client,
        "architecture/lambda-ci-project-registry.v1.json",
        head_sha,
    )
    registry_actor_set = set(
        registry.get("reconciliation", {}).get("allowed_actor_logins", [])
    )
    if registry_actor_set != allowed_actors:
        raise ReconcileControllerError("installed actor ceiling differs from reviewed registry")

    manifests: list[dict[str, Any]] = []
    for project_id, entry in sorted(registry.get("projects", {}).items()):
        if not isinstance(entry, dict):
            raise ReconcileControllerError(f"registry project invalid: {project_id}")
        path = entry.get("manifest_source_path")
        if not isinstance(path, str):
            raise ReconcileControllerError(f"manifest path missing: {project_id}")
        document, _ = _document_at(client, path, head_sha)
        manifests.append(
            {
                "project_id": project_id,
                "sha256": _sha256_json(document),
                "document": document,
            }
        )

    registry_digest = _sha256_json(registry)
    identity_material = "|".join(
        [
            SOURCE_REPOSITORY,
            head_sha,
            registry_digest,
            *[
                item["project_id"] + ":" + item["sha256"]
                for item in manifests
            ],
        ]
    )
    request_id = str(uuid.uuid5(UUID_NAMESPACE, identity_material))
    actor = run.get("actor", {}).get("login")
    return {
        "schema_version": 1,
        "request_id": request_id,
        "operation": "APPLY_PROJECT_REGISTRY",
        "source_attestation": {
            "repository": SOURCE_REPOSITORY,
            "default_branch": SOURCE_BRANCH,
            "commit_sha": head_sha,
            "workflow_path": WORKFLOW_PATH,
            "workflow_blob_sha": workflow_blob,
            "actor_login": actor,
            "verified_at": _utc_now(),
        },
        "registry": {
            "sha256": registry_digest,
            "document": registry,
        },
        "project_manifests": manifests,
        "dry_run": False,
    }


def submit_request(socket_path: pathlib.Path, request: dict[str, Any]) -> dict[str, Any]:
    payload = (json.dumps(request, sort_keys=True) + "\n").encode("utf-8")
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.settimeout(ROOT_RESPONSE_TIMEOUT_SECONDS)
    try:
        conn.connect(str(socket_path))
        conn.sendall(payload)
        handle = conn.makefile("rb")
        line = handle.readline(2 * 1024 * 1024)
    except socket.timeout as exc:
        raise ReconcileControllerError(
            "root reconciler response timed out after "
            f"{ROOT_RESPONSE_TIMEOUT_SECONDS}s"
        ) from exc
    except OSError as exc:
        raise ReconcileControllerError(
            f"root reconciler socket unavailable: {exc}"
        ) from exc
    finally:
        conn.close()
    if not line:
        raise ReconcileControllerError("root reconciler returned no response")
    try:
        response = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ReconcileControllerError("root reconciler returned invalid JSON") from exc
    if not isinstance(response, dict):
        raise ReconcileControllerError("root reconciler response must be object")
    return response


def _atomic_state(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, indent=2, sort_keys=True) + "\n"
    tmp = path.parent / f".{path.name}.tmp"
    tmp.write_text(raw, encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)


def run_once(
    *,
    token_file: pathlib.Path,
    socket_path: pathlib.Path,
    state_dir: pathlib.Path,
    allowed_actors: set[str],
) -> dict[str, Any]:
    client = GitHubClient(_load_token(token_file))
    run = _select_current_successful_run(client, allowed_actors)
    if run is None:
        return {"status": "NO_CURRENT_SUCCESSFUL_RECONCILIATION_RUN"}

    request = build_request(client, run=run, allowed_actors=allowed_actors)
    success_path = state_dir / "last-success.json"
    rejected_path = state_dir / "last-rejected.json"
    if success_path.is_file():
        prior = json.loads(success_path.read_text(encoding="utf-8"))
        if (
            prior.get("commit_sha") == request["source_attestation"]["commit_sha"]
            and prior.get("request_id") == request["request_id"]
            and prior.get("response", {}).get("status") == "PASS"
        ):
            refreshed = dict(prior)
            refreshed["timestamp_utc"] = _utc_now()
            refreshed["approved_policy_sha"] = request["source_attestation"]["commit_sha"]
            refreshed["observed_main_sha"] = run.get("_observed_main_sha")
            refreshed["policy_equivalent_to_observed_main"] = (
                run.get("_policy_equivalent_to_main") is True
            )
            _atomic_state(success_path, refreshed)
            return {"status": "ALREADY_RECONCILED", **refreshed}
    if rejected_path.is_file():
        prior = json.loads(rejected_path.read_text(encoding="utf-8"))
        if (
            prior.get("commit_sha") == request["source_attestation"]["commit_sha"]
            and prior.get("request_id") == request["request_id"]
        ):
            return {
                "status": "UNCHANGED_REJECTED_HEAD",
                "commit_sha": prior["commit_sha"],
                "request_id": prior["request_id"],
            }

    response = submit_request(socket_path, request)
    state = {
        "timestamp_utc": _utc_now(),
        "commit_sha": request["source_attestation"]["commit_sha"],
        "approved_policy_sha": request["source_attestation"]["commit_sha"],
        "observed_main_sha": run.get("_observed_main_sha"),
        "policy_equivalent_to_observed_main": (
            run.get("_policy_equivalent_to_main") is True
        ),
        "request_id": request["request_id"],
        "workflow_run_id": run.get("id"),
        "response": response,
    }
    if response.get("status") == "PASS":
        _atomic_state(success_path, state)
        if rejected_path.exists():
            rejected_path.unlink()
        return {"status": "RECONCILED", **state}
    _atomic_state(rejected_path, state)
    return {"status": "REJECTED", **state}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--token-file",
        type=pathlib.Path,
        default=pathlib.Path("/var/lib/workspace-ci/reconcile-controller/github-token"),
    )
    parser.add_argument(
        "--socket",
        type=pathlib.Path,
        default=pathlib.Path("/run/workspace-ci/reconciler.sock"),
    )
    parser.add_argument(
        "--state-dir",
        type=pathlib.Path,
        default=pathlib.Path("/var/lib/workspace-ci/reconcile-controller"),
    )
    parser.add_argument("--actor", action="append", default=["adamtrott78"])
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    allowed = set(args.actor)
    if not allowed:
        raise ReconcileControllerError("actor allowlist is empty")

    while True:
        try:
            result = run_once(
                token_file=args.token_file,
                socket_path=args.socket,
                state_dir=args.state_dir,
                allowed_actors=allowed,
            )
        except ReconcileControllerError as exc:
            result = {
                "status": "TRANSIENT_ERROR",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            print(json.dumps(result, sort_keys=True), flush=True)
            if args.once:
                return 70
        else:
            print(json.dumps(result, sort_keys=True), flush=True)
            if args.once:
                return 0 if result["status"] not in {"REJECTED"} else 70
        time.sleep(max(5, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
