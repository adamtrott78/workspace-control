#!/usr/bin/env python3
"""Transactional live refresh for the Lambda CI v3 shared runner runtime.

This updater exists only for reviewed runtime defects discovered during bounded
live canary acceptance. It mutates exactly the shared v3 runner runtime plus the
two installed generation verifiers that must attest that runtime override.

It never mutates a controller binary/policy, workflow, scale set, credential,
legacy v2 controller, Research GPU containment, route, or canary authority.
Only the already-active v3 provisioner root service is stopped and started so
it reloads the reviewed runtime. No class controller is started or enabled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any

import lambda_ci_v3_migration_transaction as migration
import lambda_ci_v3_reconciler as reconciler
import lambda_ci_v3_root_activation as activation


BASE_SOURCE_HEAD = "09c46818252991f6a55aaeedbcf046c554e2ffee"
BASE_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = Path("/etc/workspace-ci/v3/root-policy.json")
INSTALLED_RUNTIME = Path("/opt/workspace-ci/v3/provisioner/lambda_ci_runtime.py")
INSTALLED_RECONCILER = Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_reconciler.py")
INSTALLED_ACTIVATOR = Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py")
STATE_ROOT = Path("/var/lib/workspace-ci/v3")
RUNTIME_OVERRIDE = STATE_ROOT / "runtime-refresh" / "active.json"
RECONCILER_OVERRIDE = STATE_ROOT / "reconciler-refresh" / "active.json"
HELPER_OVERRIDE = STATE_ROOT / "root-reactivation-helper" / "active.json"
UPDATE_ROOT = STATE_ROOT / "migration"
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
RESEARCH_GPU_V2_UNIT = "workspace-ci-controller@research-engine-gpu.service"


class UpdateError(RuntimeError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise UpdateError(f"expected JSON object: {path}")
    return value, raw


def exact_repo(expected_head: str) -> Path:
    repo = Path(__file__).resolve().parents[1]
    git = ["git", "-C", str(repo)]
    head = subprocess.check_output(git + ["rev-parse", "HEAD"], text=True).strip()
    if head != expected_head:
        raise UpdateError(f"checkout HEAD mismatch: {head} != {expected_head}")
    dirty = subprocess.check_output(
        git + ["status", "--porcelain=v1", "--untracked-files=normal"],
        text=True,
    )
    if dirty.strip():
        raise UpdateError("checkout is dirty")
    return repo


def git_blob(repo: Path, rel: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "hash-object", rel],
        text=True,
    ).strip()


def entry_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise UpdateError("install manifest entries missing")
    out: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise UpdateError("install manifest entry invalid")
        destination = entry.get("destination")
        if not isinstance(destination, str) or destination in out:
            raise UpdateError("install manifest destination invalid/duplicate")
        out[destination] = entry
    return out


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chown(path, 0, 0)
    os.chmod(path, 0o700)


def atomic_file(path: Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(tmp, 0, 0)
        os.replace(tmp, path)
        dfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    atomic_file(path, canonical(value), 0o600)


def read_optional(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def restore_optional(path: Path, raw: bytes | None) -> None:
    if raw is None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    else:
        atomic_file(path, raw, 0o600)


def systemctl(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["systemctl", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise UpdateError(
            f"systemctl {' '.join(args)} failed rc={proc.returncode}: "
            f"{proc.stderr.strip()[:512]}"
        )
    return proc


def active(unit: str) -> bool:
    return systemctl("is-active", "--quiet", unit, check=False).returncode == 0


def unit_property(unit: str, name: str) -> str:
    return systemctl("show", unit, f"--property={name}", "--value").stdout.strip()


def wait_active(unit: str, expected: bool, timeout_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if active(unit) is expected:
            return
        time.sleep(0.1)
    raise UpdateError(f"{unit} active state did not become {expected}")


def class_units(root_policy: dict[str, Any]) -> list[str]:
    classes = root_policy.get("runner_classes")
    if not isinstance(classes, dict) or len(classes) != 9:
        raise UpdateError("installed root policy class set invalid")
    return [f"workspace-ci-v3-controller@{class_id}.service" for class_id in sorted(classes)]


def assert_no_class_controller_state(root_policy: dict[str, Any]) -> None:
    for unit in class_units(root_policy):
        active_state = unit_property(unit, "ActiveState")
        sub_state = unit_property(unit, "SubState")
        unit_file_state = unit_property(unit, "UnitFileState")
        if active_state != "inactive" or sub_state != "dead":
            raise UpdateError(
                f"class controller not quiesced: {unit}: "
                f"ActiveState={active_state} SubState={sub_state}"
            )
        if unit_file_state == "enabled":
            raise UpdateError(f"class controller unexpectedly boot-enabled: {unit}")


def assert_generation_drained(repo: Path, root_policy: dict[str, Any]) -> None:
    registry = migration._load(repo / migration.REGISTRY_PATH)
    systemd = migration.RealSystemd()
    migration._assert_research_gpu_containment(systemd)
    migration._assert_generation_drained(
        systemd,
        registry=registry,
        root_policy=root_policy,
        require_legacy_empty=False,
        require_v3_empty=True,
        state_root=migration.V3_PROVISIONER_STATE,
    )


def run_installed_reconciler_verify() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(INSTALLED_RECONCILER),
            "--verify-installed",
            "--manifest",
            str(BASE_MANIFEST),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise UpdateError(
            "installed reconciler verification failed rc="
            + str(proc.returncode)
            + ": "
            + proc.stderr.strip()[:1024]
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise UpdateError("v3 runtime live update requires root")
    if len(args.expected_head) != 40 or any(
        ch not in "0123456789abcdef" for ch in args.expected_head
    ):
        raise UpdateError("--expected-head must be full lowercase Git SHA")

    repo = exact_repo(args.expected_head)
    manifest, manifest_raw = load(BASE_MANIFEST)
    root_policy, _ = load(ROOT_POLICY)
    if manifest.get("mode") != "V3_SUBSTRATE_INSTALL_INACTIVE":
        raise UpdateError("installed manifest mode invalid")
    if manifest.get("source_head") != BASE_SOURCE_HEAD:
        raise UpdateError("installed base source head mismatch")
    if manifest.get("root_policy_sha256") != root_policy.get("root_policy_sha256"):
        raise UpdateError("installed manifest/root policy digest mismatch")

    if not active(RECONCILER_UNIT):
        raise UpdateError("v3 reconciler must remain active/exited")
    if not active(PROVISIONER_UNIT):
        raise UpdateError("v3 provisioner must be active before runtime refresh")
    if active(RESEARCH_GPU_V2_UNIT):
        raise UpdateError("Research GPU v2 containment drifted")

    assert_no_class_controller_state(root_policy)
    assert_generation_drained(repo, root_policy)

    # The candidate verifier must accept the current live generation before
    # mutation. Runtime is still base-exact at this point.
    activation.verify_effective_installed_generation(BASE_MANIFEST)
    run_installed_reconciler_verify()

    entries = entry_map(manifest)
    runtime_entry = entries.get(str(INSTALLED_RUNTIME))
    rec_entry = entries.get(str(INSTALLED_RECONCILER))
    helper_entry = entries.get(str(INSTALLED_ACTIVATOR))
    if runtime_entry is None or rec_entry is None or helper_entry is None:
        raise UpdateError("runtime/verifier entries missing from base manifest")

    runtime_mode = int(str(runtime_entry.get("mode")), 8)
    rec_mode = int(str(rec_entry.get("mode")), 8)
    helper_mode = int(str(helper_entry.get("mode")), 8)
    if runtime_mode != 0o644 or rec_mode != 0o755 or helper_mode != 0o555:
        raise UpdateError("runtime/verifier base modes are unexpected")

    candidate_runtime = (repo / "scripts/lambda_ci_runtime.py").read_bytes()
    candidate_rec = (repo / "scripts/lambda_ci_v3_reconciler.py").read_bytes()
    candidate_helper = (repo / "scripts/lambda_ci_v3_root_activation.py").read_bytes()
    candidate_runtime_sha = sha256(candidate_runtime)
    candidate_rec_sha = sha256(candidate_rec)
    candidate_helper_sha = sha256(candidate_helper)
    base_manifest_sha = sha256(manifest_raw)

    if candidate_runtime_sha == runtime_entry.get("sha256"):
        raise UpdateError("candidate runtime does not differ from base manifest")

    old_runtime = INSTALLED_RUNTIME.read_bytes()
    old_rec = INSTALLED_RECONCILER.read_bytes()
    old_helper = INSTALLED_ACTIVATOR.read_bytes()
    previous_runtime_receipt = read_optional(RUNTIME_OVERRIDE)
    previous_rec_receipt = read_optional(RECONCILER_OVERRIDE)
    previous_helper_receipt = read_optional(HELPER_OVERRIDE)

    update_dir = UPDATE_ROOT / f"runtime-live-update-{args.expected_head}"
    if update_dir.exists():
        raise UpdateError(f"update directory already exists: {update_dir}")
    ensure_dir(update_dir)
    atomic_file(update_dir / "previous-runtime.py", old_runtime, runtime_mode)
    atomic_file(update_dir / "previous-reconciler.py", old_rec, rec_mode)
    atomic_file(update_dir / "previous-root-activation.py", old_helper, helper_mode)

    runtime_receipt = {
        "schema_version": 1,
        "mode": "V3_RUNTIME_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": base_manifest_sha,
        "base_runtime_sha256": runtime_entry.get("sha256"),
        "runtime_sha256": candidate_runtime_sha,
        "runtime_mode": str(runtime_entry.get("mode")),
        "runtime_source_head": args.expected_head,
        "runtime_git_blob": git_blob(repo, "scripts/lambda_ci_runtime.py"),
        "root_policy_sha256": manifest.get("root_policy_sha256"),
        "non_runtime_generation_equivalent": True,
    }
    rec_receipt = {
        "schema_version": 1,
        "mode": "V3_RECONCILER_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": base_manifest_sha,
        "base_reconciler_sha256": rec_entry.get("sha256"),
        "reconciler_sha256": candidate_rec_sha,
        "reconciler_mode": str(rec_entry.get("mode")),
        "reconciler_source_head": args.expected_head,
        "reconciler_git_blob": git_blob(repo, "scripts/lambda_ci_v3_reconciler.py"),
        "root_policy_sha256": manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent": True,
    }
    helper_receipt = {
        "schema_version": 1,
        "mode": "V3_ROOT_REACTIVATION_HELPER_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": base_manifest_sha,
        "base_helper_sha256": helper_entry.get("sha256"),
        "helper_sha256": candidate_helper_sha,
        "helper_mode": str(helper_entry.get("mode")),
        "helper_source_head": args.expected_head,
        "candidate_git_blob": git_blob(repo, "scripts/lambda_ci_v3_root_activation.py"),
        "root_policy_sha256": manifest.get("root_policy_sha256"),
        "non_helper_generation_equivalent": True,
    }

    changed = False
    provisioner_was_active = True
    try:
        systemctl("stop", PROVISIONER_UNIT)
        wait_active(PROVISIONER_UNIT, False)
        assert_no_class_controller_state(root_policy)
        assert_generation_drained(repo, root_policy)

        atomic_json(RUNTIME_OVERRIDE, runtime_receipt)
        atomic_json(RECONCILER_OVERRIDE, rec_receipt)
        atomic_json(HELPER_OVERRIDE, helper_receipt)
        changed = True

        atomic_file(INSTALLED_RUNTIME, candidate_runtime, runtime_mode)
        atomic_file(INSTALLED_RECONCILER, candidate_rec, rec_mode)
        atomic_file(INSTALLED_ACTIVATOR, candidate_helper, helper_mode)

        effective = activation.verify_effective_installed_generation(BASE_MANIFEST)
        if not isinstance(effective, dict):
            raise UpdateError("effective generation did not expose live overrides")
        runtime_effective = effective.get("runtime_override")
        if not isinstance(runtime_effective, dict):
            raise UpdateError("runtime override was not attested")
        if runtime_effective.get("runtime_source_head") != args.expected_head:
            raise UpdateError("runtime override source head mismatch")
        run_installed_reconciler_verify()

        systemctl("start", PROVISIONER_UNIT)
        wait_active(PROVISIONER_UNIT, True)
        socket_evidence = activation.verify_provisioner_socket()

        assert_no_class_controller_state(root_policy)
        assert_generation_drained(repo, root_policy)
        if active(RESEARCH_GPU_V2_UNIT):
            raise UpdateError("Research GPU v2 containment drifted after update")

        receipt = {
            "schema_version": 1,
            "mode": "V3_RUNTIME_LIVE_UPDATE",
            "phase": "ACTIVE",
            "source_head": args.expected_head,
            "base_source_head": manifest.get("source_head"),
            "base_install_manifest_sha256": base_manifest_sha,
            "runtime_override": runtime_receipt,
            "reconciler_override": rec_receipt,
            "root_activation_helper_override": helper_receipt,
            "provisioner_restarted": True,
            "reconciler_restarted": False,
            "class_controller_mutated": False,
            "workflow_mutated": False,
            "scale_set_mutated": False,
            "legacy_v2_mutated": False,
            "research_gpu_containment_preserved": True,
            "provisioner_socket": socket_evidence,
        }
        atomic_json(update_dir / "receipt.json", receipt)
    except Exception:
        try:
            if active(PROVISIONER_UNIT):
                systemctl("stop", PROVISIONER_UNIT)
                wait_active(PROVISIONER_UNIT, False)
            if changed:
                atomic_file(INSTALLED_RUNTIME, old_runtime, runtime_mode)
                atomic_file(INSTALLED_RECONCILER, old_rec, rec_mode)
                atomic_file(INSTALLED_ACTIVATOR, old_helper, helper_mode)
                restore_optional(RUNTIME_OVERRIDE, previous_runtime_receipt)
                restore_optional(RECONCILER_OVERRIDE, previous_rec_receipt)
                restore_optional(HELPER_OVERRIDE, previous_helper_receipt)
            if provisioner_was_active:
                systemctl("start", PROVISIONER_UNIT)
                wait_active(PROVISIONER_UNIT, True)
        finally:
            pass
        raise

    print("V3_RUNTIME_LIVE_UPDATE=PASS")
    print(f"VALIDATED_HEAD={args.expected_head}")
    print(f"RUNTIME_SHA256={candidate_runtime_sha}")
    print(f"RUNTIME_OVERRIDE_RECEIPT={RUNTIME_OVERRIDE}")
    print(f"UPDATE_RECEIPT={update_dir / 'receipt.json'}")
    print("PROVISIONER_RESTART=PASS")
    print("RESEARCH_GPU_CONTAINMENT=PRESERVED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
