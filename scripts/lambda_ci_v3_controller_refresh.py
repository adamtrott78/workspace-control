#!/usr/bin/env python3
"""Bounded inactive v3 controller-binary refresh over an activated root substrate.

The base v3 install manifest remains immutable and continues to attest the root
services/config generation activated by Input #2. This helper permits one
narrow overlay: replace the shared v3 controller executable while every v3
class controller is inactive, but only when a full staged generation proves
that every other managed artifact is byte-for-byte identical to the base
install.

A root-owned active override receipt binds the effective controller binary to
its exact reviewed source head. The first-canary operator must verify this
receipt before activating any class controller.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import uuid
from typing import Any

import lambda_ci_v3_reconciler as reconciler

BASE_MANIFEST = pathlib.Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
CONTROLLER_BINARY = reconciler.V3_CONTROLLER_BINARY
REFRESH_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/controller-refresh")
ACTIVE_RECEIPT = REFRESH_ROOT / "active.json"
MIGRATION_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/migration")
ROOT_UNITS = (
    "workspace-ci-v3-reconciler.service",
    "workspace-ci-v3-provisioner.service",
)
RESEARCH_GPU_V2_UNIT = "workspace-ci-controller@research-engine-gpu.service"
MODE = "V3_INACTIVE_CONTROLLER_BINARY_OVERRIDE"


class ControllerRefreshError(RuntimeError):
    pass


def _load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ControllerRefreshError(f"{path}: expected JSON object")
    return value


def _sha256(raw: bytes) -> str:
    return reconciler._sha256(raw)


def _atomic_write(path: pathlib.Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with tmp.open("wb") as handle:
        os.chmod(tmp, mode)
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _write_json(path: pathlib.Path, value: dict[str, Any], mode: int = 0o600) -> None:
    _atomic_write(
        path,
        (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        mode,
    )


def _entry_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ControllerRefreshError("install manifest entries missing")
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ControllerRefreshError("install manifest entry invalid")
        destination = entry.get("destination")
        if not isinstance(destination, str) or destination in result:
            raise ControllerRefreshError("install manifest destination invalid/duplicate")
        result[destination] = entry
    return result


def compare_manifests_for_controller_only_refresh(
    base: dict[str, Any],
    candidate: dict[str, Any],
    *,
    controller_destination: str = str(CONTROLLER_BINARY),
) -> None:
    """Require candidate generation drift to be exactly the controller binary."""

    for field in (
        "catalog_generation_sha256",
        "root_policy_sha256",
        "runner_class_count",
        "controller_state",
        "route_state",
    ):
        if base.get(field) != candidate.get(field):
            raise ControllerRefreshError(f"controller refresh changed {field}")

    base_entries = _entry_map(base)
    candidate_entries = _entry_map(candidate)
    if set(base_entries) != set(candidate_entries):
        raise ControllerRefreshError("controller refresh changed managed destination set")
    if controller_destination not in base_entries:
        raise ControllerRefreshError("base manifest does not manage controller binary")

    for destination in sorted(base_entries):
        if destination == controller_destination:
            continue
        left = base_entries[destination]
        right = candidate_entries[destination]
        if left.get("sha256") != right.get("sha256"):
            raise ControllerRefreshError(
                f"non-controller artifact drift: {destination}"
            )
        if left.get("mode") != right.get("mode"):
            raise ControllerRefreshError(
                f"non-controller mode drift: {destination}"
            )


def assert_migration_history_rolled_back(
    migration_root: pathlib.Path = MIGRATION_ROOT,
) -> list[pathlib.Path]:
    """Require every prior one-class canary transaction to be terminally rolled back."""

    receipts: list[pathlib.Path] = []
    if not migration_root.exists():
        return receipts
    for path in sorted(migration_root.glob("*/transaction.json")):
        value = _load(path)
        if value.get("mode") != "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION":
            continue
        receipts.append(path)
        if value.get("phase") != "ROLLED_BACK_LEGACY_RESTORED":
            raise ControllerRefreshError(
                f"canary transaction is not rolled back: {path} phase={value.get('phase')}"
            )
    return receipts


def _active(unit: str) -> bool:
    return subprocess.run(
        ["systemctl", "is-active", "--quiet", unit],
        check=False,
    ).returncode == 0


def _enabled_state(unit: str) -> str:
    proc = subprocess.run(
        ["systemctl", "is-enabled", unit],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() or "unknown"


def _class_ids() -> list[str]:
    root = _load(ROOT_POLICY)
    classes = root.get("runner_classes")
    if not isinstance(classes, dict) or len(classes) != 9:
        raise ControllerRefreshError("installed root policy class set invalid")
    return sorted(classes)


def _assert_live_boundary() -> list[str]:
    for unit in ROOT_UNITS:
        if not _active(unit):
            raise ControllerRefreshError(f"required root service inactive: {unit}")
        if _enabled_state(unit) == "enabled":
            raise ControllerRefreshError(f"root service unexpectedly boot-enabled: {unit}")

    class_ids = _class_ids()
    for class_id in class_ids:
        unit = f"workspace-ci-v3-controller@{class_id}.service"
        if _active(unit):
            raise ControllerRefreshError(f"class controller active during refresh: {unit}")
        if _enabled_state(unit) == "enabled":
            raise ControllerRefreshError(f"class controller boot-enabled during refresh: {unit}")

    if _active(RESEARCH_GPU_V2_UNIT):
        raise ControllerRefreshError("Research GPU legacy controller containment drift")

    assert_migration_history_rolled_back()
    return class_ids


def _verify_base_non_controller(
    manifest: dict[str, Any],
    *,
    controller_destination: str = str(CONTROLLER_BINARY),
) -> dict[str, Any]:
    entries = _entry_map(manifest)
    controller = entries.get(controller_destination)
    if controller is None:
        raise ControllerRefreshError("controller binary absent from base manifest")
    for destination, entry in entries.items():
        if destination == controller_destination:
            continue
        path = pathlib.Path(destination)
        if not path.is_file():
            raise ControllerRefreshError(f"managed artifact missing: {path}")
        if _sha256(path.read_bytes()) != entry.get("sha256"):
            raise ControllerRefreshError(f"managed artifact digest drift: {path}")
        if stat.S_IMODE(path.stat().st_mode) != int(str(entry.get("mode")), 8):
            raise ControllerRefreshError(f"managed artifact mode drift: {path}")
    return controller


def _base_manifest(expected_base_head: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    raw = BASE_MANIFEST.read_bytes()
    manifest = json.loads(raw)
    if not isinstance(manifest, dict):
        raise ControllerRefreshError("base install manifest invalid")
    if manifest.get("mode") != "V3_SUBSTRATE_INSTALL_INACTIVE":
        raise ControllerRefreshError("base install manifest mode invalid")
    if manifest.get("source_head") != expected_base_head:
        raise ControllerRefreshError(
            f"base source head mismatch: {manifest.get('source_head')} != {expected_base_head}"
        )
    controller_entry = _verify_base_non_controller(manifest)
    return manifest, _sha256(raw), controller_entry


def _verify_current_controller(
    *,
    base_controller_entry: dict[str, Any],
    base_manifest_sha256: str,
) -> tuple[str, dict[str, Any] | None]:
    if not CONTROLLER_BINARY.is_file():
        raise ControllerRefreshError("installed controller binary missing")
    actual = _sha256(CONTROLLER_BINARY.read_bytes())

    if ACTIVE_RECEIPT.is_file():
        active = _load(ACTIVE_RECEIPT)
        if active.get("mode") != MODE or active.get("phase") != "ACTIVE":
            raise ControllerRefreshError("active controller override receipt invalid")
        if active.get("base_install_manifest_sha256") != base_manifest_sha256:
            raise ControllerRefreshError("active override/base manifest binding mismatch")
        if active.get("controller_binary_sha256") != actual:
            raise ControllerRefreshError("active override/controller digest mismatch")
        return actual, active

    if actual != base_controller_entry.get("sha256"):
        raise ControllerRefreshError(
            "controller binary drift exists without an active override receipt"
        )
    return actual, None


def _stage_candidate(
    repo_root: pathlib.Path,
    *,
    expected_head: str,
    go_bin: str,
    base_manifest: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    reconciler._git_exact_head(repo_root, expected_head)
    installed_overlay = _load(reconciler.V3_CONFIG_ROOT / "deployment-overlay.json")

    with tempfile.TemporaryDirectory(prefix="workspace-ci-v3-controller-refresh-build-") as raw:
        temp = pathlib.Path(raw)
        binary = reconciler._build_controller(
            repo_root,
            temp / "lambda-ci-controller-v3",
            go_bin,
        )
        stage = temp / "stage"
        result = reconciler.build_stage(
            repo_root,
            stage,
            controller_binary=binary,
            base_overlay=installed_overlay,
            source_head=expected_head,
        )
        candidate = result["manifest"]
        compare_manifests_for_controller_only_refresh(base_manifest, candidate)
        return bytes(binary), candidate


def verify_active_override(
    *,
    expected_source_head: str,
    expected_base_head: str,
) -> dict[str, Any]:
    _assert_live_boundary()
    base, base_sha, base_controller = _base_manifest(expected_base_head)
    actual, active = _verify_current_controller(
        base_controller_entry=base_controller,
        base_manifest_sha256=base_sha,
    )
    if active is None:
        raise ControllerRefreshError("controller override is not installed")
    if active.get("controller_source_head") != expected_source_head:
        raise ControllerRefreshError("controller override source head mismatch")
    if active.get("controller_binary_sha256") != actual:
        raise ControllerRefreshError("controller override digest mismatch")
    if active.get("non_controller_generation_equivalent") is not True:
        raise ControllerRefreshError("controller override lacks generation-equivalence proof")
    if active.get("base_source_head") != expected_base_head:
        raise ControllerRefreshError("controller override base head mismatch")
    if base.get("root_policy_sha256") != active.get("root_policy_sha256"):
        raise ControllerRefreshError("controller override root-policy binding mismatch")
    return active


def apply_refresh(
    repo_root: pathlib.Path,
    *,
    expected_source_head: str,
    expected_base_head: str,
    go_bin: str,
) -> pathlib.Path:
    if os.geteuid() != 0:
        raise ControllerRefreshError("controller refresh requires root")

    _assert_live_boundary()
    base, base_sha, base_controller = _base_manifest(expected_base_head)
    previous_sha, previous_active = _verify_current_controller(
        base_controller_entry=base_controller,
        base_manifest_sha256=base_sha,
    )
    binary, candidate = _stage_candidate(
        repo_root,
        expected_head=expected_source_head,
        go_bin=go_bin,
        base_manifest=base,
    )
    new_sha = _sha256(binary)

    if (
        previous_active is not None
        and previous_active.get("controller_source_head") == expected_source_head
        and previous_sha == new_sha
    ):
        verify_active_override(
            expected_source_head=expected_source_head,
            expected_base_head=expected_base_head,
        )
        return pathlib.Path(str(previous_active["receipt_path"]))

    REFRESH_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(REFRESH_ROOT, 0o700)
    transaction_id = str(uuid.uuid4())
    tx_dir = REFRESH_ROOT / transaction_id
    tx_dir.mkdir(mode=0o700)
    receipt_path = tx_dir / "receipt.json"
    backup_path = tx_dir / "previous-controller"
    shutil.copyfile(CONTROLLER_BINARY, backup_path)
    os.chmod(backup_path, 0o700)

    previous_active_backup = tx_dir / "previous-active.json"
    if ACTIVE_RECEIPT.is_file():
        shutil.copyfile(ACTIVE_RECEIPT, previous_active_backup)
        os.chmod(previous_active_backup, 0o600)

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "mode": MODE,
        "transaction_id": transaction_id,
        "receipt_path": str(receipt_path),
        "phase": "PREPARED",
        "base_source_head": expected_base_head,
        "controller_source_head": expected_source_head,
        "base_install_manifest_sha256": base_sha,
        "catalog_generation_sha256": base["catalog_generation_sha256"],
        "root_policy_sha256": base["root_policy_sha256"],
        "previous_controller_sha256": previous_sha,
        "controller_binary_sha256": new_sha,
        "backup_path": str(backup_path),
        "previous_active_receipt_backup": (
            str(previous_active_backup) if previous_active_backup.is_file() else None
        ),
        "non_controller_generation_equivalent": True,
        "candidate_manifest_source_head": candidate.get("source_head"),
        "root_services_preserved_active": True,
        "class_controllers_preserved_inactive": True,
    }
    _write_json(receipt_path, receipt)

    replaced = False
    try:
        _atomic_write(CONTROLLER_BINARY, binary, 0o755)
        replaced = True
        if _sha256(CONTROLLER_BINARY.read_bytes()) != new_sha:
            raise ControllerRefreshError("controller binary post-install digest mismatch")
        if stat.S_IMODE(CONTROLLER_BINARY.stat().st_mode) != 0o755:
            raise ControllerRefreshError("controller binary post-install mode mismatch")

        _assert_live_boundary()
        receipt["phase"] = "ACTIVE"
        _write_json(receipt_path, receipt)
        _write_json(ACTIVE_RECEIPT, receipt)

        verify_active_override(
            expected_source_head=expected_source_head,
            expected_base_head=expected_base_head,
        )
        return receipt_path
    except Exception:
        if replaced:
            _atomic_write(CONTROLLER_BINARY, backup_path.read_bytes(), 0o755)
            if previous_active_backup.is_file():
                _atomic_write(ACTIVE_RECEIPT, previous_active_backup.read_bytes(), 0o600)
            else:
                try:
                    ACTIVE_RECEIPT.unlink()
                except FileNotFoundError:
                    pass
            receipt["phase"] = "ROLLED_BACK"
            _write_json(receipt_path, receipt)
        raise


def rollback_refresh(receipt_path: pathlib.Path) -> None:
    if os.geteuid() != 0:
        raise ControllerRefreshError("controller refresh rollback requires root")
    _assert_live_boundary()
    receipt = _load(receipt_path)
    if receipt.get("mode") != MODE:
        raise ControllerRefreshError("controller refresh receipt mode invalid")
    backup = pathlib.Path(str(receipt.get("backup_path")))
    if not backup.is_file():
        raise ControllerRefreshError("controller refresh backup missing")
    _atomic_write(CONTROLLER_BINARY, backup.read_bytes(), 0o755)
    if _sha256(CONTROLLER_BINARY.read_bytes()) != receipt.get("previous_controller_sha256"):
        raise ControllerRefreshError("controller refresh rollback digest mismatch")

    prior = receipt.get("previous_active_receipt_backup")
    if isinstance(prior, str) and pathlib.Path(prior).is_file():
        _atomic_write(ACTIVE_RECEIPT, pathlib.Path(prior).read_bytes(), 0o600)
    else:
        try:
            ACTIVE_RECEIPT.unlink()
        except FileNotFoundError:
            pass

    receipt["phase"] = "ROLLED_BACK"
    _write_json(receipt_path, receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--expected-source-head")
    parser.add_argument("--base-source-head")
    parser.add_argument("--go-bin", default="go")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify-active", action="store_true")
    parser.add_argument("--rollback", type=pathlib.Path)
    args = parser.parse_args()

    if not args.base_source_head:
        raise ControllerRefreshError("--base-source-head is required")

    if args.apply:
        if not args.expected_source_head:
            raise ControllerRefreshError("--apply requires --expected-source-head")
        receipt = apply_refresh(
            args.repo_root.resolve(),
            expected_source_head=args.expected_source_head,
            expected_base_head=args.base_source_head,
            go_bin=args.go_bin,
        )
        print("V3_CONTROLLER_BINARY_REFRESH=PASS")
        print(f"CONTROLLER_REFRESH_RECEIPT={receipt}")
        return 0

    if args.verify_active:
        if not args.expected_source_head:
            raise ControllerRefreshError("--verify-active requires --expected-source-head")
        active = verify_active_override(
            expected_source_head=args.expected_source_head,
            expected_base_head=args.base_source_head,
        )
        print("V3_CONTROLLER_OVERRIDE_VERIFY=PASS")
        print(f"CONTROLLER_SOURCE_HEAD={active['controller_source_head']}")
        return 0

    if args.rollback:
        rollback_refresh(args.rollback)
        print("V3_CONTROLLER_BINARY_REFRESH_ROLLBACK=PASS")
        return 0

    raise ControllerRefreshError("choose --apply, --verify-active, or --rollback")


if __name__ == "__main__":
    raise SystemExit(main())
