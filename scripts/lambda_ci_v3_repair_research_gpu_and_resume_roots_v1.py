#!/usr/bin/env python3
"""Repair inherited legacy Research GPU containment and resume v3 root services.

This is a deliberately narrow post-outage operator transaction. It may mutate
only the exact legacy Research GPU controller instance needed to restore the
already-required NO_BY_DEFAULT containment invariant, then it creates a fresh
ACTIVATE_V3_ROOT_SERVICES authority and invokes the installed v3 root
activation helper.

It does not touch Research CPU, PADataset, workspace-control v2, any v3 class
controller, workflow routing, scale-set identity, or repository policy.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import uuid


RESEARCH_GPU_V2_UNIT = "workspace-ci-controller@research-engine-gpu.service"
RESEARCH_PROJECT_UNIT_PATTERN = "workspace-ci-research-engine-*.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
INSTALLED_ACTIVATOR = Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py")
INSTALL_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = Path("/etc/workspace-ci/v3/root-policy.json")
MIGRATION_ROOT = Path("/var/lib/workspace-ci/v3/migration")
VERIFIER_STACK_UPDATER_REL = Path("scripts/lambda_ci_v3_verifier_stack_live_update_v1.py")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class RecoveryError(RuntimeError):
    pass


def run(argv: list[str], *, cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RecoveryError(
            f"command failed rc={proc.returncode}: {argv[0]}: {proc.stderr.strip()}"
        )
    return proc


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_json(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise RecoveryError(f"expected JSON object: {path}")
    return value, raw


def require_root_file(path: Path, mode: int) -> None:
    if not path.is_file() or path.is_symlink():
        raise RecoveryError(f"required root file missing or symlinked: {path}")
    st = path.stat()
    if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != mode:
        raise RecoveryError(
            f"root file metadata mismatch: {path}: "
            f"uid={st.st_uid} gid={st.st_gid} mode={stat.S_IMODE(st.st_mode):04o}"
        )


def require_private_root_dir(path: Path) -> None:
    if not path.is_dir() or path.is_symlink():
        raise RecoveryError(f"required private root directory missing: {path}")
    st = path.stat()
    if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o700:
        raise RecoveryError(
            f"private root directory metadata mismatch: {path}: "
            f"uid={st.st_uid} gid={st.st_gid} mode={stat.S_IMODE(st.st_mode):04o}"
        )


def exact_repo(expected_head: str) -> Path:
    cwd = Path.cwd().resolve()
    root = run(["git", "-c", f"safe.directory={cwd}", "rev-parse", "--show-toplevel"], check=True)
    repo = Path(root.stdout.strip()).resolve()
    git = ["git", "-c", f"safe.directory={repo}", "-C", str(repo)]

    head = run(git + ["rev-parse", "HEAD"], check=True).stdout.strip()
    if head != expected_head:
        raise RecoveryError(f"checkout HEAD mismatch: {head} != {expected_head}")

    status = run(git + ["status", "--porcelain=v1", "--untracked-files=normal"], check=True)
    if status.stdout.strip():
        raise RecoveryError("checkout is dirty")
    return repo


def service_snapshot(unit: str) -> dict[str, str]:
    props = (
        "LoadState",
        "ActiveState",
        "SubState",
        "UnitFileState",
        "Result",
        "ExecMainCode",
        "ExecMainStatus",
        "NRestarts",
        "Restart",
    )
    argv = ["systemctl", "show", unit, "--no-pager"]
    for prop in props:
        argv.extend(["-p", prop])
    proc = run(argv, check=True)
    values: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    if values.get("LoadState") != "loaded":
        raise RecoveryError(f"required service is not loaded: {unit}")
    return values


def service_active(snapshot: dict[str, str]) -> bool:
    return snapshot.get("ActiveState") in {"active", "activating", "deactivating"}


def active_research_execution_units() -> list[str]:
    proc = run(
        [
            "systemctl",
            "list-units",
            "--all",
            "--plain",
            "--no-legend",
            "--no-pager",
            RESEARCH_PROJECT_UNIT_PATTERN,
        ]
    )
    if proc.returncode not in {0, 1}:
        raise RecoveryError("unable to inspect Research execution units")
    active: list[str] = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        unit, load, active_state, sub = parts[:4]
        if load == "loaded" and active_state in {"active", "activating", "deactivating"}:
            active.append(f"{unit}:{active_state}:{sub}")
    return sorted(active)


def write_json_exclusive(path: Path, payload: dict) -> None:
    raw = canonical(payload)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(path, 0, 0)
        os.chmod(path, 0o600)
        dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def repair_research_gpu_containment(expected_head: str) -> Path:
    before = service_snapshot(RESEARCH_GPU_V2_UNIT)
    roots_before = {
        RECONCILER_UNIT: service_snapshot(RECONCILER_UNIT),
        PROVISIONER_UNIT: service_snapshot(PROVISIONER_UNIT),
    }
    if any(service_active(s) for s in roots_before.values()):
        raise RecoveryError("v3 root services must remain inactive before containment repair")

    active_units = active_research_execution_units()
    if active_units:
        raise RecoveryError(
            "Research execution units are active; refusing controller containment repair: "
            + ",".join(active_units)
        )

    if service_active(before):
        run(["systemctl", "stop", RESEARCH_GPU_V2_UNIT], check=True)

    after_stop = service_snapshot(RESEARCH_GPU_V2_UNIT)
    if service_active(after_stop):
        raise RecoveryError("legacy Research GPU controller did not stop")

    if after_stop.get("UnitFileState") != "disabled":
        run(["systemctl", "disable", RESEARCH_GPU_V2_UNIT], check=True)

    after = service_snapshot(RESEARCH_GPU_V2_UNIT)
    if service_active(after):
        raise RecoveryError("legacy Research GPU controller is still active after repair")
    if after.get("UnitFileState") != "disabled":
        raise RecoveryError(
            "legacy Research GPU controller is not boot-disabled after repair: "
            + str(after.get("UnitFileState"))
        )

    active_units_after = active_research_execution_units()
    if active_units_after:
        raise RecoveryError(
            "Research execution appeared during containment repair: "
            + ",".join(active_units_after)
        )

    receipt_id = str(uuid.uuid4())
    receipt_path = MIGRATION_ROOT / f"research-gpu-containment-repair-{receipt_id}.json"
    receipt = {
        "schema_version": 1,
        "mode": "REPAIR_INHERITED_RESEARCH_GPU_CONTAINMENT",
        "receipt_id": receipt_id,
        "expected_head": expected_head,
        "legacy_unit": RESEARCH_GPU_V2_UNIT,
        "research_project_unit_pattern": RESEARCH_PROJECT_UNIT_PATTERN,
        "before": before,
        "after": after,
        "active_research_execution_units_before": active_units,
        "active_research_execution_units_after": active_units_after,
        "v3_root_services_before": roots_before,
        "research_gpu_containment": "PRESERVED_NO_BY_DEFAULT",
        "research_cpu_mutated": False,
        "padataset_mutated": False,
        "workspace_control_v2_mutated": False,
        "v3_class_controller_mutated": False,
        "workflow_mutated": False,
        "scale_set_mutated": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_json_exclusive(receipt_path, receipt)
    print("RESEARCH_GPU_CONTAINMENT_REPAIR=PASS")
    print(f"CONTAINMENT_RECEIPT={receipt_path}")
    return receipt_path


def mint_root_authority() -> Path:
    require_root_file(INSTALL_MANIFEST, 0o644)
    require_root_file(ROOT_POLICY, 0o644)
    require_root_file(INSTALLED_ACTIVATOR, 0o555)
    require_private_root_dir(MIGRATION_ROOT)

    manifest, manifest_raw = load_json(INSTALL_MANIFEST)
    root_policy, _ = load_json(ROOT_POLICY)

    source_head = manifest.get("source_head")
    if not isinstance(source_head, str) or SHA_RE.fullmatch(source_head) is None:
        raise RecoveryError("installed manifest source_head invalid")

    root_policy_sha = root_policy.get("root_policy_sha256")
    if not isinstance(root_policy_sha, str) or len(root_policy_sha) != 64:
        raise RecoveryError("installed root policy digest invalid")
    if manifest.get("root_policy_sha256") != root_policy_sha:
        raise RecoveryError("installed manifest/root policy digest mismatch")

    now = datetime.now(timezone.utc)
    authorization_id = str(uuid.uuid4())
    authority = {
        "schema_version": 1,
        "authority": "workspace-control-operator",
        "operation": "ACTIVATE_V3_ROOT_SERVICES",
        "authorization_id": authorization_id,
        "source_head": source_head,
        "install_manifest_sha256": sha256(manifest_raw),
        "root_policy_sha256": root_policy_sha,
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
    }
    path = MIGRATION_ROOT / f"root-reactivation-authority-{authorization_id}.json"
    write_json_exclusive(path, authority)
    print("FRESH_ROOT_ACTIVATION_AUTHORITY=PASS")
    print(f"AUTHORIZATION_ID={authorization_id}")
    print(f"AUTHORIZATION_RECEIPT={path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise RecoveryError("Research GPU containment repair/root activation must run as root")
    if SHA_RE.fullmatch(args.expected_head) is None:
        raise RecoveryError("--expected-head must be a full lowercase Git SHA")

    repo = exact_repo(args.expected_head)
    require_private_root_dir(MIGRATION_ROOT)

    print("RESEARCH_GPU_CONTAINMENT_AND_V3_ROOT_RESUME=BEGIN")
    print(f"EXPECTED_HEAD={args.expected_head}")

    repair_research_gpu_containment(args.expected_head)

    updater = repo / VERIFIER_STACK_UPDATER_REL
    if not updater.is_file():
        raise RecoveryError(f"verifier-stack updater missing: {updater}")
    refresh = run(
        [sys.executable, "-B", str(updater), "--expected-head", args.expected_head],
        cwd=repo,
    )
    if refresh.stdout:
        print(refresh.stdout, end="")
    if refresh.stderr:
        print(refresh.stderr, end="", file=sys.stderr)
    if refresh.returncode != 0:
        raise RecoveryError(
            f"v3 verifier-stack live update failed rc={refresh.returncode}"
        )
    print("V3_VERIFIER_STACK_REFRESH=PASS")

    authority_path = mint_root_authority()

    activation = run(
        [
            str(INSTALLED_ACTIVATOR),
            "--activate",
            "--authorization-receipt",
            str(authority_path),
        ]
    )
    if activation.stdout:
        print(activation.stdout, end="")
    if activation.stderr:
        print(activation.stderr, end="", file=sys.stderr)
    if activation.returncode != 0:
        raise RecoveryError(
            "v3 root activation failed after containment repair; containment remains "
            "fail-safe and authority/transaction evidence is preserved for diagnosis "
            f"(rc={activation.returncode})"
        )

    post_gpu = service_snapshot(RESEARCH_GPU_V2_UNIT)
    if service_active(post_gpu) or post_gpu.get("UnitFileState") != "disabled":
        raise RecoveryError(
            "Research GPU containment drifted after v3 root activation: "
            + json.dumps(post_gpu, sort_keys=True)
        )
    post_exec = active_research_execution_units()
    if post_exec:
        raise RecoveryError(
            "Research execution appeared after v3 root activation: " + ",".join(post_exec)
        )
    post_roots = {
        RECONCILER_UNIT: service_snapshot(RECONCILER_UNIT),
        PROVISIONER_UNIT: service_snapshot(PROVISIONER_UNIT),
    }
    reconciler_state = post_roots[RECONCILER_UNIT]
    provisioner_state = post_roots[PROVISIONER_UNIT]
    reconciler_ok = (
        reconciler_state.get("ActiveState") == "active"
        and reconciler_state.get("SubState") == "exited"
        and reconciler_state.get("ExecMainStatus") == "0"
        and reconciler_state.get("Result") == "success"
    )
    provisioner_ok = (
        provisioner_state.get("ActiveState") == "active"
        and provisioner_state.get("SubState") == "running"
        and provisioner_state.get("ExecMainStatus") == "0"
        and provisioner_state.get("Result") == "success"
    )
    if not reconciler_ok or not provisioner_ok:
        raise RecoveryError(
            "v3 root service post-activation attestation failed: "
            + json.dumps(post_roots, sort_keys=True)
        )

    print("POST_ACTIVATION_RESEARCH_GPU_CONTAINMENT=PASS")
    print("POST_ACTIVATION_V3_ROOT_SERVICES=PASS")
    print("RESEARCH_GPU_CONTAINMENT_AND_V3_ROOT_RESUME=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RecoveryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
