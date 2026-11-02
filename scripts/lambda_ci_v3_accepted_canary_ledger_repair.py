#!/usr/bin/env python3
"""One-time, fail-closed repair for the accepted workspace-control v3 canary ledger.

The accepted live canary GitHub job completed successfully, but generation-exclusion
rollback stopped the v3 controller before the terminal scheduler event was durably
persisted. This helper may terminalize only that exact historical ACCEPTED record,
and only after proving:
- exact GitHub run/job success from an operator-supplied proof;
- exact binding to the accepted canary source head and a fully rolled-back canary
  transaction;
- no v3 class controller is active or boot-enabled;
- v3 roots are healthy and Research GPU containment is intact;
- no v3 transient or provisioner resource claim remains.

It grants no production-cutover authority and cannot repair any other ledger record.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import uuid
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lambda_ci_policy_compiler as compiler
import lambda_ci_v3_migration_transaction as migration
import lambda_ci_v3_production_cutover as production

TARGET_CLASS = "workspace-control-control-small-v1"
TARGET_REPOSITORY = "adamtrott78/workspace-control"
TARGET_CANARY_SOURCE_HEAD = "3e8a231483413ba3a16d405ba61b55d0ab9ff3aa"
TARGET_WORKFLOW_RUN_ID = 41264356722
TARGET_GITHUB_JOB_ID = 124723948506
TARGET_GITHUB_JOB_NAME = "v3-class-canary"
TARGET_PRESTATE = "ACCEPTED"
TARGET_TERMINAL_STATE = "COMPLETED"
REPAIR_MODE = "V3_ACCEPTED_CANARY_LEDGER_TERMINALIZATION"
REPAIR_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/ledger-repair")
CONTROLLER_STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/controller/state")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
STALE_PRODUCTION_AUTHORITY_ID = "57ede177-1494-4b3d-a058-47b6b9759f62"
STALE_PRODUCTION_AUTHORITY = (
    pathlib.Path("/var/lib/workspace-ci/v3/migration")
    / f"root-production-cutover-authority-{STALE_PRODUCTION_AUTHORITY_ID}.json"
)
AUTHORITY_CONSUMPTION = (
    pathlib.Path("/var/lib/workspace-ci/v3/migration-authority")
    / f"{STALE_PRODUCTION_AUTHORITY_ID}.json"
)


class LedgerRepairError(RuntimeError):
    pass


def _load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LedgerRepairError(f"{path}: expected JSON object")
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_exact_head(repo_root: pathlib.Path, expected: str) -> None:
    actual = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if actual != expected:
        raise LedgerRepairError(f"source head mismatch: {actual} != {expected}")
    dirty = subprocess.check_output(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=no"],
        text=True,
    )
    if dirty.strip():
        raise LedgerRepairError("source tree has tracked modifications")


def _unit_enabled(unit: str) -> bool:
    return subprocess.run(
        ["systemctl", "is-enabled", "--quiet", unit],
        check=False,
    ).returncode == 0


def _assert_runtime_boundary(
    systemd: migration.Systemd,
    *,
    repo_root: pathlib.Path,
    root_policy: dict[str, Any],
    provisioner_state_root: pathlib.Path = migration.V3_PROVISIONER_STATE,
) -> None:
    if not systemd.active(migration.V3_RECONCILER_UNIT):
        raise LedgerRepairError("v3 reconciler is not active")
    if not systemd.active(migration.V3_PROVISIONER_UNIT):
        raise LedgerRepairError("v3 provisioner is not active")
    if _unit_enabled(migration.V3_RECONCILER_UNIT):
        raise LedgerRepairError("v3 reconciler unexpectedly boot-enabled")
    if _unit_enabled(migration.V3_PROVISIONER_UNIT):
        raise LedgerRepairError("v3 provisioner unexpectedly boot-enabled")

    for unit in migration.v3_controller_units(root_policy):
        if systemd.active(unit):
            raise LedgerRepairError(f"v3 class controller active during repair: {unit}")
        if _unit_enabled(unit):
            raise LedgerRepairError(f"v3 class controller boot-enabled during repair: {unit}")

    migration._assert_research_gpu_containment(systemd)
    registry = compiler.load_inputs(repo_root)["registry"]
    migration._assert_generation_drained(
        systemd,
        registry=registry,
        root_policy=root_policy,
        require_legacy_empty=False,
        require_v3_empty=True,
        state_root=provisioner_state_root,
    )


def _validate_github_proof(proof: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "repository",
        "workflow_run_id",
        "workflow_run_status",
        "workflow_run_conclusion",
        "github_job_id",
        "github_job_name",
        "github_job_status",
        "github_job_conclusion",
    }
    if set(proof) != required:
        raise LedgerRepairError("GitHub terminal proof key set invalid")
    expected = {
        "schema_version": 1,
        "repository": TARGET_REPOSITORY,
        "workflow_run_id": TARGET_WORKFLOW_RUN_ID,
        "workflow_run_status": "completed",
        "workflow_run_conclusion": "success",
        "github_job_id": TARGET_GITHUB_JOB_ID,
        "github_job_name": TARGET_GITHUB_JOB_NAME,
        "github_job_status": "completed",
        "github_job_conclusion": "success",
    }
    for key, value in expected.items():
        if proof.get(key) != value:
            raise LedgerRepairError(
                f"GitHub terminal proof mismatch: {key}={proof.get(key)!r} expected={value!r}"
            )


def _matching_canary_transactions(record: dict[str, Any]) -> list[pathlib.Path]:
    matches: list[pathlib.Path] = []
    for path in sorted(migration.MIGRATION_ROOT.glob("*/transaction.json")):
        try:
            value = _load(path)
        except (OSError, json.JSONDecodeError, LedgerRepairError):
            continue
        if value.get("mode") != "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION":
            continue
        if value.get("target_runner_class_id") != TARGET_CLASS:
            continue
        if value.get("source_head") != TARGET_CANARY_SOURCE_HEAD:
            continue
        if value.get("controller_policy_sha256") != record.get("controller_policy_sha256"):
            continue
        if value.get("workflow_blob_sha") != record.get("workflow_blob_sha"):
            continue
        if value.get("phase") != "ROLLED_BACK_LEGACY_RESTORED":
            raise LedgerRepairError(
                f"matching accepted-canary transaction is nonterminal: {path} phase={value.get('phase')}"
            )
        matches.append(path)
    if len(matches) != 1:
        raise LedgerRepairError(
            f"expected exactly one rolled-back accepted-canary transaction, found {len(matches)}"
        )
    return matches


def _assert_unconsumed_failed_production_authority(
    transaction_root: pathlib.Path = migration.MIGRATION_ROOT,
) -> None:
    if AUTHORITY_CONSUMPTION.exists():
        raise LedgerRepairError(
            "failed production authority unexpectedly has a consumption marker"
        )
    for path in transaction_root.glob("*/transaction.json"):
        try:
            value = _load(path)
        except Exception:
            continue
        if value.get("authorization_id") == STALE_PRODUCTION_AUTHORITY_ID:
            raise LedgerRepairError(
                f"failed production authority is bound to a transaction: {path}"
            )


def _remove_stale_unconsumed_authority() -> bool:
    _assert_unconsumed_failed_production_authority()
    if not STALE_PRODUCTION_AUTHORITY.exists():
        return False
    st = STALE_PRODUCTION_AUTHORITY.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise LedgerRepairError("stale production authority is not a regular file")
    if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o600:
        raise LedgerRepairError("stale production authority metadata invalid")
    STALE_PRODUCTION_AUTHORITY.unlink()
    return True


def _atomic_rewrite_preserving_owner(path: pathlib.Path, raw: bytes) -> None:
    st = path.stat()
    if not stat.S_ISREG(st.st_mode):
        raise LedgerRepairError("ledger record is not a regular file")
    if stat.S_IMODE(st.st_mode) != 0o600:
        raise LedgerRepairError("ledger record mode is not 0600")
    tmp = path.with_name(path.name + f".repair.{os.getpid()}.tmp")
    try:
        with tmp.open("wb") as handle:
            os.chmod(tmp, 0o600)
            os.fchown(handle.fileno(), st.st_uid, st.st_gid)
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


def repair(
    *,
    repo_root: pathlib.Path,
    expected_source_head: str,
    github_proof_path: pathlib.Path,
    systemd: migration.Systemd | None = None,
) -> pathlib.Path | None:
    if os.geteuid() != 0:
        raise LedgerRepairError("accepted-canary ledger repair requires root")
    _git_exact_head(repo_root, expected_source_head)
    proof = _load(github_proof_path)
    _validate_github_proof(proof)

    root_policy = _load(ROOT_POLICY)
    classes = root_policy.get("runner_classes")
    if not isinstance(classes, dict) or TARGET_CLASS not in classes:
        raise LedgerRepairError("installed root policy lacks target class")
    if classes[TARGET_CLASS].get("repository") != TARGET_REPOSITORY:
        raise LedgerRepairError("target class repository binding drift")

    live = systemd or migration.RealSystemd()
    _assert_runtime_boundary(live, repo_root=repo_root, root_policy=root_policy)

    ledger_path = (
        CONTROLLER_STATE_ROOT
        / TARGET_CLASS
        / f"scheduler-{TARGET_GITHUB_JOB_ID}.json"
    )
    if ledger_path.is_symlink() or not ledger_path.is_file():
        raise LedgerRepairError("exact accepted-canary ledger record is missing or non-regular")
    original_raw = ledger_path.read_bytes()
    record = json.loads(original_raw)
    if not isinstance(record, dict) or record.get("schema_version") != 1:
        raise LedgerRepairError("accepted-canary ledger record schema invalid")
    if record.get("runner_request_id") != TARGET_GITHUB_JOB_ID:
        raise LedgerRepairError("accepted-canary runner_request_id mismatch")
    if record.get("github_job_id") != TARGET_GITHUB_JOB_ID:
        raise LedgerRepairError("accepted-canary github_job_id mismatch")
    if record.get("workflow_run_id") != TARGET_WORKFLOW_RUN_ID:
        raise LedgerRepairError("accepted-canary workflow_run_id mismatch")
    if not isinstance(record.get("controller_policy_sha256"), str) or re.fullmatch(
        r"[0-9a-f]{64}", record["controller_policy_sha256"]
    ) is None:
        raise LedgerRepairError("accepted-canary controller policy binding invalid")
    if not isinstance(record.get("workflow_blob_sha"), str) or re.fullmatch(
        r"[0-9a-f]{40}", record["workflow_blob_sha"]
    ) is None:
        raise LedgerRepairError("accepted-canary workflow blob binding invalid")

    if record.get("state") == TARGET_TERMINAL_STATE:
        provenance = record.get("terminalization_provenance")
        if isinstance(provenance, dict) and provenance.get("mode") == REPAIR_MODE:
            production._assert_controller_ledgers_terminal(
                CONTROLLER_STATE_ROOT,
                root_policy,
            )
            return None
        raise LedgerRepairError("ledger is already terminal without expected repair provenance")
    if record.get("state") != TARGET_PRESTATE:
        raise LedgerRepairError(
            f"accepted-canary ledger state drift: {record.get('state')} != {TARGET_PRESTATE}"
        )

    matching = _matching_canary_transactions(record)
    if record.get("request_id") in migration.v3_resource_claims():
        raise LedgerRepairError("accepted-canary provisioner resource claim is still live")

    authority_removed = _remove_stale_unconsumed_authority()

    REPAIR_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(REPAIR_ROOT, 0o700)
    tx_id = str(uuid.uuid4())
    tx_dir = REPAIR_ROOT / tx_id
    tx_dir.mkdir(mode=0o700)
    backup = tx_dir / "original-ledger.json"
    backup.write_bytes(original_raw)
    os.chmod(backup, 0o600)

    now = datetime.now(timezone.utc).isoformat()
    receipt_path = tx_dir / "receipt.json"
    receipt = {
        "schema_version": 1,
        "mode": REPAIR_MODE,
        "transaction_id": tx_id,
        "phase": "PREPARED",
        "repair_source_head": expected_source_head,
        "target_runner_class_id": TARGET_CLASS,
        "accepted_canary_source_head": TARGET_CANARY_SOURCE_HEAD,
        "workflow_run_id": TARGET_WORKFLOW_RUN_ID,
        "github_job_id": TARGET_GITHUB_JOB_ID,
        "prior_state": TARGET_PRESTATE,
        "terminal_state": TARGET_TERMINAL_STATE,
        "controller_policy_sha256": record["controller_policy_sha256"],
        "workflow_blob_sha": record["workflow_blob_sha"],
        "matching_canary_transaction": str(matching[0]),
        "github_proof_sha256": _sha256(_canonical(proof)),
        "original_ledger_sha256": _sha256(original_raw),
        "stale_unconsumed_production_authority_removed": authority_removed,
        "prepared_at": now,
    }
    receipt_path.write_bytes(_canonical(receipt))
    os.chmod(receipt_path, 0o600)

    repaired = dict(record)
    repaired["state"] = TARGET_TERMINAL_STATE
    repaired["scheduler_state"] = "GITHUB_JOB_COMPLETED_SUCCESS"
    repaired["updated_at"] = now
    repaired["terminalization_provenance"] = {
        "mode": REPAIR_MODE,
        "workflow_run_id": TARGET_WORKFLOW_RUN_ID,
        "github_job_id": TARGET_GITHUB_JOB_ID,
        "github_job_conclusion": "success",
        "accepted_canary_source_head": TARGET_CANARY_SOURCE_HEAD,
        "matching_canary_transaction": str(matching[0]),
        "repaired_at": now,
    }
    repaired_raw = _canonical(repaired)
    _atomic_rewrite_preserving_owner(ledger_path, repaired_raw)

    reread = _load(ledger_path)
    if reread.get("state") != TARGET_TERMINAL_STATE:
        raise LedgerRepairError("ledger terminalization did not persist")
    provenance = reread.get("terminalization_provenance")
    if not isinstance(provenance, dict) or provenance.get("mode") != REPAIR_MODE:
        raise LedgerRepairError("ledger terminalization provenance did not persist")

    production._assert_controller_ledgers_terminal(
        CONTROLLER_STATE_ROOT,
        root_policy,
    )

    receipt["phase"] = "COMMITTED"
    receipt["repaired_ledger_sha256"] = _sha256(ledger_path.read_bytes())
    receipt["committed_at"] = datetime.now(timezone.utc).isoformat()
    receipt_path.write_bytes(_canonical(receipt))
    os.chmod(receipt_path, 0o600)
    return receipt_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--expected-source-head", required=True)
    parser.add_argument("--github-proof", type=pathlib.Path, required=True)
    args = parser.parse_args()

    receipt = repair(
        repo_root=args.repo_root.resolve(),
        expected_source_head=args.expected_source_head,
        github_proof_path=args.github_proof.resolve(),
    )
    if receipt is None:
        print("V3_ACCEPTED_CANARY_LEDGER_REPAIR=ALREADY_COMMITTED")
    else:
        print("V3_ACCEPTED_CANARY_LEDGER_REPAIR=PASS")
        print(f"LEDGER_REPAIR_RECEIPT={receipt}")
    print("V3_CONTROLLER_LEDGERS_TERMINAL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
