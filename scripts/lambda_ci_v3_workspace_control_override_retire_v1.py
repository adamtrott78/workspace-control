#!/usr/bin/env python3
"""Retire the stale workspace-control class-specific V3 controller override.

This transaction removes only the reviewed PR #604 class-specific executable
and ExecStart drop-in after proving the shared controller is the exact approved
replacement. It never writes scheduler state and never touches sibling
controllers, workflows, credentials, policy, provisioner state, or retired V2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import pwd
import stat
import subprocess
import time
import uuid
from typing import Any

TARGET_CLASS = "workspace-control-control-small-v1"
TARGET_SERVICE = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
TARGET_USER = "ci-ctl-wc-control"
TARGET_GROUP = "ci-gh-workspace-control"

SHARED_BINARY = pathlib.Path("/opt/workspace-ci/v3/controller/lambda-ci-controller-v3")
SHARED_SHA256 = "644d34b02e2166a1c24ffba48e71302f8519a807c872b45a367285146e407918"
SHARED_SOURCE_HEAD = "e0911a56a8e0088d7b90728b7d603dc1f73f824a"

STALE_OVERRIDE_BINARY = pathlib.Path(
    "/opt/workspace-ci/v3/controller-overrides/workspace-control-control-small-v1/"
    "lambda-ci-controller-v3"
)
STALE_OVERRIDE_SHA256 = "9db8161340baacd7d7aad48ad47e013651158748bfd61b13c41ab29539a35af3"
STALE_DROPIN = pathlib.Path(
    "/etc/systemd/system/"
    "workspace-ci-v3-controller@workspace-control-control-small-v1.service.d/"
    "99-terminal-revival-reviewed.conf"
)
STALE_DROPIN_BYTES = (
    "[Service]\n"
    "ExecStart=\n"
    f"ExecStart={STALE_OVERRIDE_BINARY}\n"
).encode()

REFRESH_RECEIPT = pathlib.Path("/var/lib/workspace-ci/v3/controller-refresh/active.json")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/controller/state") / TARGET_CLASS
TARGET_JOB_LEDGER = STATE_ROOT / "scheduler-131520720719.json"
POLICY_PATH = pathlib.Path(f"/etc/workspace-ci/v3/controllers/{TARGET_CLASS}.json")
INSTALL_MANIFEST = pathlib.Path("/etc/workspace-ci/v3/install-manifest.json")
RECONCILER = pathlib.Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_reconciler.py")
RECEIPT_ROOT = pathlib.Path(
    "/var/lib/workspace-ci/v3/padataset-scientific/controller-override-retirement"
)

EXPECTED_POLICY_SHA256 = "870feb9835230c1d9dd897d9fe64b7c1c23def4bcbfc34d1cafd4111681dd9aa"
TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELED"}


class OverrideRetireError(RuntimeError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OverrideRetireError(f"expected JSON object: {path}")
    return value


def atomic_write(path: pathlib.Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with tmp.open("wb") as handle:
        os.chmod(tmp, mode)
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def write_receipt(path: pathlib.Path, value: dict[str, Any]) -> None:
    value["updated_at_unix"] = time.time()
    atomic_write(
        path,
        (json.dumps(value, indent=2, sort_keys=True) + "\n").encode(),
        0o600,
    )


def git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def verify_source(repo: pathlib.Path, expected_head: str) -> None:
    if git(repo, "rev-parse", "HEAD") != expected_head:
        raise OverrideRetireError("transaction source head mismatch")
    if git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise OverrideRetireError("transaction source tree is not completely clean")
    if subprocess.run(
        ["git", "-C", str(repo), "symbolic-ref", "-q", "HEAD"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0:
        raise OverrideRetireError("transaction requires detached HEAD")


def require_regular(path: pathlib.Path, *, mode: int, uid: int = 0, gid: int = 0) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise OverrideRetireError(f"required regular file missing: {path}")
    st = path.stat()
    if stat.S_IMODE(st.st_mode) != mode or st.st_uid != uid or st.st_gid != gid:
        raise OverrideRetireError(f"metadata mismatch: {path}")
    return path.read_bytes()


def systemctl_show(unit: str) -> dict[str, str]:
    props = (
        "Id", "LoadState", "ActiveState", "SubState", "MainPID", "NRestarts",
        "InvocationID", "User", "Group", "Type", "RemainAfterExit", "Result",
        "ExecMainStatus", "DropInPaths",
    )
    raw = subprocess.check_output(
        ["systemctl", "show", unit, "--no-pager", *[f"--property={p}" for p in props]],
        text=True,
    )
    result: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            result[k] = v
    return result


def require_target_running() -> dict[str, str]:
    value = systemctl_show(TARGET_SERVICE)
    if (
        value.get("LoadState") != "loaded"
        or value.get("ActiveState") != "active"
        or value.get("SubState") != "running"
        or int(value.get("MainPID") or 0) <= 0
        or value.get("User") != TARGET_USER
        or value.get("Group") != TARGET_GROUP
    ):
        raise OverrideRetireError("target controller is not in expected healthy state")
    return value


def wait_target(state: str) -> dict[str, str]:
    for _ in range(80):
        value = systemctl_show(TARGET_SERVICE)
        pid = int(value.get("MainPID") or 0)
        if state == "stopped":
            if value.get("ActiveState") == "inactive" and value.get("SubState") == "dead" and pid == 0:
                return value
        elif state == "running":
            if value.get("ActiveState") == "active" and value.get("SubState") == "running" and pid > 0:
                return value
        time.sleep(0.25)
    raise OverrideRetireError(f"target controller did not reach {state}")


def executable_for_pid(pid: int) -> pathlib.Path:
    return pathlib.Path(os.path.realpath(f"/proc/{pid}/exe"))


def current_policy_nonterminal_records(root: pathlib.Path = STATE_ROOT) -> list[pathlib.Path]:
    result: list[pathlib.Path] = []
    if not root.exists():
        return result
    for path in sorted(root.glob("scheduler-*.json")):
        value = load_json(path)
        if value.get("controller_policy_sha256") != EXPECTED_POLICY_SHA256:
            continue
        if value.get("state") not in TERMINAL_STATES:
            result.append(path)
    return result


def snapshot_siblings() -> dict[str, dict[str, str]]:
    root = load_json(ROOT_POLICY)
    classes = root.get("runner_classes")
    if not isinstance(classes, dict) or TARGET_CLASS not in classes:
        raise OverrideRetireError("root policy runner class set invalid")
    result: dict[str, dict[str, str]] = {}
    for class_id in sorted(classes):
        if class_id == TARGET_CLASS:
            continue
        unit = f"workspace-ci-v3-controller@{class_id}.service"
        result[unit] = systemctl_show(unit)
    return result


def verify_shared_controller() -> None:
    raw = require_regular(SHARED_BINARY, mode=0o755)
    if sha256(raw) != SHARED_SHA256:
        raise OverrideRetireError("shared controller digest mismatch")
    refresh_raw = require_regular(REFRESH_RECEIPT, mode=0o600)
    refresh = json.loads(refresh_raw)
    expected = {
        "mode": "V3_INACTIVE_CONTROLLER_BINARY_OVERRIDE",
        "phase": "ACTIVE",
        "controller_source_head": SHARED_SOURCE_HEAD,
        "controller_binary_sha256": SHARED_SHA256,
        "live_controller_repair": True,
    }
    for key, value in expected.items():
        if refresh.get(key) != value:
            raise OverrideRetireError(f"controller refresh binding mismatch: {key}")


def verify_stale_override(target: dict[str, str]) -> None:
    raw = require_regular(STALE_OVERRIDE_BINARY, mode=0o755)
    if sha256(raw) != STALE_OVERRIDE_SHA256:
        raise OverrideRetireError("stale override digest mismatch")
    dropin = require_regular(STALE_DROPIN, mode=0o644)
    if dropin != STALE_DROPIN_BYTES:
        raise OverrideRetireError("stale override drop-in bytes mismatch")
    if str(STALE_DROPIN) not in target.get("DropInPaths", ""):
        raise OverrideRetireError("stale drop-in is not active in systemd")
    pid = int(target["MainPID"])
    exe = executable_for_pid(pid)
    if exe != STALE_OVERRIDE_BINARY:
        raise OverrideRetireError(f"target is not executing stale override: {exe}")
    if sha256(pathlib.Path(f"/proc/{pid}/exe").read_bytes()) != STALE_OVERRIDE_SHA256:
        raise OverrideRetireError("live stale executable digest mismatch")


def preflight(repo: pathlib.Path, expected_head: str) -> dict[str, Any]:
    if os.geteuid() != 0:
        raise OverrideRetireError("transaction requires root")
    verify_source(repo, expected_head)
    verify_shared_controller()
    target = require_target_running()
    verify_stale_override(target)

    policy = load_json(POLICY_PATH)
    if policy.get("controller_policy_sha256") != EXPECTED_POLICY_SHA256:
        raise OverrideRetireError("target controller policy digest drift")

    if TARGET_JOB_LEDGER.exists() or TARGET_JOB_LEDGER.is_symlink():
        raise OverrideRetireError("target #484 ledger already exists; fresh decision required")
    active = current_policy_nonterminal_records()
    if active:
        raise OverrideRetireError(
            "target class has nonterminal durable records: " + ", ".join(map(str, active))
        )

    return {
        "target_before": target,
        "siblings_before": snapshot_siblings(),
        "shared_sha256": SHARED_SHA256,
        "stale_override_sha256": STALE_OVERRIDE_SHA256,
    }


def restore_override(
    txdir: pathlib.Path,
    receipt: dict[str, Any],
    receipt_path: pathlib.Path,
) -> None:
    backup_bin = txdir / "backup-lambda-ci-controller-v3"
    backup_dropin = txdir / "backup-99-terminal-revival-reviewed.conf"
    try:
        subprocess.run(["systemctl", "stop", TARGET_SERVICE], check=True)
        wait_target("stopped")
        if TARGET_JOB_LEDGER.exists() or current_policy_nonterminal_records():
            receipt["phase"] = "POST_SCHEDULER_MUTATION_NO_ROLLBACK"
            write_receipt(receipt_path, receipt)
            subprocess.run(["systemctl", "start", TARGET_SERVICE], check=False)
            raise OverrideRetireError("scheduler state changed; stale override rollback forbidden")

        STALE_OVERRIDE_BINARY.parent.mkdir(parents=True, exist_ok=True)
        STALE_DROPIN.parent.mkdir(parents=True, exist_ok=True)
        if backup_bin.exists():
            os.replace(backup_bin, STALE_OVERRIDE_BINARY)
        if backup_dropin.exists():
            os.replace(backup_dropin, STALE_DROPIN)
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "start", TARGET_SERVICE], check=True)
        wait_target("running")
        receipt["phase"] = "ROLLED_BACK_BEFORE_SCHEDULER_MUTATION"
        write_receipt(receipt_path, receipt)
    except Exception:
        if receipt.get("phase") != "POST_SCHEDULER_MUTATION_NO_ROLLBACK":
            receipt["phase"] = "ROLLBACK_FAILED"
            write_receipt(receipt_path, receipt)
        raise


def apply(repo: pathlib.Path, expected_head: str) -> pathlib.Path:
    evidence = preflight(repo, expected_head)

    RECEIPT_ROOT.mkdir(parents=True, exist_ok=True)
    txid = str(uuid.uuid4())
    txdir = RECEIPT_ROOT / txid
    txdir.mkdir(mode=0o700)
    receipt_path = txdir / "receipt.json"
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "mode": "RETIRE_WORKSPACE_CONTROL_CLASS_CONTROLLER_OVERRIDE_V1",
        "phase": "PREFLIGHT_PASS",
        "transaction_id": txid,
        "source_head": expected_head,
        "target_class": TARGET_CLASS,
        "target_service": TARGET_SERVICE,
        "shared_controller_sha256": SHARED_SHA256,
        "shared_controller_source_head": SHARED_SOURCE_HEAD,
        "retired_override_sha256": STALE_OVERRIDE_SHA256,
        "target_before": evidence["target_before"],
        "siblings_before": evidence["siblings_before"],
    }
    write_receipt(receipt_path, receipt)

    backup_bin = txdir / "backup-lambda-ci-controller-v3"
    backup_dropin = txdir / "backup-99-terminal-revival-reviewed.conf"

    subprocess.run(["systemctl", "stop", TARGET_SERVICE], check=True)
    receipt["target_stopped"] = wait_target("stopped")
    write_receipt(receipt_path, receipt)

    moved_override = False
    try:
        # Re-attest after quiescence. From here to the shared-controller start,
        # scheduler authority cannot advance through this target controller.
        if TARGET_JOB_LEDGER.exists() or TARGET_JOB_LEDGER.is_symlink():
            raise OverrideRetireError("#484 ledger appeared before retirement mutation")
        if current_policy_nonterminal_records():
            raise OverrideRetireError("nonterminal target record appeared before retirement mutation")

        os.replace(STALE_OVERRIDE_BINARY, backup_bin)
        os.replace(STALE_DROPIN, backup_dropin)
        moved_override = True
        try:
            STALE_OVERRIDE_BINARY.parent.rmdir()
        except OSError:
            pass
        try:
            STALE_DROPIN.parent.rmdir()
        except OSError:
            pass

        receipt["phase"] = "STALE_OVERRIDE_DEACTIVATED"
        write_receipt(receipt_path, receipt)

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "start", TARGET_SERVICE], check=True)
        target_after = wait_target("running")
        pid = int(target_after["MainPID"])
        live_path = executable_for_pid(pid)
        live_sha = sha256(pathlib.Path(f"/proc/{pid}/exe").read_bytes())
        if live_path != SHARED_BINARY or live_sha != SHARED_SHA256:
            raise OverrideRetireError(
                f"target did not start exact shared controller: path={live_path} sha={live_sha}"
            )

        siblings_after = snapshot_siblings()
        if siblings_after != evidence["siblings_before"]:
            raise OverrideRetireError("sibling controller service generation changed")

        subprocess.run(
            [
                "/usr/bin/python3",
                str(RECONCILER),
                "--verify-installed",
                "--manifest",
                str(INSTALL_MANIFEST),
            ],
            check=True,
        )

        receipt["phase"] = "COMMITTED_SHARED_CONTROLLER_RESTORED"
        receipt["target_after"] = target_after
        receipt["live_executable"] = str(live_path)
        receipt["live_sha256"] = live_sha
        receipt["siblings_after"] = siblings_after
        write_receipt(receipt_path, receipt)
        return receipt_path
    except Exception:
        if moved_override:
            restore_override(txdir, receipt, receipt_path)
        else:
            # No host override material moved. Restore only service liveness.
            subprocess.run(["systemctl", "start", TARGET_SERVICE], check=True)
            wait_target("running")
            receipt["phase"] = "ABORTED_BEFORE_OVERRIDE_RETIREMENT"
            write_receipt(receipt_path, receipt)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--verify-preflight", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.verify_preflight == args.apply:
        raise OverrideRetireError("choose exactly one of --verify-preflight or --apply")

    repo = args.repo_root.resolve()
    if args.verify_preflight:
        value = preflight(repo, args.expected_head)
        print("WORKSPACE_CONTROL_OVERRIDE_RETIRE_PREFLIGHT=PASS")
        print(json.dumps(value, sort_keys=True))
        return 0

    receipt = apply(repo, args.expected_head)
    print("WORKSPACE_CONTROL_OVERRIDE_RETIRE=PASS")
    print(f"TRANSACTION_RECEIPT={receipt}")
    print(f"CONTROLLER_SHA256={SHARED_SHA256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
