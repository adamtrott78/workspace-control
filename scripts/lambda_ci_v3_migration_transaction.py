#!/usr/bin/env python3
"""Fail-closed v3 one-class canary generation-exclusion transaction.

This tool contains live-capable mechanics but grants no live authority. APPLY
requires a separately supplied, root-owned, mode-0600 operator authorization
receipt bound to the exact source head, generated canary generation, controller
policy, workflow blob and target class.

It deliberately does NOT:
- dispatch a GitHub workflow;
- edit an owning repository;
- enable/retire a scale set;
- alter quarantine or recovery-retry receipts;
- invoke maintenance-plane attestation actions;
- start more than one v3 class controller.

The safety invariant is stronger than convenience: v2 and v3 project
controllers are never intentionally active at the same time. Rollback restores
only the exact captured v2 controller active states, and only after all v3
class/transient/resource activity is proven absent.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any, Protocol


ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = pathlib.Path("architecture/lambda-ci-project-registry.v1.json")
DEFAULT_CANARY_MANIFEST = pathlib.Path("canary-manifest.json")
V3_CONFIG_ROOT = pathlib.Path("/etc/workspace-ci/v3")
V3_STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3")
MIGRATION_ROOT = V3_STATE_ROOT / "migration"
V3_PROVISIONER_STATE = V3_STATE_ROOT / "provisioner"
AUTHORITY_CONSUMPTION_ROOT = V3_STATE_ROOT / "migration-authority"
AUTHORITY_MAX_LIFETIME_SECONDS = 30 * 60

V3_PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
V3_RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
RESEARCH_GPU_V2_UNIT = "workspace-ci-controller@research-engine-gpu.service"
COMPATIBILITY_V2_UNITS = (
    "workspace-ci-controller.service",
    "workspace-ci-controller-gpu.service",
)
UUID_RE = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
AUTHORIZATION_ID_RE = re.compile(rf"^{UUID_RE}$")
V3_SUPERVISOR_RE = re.compile(r"^workspace-ci-v3-supervisor-[0-9a-f]{20}\.service$")


class MigrationError(RuntimeError):
    pass


class Systemd(Protocol):
    def active(self, unit: str) -> bool: ...
    def start(self, unit: str) -> None: ...
    def stop(self, unit: str) -> None: ...
    def list_units(self) -> list[str]: ...


class RealSystemd:
    def _run(self, argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check and proc.returncode != 0:
            raise MigrationError(
                f"command failed rc={proc.returncode}: {' '.join(argv)}: "
                f"{proc.stderr.strip()[:512]}"
            )
        return proc

    def active(self, unit: str) -> bool:
        return self._run(["systemctl", "is-active", "--quiet", unit], check=False).returncode == 0

    def start(self, unit: str) -> None:
        self._run(["systemctl", "start", unit])

    def stop(self, unit: str) -> None:
        self._run(["systemctl", "stop", unit])

    def list_units(self) -> list[str]:
        proc = self._run(
            [
                "systemctl",
                "list-units",
                "--all",
                "--type=service",
                "--plain",
                "--no-legend",
                "--no-pager",
            ]
        )
        units = []
        for line in proc.stdout.splitlines():
            fields = line.split()
            if fields:
                units.append(fields[0])
        return units


def _load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MigrationError(f"{path}: expected JSON object")
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: pathlib.Path, raw: bytes, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def v2_controller_units(registry: dict[str, Any]) -> list[str]:
    units = []
    for project_id, project in sorted(registry["projects"].items()):
        if project.get("activation_state") != "ACTIVE":
            continue
        for lane in sorted(project["lanes"]):
            units.append(f"workspace-ci-controller@{project_id}-{lane}.service")
    if len(units) != 5:
        raise MigrationError(f"expected exactly five v2 project controllers, got {units}")
    return units


def v3_controller_units(root_policy: dict[str, Any]) -> list[str]:
    classes = root_policy.get("runner_classes")
    if not isinstance(classes, dict) or len(classes) != 9:
        raise MigrationError("installed v3 root policy must contain exactly nine classes")
    return [
        f"workspace-ci-v3-controller@{class_id}.service"
        for class_id in sorted(classes)
    ]


def _legacy_transient_regex(registry: dict[str, Any]) -> re.Pattern[str]:
    projects = "|".join(re.escape(x) for x in sorted(registry["projects"]))
    return re.compile(rf"^workspace-ci-(?:{projects})-{UUID_RE}\.service$")


def _v3_transient_regex(root_policy: dict[str, Any]) -> re.Pattern[str]:
    classes = "|".join(
        re.escape(x) for x in sorted(root_policy["runner_classes"])
    )
    return re.compile(rf"^workspace-ci-v3-(?:{classes})-{UUID_RE}\.service$")


def transient_units(
    systemd: Systemd,
    *,
    registry: dict[str, Any],
    root_policy: dict[str, Any],
) -> tuple[list[str], list[str]]:
    legacy_re = _legacy_transient_regex(registry)
    v3_re = _v3_transient_regex(root_policy)
    legacy = []
    v3 = []
    for unit in systemd.list_units():
        if legacy_re.fullmatch(unit) and systemd.active(unit):
            legacy.append(unit)
        if (v3_re.fullmatch(unit) or V3_SUPERVISOR_RE.fullmatch(unit)) and systemd.active(unit):
            v3.append(unit)
    return sorted(legacy), sorted(v3)


def v3_resource_claims(state_root: pathlib.Path = V3_PROVISIONER_STATE) -> list[str]:
    if not state_root.exists():
        return []
    claims = []
    for path in sorted(state_root.glob("*.json")):
        if path.name.startswith("_"):
            continue
        record = _load(path)
        state = record.get("state")
        if state in {"RESERVED", "PREPARING", "ACCEPTED"} or record.get("resource_hold") is True:
            claims.append(str(record.get("request_id", path.stem)))
    return claims


def _parse_authority_time(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise MigrationError(f"live canary authorization {field} invalid") from exc
    if parsed.tzinfo is None:
        raise MigrationError(f"live canary authorization {field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _validate_authority_payload(
    receipt: dict[str, Any],
    *,
    expected_head: str,
    target_class: str,
    manifest: dict[str, Any],
    canary_policy: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    required = {
        "schema_version",
        "authority",
        "operation",
        "authorization_id",
        "source_head",
        "canary_generation_sha256",
        "target_runner_class_id",
        "controller_policy_sha256",
        "workflow_blob_sha",
        "issued_at",
        "expires_at",
    }
    if set(receipt) != required:
        raise MigrationError("live canary authorization receipt keys drift")
    if receipt["schema_version"] != 1:
        raise MigrationError("live canary authorization receipt schema invalid")
    if receipt["authority"] != "workspace-control-operator":
        raise MigrationError("live canary authorization authority invalid")
    if receipt["operation"] != "ACTIVATE_ONE_V3_CANARY":
        raise MigrationError("live canary authorization operation invalid")
    authorization_id = str(receipt["authorization_id"])
    if AUTHORIZATION_ID_RE.fullmatch(authorization_id) is None:
        raise MigrationError("live canary authorization id invalid")
    if str(uuid.UUID(authorization_id)) != authorization_id:
        raise MigrationError("live canary authorization id is not canonical")
    if receipt["source_head"] != expected_head:
        raise MigrationError("live canary authorization source head mismatch")
    if receipt["canary_generation_sha256"] != manifest["canary_generation_sha256"]:
        raise MigrationError("live canary authorization generation mismatch")
    if receipt["target_runner_class_id"] != target_class:
        raise MigrationError("live canary authorization class mismatch")
    entry = manifest["classes"][target_class]
    if receipt["controller_policy_sha256"] != canary_policy["controller_policy_sha256"]:
        raise MigrationError("live canary authorization policy mismatch")
    if receipt["workflow_blob_sha"] != entry["workflow_blob_sha"]:
        raise MigrationError("live canary authorization workflow blob mismatch")

    issued_at = _parse_authority_time(receipt["issued_at"], "issued_at")
    expires_at = _parse_authority_time(receipt["expires_at"], "expires_at")
    clock = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if expires_at <= issued_at:
        raise MigrationError("live canary authorization expiry must follow issuance")
    if (expires_at - issued_at).total_seconds() > AUTHORITY_MAX_LIFETIME_SECONDS:
        raise MigrationError("live canary authorization lifetime exceeds maximum")
    if issued_at > clock:
        raise MigrationError("live canary authorization is not yet valid")
    if expires_at <= clock:
        raise MigrationError("live canary authorization expired")
    return receipt


def _validate_authority_file(
    path: pathlib.Path,
    *,
    expected_head: str,
    target_class: str,
    manifest: dict[str, Any],
    canary_policy: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    st = path.stat()
    if st.st_uid != 0:
        raise MigrationError("live canary authorization receipt must be root-owned")
    if stat.S_IMODE(st.st_mode) != 0o600:
        raise MigrationError("live canary authorization receipt must be mode 0600")
    raw = path.read_bytes()
    try:
        receipt = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MigrationError("live canary authorization receipt is not valid JSON") from exc
    if not isinstance(receipt, dict):
        raise MigrationError("live canary authorization receipt must be object")
    return (
        _validate_authority_payload(
            receipt,
            expected_head=expected_head,
            target_class=target_class,
            manifest=manifest,
            canary_policy=canary_policy,
        ),
        raw,
    )


def _consume_authority_receipt(
    receipt: dict[str, Any],
    raw: bytes,
    *,
    consumption_root: pathlib.Path = AUTHORITY_CONSUMPTION_ROOT,
) -> tuple[pathlib.Path, str]:
    authorization_id = str(receipt["authorization_id"])
    if AUTHORIZATION_ID_RE.fullmatch(authorization_id) is None:
        raise MigrationError("live canary authorization id invalid")

    consumption_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    st = consumption_root.stat()
    if not stat.S_ISDIR(st.st_mode):
        raise MigrationError("live canary authorization consumption root is not a directory")
    if st.st_uid != os.geteuid():
        raise MigrationError("live canary authorization consumption root owner invalid")
    if stat.S_IMODE(st.st_mode) != 0o700:
        raise MigrationError("live canary authorization consumption root must be mode 0700")

    digest = _sha256(raw)
    marker = consumption_root / f"{authorization_id}.json"
    record = {
        "schema_version": 1,
        "authorization_id": authorization_id,
        "authorization_receipt_sha256": digest,
        "source_head": receipt["source_head"],
        "canary_generation_sha256": receipt["canary_generation_sha256"],
        "target_runner_class_id": receipt["target_runner_class_id"],
        "controller_policy_sha256": receipt["controller_policy_sha256"],
        "workflow_blob_sha": receipt["workflow_blob_sha"],
        "consumed_at": _utcnow(),
    }
    try:
        fd = os.open(
            marker,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError as exc:
        raise MigrationError("live canary authorization receipt already consumed") from exc
    with os.fdopen(fd, "wb") as handle:
        handle.write(_canonical(record))
        handle.flush()
        os.fsync(handle.fileno())
    dir_fd = os.open(consumption_root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    return marker, digest


def validate_canary_target(
    manifest: dict[str, Any],
    *,
    target_class: str,
    canary_policy: dict[str, Any],
) -> dict[str, Any]:
    if manifest.get("status") != "STAGED_NOT_INSTALLED_NOT_AUTHORIZED":
        raise MigrationError("canary manifest status invalid")
    classes = manifest.get("classes")
    if not isinstance(classes, dict) or target_class not in classes:
        raise MigrationError("target class absent from canary manifest")
    entry = classes[target_class]
    if entry.get("authorization_state") != "REQUIRES_SEPARATE_LIVE_CANARY_AUTHORITY":
        raise MigrationError(
            f"{target_class}: canary is blocked: {entry.get('blockers')}"
        )
    if entry.get("blockers"):
        raise MigrationError(f"{target_class}: canary blockers are nonempty")
    if canary_policy.get("runner_class_id") != target_class:
        raise MigrationError("canary controller policy class mismatch")
    if canary_policy.get("controller_policy_sha256") != entry["controller_policy_sha256"]:
        raise MigrationError("canary controller policy digest mismatch")
    workflows = canary_policy.get("trusted_workflows")
    if not isinstance(workflows, list) or len(workflows) != 1:
        raise MigrationError("canary controller policy must trust exactly one workflow")
    workflow = workflows[0]
    if workflow.get("blob_sha") != entry["workflow_blob_sha"]:
        raise MigrationError("canary workflow blob/policy mismatch")
    if workflow.get("allowed_events") != ["workflow_dispatch"]:
        raise MigrationError("canary workflow event authority drift")
    if workflow.get("allowed_actor_logins") != [manifest["owner_actor_login"]]:
        raise MigrationError("canary actor authority drift")
    return entry


def _assert_research_gpu_containment(systemd: Systemd) -> None:
    if systemd.active(RESEARCH_GPU_V2_UNIT):
        raise MigrationError(
            "research-engine GPU legacy controller is active; migration cannot consume containment"
        )
    for unit in COMPATIBILITY_V2_UNITS:
        if systemd.active(unit):
            raise MigrationError(
                f"untracked legacy compatibility controller is active: {unit}"
            )


def _assert_only_target_v3_active(
    systemd: Systemd,
    v3_units: list[str],
    target_unit: str | None,
) -> None:
    active = [unit for unit in v3_units if systemd.active(unit)]
    expected = [] if target_unit is None else [target_unit]
    if active != expected:
        raise MigrationError(f"unexpected v3 controller active set: {active} != {expected}")


def _assert_generation_drained(
    systemd: Systemd,
    *,
    registry: dict[str, Any],
    root_policy: dict[str, Any],
    require_legacy_empty: bool,
    require_v3_empty: bool,
    state_root: pathlib.Path,
) -> None:
    legacy, v3 = transient_units(
        systemd,
        registry=registry,
        root_policy=root_policy,
    )
    if require_legacy_empty and legacy:
        raise MigrationError(f"legacy transient runner units remain: {legacy}")
    if require_v3_empty and v3:
        raise MigrationError(f"v3 transient/supervisor units remain: {v3}")
    if require_v3_empty:
        claims = v3_resource_claims(state_root)
        if claims:
            raise MigrationError(f"v3 root resource claims remain: {claims}")


def _persist_transaction(path: pathlib.Path, receipt: dict[str, Any]) -> None:
    receipt["updated_at"] = _utcnow()
    _atomic_write(path, _canonical(receipt), mode=0o600)


def _backup_policy(
    transaction_dir: pathlib.Path,
    production_policy_path: pathlib.Path,
) -> tuple[pathlib.Path, str]:
    raw = production_policy_path.read_bytes()
    backup = transaction_dir / "production-controller-policy.json"
    _atomic_write(backup, raw, mode=0o600)
    return backup, _sha256(raw)


def apply_canary(
    *,
    systemd: Systemd,
    registry: dict[str, Any],
    root_policy: dict[str, Any],
    canary_manifest: dict[str, Any],
    canary_policy: dict[str, Any],
    canary_policy_raw: bytes,
    authority_receipt: dict[str, Any],
    authority_receipt_raw: bytes,
    target_class: str,
    source_head: str,
    production_policy_path: pathlib.Path,
    transaction_root: pathlib.Path = MIGRATION_ROOT,
    provisioner_state_root: pathlib.Path = V3_PROVISIONER_STATE,
    authority_consumption_root: pathlib.Path = AUTHORITY_CONSUMPTION_ROOT,
) -> pathlib.Path:
    entry = validate_canary_target(
        canary_manifest,
        target_class=target_class,
        canary_policy=canary_policy,
    )
    if authority_receipt["source_head"] != source_head:
        raise MigrationError("authorization receipt source head mismatch")
    if authority_receipt["target_runner_class_id"] != target_class:
        raise MigrationError("authorization receipt target mismatch")
    if authority_receipt["canary_generation_sha256"] != canary_manifest["canary_generation_sha256"]:
        raise MigrationError("authorization receipt generation mismatch")
    if authority_receipt["controller_policy_sha256"] != canary_policy["controller_policy_sha256"]:
        raise MigrationError("authorization receipt controller policy mismatch")
    if authority_receipt["workflow_blob_sha"] != entry["workflow_blob_sha"]:
        raise MigrationError("authorization receipt workflow blob mismatch")

    _assert_research_gpu_containment(systemd)
    v2_units = v2_controller_units(registry)
    v3_units = v3_controller_units(root_policy)
    target_unit = f"workspace-ci-v3-controller@{target_class}.service"
    _assert_only_target_v3_active(systemd, v3_units, None)

    if not systemd.active(V3_PROVISIONER_UNIT):
        raise MigrationError("v3 provisioner is not healthy/active")
    if not systemd.active(V3_RECONCILER_UNIT):
        raise MigrationError("v3 reconciler is not healthy/active")

    _assert_generation_drained(
        systemd,
        registry=registry,
        root_policy=root_policy,
        require_legacy_empty=False,
        require_v3_empty=True,
        state_root=provisioner_state_root,
    )

    authority_marker, authority_digest = _consume_authority_receipt(
        authority_receipt,
        authority_receipt_raw,
        consumption_root=authority_consumption_root,
    )

    transaction_id = str(uuid.uuid4())
    transaction_dir = transaction_root / transaction_id
    transaction_dir.mkdir(parents=True, exist_ok=False)
    os.chmod(transaction_dir, 0o700)
    backup_path, backup_sha = _backup_policy(transaction_dir, production_policy_path)
    prestate = {unit: systemd.active(unit) for unit in v2_units}
    if prestate.get(RESEARCH_GPU_V2_UNIT):
        raise MigrationError("research GPU containment drifted during prestate capture")

    receipt_path = transaction_dir / "transaction.json"
    receipt = {
        "schema_version": 1,
        "transaction_id": transaction_id,
        "mode": "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION",
        "authorization_id": authority_receipt["authorization_id"],
        "authorization_receipt_sha256": authority_digest,
        "authorization_consumption_marker": str(authority_marker),
        "source_head": source_head,
        "canary_generation_sha256": canary_manifest["canary_generation_sha256"],
        "target_runner_class_id": target_class,
        "target_controller_unit": target_unit,
        "workflow_blob_sha": entry["workflow_blob_sha"],
        "controller_policy_sha256": canary_policy["controller_policy_sha256"],
        "production_policy_path": str(production_policy_path),
        "production_policy_backup_path": str(backup_path),
        "production_policy_sha256": backup_sha,
        "v2_prestate": prestate,
        "research_gpu_containment_preserved": True,
        "quarantine_or_retry_authority_mutated": False,
        "workflow_dispatched": False,
        "phase": "PREPARED",
    }
    _persist_transaction(receipt_path, receipt)

    try:
        for unit in v2_units:
            if prestate[unit]:
                systemd.stop(unit)
        if any(systemd.active(unit) for unit in v2_units):
            raise MigrationError("v2 project controller remained active after stop")
        _assert_research_gpu_containment(systemd)
        _assert_generation_drained(
            systemd,
            registry=registry,
            root_policy=root_policy,
            require_legacy_empty=True,
            require_v3_empty=True,
            state_root=provisioner_state_root,
        )
        receipt["phase"] = "V2_QUIESCED"
        _persist_transaction(receipt_path, receipt)

        _atomic_write(production_policy_path, canary_policy_raw, mode=0o644)
        if _load(production_policy_path).get("controller_policy_sha256") != canary_policy["controller_policy_sha256"]:
            raise MigrationError("installed canary controller policy drifted")
        receipt["phase"] = "CANARY_POLICY_INSTALLED"
        _persist_transaction(receipt_path, receipt)

        systemd.start(target_unit)
        _assert_only_target_v3_active(systemd, v3_units, target_unit)
        if any(systemd.active(unit) for unit in v2_units):
            raise MigrationError("generation overlap detected after v3 start")
        receipt["phase"] = "CANARY_ACTIVE"
        _persist_transaction(receipt_path, receipt)
        return receipt_path
    except Exception:
        # Caller must invoke rollback using the durable receipt. Never resume v2
        # from an exception path unless v3 drain proof succeeds.
        receipt["phase"] = "ROLLBACK_REQUIRED"
        _persist_transaction(receipt_path, receipt)
        raise


def rollback(
    *,
    systemd: Systemd,
    registry: dict[str, Any],
    root_policy: dict[str, Any],
    receipt_path: pathlib.Path,
    provisioner_state_root: pathlib.Path = V3_PROVISIONER_STATE,
) -> None:
    receipt = _load(receipt_path)
    if receipt.get("mode") != "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION":
        raise MigrationError("transaction mode invalid")
    if receipt.get("research_gpu_containment_preserved") is not True:
        raise MigrationError("transaction did not preserve Research GPU containment")

    v2_units = v2_controller_units(registry)
    v3_units = v3_controller_units(root_policy)
    target_unit = receipt["target_controller_unit"]

    if systemd.active(target_unit):
        systemd.stop(target_unit)
    _assert_only_target_v3_active(systemd, v3_units, None)
    _assert_generation_drained(
        systemd,
        registry=registry,
        root_policy=root_policy,
        require_legacy_empty=False,
        require_v3_empty=True,
        state_root=provisioner_state_root,
    )

    backup = pathlib.Path(receipt["production_policy_backup_path"])
    raw = backup.read_bytes()
    if _sha256(raw) != receipt["production_policy_sha256"]:
        raise MigrationError("production controller policy backup digest drift")
    production_path = pathlib.Path(receipt["production_policy_path"])
    _atomic_write(production_path, raw, mode=0o644)
    receipt["phase"] = "V3_DRAINED_POLICY_RESTORED"
    _persist_transaction(receipt_path, receipt)

    prestate = receipt["v2_prestate"]
    if prestate.get(RESEARCH_GPU_V2_UNIT) is not False:
        raise MigrationError("stored prestate would restore Research GPU controller")
    for unit in v2_units:
        wanted = bool(prestate[unit])
        active = systemd.active(unit)
        if wanted and not active:
            systemd.start(unit)
        elif not wanted and active:
            systemd.stop(unit)
    _assert_research_gpu_containment(systemd)
    for unit in v2_units:
        if systemd.active(unit) != bool(prestate[unit]):
            raise MigrationError(f"legacy controller state restore failed: {unit}")

    receipt["phase"] = "ROLLED_BACK_LEGACY_RESTORED"
    _persist_transaction(receipt_path, receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--apply-canary", action="store_true")
    parser.add_argument("--rollback", type=pathlib.Path)
    parser.add_argument("--source-head")
    parser.add_argument("--target-class")
    parser.add_argument("--canary-manifest", type=pathlib.Path)
    parser.add_argument("--canary-policy", type=pathlib.Path)
    parser.add_argument("--authorization-receipt", type=pathlib.Path)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise MigrationError("live migration transaction must run as root")

    repo_root = args.repo_root.resolve()
    registry = _load(repo_root / REGISTRY_PATH)
    root_policy = _load(V3_CONFIG_ROOT / "root-policy.json")
    systemd = RealSystemd()

    if args.rollback:
        rollback(
            systemd=systemd,
            registry=registry,
            root_policy=root_policy,
            receipt_path=args.rollback,
        )
        print("V3_CANARY_ROLLBACK=PASS")
        return 0

    if not args.apply_canary:
        raise MigrationError("choose --apply-canary or --rollback")
    if not all(
        (
            args.source_head,
            args.target_class,
            args.canary_manifest,
            args.canary_policy,
            args.authorization_receipt,
        )
    ):
        raise MigrationError("apply-canary requires exact source/class/manifest/policy/authority inputs")

    head = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if head != args.source_head:
        raise MigrationError(f"source head mismatch: {head} != {args.source_head}")
    dirty = subprocess.check_output(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=no"],
        text=True,
    )
    if dirty.strip():
        raise MigrationError("source tree has tracked modifications")

    manifest = _load(args.canary_manifest)
    policy_raw = args.canary_policy.read_bytes()
    policy = json.loads(policy_raw)
    if not isinstance(policy, dict):
        raise MigrationError("canary policy must be object")
    authority, authority_raw = _validate_authority_file(
        args.authorization_receipt,
        expected_head=args.source_head,
        target_class=args.target_class,
        manifest=manifest,
        canary_policy=policy,
    )

    production_policy = (
        V3_CONFIG_ROOT / "controllers" / f"{args.target_class}.json"
    )
    receipt = apply_canary(
        systemd=systemd,
        registry=registry,
        root_policy=root_policy,
        canary_manifest=manifest,
        canary_policy=policy,
        canary_policy_raw=policy_raw,
        authority_receipt=authority,
        authority_receipt_raw=authority_raw,
        target_class=args.target_class,
        source_head=args.source_head,
        production_policy_path=production_policy,
    )
    print("V3_ONE_CLASS_CANARY_ACTIVE=PASS")
    print(f"TRANSACTION_RECEIPT={receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
