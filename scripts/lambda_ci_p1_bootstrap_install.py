#!/usr/bin/env python3
"""One-shot rollback-safe GitRunner P1 bootstrap installer.

This script is intentionally narrower than P1 activation. It installs the
already-reviewed controller/runtime/reconciler and L0 maintenance substrate
against the exact live-host fingerprint captured on 2026-10-27, while keeping
workspace-control MIGRATION_CANDIDATE_NOT_INSTALLED / PLANNED_NOT_BOUND.

It never activates the workspace-control runner, never changes maxRunners or
project concurrency, never enables P2/P3, and intentionally leaves the automatic
GitHub reconciliation controller stopped after success so the next activation
gate remains explicit.

Run only via sudo from an exact reviewed workspace-control checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import pwd
import grp
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

MAINTENANCE_ISSUE_NUMBER = 527
GO_BIN = pathlib.Path("/opt/workspace-ci/go/1.26.3/bin/go")

EXPECTED_INSTALLED_SHA256 = {
    "/opt/workspace-ci/controller/lambda-ci-controller": "11b0aa8d16eceaabdb5d3cf92d2d9525722bd73ff98960665eb857b39f6ef837",
    "/opt/workspace-ci/provisioner/lambda_ci_admission.py": "b86297e41e3ab73da6a574eb023ac1dc8812b6b3aaae29b143c34f363d123686",
    "/opt/workspace-ci/provisioner/lambda_ci_multirepo.py": "c47b41c1171a9afce290a23abc4c07d1310c35e3d83e4e7b1ad3528f384bf47d",
    "/opt/workspace-ci/provisioner/lambda_ci_provisioner.py": "c98f8223e2ccd84ff9fc2753c083de70a292238279cc825377c2cef9001bde71",
    "/opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py": "e7672ae82d94ae8e994db4c5df948d4cfed0882ef39d6d4688cffc7a3b95f31e",
    "/opt/workspace-ci/provisioner/lambda_ci_runtime.py": "f221f91d5b744c2350303b96b6df4e29f99e73cc15199fcb68ab9d31df1f5ce0",
    "/opt/workspace-ci/reconciler/lambda_ci_multirepo.py": "c47b41c1171a9afce290a23abc4c07d1310c35e3d83e4e7b1ad3528f384bf47d",
    "/opt/workspace-ci/reconciler/lambda_ci_reconciler.py": "c424e62c20cd38fa0380d315e4cf28831ce63ff63dd7aa9711913a41c405fcc6",
    "/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py": "0dc9d6b03f73d906f67c36dafafdf3962bed26f2f84250c52e31478ea7151c80",
    "/etc/systemd/system/workspace-ci-controller@.service": "13277bbbfd6ab720e2bd4d5246c204fa925d52507fcaad17ce3da95a3ea67344",
    "/etc/systemd/system/workspace-ci-reconciler.service": "f1debf5cfe0f8a5efabbfdb62976c4ada048a8916a2399be54cc200d7279abe2",
    "/etc/systemd/system/workspace-ci-reconcile-controller.service": "e7f7704c4f1fef122c067cbee7e0fad054b326bcb618010a945f98b9ffac2da6",
    "/etc/tmpfiles.d/workspace-ci.conf": "ab38292fa105a6a6d5c00a4fd63f591ed9314976d9882b443d48a262b40fbce9",
    "/etc/workspace-ci/lambda-ci-project-registry.v1.json": "49b9a63c895f0df5ad0a41c1289491036de8cf92410cc325973043b68526f694",
    "/etc/workspace-ci/lambda-ci-execution-contracts.v1.json": "ac6f9e604898810574e9561f5cf01fb268be4a9f574f7e9b0b75753040af3cf8",
    "/etc/workspace-ci/lambda-ci-reconciliation-ceiling.v1.json": "2705eefea726349ec91589902396e4e28d3d76dc22080158b1e9c1f192a3c717",
    "/etc/workspace-ci/lambda-ci-systemd-profiles.v1.json": "3a5824d16e42747b85dc9834d801e14e28b20dd93d026527859f5206d022b0bb",
    "/etc/workspace-ci/lambda-ci-upstream-pins.v1.json": "52feaa34b76a80772c6987574a7063bbf3ee3305e22e48101b49c73b092616ae",
    "/etc/workspace-ci/lambda-ci-workload-policy.v1.json": "22d117978f2959c3d9cea2fb8bd3acde85f8a9c18cd2ea7fdd7038337694f9a8",
    "/etc/workspace-ci/projects/research-engine.json": "81ad10d9b1b42050bbc93606d1e86c6b38d15d94a68d2269229bbccfdf043503",
    "/etc/workspace-ci/projects/padataset.json": "e902573223dc931994c5ee7803632ad9f526ffe8a796d4054f43163358bbc01b",
}

EXPECTED_ABSENT_PATHS = [
    "/opt/workspace-ci/maintenance/lambda_ci_maintenance_service.py",
    "/opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py",
    "/etc/systemd/system/workspace-ci-maintenance.service",
    "/etc/systemd/system/workspace-ci-maintenance-controller.service",
    "/etc/sysusers.d/workspace-ci.conf",
    "/etc/workspace-ci/projects/workspace-control.json",
    "/var/lib/workspace-ci/controller/state",
    "/var/lib/workspace-ci/maintenance",
    "/var/lib/workspace-ci/maintenance-controller",
    "/srv/workspace-ci/workspace-control",
]

HEALTHY_CONTROLLERS = [
    "workspace-ci-controller@research-engine-gpu.service",
    "workspace-ci-controller@padataset-cpu.service",
    "workspace-ci-controller@padataset-gpu.service",
]
RESEARCH_CPU = "workspace-ci-controller@research-engine-cpu.service"
RECONCILE_CONTROLLER = "workspace-ci-reconcile-controller.service"
PROVISIONER = "workspace-ci-provisioner.service"
RECONCILER = "workspace-ci-reconciler.service"
MAINTENANCE_ROOT = "workspace-ci-maintenance.service"
MAINTENANCE_CONTROLLER = "workspace-ci-maintenance-controller.service"

TARGET_FILES = [
    "/opt/workspace-ci/controller/lambda-ci-controller",
    "/opt/workspace-ci/provisioner/lambda_ci_multirepo.py",
    "/opt/workspace-ci/provisioner/lambda_ci_runtime.py",
    "/opt/workspace-ci/reconciler/lambda_ci_multirepo.py",
    "/opt/workspace-ci/reconciler/lambda_ci_reconciler.py",
    "/opt/workspace-ci/maintenance/lambda_ci_maintenance_service.py",
    "/opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py",
    "/etc/systemd/system/workspace-ci-controller@.service",
    "/etc/systemd/system/workspace-ci-reconciler.service",
    "/etc/systemd/system/workspace-ci-maintenance.service",
    "/etc/systemd/system/workspace-ci-maintenance-controller.service",
    "/etc/tmpfiles.d/workspace-ci.conf",
    "/etc/sysusers.d/workspace-ci.conf",
    "/etc/workspace-ci/lambda-ci-project-registry.v1.json",
    "/etc/workspace-ci/lambda-ci-execution-contracts.v1.json",
    "/etc/workspace-ci/lambda-ci-reconciliation-ceiling.v1.json",
    "/etc/workspace-ci/lambda-ci-systemd-profiles.v1.json",
    "/etc/workspace-ci/lambda-ci-workload-policy.v1.json",
    "/etc/workspace-ci/projects/workspace-control.json",
    "/etc/workspace-ci/maintenance-controller.env",
    "/var/lib/workspace-ci/maintenance-controller/github-read-token",
    "/var/lib/workspace-ci/maintenance-controller/runner-token",
]

NEW_STATE_PATHS = [
    "/var/lib/workspace-ci/controller/state",
    "/var/lib/workspace-ci/maintenance",
    "/var/lib/workspace-ci/maintenance-controller",
    "/run/workspace-ci/maintenance",
]


class BootstrapError(RuntimeError):
    pass


def run(
    argv: list[str],
    *,
    check: bool = True,
    user: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = argv
    if user is not None:
        command = ["runuser", "-u", user, "--", *argv]
    proc = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
    )
    if check and proc.returncode != 0:
        raise BootstrapError(
            f"command failed rc={proc.returncode}: {command!r}: {proc.stderr.strip()}"
        )
    return proc


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_as(invoker: str, repo: pathlib.Path, *args: str) -> str:
    proc = run(["git", "-C", str(repo), *args], user=invoker)
    return proc.stdout.strip()


def service_active(name: str) -> bool:
    return run(["systemctl", "is-active", "--quiet", name], check=False).returncode == 0


def service_enabled(name: str) -> bool:
    return run(["systemctl", "is-enabled", "--quiet", name], check=False).returncode == 0


def service_show(name: str, *properties: str) -> dict[str, str]:
    argv = ["systemctl", "show", name, "--no-pager"]
    for prop in properties:
        argv.extend(["-p", prop])
    proc = run(argv, check=False)
    values: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def no_active_project_execution() -> None:
    proc = run(
        [
            "systemctl",
            "list-units",
            "--all",
            "--plain",
            "--no-legend",
            "--no-pager",
            "workspace-ci-research-engine-*.service",
            "workspace-ci-padataset-*.service",
        ],
        check=False,
    )
    if proc.returncode not in {0, 1}:
        raise BootstrapError("unable to inspect active project execution units")
    active = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[2] in {"active", "activating", "deactivating"}:
            active.append(line)
    if active:
        raise BootstrapError(
            "active project execution exists; bootstrap refuses to mutate:\n"
            + "\n".join(active)
        )


def github_get_with_token(token_path: pathlib.Path, api_path: str) -> Any:
    st = token_path.stat()
    if st.st_mode & 0o077:
        raise BootstrapError(f"source token permissions too broad: {token_path}")
    token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        raise BootstrapError(f"source token empty: {token_path}")
    req = urllib.request.Request(
        "https://api.github.com" + api_path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "workspace-control-p1-bootstrap/1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read(2048).decode("utf-8", errors="replace")
        raise BootstrapError(
            f"GitHub credential preflight HTTP {exc.code} for {api_path}: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise BootstrapError(
            f"GitHub credential preflight unavailable for {api_path}: {exc}"
        ) from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BootstrapError(
            f"GitHub credential preflight returned invalid JSON for {api_path}"
        ) from exc


def verify_credential_scope() -> None:
    read_token = pathlib.Path(
        "/var/lib/workspace-ci/reconcile-controller/github-token"
    )
    runner_token = pathlib.Path("/var/lib/workspace-ci/controller/github-token")

    issue = github_get_with_token(
        read_token,
        f"/repos/adamtrott78/workspace-control/issues/{MAINTENANCE_ISSUE_NUMBER}",
    )
    if not isinstance(issue, dict) or issue.get("state") != "open":
        raise BootstrapError("reconciliation token cannot read maintenance issue #527")
    comments = github_get_with_token(
        read_token,
        f"/repos/adamtrott78/workspace-control/issues/{MAINTENANCE_ISSUE_NUMBER}/comments?per_page=1",
    )
    if not isinstance(comments, list):
        raise BootstrapError("reconciliation token cannot read maintenance comments")

    runners = github_get_with_token(
        runner_token,
        "/repos/adamtrott78/workspace-control/actions/runners?per_page=1",
    )
    if not isinstance(runners, dict) or not isinstance(runners.get("runners"), list):
        raise BootstrapError(
            "controller token lacks workspace-control Actions runner read/admin scope"
        )


def verify_live_fingerprint() -> None:
    for raw, expected in EXPECTED_INSTALLED_SHA256.items():
        path = pathlib.Path(raw)
        if not path.is_file():
            raise BootstrapError(f"preflight file disappeared: {path}")
        actual = sha256(path)
        if actual != expected:
            raise BootstrapError(
                f"live host drift: {path}: actual={actual} expected={expected}"
            )
    for raw in EXPECTED_ABSENT_PATHS:
        if pathlib.Path(raw).exists():
            raise BootstrapError(f"preflight absent path now exists: {raw}")

    for service in [PROVISIONER, RECONCILER, RECONCILE_CONTROLLER, *HEALTHY_CONTROLLERS]:
        if not service_active(service):
            raise BootstrapError(f"required pre-bootstrap service is not active: {service}")

    if service_active("workspace-ci-controller@workspace-control-cpu.service"):
        raise BootstrapError("workspace-control controller became active before bootstrap")
    if service_active(MAINTENANCE_ROOT) or service_active(MAINTENANCE_CONTROLLER):
        raise BootstrapError("maintenance plane became active before bootstrap")

    for user in ["ci-controller", "ci-reconciler", "ci-research-engine", "ci-padataset"]:
        try:
            pwd.getpwnam(user)
        except KeyError as exc:
            raise BootstrapError(f"required identity missing: {user}") from exc
    for user in ["ci-maintenance", "ci-workspace-control"]:
        try:
            pwd.getpwnam(user)
        except KeyError:
            pass
        else:
            raise BootstrapError(f"preflight absent identity now exists: {user}")

    registry = json.loads(
        pathlib.Path("/etc/workspace-ci/lambda-ci-project-registry.v1.json").read_text(
            encoding="utf-8"
        )
    )
    projects = registry.get("projects", {})
    if set(projects) != {"research-engine", "padataset"}:
        raise BootstrapError(
            f"installed registry changed since preflight: {sorted(projects)}"
        )
    if any(
        projects[name].get("activation_state") != "ACTIVE"
        for name in ("research-engine", "padataset")
    ):
        raise BootstrapError("existing projects are not ACTIVE in installed registry")

    no_active_project_execution()


def install_file(src: pathlib.Path, dst: pathlib.Path, mode: int = 0o644) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.parent / f".{dst.name}.p1-install-{os.getpid()}"
    shutil.copyfile(src, tmp)
    os.chown(tmp, 0, 0)
    os.chmod(tmp, mode)
    os.replace(tmp, dst)


def copy_token(src: pathlib.Path, dst: pathlib.Path, uid: int, gid: int) -> None:
    st = src.stat()
    if st.st_mode & 0o077:
        raise BootstrapError(f"source token permissions too broad: {src}")
    data = src.read_bytes()
    if not data:
        raise BootstrapError(f"source token empty: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.parent / f".{dst.name}.p1-install-{os.getpid()}"
    tmp.write_bytes(data)
    os.chown(tmp, uid, gid)
    os.chmod(tmp, 0o600)
    os.replace(tmp, dst)


def build_controller(repo: pathlib.Path) -> pathlib.Path:
    if not GO_BIN.is_file():
        raise BootstrapError("isolated Go 1.26.3 toolchain missing")
    version = run([str(GO_BIN), "env", "GOVERSION"]).stdout.strip()
    if version != "go1.26.3":
        raise BootstrapError(f"isolated Go version drift: {version}")

    build_root = pathlib.Path(tempfile.mkdtemp(prefix="workspace-ci-p1-build-"))
    src = repo / "controller" / "lambda-ci-controller"
    shutil.copytree(src, build_root / "src")
    work = build_root / "src"
    controller = pwd.getpwnam("ci-controller")
    for root, dirs, files in os.walk(work):
        os.chown(root, controller.pw_uid, controller.pw_gid)
        for name in dirs:
            os.chown(os.path.join(root, name), controller.pw_uid, controller.pw_gid)
        for name in files:
            os.chown(os.path.join(root, name), controller.pw_uid, controller.pw_gid)
    out = work / "lambda-ci-controller"
    env = {
        "PATH": "/opt/workspace-ci/go/1.26.3/bin:/usr/bin:/bin",
        "HOME": "/var/lib/workspace-ci/controller",
        "GOCACHE": str(work / ".gocache"),
        "GOMODCACHE": str(work / ".gomodcache"),
    }
    run(
        [
            str(GO_BIN),
            "-C",
            str(work),
            "build",
            "-mod=mod",
            "-trimpath",
            "-o",
            str(out),
            ".",
        ],
        user="ci-controller",
        env=env,
    )
    if not out.is_file():
        raise BootstrapError("controller build produced no binary")
    return out


def backup_targets(backup_dir: pathlib.Path) -> dict[str, Any]:
    backup_dir.mkdir(parents=True, mode=0o700)
    manifest: dict[str, Any] = {"targets": {}}
    files_dir = backup_dir / "files"
    files_dir.mkdir(mode=0o700)
    for raw in TARGET_FILES:
        path = pathlib.Path(raw)
        key = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        record: dict[str, Any] = {"path": raw, "present": path.exists()}
        if path.exists():
            if not path.is_file():
                raise BootstrapError(f"backup target is not regular file: {path}")
            dst = files_dir / key
            shutil.copy2(path, dst)
            record["backup"] = str(dst)
            record["mode"] = path.stat().st_mode & 0o777
            record["uid"] = path.stat().st_uid
            record["gid"] = path.stat().st_gid
        manifest["targets"][raw] = record
    manifest["ci_maintenance_preexisting"] = False
    manifest["workspace_ci_maintenance_group_preexisting"] = False
    try:
        pwd.getpwnam("ci-maintenance")
    except KeyError:
        pass
    else:
        manifest["ci_maintenance_preexisting"] = True
    try:
        grp.getgrnam("workspace-ci-maintenance")
    except KeyError:
        pass
    else:
        manifest["workspace_ci_maintenance_group_preexisting"] = True
    manifest["services"] = {
        service: {
            "active": service_active(service),
            "enabled": service_enabled(service),
        }
        for service in [
            PROVISIONER,
            RECONCILER,
            RECONCILE_CONTROLLER,
            RESEARCH_CPU,
            *HEALTHY_CONTROLLERS,
            MAINTENANCE_ROOT,
            MAINTENANCE_CONTROLLER,
        ]
    }
    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def restore_targets(manifest: dict[str, Any]) -> None:
    run(["systemctl", "disable", "--now", MAINTENANCE_CONTROLLER], check=False)
    run(["systemctl", "disable", "--now", MAINTENANCE_ROOT], check=False)
    run(["systemctl", "stop", RESEARCH_CPU], check=False)
    run(["systemctl", "stop", PROVISIONER], check=False)
    run(["systemctl", "stop", RECONCILER], check=False)

    for raw, record in manifest["targets"].items():
        path = pathlib.Path(raw)
        if record["present"]:
            backup = pathlib.Path(record["backup"])
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(backup, path)
            os.chown(path, int(record["uid"]), int(record["gid"]))
            os.chmod(path, int(record["mode"]))
        else:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    for raw in reversed(NEW_STATE_PATHS):
        path = pathlib.Path(raw)
        if path.exists():
            shutil.rmtree(path)

    if not manifest.get("ci_maintenance_preexisting"):
        run(["userdel", "ci-maintenance"], check=False)
    if not manifest.get("workspace_ci_maintenance_group_preexisting"):
        run(["groupdel", "workspace-ci-maintenance"], check=False)

    run(["systemctl", "daemon-reload"], check=False)

    for service, prior in manifest["services"].items():
        if prior["enabled"]:
            run(["systemctl", "enable", service], check=False)
        else:
            run(["systemctl", "disable", service], check=False)
        if prior["active"]:
            run(["systemctl", "restart", service], check=False)
        else:
            run(["systemctl", "stop", service], check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("ERROR=ROOT_REQUIRED_RUN_VIA_SUDO", file=sys.stderr)
        return 70
    invoker = os.environ.get("SUDO_USER", "")
    if not invoker or invoker == "root":
        print("ERROR=RUN_VIA_SUDO_FROM_OPERATOR_ACCOUNT", file=sys.stderr)
        return 70

    invoker_home = pathlib.Path(pwd.getpwnam(invoker).pw_dir)
    repo_proc = run(["git", "rev-parse", "--show-toplevel"], user=invoker)
    repo = pathlib.Path(repo_proc.stdout.strip()).resolve()
    head = git_as(invoker, repo, "rev-parse", "HEAD")
    if head != args.expected_head:
        raise BootstrapError(
            f"unexpected source HEAD: actual={head} expected={args.expected_head}"
        )
    tracked = git_as(
        invoker, repo, "status", "--porcelain", "--untracked-files=no"
    )
    if tracked:
        raise BootstrapError("tracked reviewed source is dirty:\n" + tracked)

    print(f"repo={repo}")
    print(f"head={head}")
    verify_live_fingerprint()
    print("LIVE_PREFLIGHT_FINGERPRINT=PASS")
    verify_credential_scope()
    print("GITHUB_CREDENTIAL_SCOPE_PREFLIGHT=PASS")

    # Build before the first host mutation.
    built_controller = build_controller(repo)
    print(f"CONTROLLER_BUILD_SHA256={sha256(built_controller)}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = (
        invoker_home
        / "adamArchives"
        / "Adam"
        / "workspace-control-tmp"
        / f"gitrunner-p1-bootstrap-{stamp}"
    )
    backup = out / "rollback"
    out.mkdir(parents=True, mode=0o700)
    manifest = backup_targets(backup)
    mutated = False

    try:
        # Freeze only the automatic reconciliation ingress. Existing runner
        # controllers and the root provisioner remain available until their
        # narrowly scoped restart below.
        run(["systemctl", "stop", RECONCILE_CONTROLLER])
        # This lane was already in an auto-restart storm at read-only
        # preflight. Quiesce it before replacing the shared controller binary
        # so it cannot race through a mixed old-unit/new-binary interval.
        run(["systemctl", "stop", RESEARCH_CPU])
        mutated = True

        install_file(
            built_controller,
            pathlib.Path("/opt/workspace-ci/controller/lambda-ci-controller"),
            0o755,
        )
        install_file(
            repo / "scripts/lambda_ci_multirepo.py",
            pathlib.Path("/opt/workspace-ci/provisioner/lambda_ci_multirepo.py"),
            0o755,
        )
        install_file(
            repo / "scripts/lambda_ci_runtime.py",
            pathlib.Path("/opt/workspace-ci/provisioner/lambda_ci_runtime.py"),
            0o755,
        )
        install_file(
            repo / "scripts/lambda_ci_multirepo.py",
            pathlib.Path("/opt/workspace-ci/reconciler/lambda_ci_multirepo.py"),
            0o755,
        )
        install_file(
            repo / "scripts/lambda_ci_reconciler.py",
            pathlib.Path("/opt/workspace-ci/reconciler/lambda_ci_reconciler.py"),
            0o755,
        )
        install_file(
            repo / "scripts/lambda_ci_maintenance_service.py",
            pathlib.Path("/opt/workspace-ci/maintenance/lambda_ci_maintenance_service.py"),
            0o755,
        )
        install_file(
            repo / "scripts/lambda_ci_maintenance_controller.py",
            pathlib.Path(
                "/opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py"
            ),
            0o755,
        )

        install_file(
            repo / "templates/lambda-ci/workspace-ci-controller@.service.in",
            pathlib.Path("/etc/systemd/system/workspace-ci-controller@.service"),
        )
        install_file(
            repo / "systemd/workspace-ci-reconciler.service",
            pathlib.Path("/etc/systemd/system/workspace-ci-reconciler.service"),
        )
        install_file(
            repo / "systemd/workspace-ci-maintenance.service",
            pathlib.Path("/etc/systemd/system/workspace-ci-maintenance.service"),
        )
        install_file(
            repo / "systemd/workspace-ci-maintenance-controller.service",
            pathlib.Path(
                "/etc/systemd/system/workspace-ci-maintenance-controller.service"
            ),
        )
        install_file(
            repo / "systemd/workspace-ci-tmpfiles.conf",
            pathlib.Path("/etc/tmpfiles.d/workspace-ci.conf"),
        )
        install_file(
            repo / "systemd/workspace-ci-sysusers.conf",
            pathlib.Path("/etc/sysusers.d/workspace-ci.conf"),
        )

        policy_map = {
            "architecture/lambda-ci-project-registry.v1.json":
                "/etc/workspace-ci/lambda-ci-project-registry.v1.json",
            "architecture/lambda-ci-execution-contracts.v1.json":
                "/etc/workspace-ci/lambda-ci-execution-contracts.v1.json",
            "architecture/lambda-ci-reconciliation-ceiling.v1.json":
                "/etc/workspace-ci/lambda-ci-reconciliation-ceiling.v1.json",
            "architecture/lambda-ci-systemd-profiles.v1.json":
                "/etc/workspace-ci/lambda-ci-systemd-profiles.v1.json",
            "architecture/lambda-ci-workload-policy.v1.json":
                "/etc/workspace-ci/lambda-ci-workload-policy.v1.json",
            "architecture/lambda-ci-project-workspace-control.v1.json":
                "/etc/workspace-ci/projects/workspace-control.json",
        }
        for src, dst in policy_map.items():
            install_file(repo / src, pathlib.Path(dst))

        env_path = pathlib.Path("/etc/workspace-ci/maintenance-controller.env")
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text(
            f"WORKSPACE_CI_MAINTENANCE_ISSUE_NUMBER={MAINTENANCE_ISSUE_NUMBER}\n",
            encoding="utf-8",
        )
        os.chown(env_path, 0, 0)
        os.chmod(env_path, 0o644)

        run(["systemd-sysusers", "/etc/sysusers.d/workspace-ci.conf"])
        run(["systemd-tmpfiles", "--create", "/etc/tmpfiles.d/workspace-ci.conf"])

        maint = pwd.getpwnam("ci-maintenance")
        maint_group = grp.getgrnam("workspace-ci-maintenance")
        if maint.pw_gid != maint_group.gr_gid:
            raise BootstrapError("ci-maintenance primary group mismatch")

        copy_token(
            pathlib.Path("/var/lib/workspace-ci/reconcile-controller/github-token"),
            pathlib.Path(
                "/var/lib/workspace-ci/maintenance-controller/github-read-token"
            ),
            maint.pw_uid,
            maint_group.gr_gid,
        )
        copy_token(
            pathlib.Path("/var/lib/workspace-ci/controller/github-token"),
            pathlib.Path("/var/lib/workspace-ci/maintenance-controller/runner-token"),
            maint.pw_uid,
            maint_group.gr_gid,
        )

        run(
            [
                "systemd-analyze",
                "verify",
                "/etc/systemd/system/workspace-ci-controller@.service",
                "/etc/systemd/system/workspace-ci-reconciler.service",
                "/etc/systemd/system/workspace-ci-maintenance.service",
                "/etc/systemd/system/workspace-ci-maintenance-controller.service",
            ]
        )
        run(["systemctl", "daemon-reload"])

        # Reload only shared daemons whose imported policy/runtime changed.
        run(["systemctl", "restart", PROVISIONER])
        run(["systemctl", "restart", RECONCILER])
        if not service_active(PROVISIONER) or not service_active(RECONCILER):
            raise BootstrapError("shared provisioner/reconciler failed after P1 install")
        if not pathlib.Path("/run/workspace-ci/provisioner.sock").is_socket():
            raise BootstrapError("provisioner socket missing after restart")
        if not pathlib.Path("/run/workspace-ci/reconciler.sock").is_socket():
            raise BootstrapError("reconciler socket missing after restart")

        # Healthy project/lane controllers are intentionally not restarted.
        for service in HEALTHY_CONTROLLERS:
            if not service_active(service):
                raise BootstrapError(f"previously healthy controller regressed: {service}")

        # The CPU lane was already in an 11k+ restart storm at preflight. It is
        # the only existing controller deliberately restarted onto the reviewed
        # P1 binary/template/state contract.
        run(["systemctl", "restart", RESEARCH_CPU])
        time.sleep(6)
        first = service_show(RESEARCH_CPU, "ActiveState", "SubState", "NRestarts", "ExecMainStatus")
        if first.get("ActiveState") != "active":
            journal = run(
                ["journalctl", "-u", RESEARCH_CPU, "-n", "60", "--no-pager"],
                check=False,
            )
            raise BootstrapError(
                "research-engine CPU did not stabilize on P1 controller: "
                + json.dumps(first, sort_keys=True)
                + "\n"
                + journal.stdout[-12000:]
            )
        restarts_1 = int(first.get("NRestarts") or 0)
        time.sleep(6)
        second = service_show(RESEARCH_CPU, "ActiveState", "SubState", "NRestarts", "ExecMainStatus")
        if second.get("ActiveState") != "active" or int(second.get("NRestarts") or 0) != restarts_1:
            raise BootstrapError(
                "research-engine CPU restart count is not stable after P1 install: "
                + json.dumps({"first": first, "second": second}, sort_keys=True)
            )

        # Install and commission L0. First --once call creates a watermark and
        # executes no historical comments by construction.
        run(["systemctl", "enable", "--now", MAINTENANCE_ROOT])
        if not service_active(MAINTENANCE_ROOT):
            raise BootstrapError("root maintenance service failed to start")
        maintenance_socket = pathlib.Path(
            "/run/workspace-ci/maintenance/maintenance.sock"
        )
        if not maintenance_socket.is_socket():
            raise BootstrapError("maintenance root socket missing")

        once = run(
            [
                "/opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py",
                "--issue-number",
                str(MAINTENANCE_ISSUE_NUMBER),
                "--once",
            ],
            user="ci-maintenance",
            env={
                "PATH": "/usr/bin:/bin",
                "HOME": "/var/lib/workspace-ci/maintenance-controller",
            },
        )
        try:
            once_json = json.loads(once.stdout.splitlines()[-1])
        except Exception as exc:
            raise BootstrapError(
                "maintenance controller commissioning output invalid: " + once.stdout
            ) from exc
        if once_json.get("status") not in {
            "INITIALIZED_NO_COMMANDS_EXECUTED",
            "PASS",
        }:
            raise BootstrapError(
                "maintenance controller commissioning failed: "
                + json.dumps(once_json, sort_keys=True)
            )

        run(["systemctl", "enable", "--now", MAINTENANCE_CONTROLLER])
        time.sleep(5)
        if not service_active(MAINTENANCE_CONTROLLER):
            journal = run(
                ["journalctl", "-u", MAINTENANCE_CONTROLLER, "-n", "60", "--no-pager"],
                check=False,
            )
            raise BootstrapError(
                "maintenance controller failed to remain active:\n"
                + journal.stdout[-12000:]
            )

        for service in HEALTHY_CONTROLLERS:
            if not service_active(service):
                raise BootstrapError(f"healthy controller regressed late: {service}")

        registry = json.loads(
            pathlib.Path(
                "/etc/workspace-ci/lambda-ci-project-registry.v1.json"
            ).read_text(encoding="utf-8")
        )
        wc_entry = registry.get("projects", {}).get("workspace-control", {})
        wc_manifest = json.loads(
            pathlib.Path(
                "/etc/workspace-ci/projects/workspace-control.json"
            ).read_text(encoding="utf-8")
        )
        if wc_entry.get("activation_state") != "MIGRATION_CANDIDATE_NOT_INSTALLED":
            raise BootstrapError("bootstrap accidentally activated workspace-control registry")
        if wc_manifest.get("status") != "MIGRATION_CANDIDATE_NOT_INSTALLED":
            raise BootstrapError("bootstrap accidentally activated workspace-control manifest")
        route = wc_manifest.get("routes", {}).get("control-validation", {})
        if route.get("activation_state") != "PLANNED_NOT_BOUND":
            raise BootstrapError("bootstrap accidentally activated workspace-control route")
        if service_active("workspace-ci-controller@workspace-control-cpu.service"):
            raise BootstrapError("workspace-control controller unexpectedly active")

        receipt = {
            "schema_version": 1,
            "phase": "GITRUNNER_P1_BOOTSTRAP_INSTALL",
            "decision": "PASS",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "workspace_control_source_sha": head,
            "maintenance_issue_number": MAINTENANCE_ISSUE_NUMBER,
            "backup_directory": str(backup),
            "automatic_reconcile_controller_frozen": not service_active(
                RECONCILE_CONTROLLER
            ),
            "workspace_control_activation_state":
                wc_entry.get("activation_state"),
            "workspace_control_manifest_status": wc_manifest.get("status"),
            "workspace_control_route_state": route.get("activation_state"),
            "workspace_control_controller_active": False,
            "maintenance_root_active": service_active(MAINTENANCE_ROOT),
            "maintenance_controller_active": service_active(MAINTENANCE_CONTROLLER),
            "maintenance_commissioning": once_json,
            "research_engine_cpu": second,
            "healthy_controllers_preserved": {
                service: service_active(service) for service in HEALTHY_CONTROLLERS
            },
            "installed_sha256": {
                raw: sha256(pathlib.Path(raw))
                for raw in TARGET_FILES
                if pathlib.Path(raw).is_file()
                and "token" not in raw
            },
            "credential_contents_exposed": False,
            "p2_p3_authority_changed": False,
            "capacity_changed": False,
            "activation_performed": False,
            "next_gate":
                "Post one owner diagnose command on maintenance issue #527 and "
                "prove the durable L0/root receipt before workspace-control activation.",
        }
        receipt_path = out / "p1-bootstrap-install.json"
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        inv = pwd.getpwnam(invoker)
        for path in [out, receipt_path]:
            os.chown(path, inv.pw_uid, inv.pw_gid)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        print("P1_BOOTSTRAP_INSTALL=PASS")
        print(f"RECEIPT={receipt_path}")
        print("WORKSPACE_CONTROL_ACTIVATED=false")
        print("RECONCILE_CONTROLLER_FROZEN=true")
        print("NEXT=Return this receipt/output to the durable task.")
        return 0
    except Exception:
        if mutated:
            print("P1_BOOTSTRAP_ROLLBACK=BEGIN", file=sys.stderr)
            restore_targets(manifest)
            print("P1_BOOTSTRAP_ROLLBACK=COMPLETE", file=sys.stderr)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BootstrapError as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(70)
