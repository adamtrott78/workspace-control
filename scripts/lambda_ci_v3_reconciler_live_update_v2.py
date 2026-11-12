#!/usr/bin/env python3
"""Transactional live refresh of only the installed v3 reconciler verifier.

This updater is intentionally narrower than the original verifier-stack refresh:
the v3 provisioner remains active, the reconciler must be active/exited with no
running process, every v3 class controller must be inactive, and legacy Research
GPU containment must remain intact.  It replaces only the reconciler script and
its exact root-owned override receipt.

The updater grants no production-cutover authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from typing import Any

import lambda_ci_v3_reconciler as candidate


BASE_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = Path("/etc/workspace-ci/v3/root-policy.json")
INSTALLED_RECONCILER = Path(
    "/opt/workspace-ci/v3/reconciler/lambda_ci_v3_reconciler.py"
)
RECONCILER_OVERRIDE = Path(
    "/var/lib/workspace-ci/v3/reconciler-refresh/active.json"
)
MIGRATION_ROOT = Path("/var/lib/workspace-ci/v3/migration")
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
RESEARCH_GPU_UNIT = "workspace-ci-controller@research-engine-gpu.service"


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


def systemd_properties(unit: str) -> dict[str, str]:
    proc = subprocess.run(
        [
            "systemctl",
            "show",
            unit,
            "-p",
            "LoadState",
            "-p",
            "ActiveState",
            "-p",
            "SubState",
            "-p",
            "MainPID",
            "-p",
            "UnitFileState",
            "--no-pager",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise UpdateError(
            f"systemctl show failed for {unit}: {proc.stderr.strip()[:512]}"
        )
    values: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def class_units() -> list[str]:
    policy, _ = load(ROOT_POLICY)
    classes = policy.get("runner_classes")
    if not isinstance(classes, dict) or len(classes) != 9:
        raise UpdateError("installed root policy class set invalid")
    return [
        f"workspace-ci-v3-controller@{class_id}.service"
        for class_id in sorted(classes)
    ]


def require_live_boundary() -> None:
    provisioner = systemd_properties(PROVISIONER_UNIT)
    if (
        provisioner.get("ActiveState") != "active"
        or provisioner.get("SubState") != "running"
    ):
        raise UpdateError("v3 provisioner must remain active/running")

    reconciler = systemd_properties(RECONCILER_UNIT)
    if reconciler.get("ActiveState") != "active":
        raise UpdateError("v3 reconciler must remain active")
    if reconciler.get("SubState") != "exited":
        raise UpdateError("v3 reconciler must be active/exited")
    if reconciler.get("MainPID") not in {"", "0"}:
        raise UpdateError("v3 reconciler unexpectedly has a running process")

    for unit in class_units():
        state = systemd_properties(unit)
        if state.get("ActiveState") in {"active", "activating", "reloading"}:
            raise UpdateError(f"v3 class controller is not inactive: {unit}")
        if state.get("SubState") == "auto-restart":
            raise UpdateError(f"v3 class controller is auto-restarting: {unit}")

    research = systemd_properties(RESEARCH_GPU_UNIT)
    if research.get("ActiveState") != "inactive":
        raise UpdateError("legacy Research GPU containment is not inactive")
    if research.get("UnitFileState") != "disabled":
        raise UpdateError("legacy Research GPU containment is not disabled")


def exact_repo(expected_head: str) -> Path:
    if re.fullmatch(r"[0-9a-f]{40}", expected_head) is None:
        raise UpdateError("--expected-head must be a full lowercase Git SHA")
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


def validate_current_override(
    *,
    manifest: dict[str, Any],
    manifest_raw: bytes,
    rec_entry: dict[str, Any],
    actual_sha: str,
) -> bytes | None:
    base_sha = rec_entry.get("sha256")
    if actual_sha == base_sha:
        return None
    current, raw = load(RECONCILER_OVERRIDE)
    required = {
        "schema_version": 1,
        "mode": "V3_RECONCILER_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": sha256(manifest_raw),
        "base_reconciler_sha256": base_sha,
        "reconciler_sha256": actual_sha,
        "reconciler_mode": str(rec_entry.get("mode")),
        "root_policy_sha256": manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent": True,
    }
    for key, expected in required.items():
        if current.get(key) != expected:
            raise UpdateError(f"current reconciler override mismatch: {key}")
    source = current.get("reconciler_source_head")
    if not isinstance(source, str) or re.fullmatch(r"[0-9a-f]{40}", source) is None:
        raise UpdateError("current reconciler override source head invalid")
    st = RECONCILER_OVERRIDE.stat()
    if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o600:
        raise UpdateError("current reconciler override metadata invalid")
    return raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise UpdateError("reconciler live update requires root")

    repo = exact_repo(args.expected_head)
    require_live_boundary()

    # The candidate verifier must understand the currently installed effective
    # generation before it is allowed to replace the installed verifier.
    candidate.verify_installed(BASE_MANIFEST)

    manifest, manifest_raw = load(BASE_MANIFEST)
    entries = entry_map(manifest)
    rec_entry = entries.get(str(INSTALLED_RECONCILER))
    if rec_entry is None:
        raise UpdateError("base manifest does not manage the reconciler")
    mode = int(str(rec_entry.get("mode")), 8)
    if mode != 0o755:
        raise UpdateError("reconciler base mode is unexpected")

    old_rec = INSTALLED_RECONCILER.read_bytes()
    old_sha = sha256(old_rec)
    old_override_raw = validate_current_override(
        manifest=manifest,
        manifest_raw=manifest_raw,
        rec_entry=rec_entry,
        actual_sha=old_sha,
    )

    candidate_rec = (repo / "scripts/lambda_ci_v3_reconciler.py").read_bytes()
    candidate_sha = sha256(candidate_rec)
    if candidate_sha == old_sha:
        raise UpdateError("candidate reconciler is already installed")

    git_blob = subprocess.check_output(
        [
            "git",
            "-C",
            str(repo),
            "hash-object",
            "scripts/lambda_ci_v3_reconciler.py",
        ],
        text=True,
    ).strip()

    new_override = {
        "schema_version": 1,
        "mode": "V3_RECONCILER_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": sha256(manifest_raw),
        "base_reconciler_sha256": rec_entry.get("sha256"),
        "reconciler_sha256": candidate_sha,
        "reconciler_mode": str(rec_entry.get("mode")),
        "reconciler_source_head": args.expected_head,
        "reconciler_git_blob": git_blob,
        "root_policy_sha256": manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent": True,
    }

    changed = False
    try:
        atomic_json(RECONCILER_OVERRIDE, new_override)
        changed = True
        atomic_file(INSTALLED_RECONCILER, candidate_rec, mode)

        # Verify through both the imported candidate and the just-installed file.
        candidate.verify_installed(BASE_MANIFEST)
        proc = subprocess.run(
            [
                "/usr/bin/python3",
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
                "installed reconciler self-verification failed rc="
                + str(proc.returncode)
                + ": "
                + proc.stderr.strip()[:1024]
            )

        require_live_boundary()

        update_dir = MIGRATION_ROOT / f"reconciler-live-update-{args.expected_head}"
        ensure_dir(update_dir)
        receipt = {
            "schema_version": 1,
            "mode": "V3_RECONCILER_LIVE_UPDATE",
            "phase": "ACTIVE",
            "source_head": args.expected_head,
            "previous_reconciler_sha256": old_sha,
            "reconciler_sha256": candidate_sha,
            "reconciler_override": new_override,
            "provisioner_restarted": False,
            "reconciler_restarted": False,
            "class_controller_mutation": False,
            "workflow_mutation": False,
            "scale_set_mutation": False,
            "v2_mutation": False,
            "research_gpu_containment_preserved": True,
        }
        atomic_json(update_dir / "receipt.json", receipt)
        print("V3_RECONCILER_LIVE_UPDATE=PASS")
        print(f"VALIDATED_HEAD={args.expected_head}")
        print(f"RECONCILER_SHA256={candidate_sha}")
        print("PROVISIONER_RESTARTED=false")
        print("RECONCILER_RESTARTED=false")
        print("RESEARCH_GPU_CONTAINMENT=PRESERVED")
        print(f"UPDATE_RECEIPT={update_dir / 'receipt.json'}")
        return 0
    except BaseException:
        if changed:
            atomic_file(INSTALLED_RECONCILER, old_rec, mode)
            if old_override_raw is None:
                try:
                    RECONCILER_OVERRIDE.unlink()
                except FileNotFoundError:
                    pass
            else:
                atomic_file(RECONCILER_OVERRIDE, old_override_raw, 0o600)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
