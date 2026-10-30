#!/usr/bin/env python3
"""One-shot activation/rollback for Lambda CI v3 root services only.

This helper bridges the inactive substrate install to the first class canary.
It grants no class-controller, workflow, route, scale-set, containment, or
retry authority.

ACTIVATE requires a short-lived, one-shot, root-owned authorization receipt
bound to the exact installed manifest, source head, and root-policy digest.
It then:
- re-attests every installed managed artifact via the reconciler;
- proves all v3 class controllers/transients/resource claims are absent;
- atomically consumes the authorization before the first service mutation;
- starts the reconciler first and requires its installed-generation attestation;
- starts the provisioner second and verifies its Unix socket;
- re-proves all class controllers/transients/resource claims remain absent.

Any activation failure stops both root services. Receipt-driven rollback also
stops only these two root services and never deletes/reopens consumed authority.
"""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
import pathlib
import re
import socket
import stat
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

import lambda_ci_v3_reconciler as reconciler


V3_CONFIG_ROOT = pathlib.Path("/etc/workspace-ci/v3")
INSTALL_MANIFEST = V3_CONFIG_ROOT / "install-manifest.json"
ROOT_POLICY = V3_CONFIG_ROOT / "root-policy.json"
V3_STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3")
MIGRATION_ROOT = V3_STATE_ROOT / "migration"
AUTHORITY_CONSUMPTION_ROOT = V3_STATE_ROOT / "migration-authority"
V3_PROVISIONER_STATE = V3_STATE_ROOT / "provisioner"
PROVISIONER_SOCKET = pathlib.Path("/run/workspace-ci/v3/provisioner.sock")
PROVISIONER_SOCKET_GROUP = "workspace-ci-v3-provisioner"

PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
RESEARCH_GPU_V2_UNIT = "workspace-ci-controller@research-engine-gpu.service"
AUTHORITY_MAX_LIFETIME_SECONDS = 30 * 60
UUID_RE = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
AUTHORIZATION_ID_RE = re.compile(rf"^{UUID_RE}$")
V3_SUPERVISOR_RE = re.compile(r"^workspace-ci-v3-supervisor-[0-9a-f]{20}\.service$")


class RootActivationError(RuntimeError):
    pass


class Systemd(Protocol):
    def active(self, unit: str) -> bool: ...
    def enabled(self, unit: str) -> bool: ...
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
            raise RootActivationError(
                f"command failed rc={proc.returncode}: {' '.join(argv)}: "
                f"{proc.stderr.strip()[:512]}"
            )
        return proc

    def active(self, unit: str) -> bool:
        return self._run(["systemctl", "is-active", "--quiet", unit], check=False).returncode == 0

    def enabled(self, unit: str) -> bool:
        return self._run(["systemctl", "is-enabled", "--quiet", unit], check=False).returncode == 0

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
        units: list[str] = []
        for line in proc.stdout.splitlines():
            fields = line.split()
            if fields:
                units.append(fields[0])
        return units


def _load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RootActivationError(f"{path}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise RootActivationError(f"{path}: expected JSON object")
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
        dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _validate_private_state_dir(path: pathlib.Path, label: str) -> None:
    try:
        st = path.stat()
    except FileNotFoundError as exc:
        raise RootActivationError(f"{label} is missing; inactive substrate is incomplete") from exc
    if not stat.S_ISDIR(st.st_mode):
        raise RootActivationError(f"{label} is not a directory")
    if st.st_uid != os.geteuid():
        raise RootActivationError(f"{label} owner invalid")
    if stat.S_IMODE(st.st_mode) != 0o700:
        raise RootActivationError(f"{label} must be mode 0700")


def _parse_authority_time(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RootActivationError(f"root activation authorization {field} invalid") from exc
    if parsed.tzinfo is None:
        raise RootActivationError(
            f"root activation authorization {field} must be timezone-aware"
        )
    return parsed.astimezone(timezone.utc)


def _validate_authority_payload(
    receipt: dict[str, Any],
    *,
    expected_source_head: str,
    expected_install_manifest_sha256: str,
    expected_root_policy_sha256: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    required = {
        "schema_version",
        "authority",
        "operation",
        "authorization_id",
        "source_head",
        "install_manifest_sha256",
        "root_policy_sha256",
        "issued_at",
        "expires_at",
    }
    if set(receipt) != required:
        raise RootActivationError("root activation authorization receipt keys drift")
    if receipt["schema_version"] != 1:
        raise RootActivationError("root activation authorization schema invalid")
    if receipt["authority"] != "workspace-control-operator":
        raise RootActivationError("root activation authorization authority invalid")
    if receipt["operation"] != "ACTIVATE_V3_ROOT_SERVICES":
        raise RootActivationError("root activation authorization operation invalid")

    authorization_id = str(receipt["authorization_id"])
    if AUTHORIZATION_ID_RE.fullmatch(authorization_id) is None:
        raise RootActivationError("root activation authorization id invalid")
    if str(uuid.UUID(authorization_id)) != authorization_id:
        raise RootActivationError("root activation authorization id is not canonical")
    if receipt["source_head"] != expected_source_head:
        raise RootActivationError("root activation authorization source head mismatch")
    if receipt["install_manifest_sha256"] != expected_install_manifest_sha256:
        raise RootActivationError("root activation authorization manifest mismatch")
    if receipt["root_policy_sha256"] != expected_root_policy_sha256:
        raise RootActivationError("root activation authorization root policy mismatch")

    issued_at = _parse_authority_time(receipt["issued_at"], "issued_at")
    expires_at = _parse_authority_time(receipt["expires_at"], "expires_at")
    clock = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if expires_at <= issued_at:
        raise RootActivationError("root activation authorization expiry must follow issuance")
    if (expires_at - issued_at).total_seconds() > AUTHORITY_MAX_LIFETIME_SECONDS:
        raise RootActivationError("root activation authorization lifetime exceeds maximum")
    if issued_at > clock:
        raise RootActivationError("root activation authorization is not yet valid")
    if expires_at <= clock:
        raise RootActivationError("root activation authorization expired")
    return receipt


def _validate_authority_file(
    path: pathlib.Path,
    *,
    expected_source_head: str,
    expected_install_manifest_sha256: str,
    expected_root_policy_sha256: str,
) -> tuple[dict[str, Any], bytes]:
    st = path.stat()
    if st.st_uid != 0:
        raise RootActivationError("root activation authorization receipt must be root-owned")
    if stat.S_IMODE(st.st_mode) != 0o600:
        raise RootActivationError("root activation authorization receipt must be mode 0600")
    raw = path.read_bytes()
    try:
        receipt = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RootActivationError("root activation authorization receipt is not valid JSON") from exc
    if not isinstance(receipt, dict):
        raise RootActivationError("root activation authorization receipt must be object")
    return (
        _validate_authority_payload(
            receipt,
            expected_source_head=expected_source_head,
            expected_install_manifest_sha256=expected_install_manifest_sha256,
            expected_root_policy_sha256=expected_root_policy_sha256,
        ),
        raw,
    )


def _consume_authority(
    receipt: dict[str, Any],
    raw: bytes,
    *,
    consumption_root: pathlib.Path,
) -> tuple[pathlib.Path, str]:
    _validate_private_state_dir(
        consumption_root,
        "root activation authorization consumption root",
    )
    authorization_id = str(receipt["authorization_id"])
    digest = _sha256(raw)
    marker = consumption_root / f"{authorization_id}.json"
    record = {
        "schema_version": 1,
        "operation": receipt["operation"],
        "authorization_id": authorization_id,
        "authorization_receipt_sha256": digest,
        "source_head": receipt["source_head"],
        "install_manifest_sha256": receipt["install_manifest_sha256"],
        "root_policy_sha256": receipt["root_policy_sha256"],
        "consumed_at": _utcnow(),
    }
    try:
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise RootActivationError("root activation authorization already consumed") from exc
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


def _class_ids(root_policy: dict[str, Any]) -> list[str]:
    classes = root_policy.get("runner_classes")
    if not isinstance(classes, dict) or len(classes) != 9:
        raise RootActivationError("installed root policy must contain exactly nine classes")
    return sorted(classes)


def _class_units(root_policy: dict[str, Any]) -> list[str]:
    return [
        f"workspace-ci-v3-controller@{class_id}.service"
        for class_id in _class_ids(root_policy)
    ]


def _assert_research_gpu_contained(systemd: Systemd) -> None:
    if systemd.active(RESEARCH_GPU_V2_UNIT):
        raise RootActivationError(
            "legacy Research GPU controller is active; inherited containment drifted"
        )


def _assert_v3_units_not_enabled(systemd: Systemd, root_policy: dict[str, Any]) -> None:
    units = [RECONCILER_UNIT, PROVISIONER_UNIT, *_class_units(root_policy)]
    enabled = [unit for unit in units if systemd.enabled(unit)]
    if enabled:
        raise RootActivationError(
            f"v3 units unexpectedly enabled for boot persistence: {enabled}"
        )


def _assert_class_controllers_inactive(systemd: Systemd, root_policy: dict[str, Any]) -> None:
    active = [unit for unit in _class_units(root_policy) if systemd.active(unit)]
    if active:
        raise RootActivationError(f"v3 class controller unexpectedly active: {active}")


def _active_v3_transients(systemd: Systemd, root_policy: dict[str, Any]) -> list[str]:
    class_pattern = "|".join(re.escape(x) for x in _class_ids(root_policy))
    runner_re = re.compile(
        rf"^workspace-ci-v3-(?:{class_pattern})-{UUID_RE}\.service$"
    )
    active: list[str] = []
    for unit in systemd.list_units():
        if (
            runner_re.fullmatch(unit)
            or V3_SUPERVISOR_RE.fullmatch(unit)
        ) and systemd.active(unit):
            active.append(unit)
    return sorted(active)


def _resource_claims(
    state_root: pathlib.Path = V3_PROVISIONER_STATE,
) -> list[str]:
    if not state_root.exists():
        return []
    claims: list[str] = []
    for path in sorted(state_root.glob("*.json")):
        if path.name.startswith("_"):
            continue
        record = _load(path)
        if (
            record.get("state") in {"RESERVED", "PREPARING", "ACCEPTED"}
            or record.get("resource_hold") is True
        ):
            claims.append(str(record.get("request_id", path.stem)))
    return claims


def _assert_no_execution_state(
    systemd: Systemd,
    root_policy: dict[str, Any],
    *,
    provisioner_state_root: pathlib.Path,
) -> None:
    _assert_class_controllers_inactive(systemd, root_policy)
    transients = _active_v3_transients(systemd, root_policy)
    if transients:
        raise RootActivationError(f"v3 transient/supervisor units remain: {transients}")
    claims = _resource_claims(provisioner_state_root)
    if claims:
        raise RootActivationError(f"v3 root resource claims remain: {claims}")


def verify_provisioner_socket(
    path: pathlib.Path = PROVISIONER_SOCKET,
    *,
    group_name: str = PROVISIONER_SOCKET_GROUP,
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    expected_gid = grp.getgrnam(group_name).gr_gid
    deadline = time.monotonic() + timeout_seconds
    last = "socket unavailable"
    while time.monotonic() <= deadline:
        try:
            st = path.lstat()
        except FileNotFoundError:
            last = "socket missing"
            time.sleep(0.05)
            continue
        if not stat.S_ISSOCK(st.st_mode):
            last = "path is not a Unix socket"
        elif st.st_uid != 0:
            last = f"socket uid {st.st_uid} != 0"
        elif st.st_gid != expected_gid:
            last = f"socket gid {st.st_gid} != {expected_gid}"
        elif stat.S_IMODE(st.st_mode) != 0o660:
            last = f"socket mode {oct(stat.S_IMODE(st.st_mode))} != 0o660"
        else:
            return {
                "path": str(path),
                "uid": st.st_uid,
                "gid": st.st_gid,
                "mode": "0660",
                "group": group_name,
            }
        time.sleep(0.05)
    raise RootActivationError(f"provisioner socket verification failed: {last}")


def _persist_receipt(path: pathlib.Path, receipt: dict[str, Any]) -> None:
    receipt["updated_at"] = _utcnow()
    _atomic_write(path, _canonical(receipt), mode=0o600)


def activate_root_services(
    *,
    systemd: Systemd,
    root_policy: dict[str, Any],
    install_manifest: dict[str, Any],
    install_manifest_sha256: str,
    authority_receipt: dict[str, Any],
    authority_receipt_raw: bytes,
    socket_probe: Callable[[], dict[str, Any]],
    transaction_root: pathlib.Path = MIGRATION_ROOT,
    authority_consumption_root: pathlib.Path = AUTHORITY_CONSUMPTION_ROOT,
    provisioner_state_root: pathlib.Path = V3_PROVISIONER_STATE,
) -> pathlib.Path:
    source_head = install_manifest.get("source_head")
    if not isinstance(source_head, str) or not re.fullmatch(r"[0-9a-f]{40}", source_head):
        raise RootActivationError("installed manifest source head invalid")
    if install_manifest.get("mode") != "V3_SUBSTRATE_INSTALL_INACTIVE":
        raise RootActivationError("installed manifest mode invalid")
    if install_manifest.get("runner_class_count") != 9:
        raise RootActivationError("installed manifest runner class count invalid")
    root_policy_sha256 = str(root_policy.get("root_policy_sha256", ""))
    if install_manifest.get("root_policy_sha256") != root_policy_sha256:
        raise RootActivationError("installed manifest/root policy digest mismatch")

    _validate_authority_payload(
        authority_receipt,
        expected_source_head=source_head,
        expected_install_manifest_sha256=install_manifest_sha256,
        expected_root_policy_sha256=root_policy_sha256,
    )
    _validate_private_state_dir(transaction_root, "v3 migration transaction root")
    _validate_private_state_dir(
        authority_consumption_root,
        "root activation authorization consumption root",
    )
    if systemd.active(PROVISIONER_UNIT) or systemd.active(RECONCILER_UNIT):
        raise RootActivationError("root v3 services must both be inactive before activation")
    _assert_research_gpu_contained(systemd)
    _assert_v3_units_not_enabled(systemd, root_policy)
    _assert_no_execution_state(
        systemd,
        root_policy,
        provisioner_state_root=provisioner_state_root,
    )

    marker, authority_digest = _consume_authority(
        authority_receipt,
        authority_receipt_raw,
        consumption_root=authority_consumption_root,
    )
    receipt_path = (
        transaction_root
        / f"root-activation-{authority_receipt['authorization_id']}.json"
    )
    receipt = {
        "schema_version": 1,
        "mode": "V3_ROOT_SERVICES_ACTIVATION",
        "phase": "PREPARED",
        "authorization_id": authority_receipt["authorization_id"],
        "authorization_receipt_sha256": authority_digest,
        "authorization_consumption_marker": str(marker),
        "source_head": source_head,
        "install_manifest_sha256": install_manifest_sha256,
        "root_policy_sha256": root_policy_sha256,
        "root_services": [RECONCILER_UNIT, PROVISIONER_UNIT],
        "class_controller_count": len(_class_units(root_policy)),
        "class_controllers_activated": False,
        "workflow_mutated": False,
        "legacy_v2_mutated": False,
        "containment_or_retry_authority_mutated": False,
        "research_gpu_containment_preserved": True,
        "v3_units_enabled": False,
    }
    _persist_receipt(receipt_path, receipt)

    try:
        systemd.start(RECONCILER_UNIT)
        if not systemd.active(RECONCILER_UNIT):
            raise RootActivationError("v3 reconciler failed to become active")
        _assert_research_gpu_contained(systemd)
        _assert_v3_units_not_enabled(systemd, root_policy)
        _assert_no_execution_state(
            systemd,
            root_policy,
            provisioner_state_root=provisioner_state_root,
        )
        receipt["phase"] = "RECONCILER_ATTESTED"
        _persist_receipt(receipt_path, receipt)

        systemd.start(PROVISIONER_UNIT)
        if not systemd.active(PROVISIONER_UNIT):
            raise RootActivationError("v3 provisioner failed to become active")
        socket_evidence = socket_probe()
        _assert_research_gpu_contained(systemd)
        _assert_v3_units_not_enabled(systemd, root_policy)
        _assert_no_execution_state(
            systemd,
            root_policy,
            provisioner_state_root=provisioner_state_root,
        )
        receipt["provisioner_socket"] = socket_evidence
        receipt["phase"] = "ROOT_SERVICES_ACTIVE"
        _persist_receipt(receipt_path, receipt)
        return receipt_path
    except Exception:
        if systemd.active(PROVISIONER_UNIT):
            systemd.stop(PROVISIONER_UNIT)
        if systemd.active(RECONCILER_UNIT):
            systemd.stop(RECONCILER_UNIT)
        receipt["phase"] = "ROLLED_BACK_AFTER_ACTIVATION_FAILURE"
        _persist_receipt(receipt_path, receipt)
        raise


def rollback_root_services(
    *,
    systemd: Systemd,
    root_policy: dict[str, Any],
    receipt_path: pathlib.Path,
    provisioner_state_root: pathlib.Path = V3_PROVISIONER_STATE,
) -> None:
    receipt = _load(receipt_path)
    if receipt.get("mode") != "V3_ROOT_SERVICES_ACTIVATION":
        raise RootActivationError("root activation receipt mode invalid")
    if receipt.get("class_controllers_activated") is not False:
        raise RootActivationError("root activation receipt does not prove class controllers inactive")
    _assert_no_execution_state(
        systemd,
        root_policy,
        provisioner_state_root=provisioner_state_root,
    )
    if systemd.active(PROVISIONER_UNIT):
        systemd.stop(PROVISIONER_UNIT)
    if systemd.active(RECONCILER_UNIT):
        systemd.stop(RECONCILER_UNIT)
    if systemd.active(PROVISIONER_UNIT) or systemd.active(RECONCILER_UNIT):
        raise RootActivationError("root service rollback failed")
    receipt["phase"] = "ROOT_SERVICES_ROLLED_BACK"
    _persist_receipt(receipt_path, receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--rollback", type=pathlib.Path)
    parser.add_argument("--authorization-receipt", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path, default=INSTALL_MANIFEST)
    parser.add_argument("--root-policy", type=pathlib.Path, default=ROOT_POLICY)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise RootActivationError("v3 root service activation must run as root")
    if bool(args.activate) == bool(args.rollback):
        raise RootActivationError("choose exactly one of --activate or --rollback")

    root_policy = _load(args.root_policy)
    systemd = RealSystemd()

    if args.rollback:
        rollback_root_services(
            systemd=systemd,
            root_policy=root_policy,
            receipt_path=args.rollback,
        )
        print("V3_ROOT_SERVICES_ROLLBACK=PASS")
        return 0

    if args.authorization_receipt is None:
        raise RootActivationError("--activate requires --authorization-receipt")

    reconciler.verify_installed(args.manifest)
    install_manifest_raw = args.manifest.read_bytes()
    install_manifest = _load(args.manifest)
    install_manifest_sha256 = _sha256(install_manifest_raw)
    authority, authority_raw = _validate_authority_file(
        args.authorization_receipt,
        expected_source_head=str(install_manifest.get("source_head", "")),
        expected_install_manifest_sha256=install_manifest_sha256,
        expected_root_policy_sha256=str(root_policy.get("root_policy_sha256", "")),
    )
    receipt_path = activate_root_services(
        systemd=systemd,
        root_policy=root_policy,
        install_manifest=install_manifest,
        install_manifest_sha256=install_manifest_sha256,
        authority_receipt=authority,
        authority_receipt_raw=authority_raw,
        socket_probe=verify_provisioner_socket,
    )
    print("V3_ROOT_SERVICES_ACTIVATION=PASS")
    print(f"ACTIVATION_RECEIPT={receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
