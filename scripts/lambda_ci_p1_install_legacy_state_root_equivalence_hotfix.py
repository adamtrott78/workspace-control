#!/usr/bin/env python3
"""Install the reviewed legacy-state-root equivalence hotfix only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import pwd
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

EXPECTED_HELPER = pathlib.Path(
    "scripts/lambda_ci_p1_install_legacy_state_root_equivalence_hotfix.py"
)
SOURCE_ROOT = pathlib.Path("scripts/lambda_ci_reconciler.py")

INSTALLED_ROOT = pathlib.Path(
    "/opt/workspace-ci/reconciler/lambda_ci_reconciler.py"
)
INSTALLED_RECONCILE_CONTROLLER = pathlib.Path(
    "/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py"
)
INSTALLED_ONE_SHOT_UNIT = pathlib.Path(
    "/etc/systemd/system/workspace-ci-reconcile-controller-once.service"
)
INSTALLED_CONTROLLER_BINARY = pathlib.Path(
    "/opt/workspace-ci/controller/lambda-ci-controller"
)

RECONCILE_CONTROLLER_STATE = pathlib.Path(
    "/var/lib/workspace-ci/reconcile-controller"
)
LAST_REJECTED = RECONCILE_CONTROLLER_STATE / "last-rejected.json"
ARCHIVED_REJECTED = (
    RECONCILE_CONTROLLER_STATE
    / "last-rejected.pre-legacy-state-root-equivalence-hotfix.json"
)

ROOT_SERVICE = "workspace-ci-reconciler.service"
AUTO_CONTROLLER = "workspace-ci-reconcile-controller.service"
ONE_SHOT = "workspace-ci-reconcile-controller-once.service"
WORKSPACE_CPU = "workspace-ci-controller@workspace-control-cpu.service"
PRESERVED = [
    "workspace-ci-controller@padataset-cpu.service",
    "workspace-ci-controller@padataset-gpu.service",
    "workspace-ci-controller@research-engine-cpu.service",
    "workspace-ci-controller@research-engine-gpu.service",
]
ROOT_SOCKET = pathlib.Path("/run/workspace-ci/reconciler.sock")

EXPECTED_POLICY_SHA = "e8a458a8ce922ac89ad91354b29f5dc4ecbd5e91"
EXPECTED_REQUEST_ID = "94e3e5ae-d1a7-541b-9185-7acb5c5b7103"
EXPECTED_WORKFLOW_RUN_ID = 40587498629
EXPECTED_OLD_ROOT_SHA256 = (
    "865cedf8f0d437f4e67f0d04d748e16d70fbc162708248dbef038b8afb4d29bd"
)
EXPECTED_RECONCILE_CONTROLLER_SHA256 = (
    "09130c0d8c8a83339b2110cb4a7163b2abd7d5ea18d423083b8437db038df34a"
)
EXPECTED_ONE_SHOT_UNIT_SHA256 = (
    "6e32ccf001161e17fdd3ad01abadfb44f57576b4d46ae9c3ebc102fb935fa69b"
)
EXPECTED_CONTROLLER_BINARY_SHA256 = (
    "6acd290f2312f0908d17443a2f5ee8d31711fbdb3f0bf9318171e9edd0ddee12"
)
EXPECTED_REVIEWED_SOURCE_HEAD = "a2587410cde8ca2e077ea9228342b7651abb793d"
EXPECTED_REVIEWED_RECONCILER_GIT_BLOB = (
    "ee86b28412c0dff70fe79d915978fc9cd1f7cbd7"
)
EXPECTED_REVIEW_TASK_ID = "workspace-github-actions-selfhosted-control-plane-v1"
EXPECTED_REVIEW_PR_NUMBER = 560
EXPECTED_REVIEW_OWNER = "adamtrott78"
EXPECTED_PRIOR_BLOCKING_REVIEW_COMMENT_ID = 6459054952
REVIEW_AUTHORITY_MARKER = "WORKSPACE_CONTROL_PRIVILEGED_INSTALL_REVIEW_V1"
REVIEW_AUTHORITY_END = "END_WORKSPACE_CONTROL_PRIVILEGED_INSTALL_REVIEW_V1"
REVIEW_API_URL = (
    "https://api.github.com/repos/adamtrott78/workspace-control/issues/560/comments"
)
REVIEW_API_TIMEOUT_SECONDS = 5.0
REVIEW_API_MAX_PAGES = 10
REVIEW_API_MAX_BYTES = 4 * 1024 * 1024
EXPECTED_LOCAL_SUBNET = "134.88.12.0/22"
LEGACY_SIBLING_MANIFESTS = {
    "padataset": pathlib.Path(
        "architecture/lambda-ci-project-padataset.v1.json"
    ),
    "research-engine": pathlib.Path(
        "architecture/lambda-ci-project-research-engine.v2.json"
    ),
}

EXPECTED_AUTO = {
    "LoadState": "loaded",
    "ActiveState": "inactive",
    "SubState": "dead",
    "UnitFileState": "enabled",
    "NRestarts": "0",
    "ExecMainStatus": "15",
    "MainPID": "0",
    "InvocationID": "294fcee8ea1548f8863d17680f21cf92",
}
EXPECTED_ONE_SHOT = {
    "LoadState": "loaded",
    "ActiveState": "failed",
    "SubState": "failed",
    "UnitFileState": "static",
    "NRestarts": "0",
    "ExecMainStatus": "70",
    "MainPID": "0",
    "InvocationID": "9659518ca16b4596a6936d72bd5e1e34",
}
EXPECTED_WORKSPACE_CPU = {
    "LoadState": "loaded",
    "ActiveState": "inactive",
    "SubState": "dead",
    "UnitFileState": "disabled",
    "NRestarts": "0",
    "ExecMainStatus": "0",
    "MainPID": "0",
    "InvocationID": "",
}
EXPECTED_SIBLINGS = {
    "workspace-ci-controller@padataset-cpu.service": {
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
        "UnitFileState": "enabled",
        "NRestarts": "0",
        "ExecMainStatus": "0",
        "MainPID": "2433911",
        "InvocationID": "264b5b8d1ff847d1873ebabdd0f466fd",
    },
    "workspace-ci-controller@padataset-gpu.service": {
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
        "UnitFileState": "enabled",
        "NRestarts": "0",
        "ExecMainStatus": "0",
        "MainPID": "2433913",
        "InvocationID": "a2c4a67262dc488a97929cf77cf83805",
    },
    "workspace-ci-controller@research-engine-cpu.service": {
        "LoadState": "loaded",
        "ActiveState": "inactive",
        "SubState": "dead",
        "UnitFileState": "enabled",
        "NRestarts": "12411",
        "ExecMainStatus": "1",
        "MainPID": "0",
        "InvocationID": "fdb8c54f1bf34556942f7137dac4fe92",
    },
    "workspace-ci-controller@research-engine-gpu.service": {
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
        "UnitFileState": "enabled",
        "NRestarts": "0",
        "ExecMainStatus": "0",
        "MainPID": "2433914",
        "InvocationID": "b79c01d618f4492c8630994f1d301ba8",
    },
}


class HotfixError(RuntimeError):
    pass


def run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise HotfixError(
            f"command failed rc={proc.returncode}: {argv!r}: {proc.stderr.strip()}"
        )
    return proc


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def parse_review_authority_block(body: str) -> dict[str, str]:
    start = body.count(REVIEW_AUTHORITY_MARKER)
    end = body.count(REVIEW_AUTHORITY_END)
    if start != 1 or end != 1:
        raise HotfixError("review authority marker count mismatch")
    before, rest = body.split(REVIEW_AUTHORITY_MARKER, 1)
    block, after = rest.split(REVIEW_AUTHORITY_END, 1)
    del before, after
    lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
    parsed: dict[str, str] = {}
    for line in lines:
        if "=" not in line:
            raise HotfixError("review authority block contains malformed line")
        key, value = line.split("=", 1)
        if not key or key in parsed:
            raise HotfixError("review authority block contains duplicate/empty key")
        parsed[key] = value
    expected_keys = {
        "task_id",
        "pr_number",
        "head_sha",
        "installer_blob",
        "reconciler_blob",
        "prior_blocking_comment_id",
        "review_request_comment_id",
        "disposition",
    }
    if set(parsed) != expected_keys:
        raise HotfixError(
            "review authority block keys mismatch: "
            f"actual={sorted(parsed)} expected={sorted(expected_keys)}"
        )
    return parsed


def fetch_review_comments() -> list[dict]:
    comments: list[dict] = []
    for page in range(1, REVIEW_API_MAX_PAGES + 1):
        request = urllib.request.Request(
            f"{REVIEW_API_URL}?per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "workspace-control-p1-hotfix-review-authority/1",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=REVIEW_API_TIMEOUT_SECONDS,
            ) as response:
                if getattr(response, "status", 200) != 200:
                    raise HotfixError(
                        "review authority API returned non-200 status: "
                        f"{getattr(response, 'status', None)}"
                    )
                raw = response.read(REVIEW_API_MAX_BYTES + 1)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise HotfixError(
                f"unable to fetch external review authority: {exc}"
            ) from exc
        if len(raw) > REVIEW_API_MAX_BYTES:
            raise HotfixError("review authority API response exceeds size bound")
        try:
            page_comments = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HotfixError("review authority API returned invalid JSON") from exc
        if not isinstance(page_comments, list):
            raise HotfixError("review authority API response is not a comment list")
        for comment in page_comments:
            if not isinstance(comment, dict):
                raise HotfixError("review authority API contains non-object comment")
        comments.extend(page_comments)
        if len(page_comments) < 100:
            return comments
    raise HotfixError("review authority comment pagination exceeded bound")


def require_external_review_authority(
    head: str,
    helper_blob: str,
) -> dict[str, object]:
    comments = fetch_review_comments()
    by_id: dict[int, dict] = {}
    for comment in comments:
        comment_id = comment.get("id")
        if isinstance(comment_id, int):
            by_id[comment_id] = comment

    matches: list[dict[str, object]] = []
    for comment in comments:
        body = comment.get("body")
        if not isinstance(body, str) or REVIEW_AUTHORITY_MARKER not in body:
            continue
        parsed = parse_review_authority_block(body)
        comment_id = comment.get("id")
        user = comment.get("user")
        if (
            not isinstance(comment_id, int)
            or comment_id <= EXPECTED_PRIOR_BLOCKING_REVIEW_COMMENT_ID
        ):
            raise HotfixError("review authority comment identity is stale/invalid")
        if not isinstance(user, dict) or user.get("login") != EXPECTED_REVIEW_OWNER:
            raise HotfixError("review authority comment owner mismatch")
        if comment.get("author_association") != "OWNER":
            raise HotfixError("review authority comment association mismatch")
        if (
            not isinstance(comment.get("created_at"), str)
            or comment.get("created_at") != comment.get("updated_at")
        ):
            raise HotfixError("review authority comment was edited or lacks timestamps")

        expected = {
            "task_id": EXPECTED_REVIEW_TASK_ID,
            "pr_number": str(EXPECTED_REVIEW_PR_NUMBER),
            "head_sha": head,
            "installer_blob": helper_blob,
            "reconciler_blob": EXPECTED_REVIEWED_RECONCILER_GIT_BLOB,
            "prior_blocking_comment_id": str(
                EXPECTED_PRIOR_BLOCKING_REVIEW_COMMENT_ID
            ),
            "disposition": "NO_BLOCKING_FINDING",
        }
        if any(parsed.get(key) != value for key, value in expected.items()):
            continue

        try:
            request_comment_id = int(parsed["review_request_comment_id"])
        except ValueError as exc:
            raise HotfixError("review request comment ID is not an integer") from exc
        request_comment = by_id.get(request_comment_id)
        if (
            request_comment_id <= EXPECTED_PRIOR_BLOCKING_REVIEW_COMMENT_ID
            or not isinstance(request_comment, dict)
        ):
            raise HotfixError("bound review request comment is missing/stale")
        request_body = request_comment.get("body")
        request_user = request_comment.get("user")
        if (
            not isinstance(request_body, str)
            or "Fresh independent exact-head re-review request" not in request_body
            or head not in request_body
            or not isinstance(request_user, dict)
            or request_user.get("login") != EXPECTED_REVIEW_OWNER
            or request_comment.get("author_association") != "OWNER"
            or request_comment.get("created_at") != request_comment.get("updated_at")
        ):
            raise HotfixError("bound review request comment is not exact/unedited")
        if request_comment.get("created_at") >= comment.get("created_at"):
            raise HotfixError("review authority predates its bound review request")

        matches.append(
            {
                "comment_id": comment_id,
                "review_request_comment_id": request_comment_id,
                "created_at": comment["created_at"],
                "body_sha256": sha256_bytes(body.encode("utf-8")),
                "head_sha": head,
                "installer_blob": helper_blob,
                "reconciler_blob": EXPECTED_REVIEWED_RECONCILER_GIT_BLOB,
            }
        )

    if len(matches) != 1:
        raise HotfixError(
            "external independent review authority missing or ambiguous: "
            f"matches={len(matches)}"
        )
    return matches[0]


def attest_source(
    expected_head: str,
    invoker: str,
) -> tuple[pathlib.Path, dict[str, object]]:
    helper = pathlib.Path(__file__).resolve()
    repo = helper.parents[1]
    if helper != (repo / EXPECTED_HELPER).resolve():
        raise HotfixError("executing helper is outside reviewed tracked path")
    prefix = ["/usr/sbin/runuser", "-u", invoker, "--", "git", "-C", str(repo)]
    if run([*prefix, "rev-parse", "--show-toplevel"]).stdout.strip() != str(repo):
        raise HotfixError("reviewed repository top-level mismatch")

    head = run([*prefix, "rev-parse", "HEAD"]).stdout.strip()
    if head != expected_head:
        raise HotfixError(
            f"HEAD mismatch: actual={head} expected={expected_head}"
        )

    symbolic = run([*prefix, "symbolic-ref", "-q", "HEAD"], check=False)
    if symbolic.returncode == 0:
        raise HotfixError(
            "HEAD must be detached; attached="
            + (symbolic.stdout.strip() or "<unknown>")
        )
    if symbolic.returncode != 1:
        raise HotfixError(
            "unable to prove detached HEAD: "
            f"rc={symbolic.returncode} stderr={symbolic.stderr.strip()}"
        )

    if run(
        [*prefix, "status", "--porcelain=v1", "--untracked-files=no"]
    ).stdout.strip():
        raise HotfixError("reviewed tracked tree is dirty")
    for path in (EXPECTED_HELPER, SOURCE_ROOT):
        if run(
            [*prefix, "ls-files", "--error-unmatch", str(path)],
            check=False,
        ).returncode != 0:
            raise HotfixError(f"reviewed tracked source is absent: {path}")

    if run(
        [
            *prefix,
            "cat-file",
            "-e",
            f"{EXPECTED_REVIEWED_SOURCE_HEAD}^{{commit}}",
        ],
        check=False,
    ).returncode != 0:
        raise HotfixError("reviewed immutable source authority is unavailable")

    reviewed_blob = run(
        [
            *prefix,
            "rev-parse",
            f"{EXPECTED_REVIEWED_SOURCE_HEAD}:{SOURCE_ROOT}",
        ]
    ).stdout.strip()
    if reviewed_blob != EXPECTED_REVIEWED_RECONCILER_GIT_BLOB:
        raise HotfixError(
            "reviewed reconciler authority blob mismatch: "
            f"actual={reviewed_blob} "
            f"expected={EXPECTED_REVIEWED_RECONCILER_GIT_BLOB}"
        )

    head_blob = run(
        [*prefix, "rev-parse", f"HEAD:{SOURCE_ROOT}"]
    ).stdout.strip()
    if head_blob != EXPECTED_REVIEWED_RECONCILER_GIT_BLOB:
        raise HotfixError(
            "reconciler source blob mismatch: "
            f"actual={head_blob} "
            f"expected={EXPECTED_REVIEWED_RECONCILER_GIT_BLOB}"
        )

    helper_blob = run(
        [*prefix, "rev-parse", f"HEAD:{EXPECTED_HELPER}"]
    ).stdout.strip()
    if len(helper_blob) != 40 or any(
        char not in "0123456789abcdef" for char in helper_blob
    ):
        raise HotfixError("executing helper Git blob identity is malformed")

    review_authority = require_external_review_authority(head, helper_blob)
    return repo, review_authority


def snapshot(service: str) -> dict[str, str]:
    props = [
        "LoadState",
        "ActiveState",
        "SubState",
        "UnitFileState",
        "NRestarts",
        "ExecMainStatus",
        "MainPID",
        "InvocationID",
    ]
    out = run(
        ["systemctl", "show", service, *[f"--property={p}" for p in props]]
    ).stdout
    value: dict[str, str] = {}
    for line in out.splitlines():
        if "=" in line:
            key, item = line.split("=", 1)
            value[key] = item
    if set(value) != set(props):
        raise HotfixError(f"incomplete service snapshot: {service}: {value}")
    return value


def require_snapshot(service: str, expected: dict[str, str]) -> dict[str, str]:
    actual = snapshot(service)
    if actual != expected:
        raise HotfixError(
            f"service snapshot mismatch for {service}: "
            f"actual={actual} expected={expected}"
        )
    return actual


def require_root_healthy() -> dict[str, str]:
    value = snapshot(ROOT_SERVICE)
    if (
        value["LoadState"] != "loaded"
        or value["ActiveState"] != "active"
        or value["SubState"] != "running"
        or value["ExecMainStatus"] != "0"
        or value["MainPID"] == "0"
    ):
        raise HotfixError(f"root reconciler is not healthy: {value}")
    return value


def validate_rejected_marker(raw: bytes) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HotfixError("last-rejected marker is invalid JSON") from exc
    if not isinstance(value, dict):
        raise HotfixError("last-rejected marker must be object")
    if value.get("status") != "REJECTED":
        raise HotfixError("last-rejected status mismatch")
    if value.get("commit_sha") != EXPECTED_POLICY_SHA:
        raise HotfixError("last-rejected policy SHA mismatch")
    if value.get("approved_policy_sha") != EXPECTED_POLICY_SHA:
        raise HotfixError("last-rejected approved policy SHA mismatch")
    if value.get("observed_main_sha") != EXPECTED_POLICY_SHA:
        raise HotfixError("last-rejected observed main SHA mismatch")
    if value.get("policy_equivalent_to_observed_main") is not True:
        raise HotfixError("last-rejected policy equivalence mismatch")
    if value.get("request_id") != EXPECTED_REQUEST_ID:
        raise HotfixError("last-rejected request ID mismatch")
    if value.get("workflow_run_id") != EXPECTED_WORKFLOW_RUN_ID:
        raise HotfixError("last-rejected workflow run mismatch")
    response = value.get("response")
    if not isinstance(response, dict):
        raise HotfixError("last-rejected response missing")
    if response.get("status") != "REJECTED":
        raise HotfixError("last-rejected root response status mismatch")
    if response.get("error_type") != "ReconcileError":
        raise HotfixError("last-rejected root error type mismatch")
    error = response.get("error")
    required_fragments = [
        "derived controller transaction differs from reviewed expected transaction",
        "workspace-ci-controller@padataset-cpu.service",
        "workspace-ci-controller@padataset-gpu.service",
        "workspace-ci-controller@research-engine-cpu.service",
        "workspace-ci-controller@research-engine-gpu.service",
        "workspace-ci-controller@workspace-control-cpu.service",
    ]
    if not isinstance(error, str) or any(
        fragment not in error for fragment in required_fragments
    ):
        raise HotfixError("last-rejected root error does not match reviewed rejection")
    return value


def render_legacy_controller_env(
    manifest: dict,
    lane: str,
) -> bytes:
    lane_cfg = manifest["derived_identity"]["lanes"][lane]
    values = {
        "WORKSPACE_CI_ADMISSION_V2_ENABLED": "YES",
        "WORKSPACE_CI_GITHUB_URL": f"https://github.com/{manifest['repository']}",
        "WORKSPACE_CI_LANE": lane,
        "WORKSPACE_CI_PAT_FILE": "/var/lib/workspace-ci/controller/github-token",
        "WORKSPACE_CI_PROJECT_ID": manifest["project_id"],
        "WORKSPACE_CI_PROVISIONER_SOCKET": "/run/workspace-ci/provisioner.sock",
        "WORKSPACE_CI_RUNNER_PREFIX": lane_cfg["runner_prefix"],
        "WORKSPACE_CI_SCALESET_NAME": lane_cfg["scale_set_name"],
    }
    return "".join(
        f"{key}={values[key]}\n" for key in sorted(values)
    ).encode("utf-8")


def verify_exact_legacy_sibling_material(repo: pathlib.Path) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for project_id, relative_manifest in LEGACY_SIBLING_MANIFESTS.items():
        manifest = json.loads((repo / relative_manifest).read_text(encoding="utf-8"))
        for lane in ("cpu", "gpu"):
            env_path = pathlib.Path(
                f"/etc/workspace-ci/controllers/{project_id}-{lane}.env"
            )
            expected_env = render_legacy_controller_env(manifest, lane)
            if not env_path.is_file() or env_path.read_bytes() != expected_env:
                raise HotfixError(
                    f"legacy sibling env mismatch: {project_id}-{lane}"
                )
            dropin_path = pathlib.Path(
                "/etc/systemd/system/"
                f"workspace-ci-controller@{project_id}-{lane}.service.d/network.conf"
            )
            expected_dropin = (
                f"[Service]\nIPAddressDeny={EXPECTED_LOCAL_SUBNET}\n"
            ).encode("utf-8")
            if not dropin_path.is_file() or dropin_path.read_bytes() != expected_dropin:
                raise HotfixError(
                    f"legacy sibling network drop-in mismatch: {project_id}-{lane}"
                )
            evidence[f"{project_id}-{lane}"] = {
                "env_sha256": sha256_bytes(expected_env),
                "dropin_sha256": sha256_bytes(expected_dropin),
            }
    return evidence


def wait_socket() -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(0.25)
        try:
            client.connect(str(ROOT_SOCKET))
            return
        except OSError:
            time.sleep(0.1)
        finally:
            client.close()
    raise HotfixError("root reconciler AF_UNIX socket is not ready")


def atomic_write(path: pathlib.Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = pathlib.Path(tmp_raw)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(tmp, 0, 0)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def certify_preserved(
    auto_before: dict[str, str],
    one_shot_before: dict[str, str],
    workspace_before: dict[str, str],
    siblings_before: dict[str, dict[str, str]],
) -> None:
    if snapshot(AUTO_CONTROLLER) != auto_before:
        raise HotfixError("automatic reconcile-controller changed")
    if snapshot(ONE_SHOT) != one_shot_before:
        raise HotfixError("one-shot reconcile-controller changed")
    if snapshot(WORKSPACE_CPU) != workspace_before:
        raise HotfixError("workspace-control CPU changed")
    for service, before in siblings_before.items():
        if snapshot(service) != before:
            raise HotfixError(f"preserved sibling changed: {service}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise HotfixError("installer must run as root via sudo")
    invoker = os.environ.get("SUDO_USER", "")
    if not invoker or invoker == "root":
        raise HotfixError("installer requires a non-root sudo invoker")
    pwd.getpwnam(invoker)

    repo, review_authority = attest_source(args.expected_head, invoker)
    source_root = (repo / SOURCE_ROOT).read_bytes()

    if sha256_path(INSTALLED_ROOT) != EXPECTED_OLD_ROOT_SHA256:
        raise HotfixError("installed root reconciler baseline mismatch")
    if (
        sha256_path(INSTALLED_RECONCILE_CONTROLLER)
        != EXPECTED_RECONCILE_CONTROLLER_SHA256
    ):
        raise HotfixError("installed reconcile-controller baseline mismatch")
    if sha256_path(INSTALLED_ONE_SHOT_UNIT) != EXPECTED_ONE_SHOT_UNIT_SHA256:
        raise HotfixError("installed one-shot unit baseline mismatch")
    if sha256_path(INSTALLED_CONTROLLER_BINARY) != EXPECTED_CONTROLLER_BINARY_SHA256:
        raise HotfixError("installed project-controller binary baseline mismatch")

    if not LAST_REJECTED.is_file():
        raise HotfixError("expected rejected one-shot marker is absent")
    if ARCHIVED_REJECTED.exists():
        raise HotfixError("rejected one-shot archive already exists")
    rejected_raw = LAST_REJECTED.read_bytes()
    rejected = validate_rejected_marker(rejected_raw)

    root_before = require_root_healthy()
    auto_before = require_snapshot(AUTO_CONTROLLER, EXPECTED_AUTO)
    one_shot_before = require_snapshot(ONE_SHOT, EXPECTED_ONE_SHOT)
    workspace_before = require_snapshot(WORKSPACE_CPU, EXPECTED_WORKSPACE_CPU)
    siblings_before = {
        service: require_snapshot(service, expected)
        for service, expected in EXPECTED_SIBLINGS.items()
    }
    legacy_material = verify_exact_legacy_sibling_material(repo)

    old_root = INSTALLED_ROOT.read_bytes()
    rollback_armed = True
    rejected_archived = False
    try:
        atomic_write(INSTALLED_ROOT, source_root, 0o755)
        run([
            "systemctl",
            "--job-mode=ignore-dependencies",
            "restart",
            ROOT_SERVICE,
        ])
        wait_socket()
        root_after = require_root_healthy()
        certify_preserved(
            auto_before,
            one_shot_before,
            workspace_before,
            siblings_before,
        )
        if sha256_path(INSTALLED_ROOT) != sha256_bytes(source_root):
            raise HotfixError("root reconciler install digest mismatch")

        os.replace(LAST_REJECTED, ARCHIVED_REJECTED)
        rejected_archived = True
        if LAST_REJECTED.exists():
            raise HotfixError("last-rejected marker still present after archive")
        if ARCHIVED_REJECTED.read_bytes() != rejected_raw:
            raise HotfixError("archived rejected marker bytes mismatch")

        receipt = {
            "schema_version": 1,
            "status": "P1_LEGACY_STATE_ROOT_EQUIVALENCE_HOTFIX_INSTALLED",
            "source_head": args.expected_head,
            "external_review_authority": review_authority,
            "installed_root_sha256": sha256_bytes(source_root),
            "controller_binary_sha256": sha256_path(INSTALLED_CONTROLLER_BINARY),
            "reconcile_controller_sha256": sha256_path(
                INSTALLED_RECONCILE_CONTROLLER
            ),
            "one_shot_unit_sha256": sha256_path(INSTALLED_ONE_SHOT_UNIT),
            "rejected_request": {
                "request_id": rejected["request_id"],
                "commit_sha": rejected["commit_sha"],
                "workflow_run_id": rejected["workflow_run_id"],
                "status": rejected["status"],
                "archived_path": str(ARCHIVED_REJECTED),
                "archived_sha256": sha256_bytes(rejected_raw),
            },
            "root_before": root_before,
            "root_after": root_after,
            "automatic_reconcile_controller": auto_before,
            "one_shot_controller": one_shot_before,
            "workspace_control_cpu": workspace_before,
            "preserved_siblings": siblings_before,
            "verified_legacy_sibling_material": legacy_material,
            "activation_performed": False,
            "retry_performed": False,
            "automatic_workflow_triggered": False,
        }
        print(
            "P1_LEGACY_STATE_ROOT_EQUIVALENCE_HOTFIX_RECEIPT="
            + json.dumps(receipt, sort_keys=True)
        )
        return 0
    except Exception as exc:
        if not rollback_armed:
            raise
        rollback_errors: list[str] = []
        try:
            atomic_write(INSTALLED_ROOT, old_root, 0o755)
            if rejected_archived:
                if LAST_REJECTED.exists():
                    raise HotfixError(
                        "cannot restore rejected marker because destination exists"
                    )
                os.replace(ARCHIVED_REJECTED, LAST_REJECTED)
            run([
                "systemctl",
                "--job-mode=ignore-dependencies",
                "restart",
                ROOT_SERVICE,
            ])
            wait_socket()
            require_root_healthy()
            certify_preserved(
                auto_before,
                one_shot_before,
                workspace_before,
                siblings_before,
            )
            if INSTALLED_ROOT.read_bytes() != old_root:
                raise HotfixError("rollback did not restore exact old root bytes")
            if LAST_REJECTED.read_bytes() != rejected_raw:
                raise HotfixError("rollback did not restore exact rejected marker")
            if ARCHIVED_REJECTED.exists():
                raise HotfixError("rollback left rejected archive behind")
        except Exception as rollback_exc:
            rollback_errors.append(str(rollback_exc))
        if rollback_errors:
            raise HotfixError(
                "legacy-state-root hotfix failed and rollback incomplete: "
                f"original={type(exc).__name__}:{exc}; "
                f"rollback={'; '.join(rollback_errors)}"
            ) from exc
        raise HotfixError(
            "legacy-state-root hotfix failed and rollback completed: "
            f"{type(exc).__name__}:{exc}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
