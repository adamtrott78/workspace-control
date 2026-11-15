#!/usr/bin/env python3
"""Transactional hotfix for PADataset scientific lane-B runtime profile support.

This repair intentionally does not restart the provisioner, controllers, or any
runner. New supervisor worker processes import the shared runtime from disk on
each attempt; already-running runner units are therefore unaffected.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import uuid
from typing import Any

import lambda_ci_v3_reconciler as reconciler

BASE_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = Path("/etc/workspace-ci/v3/root-policy.json")
INSTALLED_RUNTIME = Path("/opt/workspace-ci/v3/provisioner/lambda_ci_runtime.py")
RUNTIME_OVERRIDE = Path("/var/lib/workspace-ci/v3/runtime-refresh/active.json")
TX_ROOT = Path("/var/lib/workspace-ci/v3/padataset-scientific/lane-b-runtime-profile/transactions")
AUTH_CONSUMED = Path("/var/lib/workspace-ci/v3/padataset-scientific/lane-b-runtime-profile/authority-consumption")
TARGET_CLASS = "padataset-scientific-single-gpu-2-v1"
TARGET_PROFILE = "gpu-scientific-single-2"
OLD_LINE = b'SINGLE_GPU_EXECUTION_PROFILES = frozenset({"gpu-small", "gpu-scientific-single"})'
NEW_LINE = b'SINGLE_GPU_EXECUTION_PROFILES = frozenset({"gpu-small", "gpu-scientific-single", "gpu-scientific-single-2"})'
SHA40 = re.compile(r"^[0-9a-f]{40}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

class HotfixError(RuntimeError):
    pass

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()

def load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise HotfixError(f"expected object: {path}")
    return value, raw

def exact_repo(expected: str) -> Path:
    if SHA40.fullmatch(expected) is None:
        raise HotfixError("expected head invalid")
    repo = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if head != expected:
        raise HotfixError(f"source head mismatch: {head} != {expected}")
    dirty = subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain=v1", "--untracked-files=normal"],
        text=True,
    )
    if dirty.strip():
        raise HotfixError("source checkout dirty")
    return repo

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

def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chown(path, 0, 0)
    os.chmod(path, 0o700)

def atomic_json(path: Path, value: dict[str, Any]) -> None:
    ensure_private_dir(path.parent)
    atomic_file(path, canonical(value), 0o600)

def unit_snapshot(unit: str) -> dict[str, str]:
    p = subprocess.run(
        ["systemctl", "show", unit, "-p", "ActiveState", "-p", "SubState", "-p", "MainPID", "-p", "InvocationID", "--no-pager"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if p.returncode:
        raise HotfixError(f"systemctl show failed: {unit}: {p.stderr.strip()[:512]}")
    out: dict[str, str] = {}
    for line in p.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key] = value
    return out

def validate_authority(path: Path, expected: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o600:
        raise HotfixError("authority metadata invalid")
    value, raw = load(path)
    required = {"schema_version", "authority", "operation", "authorization_id", "issued_at", "expires_at", *expected}
    if set(value) != required:
        raise HotfixError("authority keys drift")
    if value["schema_version"] != 1 or value["authority"] != "workspace-control-operator":
        raise HotfixError("authority identity invalid")
    if value["operation"] != "HOTFIX_PADATASET_LANE_B_RUNTIME_PROFILE_V1":
        raise HotfixError("authority operation invalid")
    aid = value["authorization_id"]
    if not isinstance(aid, str) or UUID_RE.fullmatch(aid) is None or str(uuid.UUID(aid)) != aid:
        raise HotfixError("authorization id invalid")
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise HotfixError(f"authority binding mismatch: {key}")
    def parse(v: Any) -> datetime:
        if not isinstance(v, str):
            raise HotfixError("authority time invalid")
        parsed = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise HotfixError("authority time must be aware")
        return parsed.astimezone(timezone.utc)
    issued = parse(value["issued_at"])
    expires = parse(value["expires_at"])
    now = datetime.now(timezone.utc)
    if not (issued <= now <= expires) or (expires - issued).total_seconds() > 1800:
        raise HotfixError("authority validity invalid")
    return value, raw

def consume_authority(value: dict[str, Any], raw: bytes) -> None:
    ensure_private_dir(AUTH_CONSUMED)
    path = AUTH_CONSUMED / f"{value['authorization_id']}.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(canonical({
            "schema_version": 1,
            "authorization_id": value["authorization_id"],
            "operation": value["operation"],
            "authority_sha256": sha(raw),
            "consumed_at": datetime.now(timezone.utc).isoformat(),
        }))
        handle.flush()
        os.fsync(handle.fileno())
    os.chown(path, 0, 0)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--authorization-receipt", type=Path, required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise HotfixError("lane-B runtime profile hotfix requires root")
    repo = exact_repo(args.expected_head)

    reconciler.verify_installed(BASE_MANIFEST)
    manifest, manifest_raw = load(BASE_MANIFEST)
    root_policy, _ = load(ROOT_POLICY)
    lane = root_policy.get("runner_classes", {}).get(TARGET_CLASS)
    if not isinstance(lane, dict):
        raise HotfixError("lane-B class missing from live root policy")
    if lane.get("execution_contract", {}).get("execution_profile") != TARGET_PROFILE:
        raise HotfixError("lane-B execution profile binding drift")

    current = INSTALLED_RUNTIME.read_bytes()
    candidate = (repo / "scripts/lambda_ci_runtime.py").read_bytes()
    if NEW_LINE in current:
        raise HotfixError("lane-B runtime profile support is already installed")
    if current.count(OLD_LINE) != 1:
        raise HotfixError("installed runtime profile allowlist is not the expected predecessor")
    expected_candidate = current.replace(OLD_LINE, NEW_LINE, 1)
    if candidate != expected_candidate:
        raise HotfixError("candidate runtime is not the exact one-line lane-B profile addition")

    compile(candidate, str(INSTALLED_RUNTIME), "exec")

    current_sha = sha(current)
    candidate_sha = sha(candidate)
    previous_override_raw = RUNTIME_OVERRIDE.read_bytes() if RUNTIME_OVERRIDE.is_file() else None
    previous_override_sha = sha(previous_override_raw) if previous_override_raw is not None else None

    expected = {
        "source_head": args.expected_head,
        "current_runtime_sha256": current_sha,
        "candidate_runtime_sha256": candidate_sha,
        "previous_runtime_override_sha256": previous_override_sha,
        "target_class_id": TARGET_CLASS,
        "target_profile": TARGET_PROFILE,
    }
    authority, authority_raw = validate_authority(args.authorization_receipt, expected)

    entries = {
        str(item["destination"]): item
        for item in manifest.get("entries", [])
        if isinstance(item, dict) and "destination" in item
    }
    runtime_entry = entries.get(str(INSTALLED_RUNTIME))
    if not isinstance(runtime_entry, dict):
        raise HotfixError("base runtime manifest entry missing")
    runtime_mode = int(str(runtime_entry.get("mode")), 8)
    if runtime_mode != 0o644:
        raise HotfixError("runtime mode drift")

    watched_units = {
        "provisioner": "workspace-ci-v3-provisioner.service",
        "lane_a": "workspace-ci-v3-controller@padataset-scientific-single-gpu-v1.service",
        "lane_b": "workspace-ci-v3-controller@padataset-scientific-single-gpu-2-v1.service",
    }
    before = {name: unit_snapshot(unit) for name, unit in watched_units.items()}
    if before["provisioner"].get("ActiveState") != "active":
        raise HotfixError("provisioner must remain active")
    if before["lane_a"].get("ActiveState") != "active" or before["lane_b"].get("ActiveState") != "active":
        raise HotfixError("both scientific controllers must remain active")

    consume_authority(authority, authority_raw)
    ensure_private_dir(TX_ROOT)
    tx_dir = TX_ROOT / f"hotfix-{uuid.uuid4()}"
    ensure_private_dir(tx_dir)
    tx_path = tx_dir / "receipt.json"
    atomic_file(tx_dir / "previous-runtime.py", current, runtime_mode)
    if previous_override_raw is not None:
        atomic_file(tx_dir / "previous-runtime-override.json", previous_override_raw, 0o600)

    runtime_receipt = {
        "schema_version": 1,
        "mode": "V3_RUNTIME_OVERRIDE",
        "phase": "ACTIVE",
        "base_source_head": manifest.get("source_head"),
        "base_install_manifest_sha256": sha(manifest_raw),
        "base_runtime_sha256": runtime_entry.get("sha256"),
        "runtime_sha256": candidate_sha,
        "runtime_mode": str(runtime_entry.get("mode")),
        "runtime_source_head": args.expected_head,
        "runtime_git_blob": subprocess.check_output(
            ["git", "-C", str(repo), "hash-object", "scripts/lambda_ci_runtime.py"],
            text=True,
        ).strip(),
        "root_policy_sha256": manifest.get("root_policy_sha256"),
        "non_runtime_generation_equivalent": True,
        "previous_runtime_override_sha256": previous_override_sha,
        "hotfix_scope": "ADD_PADATASET_SCIENTIFIC_SINGLE_GPU_2_PROFILE_ONLY",
    }

    tx = {
        "schema_version": 1,
        "mode": "V3_PADATASET_LANE_B_RUNTIME_PROFILE_HOTFIX",
        "phase": "PREPARED",
        "source_head": args.expected_head,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": sha(authority_raw),
        "current_runtime_sha256": current_sha,
        "candidate_runtime_sha256": candidate_sha,
        "unit_snapshot_before": before,
    }
    atomic_json(tx_path, tx)

    changed = False
    try:
        atomic_file(INSTALLED_RUNTIME, candidate, runtime_mode)
        atomic_json(RUNTIME_OVERRIDE, runtime_receipt)
        changed = True

        reconciler.verify_installed(BASE_MANIFEST)
        if sha(INSTALLED_RUNTIME.read_bytes()) != candidate_sha:
            raise HotfixError("installed runtime digest mismatch after hotfix")

        after = {name: unit_snapshot(unit) for name, unit in watched_units.items()}
        for name in watched_units:
            for field in ("ActiveState", "SubState", "MainPID", "InvocationID"):
                if after[name].get(field) != before[name].get(field):
                    raise HotfixError(f"{name} changed during runtime hotfix: {field}")

        tx.update({
            "phase": "COMMITTED_ACTIVE",
            "unit_snapshot_after": after,
            "runtime_override_sha256": sha(RUNTIME_OVERRIDE.read_bytes()),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        atomic_json(tx_path, tx)
    except BaseException as exc:
        if changed:
            atomic_file(INSTALLED_RUNTIME, current, runtime_mode)
            if previous_override_raw is None:
                try:
                    RUNTIME_OVERRIDE.unlink()
                except FileNotFoundError:
                    pass
            else:
                atomic_file(RUNTIME_OVERRIDE, previous_override_raw, 0o600)
        try:
            reconciler.verify_installed(BASE_MANIFEST)
        except BaseException as rollback_exc:
            tx["rollback_verification_error"] = str(rollback_exc)
        tx["phase"] = "ROLLED_BACK"
        tx["failure"] = str(exc)
        tx["failed_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json(tx_path, tx)
        raise

    print("PADATASET_LANE_B_RUNTIME_PROFILE_HOTFIX=PASS")
    print(f"VALIDATED_HEAD={args.expected_head}")
    print(f"RUNTIME_SHA256={candidate_sha}")
    print(f"TRANSACTION_RECEIPT={tx_path}")
    print("PROVISIONER_RESTARTED=0")
    print("CONTROLLERS_RESTARTED=0")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HotfixError as exc:
        print(f"ERROR: {exc}", file=os.sys.stderr)
        raise SystemExit(2)
