#!/usr/bin/env python3
"""Unprivileged outbound-only Workspace CI P1 maintenance controller.

The controller polls one fixed workspace-control issue for owner-authored
commands. It never executes repository content. Root mutations are requested
through the bounded maintenance socket; GitHub scale-set mutation is delegated
to the installed controller binary's exact configured-scale-set helper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any

SOURCE_REPOSITORY = "adamtrott78/workspace-control"
API_ROOT = "https://api.github.com"
USER_AGENT = "workspace-control-maintenance-controller/1"
OWNER_LOGIN = "adamtrott78"
UUID_NAMESPACE = uuid.UUID("450ecef9-fbb0-5cf8-a216-60d6f28f5c5c")
PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]{1,20}$")
RESET_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
ALLOWED_ENV_KEYS = {
    "WORKSPACE_CI_ADMISSION_V2_ENABLED",
    "WORKSPACE_CI_GITHUB_URL",
    "WORKSPACE_CI_LANE",
    "WORKSPACE_CI_PAT_FILE",
    "WORKSPACE_CI_PROJECT_ID",
    "WORKSPACE_CI_PROVISIONER_SOCKET",
    "WORKSPACE_CI_RUNNER_PREFIX",
    "WORKSPACE_CI_SCALESET_NAME",
    "WORKSPACE_CI_CONTROLLER_STATE_ROOT",
}
ZERO_SETTLE_SECONDS = 15


class MaintenanceControllerError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _atomic_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, indent=2, sort_keys=True) + "\n"
    tmp = path.parent / f".{path.name}.tmp"
    tmp.write_text(raw, encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)


def _load_token(path: pathlib.Path) -> str:
    st = path.stat()
    if st.st_mode & 0o077:
        raise MaintenanceControllerError("maintenance token permissions are too broad")
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise MaintenanceControllerError("maintenance token is empty")
    return token


class GitHubClient:
    def __init__(self, token: str):
        if not token:
            raise MaintenanceControllerError("GitHub token is empty")
        self.token = token

    def get_json(self, path: str) -> Any:
        req = urllib.request.Request(
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
            with urllib.request.urlopen(req, timeout=20) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read(2048).decode("utf-8", errors="replace")
            raise MaintenanceControllerError(
                f"GitHub API HTTP {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise MaintenanceControllerError(f"GitHub API unavailable: {exc}") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MaintenanceControllerError("GitHub API returned invalid JSON") from exc


def parse_command(body: Any) -> dict[str, Any] | None:
    if not isinstance(body, str):
        return None
    if "\n" in body or "\r" in body:
        return None
    parts = body.strip().split(" ")
    if not parts or parts[0] != "/workspace-ci-maintain":
        return None
    if any(part == "" for part in parts):
        return None

    if len(parts) == 4 and parts[1] in {"diagnose", "restart"}:
        action, project_id, lane = parts[1:]
        quarantine = None
    elif len(parts) == 5 and parts[1] == "reset-stale":
        action, project_id, lane, quarantine = parts[1:]
        if RESET_UUID_RE.fullmatch(quarantine) is None:
            raise MaintenanceControllerError("reset-stale quarantine receipt id is invalid")
    else:
        raise MaintenanceControllerError("maintenance command grammar is invalid")

    if PROJECT_RE.fullmatch(project_id) is None:
        raise MaintenanceControllerError("maintenance project id is invalid")
    if lane not in {"cpu", "gpu"}:
        raise MaintenanceControllerError("maintenance lane is invalid")
    return {
        "action": action,
        "project_id": project_id,
        "lane": lane,
        "quarantine_receipt_id": quarantine,
    }


def maintenance_request_id(
    comment_id: int,
    command: dict[str, Any],
    operation: str,
    reset_generation: str | None = None,
) -> str:
    material = "|".join(
        [
            SOURCE_REPOSITORY,
            str(comment_id),
            command["action"],
            command["project_id"],
            command["lane"],
            str(command.get("quarantine_receipt_id") or ""),
            operation,
            str(reset_generation or ""),
        ]
    )
    return str(uuid.uuid5(UUID_NAMESPACE, material))


def build_root_request(
    *,
    comment_id: int,
    command: dict[str, Any],
    operation: str,
    reset_generation: str | None = None,
) -> dict[str, Any]:
    recovery_operation = operation in {
        "QUIESCE_LANE_FOR_RECOVERY",
        "RESUME_LANE_AFTER_RESET",
    }
    return {
        "schema_version": 1,
        "request_id": maintenance_request_id(
            comment_id,
            command,
            operation,
            reset_generation,
        ),
        "operation": operation,
        "project_id": command["project_id"],
        "lane": command["lane"],
        "quarantine_receipt_id": (
            command.get("quarantine_receipt_id") if recovery_operation else None
        ),
        "reset_generation": (
            reset_generation
            if operation == "RESUME_LANE_AFTER_RESET"
            or (
                operation == "QUIESCE_LANE_FOR_RECOVERY"
                and reset_generation is not None
            )
            else None
        ),
    }


def submit_root(
    socket_path: pathlib.Path,
    *,
    comment_id: int,
    command: dict[str, Any],
    operation: str,
    reset_generation: str | None = None,
) -> dict[str, Any]:
    request = build_root_request(
        comment_id=comment_id,
        command=command,
        operation=operation,
        reset_generation=reset_generation,
    )
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.settimeout(30)
    try:
        conn.connect(str(socket_path))
        conn.sendall((json.dumps(request, sort_keys=True) + "\n").encode("utf-8"))
        conn.shutdown(socket.SHUT_WR)
        line = conn.makefile("rb").readline(1024 * 1024)
    except OSError as exc:
        raise MaintenanceControllerError(f"root maintenance socket unavailable: {exc}") from exc
    finally:
        conn.close()
    if not line:
        raise MaintenanceControllerError("root maintenance service returned no response")
    try:
        response = json.loads(line)
    except json.JSONDecodeError as exc:
        raise MaintenanceControllerError("root maintenance response is invalid JSON") from exc
    if not isinstance(response, dict) or response.get("status") != "PASS":
        raise MaintenanceControllerError(
            "root maintenance request rejected: "
            + str(response.get("error") if isinstance(response, dict) else response)
        )
    return response["receipt"]


def load_controller_env(
    controllers_dir: pathlib.Path,
    project_id: str,
    lane: str,
    *,
    runner_token_file: pathlib.Path,
) -> dict[str, str]:
    path = controllers_dir / f"{project_id}-{lane}.env"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise MaintenanceControllerError("installed controller environment unavailable") from exc
    values: dict[str, str] = {}
    for line in lines:
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise MaintenanceControllerError("installed controller environment is malformed")
        key, value = line.split("=", 1)
        if key not in ALLOWED_ENV_KEYS:
            raise MaintenanceControllerError(
                f"installed controller environment contains unsupported key: {key}"
            )
        if not key or "\x00" in value or "\n" in value or "\r" in value:
            raise MaintenanceControllerError("installed controller environment value is invalid")
        values[key] = value
    required = {
        "WORKSPACE_CI_ADMISSION_V2_ENABLED",
        "WORKSPACE_CI_GITHUB_URL",
        "WORKSPACE_CI_LANE",
        "WORKSPACE_CI_PROJECT_ID",
        "WORKSPACE_CI_RUNNER_PREFIX",
        "WORKSPACE_CI_SCALESET_NAME",
    }
    if not required.issubset(values):
        raise MaintenanceControllerError("installed controller environment is incomplete")
    if values["WORKSPACE_CI_PROJECT_ID"] != project_id or values["WORKSPACE_CI_LANE"] != lane:
        raise MaintenanceControllerError("installed controller environment identity mismatch")
    values["WORKSPACE_CI_PAT_FILE"] = str(runner_token_file)
    values.pop("WORKSPACE_CI_APP_CLIENT_ID", None)
    values.pop("WORKSPACE_CI_APP_INSTALLATION_ID", None)
    values.pop("WORKSPACE_CI_APP_PRIVATE_KEY_FILE", None)
    return values


def invoke_scale_set_helper(
    binary: pathlib.Path,
    env_values: dict[str, str],
    operation: str,
    expected_scale_set_id: int,
) -> dict[str, Any]:
    if operation not in {"INSPECT", "DELETE"}:
        raise MaintenanceControllerError("scale-set helper operation is unsupported")
    request = {
        "schema_version": 1,
        "operation": operation,
        "expected_scale_set_id": expected_scale_set_id,
    }
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": "/var/lib/workspace-ci/maintenance-controller",
        **env_values,
    }
    proc = subprocess.run(
        [str(binary), "--scale-set-maintenance"],
        input=json.dumps(request) + "\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        raise MaintenanceControllerError(
            "scale-set helper failed: " + proc.stderr.strip()
        )
    try:
        response = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise MaintenanceControllerError("scale-set helper returned invalid JSON") from exc
    if not isinstance(response, dict):
        raise MaintenanceControllerError("scale-set helper response must be object")
    return response


def _zero_observation(scale: dict[str, Any], root_diag: dict[str, Any]) -> bool:
    stats = scale.get("statistics")
    if not isinstance(stats, dict):
        return False
    required_zero = [
        "TotalAvailableJobs",
        "TotalAcquiredJobs",
        "TotalAssignedJobs",
        "TotalRunningJobs",
        "TotalRegisteredRunners",
        "TotalBusyRunners",
        "TotalIdleRunners",
    ]
    # Go JSON field tags use lower camel case.
    camel = {
        "TotalAvailableJobs": "totalAvailableJobs",
        "TotalAcquiredJobs": "totalAcquiredJobs",
        "TotalAssignedJobs": "totalAssignedJobs",
        "TotalRunningJobs": "totalRunningJobs",
        "TotalRegisteredRunners": "totalRegisteredRunners",
        "TotalBusyRunners": "totalBusyRunners",
        "TotalIdleRunners": "totalIdleRunners",
    }
    if any(int(stats.get(camel[key], -1)) != 0 for key in required_zero):
        return False
    result = root_diag.get("result") if root_diag.get("status") == "COMPLETED" else root_diag
    if not isinstance(result, dict):
        return False
    return result.get("active_project_units") == [] and result.get("service_active") is True


def execute_reset(
    *,
    comment_id: int,
    command: dict[str, Any],
    root_socket: pathlib.Path,
    controller_binary: pathlib.Path,
    controllers_dir: pathlib.Path,
    runner_token_file: pathlib.Path,
    sleep_fn=time.sleep,
    max_new_scale_set_waits: int = 20,
    max_ready_waits: int = 30,
) -> dict[str, Any]:
    generation = str(
        uuid.uuid5(
            UUID_NAMESPACE,
            f"reset-generation|{comment_id}|{command['quarantine_receipt_id']}",
        )
    )
    env_values = load_controller_env(
        controllers_dir,
        command["project_id"],
        command["lane"],
        runner_token_file=runner_token_file,
    )

    quiesce = submit_root(
        root_socket,
        comment_id=comment_id,
        command=command,
        operation="QUIESCE_LANE_FOR_RECOVERY",
    )
    qresult = quiesce.get("result")
    if not isinstance(qresult, dict) or qresult.get("local_execution_absent") is not True:
        raise MaintenanceControllerError("root quiescence proof is incomplete")
    old_id = qresult.get("quarantine_scale_set_id")
    if not isinstance(old_id, int) or old_id <= 0:
        raise MaintenanceControllerError("quarantine has no exact old scale-set id")

    before = invoke_scale_set_helper(
        controller_binary,
        env_values,
        "INSPECT",
        old_id,
    )
    stats = before.get("statistics")
    if not isinstance(stats, dict):
        raise MaintenanceControllerError("old scale-set statistics unavailable")
    for key in ("totalRegisteredRunners", "totalBusyRunners", "totalRunningJobs"):
        if int(stats.get(key, -1)) != 0:
            raise MaintenanceControllerError(
                f"old scale set not quiescent: {key}={stats.get(key)}"
            )

    deleted = invoke_scale_set_helper(
        controller_binary,
        env_values,
        "DELETE",
        old_id,
    )
    if deleted.get("status") != "DELETED" or deleted.get("scale_set_id") != old_id:
        raise MaintenanceControllerError("exact old scale set was not deleted")

    resumed = False
    try:
        submit_root(
            root_socket,
            comment_id=comment_id,
            command=command,
            operation="RESUME_LANE_AFTER_RESET",
            reset_generation=generation,
        )
        resumed = True

        new_id = None
        first_observation = None
        second_observation = None
        for _ in range(max_new_scale_set_waits):
            inspected = invoke_scale_set_helper(
                controller_binary,
                env_values,
                "INSPECT",
                0,
            )
            candidate = inspected.get("scale_set_id")
            if inspected.get("status") == "PRESENT" and isinstance(candidate, int):
                if candidate == old_id:
                    raise MaintenanceControllerError(
                        "scale-set reset did not produce a fresh numeric id"
                    )
                new_id = candidate
                diag = submit_root(
                    root_socket,
                    comment_id=comment_id,
                    command=command,
                    operation="DIAGNOSE_LANE",
                )
                if _zero_observation(inspected, diag):
                    first_observation = {
                        "timestamp_utc": _utc_now(),
                        "scale_set": inspected,
                        "root_diagnosis": diag,
                    }
                    break
            sleep_fn(1)
        if new_id is None or first_observation is None:
            raise MaintenanceControllerError(
                "fresh zero-state scale set was not observed"
            )

        sleep_fn(ZERO_SETTLE_SECONDS)
        inspected = invoke_scale_set_helper(
            controller_binary,
            env_values,
            "INSPECT",
            new_id,
        )
        diag = submit_root(
            root_socket,
            comment_id=comment_id,
            command=command,
            operation="DIAGNOSE_LANE",
        )
        if inspected.get("scale_set_id") != new_id or not _zero_observation(inspected, diag):
            raise MaintenanceControllerError(
                "second zero-state observation failed"
            )
        second_observation = {
            "timestamp_utc": _utc_now(),
            "scale_set": inspected,
            "root_diagnosis": diag,
        }

        controller_ready = None
        for _ in range(max_ready_waits):
            inspected = invoke_scale_set_helper(
                controller_binary,
                env_values,
                "INSPECT",
                new_id,
            )
            diag = submit_root(
                root_socket,
                comment_id=comment_id,
                command=command,
                operation="DIAGNOSE_LANE",
            )
            if inspected.get("scale_set_id") != new_id or not _zero_observation(
                inspected,
                diag,
            ):
                raise MaintenanceControllerError(
                    "zero-state drifted before controller READY receipt"
                )
            ready = diag.get("ready_for_single_retry")
            if isinstance(ready, dict):
                if (
                    ready.get("status") != "READY_FOR_SINGLE_RETRY"
                    or ready.get("receipt_id")
                    != command["quarantine_receipt_id"]
                    or ready.get("reset_generation") != generation
                    or ready.get("old_scale_set_id") != old_id
                    or ready.get("new_scale_set_id") != new_id
                    or ready.get("automatic_workflow_triggered") is not False
                ):
                    raise MaintenanceControllerError(
                        "controller READY receipt identity mismatch"
                    )
                controller_ready = ready
                break
            sleep_fn(1)
        if controller_ready is None:
            raise MaintenanceControllerError(
                "controller did not emit READY_FOR_SINGLE_RETRY within bound"
            )

        return {
            "status": "READY_FOR_SINGLE_RETRY",
            "reset_generation": generation,
            "old_scale_set_id": old_id,
            "new_scale_set_id": new_id,
            "first_zero_observation": first_observation,
            "second_zero_observation": second_observation,
            "controller_ready_receipt": controller_ready,
            "automatic_workflow_triggered": False,
        }
    except Exception:
        if resumed:
            try:
                submit_root(
                    root_socket,
                    comment_id=comment_id,
                    command=command,
                    operation="QUIESCE_LANE_FOR_RECOVERY",
                    reset_generation=generation,
                )
            except Exception as re_quiesce_error:
                raise MaintenanceControllerError(
                    "reset failed after resume and re-quiesce also failed: "
                    + str(re_quiesce_error)
                )
        raise


def process_comment(
    comment: dict[str, Any],
    *,
    state_dir: pathlib.Path,
    root_socket: pathlib.Path,
    controller_binary: pathlib.Path,
    controllers_dir: pathlib.Path,
    runner_token_file: pathlib.Path,
    sleep_fn=time.sleep,
) -> dict[str, Any] | None:
    comment_id = comment.get("id")
    if not isinstance(comment_id, int) or comment_id <= 0:
        return None
    user = comment.get("user")
    if not isinstance(user, dict) or user.get("login") != OWNER_LOGIN:
        return None
    if comment.get("author_association") != "OWNER":
        return None

    command = parse_command(comment.get("body"))
    if command is None:
        return None

    receipt_path = state_dir / "receipts" / f"{comment_id}.json"
    identity = {
        "comment_id": comment_id,
        "repository": SOURCE_REPOSITORY,
        "actor": OWNER_LOGIN,
        "command": command,
        "command_sha256": _sha256(command),
    }
    if receipt_path.is_file():
        prior = json.loads(receipt_path.read_text(encoding="utf-8"))
        if prior.get("identity") != identity:
            raise MaintenanceControllerError("comment replay identity mismatch")
        if prior.get("status") in {
            "COMPLETED",
            "READY_FOR_SINGLE_RETRY",
            "FAILED_CLOSED",
        }:
            return prior
        raise MaintenanceControllerError(
            "prior maintenance command is non-terminal; refusing destructive replay"
        )

    in_progress = {
        "schema_version": 1,
        "status": "IN_PROGRESS",
        "identity": identity,
        "timestamp_utc": _utc_now(),
    }
    _atomic_json(receipt_path, in_progress)

    try:
        if command["action"] == "diagnose":
            result = submit_root(
                root_socket,
                comment_id=comment_id,
                command=command,
                operation="DIAGNOSE_LANE",
            )
            status = "COMPLETED"
        elif command["action"] == "restart":
            result = submit_root(
                root_socket,
                comment_id=comment_id,
                command=command,
                operation="RESTART_CONTROLLER",
            )
            status = "COMPLETED"
        elif command["action"] == "reset-stale":
            result = execute_reset(
                comment_id=comment_id,
                command=command,
                root_socket=root_socket,
                controller_binary=controller_binary,
                controllers_dir=controllers_dir,
                runner_token_file=runner_token_file,
                sleep_fn=sleep_fn,
            )
            status = "READY_FOR_SINGLE_RETRY"
        else:
            raise MaintenanceControllerError("unsupported parsed action")
    except Exception as exc:
        failed = {
            "schema_version": 1,
            "status": "FAILED_CLOSED",
            "identity": identity,
            "timestamp_utc": _utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "automatic_workflow_triggered": False,
        }
        _atomic_json(receipt_path, failed)
        raise

    receipt = {
        "schema_version": 1,
        "status": status,
        "identity": identity,
        "timestamp_utc": _utc_now(),
        "result": result,
        "automatic_workflow_triggered": False,
    }
    _atomic_json(receipt_path, receipt)
    return receipt


def run_once(
    *,
    token_file: pathlib.Path,
    issue_number: int,
    state_dir: pathlib.Path,
    root_socket: pathlib.Path,
    controller_binary: pathlib.Path,
    controllers_dir: pathlib.Path,
    runner_token_file: pathlib.Path,
) -> dict[str, Any]:
    client = GitHubClient(_load_token(token_file))
    issue = client.get_json(f"/repos/{SOURCE_REPOSITORY}/issues/{issue_number}")
    if not isinstance(issue, dict) or issue.get("state") != "open":
        raise MaintenanceControllerError("maintenance issue is not open")
    if "pull_request" in issue:
        raise MaintenanceControllerError("maintenance issue must not be a pull request")

    cursor_path = state_dir / "cursor.json"
    since = None
    cursor = None
    if cursor_path.is_file():
        try:
            cursor = json.loads(cursor_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MaintenanceControllerError("maintenance cursor is invalid") from exc
        if not isinstance(cursor, dict):
            raise MaintenanceControllerError("maintenance cursor must be object")
        since = cursor.get("last_seen_updated_at")
        if not isinstance(since, str) or not since:
            raise MaintenanceControllerError("maintenance cursor timestamp is invalid")

    comments: list[dict[str, Any]] = []
    page = 1
    while True:
        query = f"per_page=100&page={page}"
        if since is not None:
            # Re-read the boundary second. Durable per-comment receipts make
            # duplicates harmless and this avoids timestamp-edge command loss.
            try:
                boundary = datetime.fromisoformat(since.replace("Z", "+00:00"))
            except ValueError as exc:
                raise MaintenanceControllerError("maintenance cursor timestamp is invalid") from exc
            boundary = boundary.replace(microsecond=0)
            boundary = boundary.timestamp() - 1
            query += "&since=" + urllib.parse.quote(
                datetime.fromtimestamp(boundary, timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                safe="",
            )
        batch = client.get_json(
            f"/repos/{SOURCE_REPOSITORY}/issues/{issue_number}/comments?{query}"
        )
        if not isinstance(batch, list):
            raise MaintenanceControllerError("maintenance issue comments are invalid")
        comments.extend(c for c in batch if isinstance(c, dict))
        if len(batch) < 100:
            break
        page += 1
        if page > 100:
            raise MaintenanceControllerError("maintenance comment pagination exceeded bound")

    comments.sort(key=lambda item: int(item.get("id") or 0))
    if cursor is None:
        # Commissioning is fail-closed: never execute commands that predate
        # first successful controller observation. Create/open the dedicated
        # issue first, start the controller, then issue maintenance commands.
        latest = max(
            (
                str(comment.get("updated_at"))
                for comment in comments
                if isinstance(comment.get("updated_at"), str)
            ),
            default=_utc_now(),
        )
        max_id = max(
            (int(comment.get("id") or 0) for comment in comments),
            default=0,
        )
        _atomic_json(
            cursor_path,
            {
                "schema_version": 1,
                "initialized_at": _utc_now(),
                "last_seen_comment_id": max_id,
                "last_seen_updated_at": latest,
            },
        )
        return {
            "status": "INITIALIZED_NO_COMMANDS_EXECUTED",
            "watermark_comment_id": max_id,
        }

    last_seen_id = int(cursor.get("last_seen_comment_id") or 0)
    processed = []
    max_seen_id = last_seen_id
    max_seen_updated = since
    for comment in comments:
        comment_id = int(comment.get("id") or 0)
        updated_at = comment.get("updated_at")
        if comment_id <= 0:
            continue
        max_seen_id = max(max_seen_id, comment_id)
        if isinstance(updated_at, str) and (
            max_seen_updated is None or updated_at > max_seen_updated
        ):
            max_seen_updated = updated_at
        # Re-read comments at the timestamp boundary, but execute only comments
        # with a new immutable numeric ID. Edited old comments cannot become a
        # new command after the fact.
        if comment_id <= last_seen_id:
            continue
        try:
            receipt = process_comment(
                comment,
                state_dir=state_dir,
                root_socket=root_socket,
                controller_binary=controller_binary,
                controllers_dir=controllers_dir,
                runner_token_file=runner_token_file,
            )
        except MaintenanceControllerError as exc:
            processed.append(
                {
                    "comment_id": comment_id,
                    "status": "FAILED_CLOSED",
                    "error": str(exc),
                }
            )
        else:
            if receipt is not None:
                processed.append(
                    {
                        "comment_id": comment_id,
                        "status": receipt["status"],
                    }
                )

    _atomic_json(
        cursor_path,
        {
            "schema_version": 1,
            "initialized_at": cursor.get("initialized_at"),
            "last_seen_comment_id": max_seen_id,
            "last_seen_updated_at": max_seen_updated or _utc_now(),
        },
    )
    return {
        "status": "PASS",
        "processed": processed,
        "last_seen_comment_id": max_seen_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--token-file",
        type=pathlib.Path,
        default=pathlib.Path(
            "/var/lib/workspace-ci/maintenance-controller/github-read-token"
        ),
    )
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument(
        "--state-dir",
        type=pathlib.Path,
        default=pathlib.Path("/var/lib/workspace-ci/maintenance-controller"),
    )
    parser.add_argument(
        "--root-socket",
        type=pathlib.Path,
        default=pathlib.Path("/run/workspace-ci/maintenance.sock"),
    )
    parser.add_argument(
        "--controller-binary",
        type=pathlib.Path,
        default=pathlib.Path("/opt/workspace-ci/controller/lambda-ci-controller"),
    )
    parser.add_argument(
        "--controllers-dir",
        type=pathlib.Path,
        default=pathlib.Path("/etc/workspace-ci/controllers"),
    )
    parser.add_argument(
        "--runner-token-file",
        type=pathlib.Path,
        default=pathlib.Path(
            "/var/lib/workspace-ci/maintenance-controller/runner-token"
        ),
    )
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.issue_number <= 0:
        raise MaintenanceControllerError("issue number must be positive")

    while True:
        try:
            result = run_once(
                token_file=args.token_file,
                issue_number=args.issue_number,
                state_dir=args.state_dir,
                root_socket=args.root_socket,
                controller_binary=args.controller_binary,
                controllers_dir=args.controllers_dir,
                runner_token_file=args.runner_token_file,
            )
        except MaintenanceControllerError as exc:
            print(
                json.dumps(
                    {
                        "status": "TRANSIENT_ERROR",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            if args.once:
                return 70
        else:
            print(json.dumps(result, sort_keys=True), flush=True)
            if args.once:
                return 0
        time.sleep(max(5, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
