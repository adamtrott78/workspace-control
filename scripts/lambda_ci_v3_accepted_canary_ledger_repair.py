#!/usr/bin/env python3
"""Fail-closed terminalization of orphaned v3 migration-canary ledger records.

Generation-exclusion rollback can stop a class controller after the GitHub job is
already terminal but before the terminal scheduler event is persisted. Production
cutover must not weaken its nonterminal-ledger gate. This one-time repair instead
terminalizes only a closed set of known canary jobs whose GitHub terminal result and
rolled-back canary transaction are both proven exactly.

Unknown nonterminal ledger state fails closed before any ledger mutation.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import pathlib
import re
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

CANARY_SOURCE_HEAD = "3e8a231483413ba3a16d405ba61b55d0ab9ff3aa"
REPAIR_MODE = "V3_MIGRATION_CANARY_LEDGER_TERMINALIZATION"
REPAIR_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/ledger-repair")
CONTROLLER_STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/controller/state")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
ALLOWED_PRETERMINAL_STATES = {"ACCEPTED", "RUNNING"}
STALE_PRODUCTION_AUTHORITY_ID = "57ede177-1494-4b3d-a058-47b6b9759f62"
STALE_PRODUCTION_AUTHORITY = (
    pathlib.Path("/var/lib/workspace-ci/v3/migration")
    / f"root-production-cutover-authority-{STALE_PRODUCTION_AUTHORITY_ID}.json"
)
STALE_PRODUCTION_AUTHORITY_MARKER = (
    pathlib.Path("/var/lib/workspace-ci/v3/migration-authority")
    / f"{STALE_PRODUCTION_AUTHORITY_ID}.json"
)

CANARIES = (
    {
        "class_id": "workspace-control-control-small-v1",
        "repository": "adamtrott78/workspace-control",
        "workflow_run_id": 41264356722,
        "github_job_id": 124723948506,
        "github_job_name": "v3-class-canary",
        "github_job_conclusion": "success",
        "transaction_id": None,
    },
    {
        "class_id": "padataset-cpu-public-v1",
        "repository": "adamtrott78/PADataset",
        "workflow_run_id": 41418580438,
        "github_job_id": 125188348656,
        "github_job_name": "v3-class-canary",
        "github_job_conclusion": "success",
        "transaction_id": "b63ef32d-55f8-49c2-aa20-9bce412ccedf",
    },
    {
        "class_id": "padataset-gpu-single-public-v1",
        "repository": "adamtrott78/PADataset",
        "workflow_run_id": 41420426352,
        "github_job_id": 125194478681,
        "github_job_name": "v3-class-canary",
        "github_job_conclusion": "failure",
        "transaction_id": "f974ebde-388f-4d7b-a235-d41469134dfc",
    },
    {
        "class_id": "padataset-gpu-single-public-v1",
        "repository": "adamtrott78/PADataset",
        "workflow_run_id": 41425633192,
        "github_job_id": 125211444476,
        "github_job_name": "v3-class-canary",
        "github_job_conclusion": "success",
        "transaction_id": "c43f3dec-ca6b-4515-9a35-fa6622cd3d46",
    },
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


def _spec_key(spec: dict[str, Any]) -> tuple[str, int]:
    return str(spec["class_id"]), int(spec["github_job_id"])


def _validate_terminal_proofs(payload: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    if set(payload) != {"schema_version", "jobs"} or payload["schema_version"] != 1:
        raise LedgerRepairError("GitHub terminal proof envelope invalid")
    jobs = payload["jobs"]
    if not isinstance(jobs, list):
        raise LedgerRepairError("GitHub terminal proof jobs must be a list")
    expected_by_identity = {
        (str(spec["repository"]), int(spec["workflow_run_id"]), int(spec["github_job_id"])): spec
        for spec in CANARIES
    }
    if len(jobs) != len(expected_by_identity):
        raise LedgerRepairError("GitHub terminal proof job count invalid")
    proofs: dict[tuple[str, int], dict[str, Any]] = {}
    for proof in jobs:
        if not isinstance(proof, dict):
            raise LedgerRepairError("GitHub terminal proof row invalid")
        required = {
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
            raise LedgerRepairError("GitHub terminal proof row key set invalid")
        identity = (
            str(proof["repository"]),
            int(proof["workflow_run_id"]),
            int(proof["github_job_id"]),
        )
        spec = expected_by_identity.get(identity)
        if spec is None:
            raise LedgerRepairError(f"unexpected GitHub terminal proof identity: {identity}")
        if proof["workflow_run_status"] != "completed":
            raise LedgerRepairError(f"{identity}: workflow run is not terminal")
        if proof["github_job_status"] != "completed":
            raise LedgerRepairError(f"{identity}: GitHub job is not terminal")
        if proof["github_job_name"] != spec["github_job_name"]:
            raise LedgerRepairError(f"{identity}: GitHub job name mismatch")
        if proof["github_job_conclusion"] != spec["github_job_conclusion"]:
            raise LedgerRepairError(f"{identity}: GitHub job conclusion mismatch")
        if proof["workflow_run_conclusion"] != spec["github_job_conclusion"]:
            raise LedgerRepairError(f"{identity}: workflow conclusion mismatch")
        proofs[_spec_key(spec)] = proof
    if set(proofs) != {_spec_key(spec) for spec in CANARIES}:
        raise LedgerRepairError("GitHub terminal proof set incomplete")
    return proofs


def _load_nonterminal_ledgers(
    controller_state_root: pathlib.Path,
    root_policy: dict[str, Any],
) -> dict[tuple[str, int], tuple[pathlib.Path, dict[str, Any], bytes]]:
    classes = root_policy.get("runner_classes")
    if not isinstance(classes, dict):
        raise LedgerRepairError("installed root policy class set invalid")
    found: dict[tuple[str, int], tuple[pathlib.Path, dict[str, Any], bytes]] = {}
    for class_id in sorted(classes):
        class_root = controller_state_root / class_id
        if not class_root.exists():
            continue
        if class_root.is_symlink() or not class_root.is_dir():
            raise LedgerRepairError(f"{class_id}: controller state path invalid")
        for path in sorted(class_root.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                raise LedgerRepairError(f"{class_id}: controller ledger entry invalid")
            raw = path.read_bytes()
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise LedgerRepairError(f"{class_id}: controller ledger unreadable: {path.name}") from exc
            if not isinstance(record, dict) or record.get("schema_version") != 1:
                raise LedgerRepairError(f"{class_id}: controller ledger schema invalid")
            request_id = record.get("runner_request_id")
            if not isinstance(request_id, int) or request_id <= 0:
                raise LedgerRepairError(f"{class_id}: controller ledger identity invalid")
            if record.get("state") in production.TERMINAL_CONTROLLER_STATES:
                continue
            found[(class_id, request_id)] = (path, record, raw)
    return found


def _matching_transaction(spec: dict[str, Any], record: dict[str, Any]) -> pathlib.Path:
    transaction_id = spec.get("transaction_id")
    if transaction_id:
        candidates = [migration.MIGRATION_ROOT / str(transaction_id) / "transaction.json"]
    else:
        candidates = sorted(migration.MIGRATION_ROOT.glob("*/transaction.json"))

    matches: list[pathlib.Path] = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            value = _load(path)
        except (OSError, json.JSONDecodeError, LedgerRepairError):
            continue
        if value.get("mode") != "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION":
            continue
        if value.get("target_runner_class_id") != spec["class_id"]:
            continue
        if value.get("source_head") != CANARY_SOURCE_HEAD:
            continue
        if value.get("controller_policy_sha256") != record.get("controller_policy_sha256"):
            continue
        if value.get("workflow_blob_sha") != record.get("workflow_blob_sha"):
            continue
        if value.get("phase") != "ROLLED_BACK_LEGACY_RESTORED":
            raise LedgerRepairError(
                f"{spec['class_id']}/{spec['github_job_id']}: matching canary transaction "
                f"is nonterminal: {path} phase={value.get('phase')}"
            )
        matches.append(path)

    if len(matches) != 1:
        raise LedgerRepairError(
            f"{spec['class_id']}/{spec['github_job_id']}: expected exactly one "
            f"rolled-back canary transaction, found {len(matches)}"
        )
    return matches[0]


def _assert_unconsumed_failed_production_authority() -> bool:
    if STALE_PRODUCTION_AUTHORITY_MARKER.exists():
        raise LedgerRepairError("failed production authority unexpectedly consumed")
    for path in migration.MIGRATION_ROOT.glob("*/transaction.json"):
        try:
            value = _load(path)
        except Exception:
            continue
        if value.get("authorization_id") == STALE_PRODUCTION_AUTHORITY_ID:
            raise LedgerRepairError(
                f"failed production authority unexpectedly bound to transaction: {path}"
            )
    if not STALE_PRODUCTION_AUTHORITY.exists():
        return False
    st = STALE_PRODUCTION_AUTHORITY.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise LedgerRepairError("stale production authority is not a regular file")
    if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o600:
        raise LedgerRepairError("stale production authority metadata invalid")
    return True


def _atomic_rewrite_preserving_owner(path: pathlib.Path, raw: bytes) -> None:
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o600:
        raise LedgerRepairError("ledger record metadata invalid")
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
        raise LedgerRepairError("migration-canary ledger repair requires root")
    _git_exact_head(repo_root, expected_source_head)
    proofs = _validate_terminal_proofs(_load(github_proof_path))

    root_policy = _load(ROOT_POLICY)
    live = systemd or migration.RealSystemd()
    _assert_runtime_boundary(live, repo_root=repo_root, root_policy=root_policy)

    nonterminal = _load_nonterminal_ledgers(CONTROLLER_STATE_ROOT, root_policy)
    if not nonterminal:
        production._assert_controller_ledgers_terminal(CONTROLLER_STATE_ROOT, root_policy)
        return None

    spec_by_key = {_spec_key(spec): spec for spec in CANARIES}
    unknown = sorted(set(nonterminal) - set(spec_by_key))
    if unknown:
        rendered = ", ".join(
            f"{class_id}/{request_id}:{nonterminal[(class_id, request_id)][1].get('state')}"
            for class_id, request_id in unknown
        )
        raise LedgerRepairError(
            "unknown nonterminal controller ledger blocks bounded repair: " + rendered
        )

    claims = set(migration.v3_resource_claims())
    prepared: list[dict[str, Any]] = []
    for key in sorted(nonterminal):
        path, record, raw = nonterminal[key]
        spec = spec_by_key[key]
        proof = proofs[key]
        if record.get("github_job_id") != spec["github_job_id"]:
            raise LedgerRepairError(f"{key}: github_job_id mismatch")
        if record.get("workflow_run_id") != spec["workflow_run_id"]:
            raise LedgerRepairError(f"{key}: workflow_run_id mismatch")
        if record.get("state") not in ALLOWED_PRETERMINAL_STATES:
            raise LedgerRepairError(
                f"{key}: nonterminal state is not safely repairable: {record.get('state')}"
            )
        digest = record.get("controller_policy_sha256")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise LedgerRepairError(f"{key}: controller policy binding invalid")
        blob = record.get("workflow_blob_sha")
        if not isinstance(blob, str) or re.fullmatch(r"[0-9a-f]{40}", blob) is None:
            raise LedgerRepairError(f"{key}: workflow blob binding invalid")
        request_id = record.get("request_id")
        if request_id in claims:
            raise LedgerRepairError(f"{key}: provisioner resource claim still live")
        tx = _matching_transaction(spec, record)
        terminal_state = (
            "COMPLETED" if proof["github_job_conclusion"] == "success" else "FAILED"
        )
        prepared.append(
            {
                "key": key,
                "path": path,
                "record": record,
                "raw": raw,
                "spec": spec,
                "proof": proof,
                "transaction": tx,
                "terminal_state": terminal_state,
            }
        )

    stale_authority_present = _assert_unconsumed_failed_production_authority()

    REPAIR_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(REPAIR_ROOT, 0o700)
    tx_id = str(uuid.uuid4())
    tx_dir = REPAIR_ROOT / tx_id
    tx_dir.mkdir(mode=0o700)

    receipt_path = tx_dir / "receipt.json"
    receipt = {
        "schema_version": 1,
        "mode": REPAIR_MODE,
        "transaction_id": tx_id,
        "phase": "PREPARED",
        "repair_source_head": expected_source_head,
        "canary_source_head": CANARY_SOURCE_HEAD,
        "stale_unconsumed_production_authority_id": (
            STALE_PRODUCTION_AUTHORITY_ID if stale_authority_present else None
        ),
        "repairs": [],
        "prepared_at": datetime.now(timezone.utc).isoformat(),
    }

    for item in prepared:
        class_id, request_id = item["key"]
        backup = tx_dir / f"{class_id}-{request_id}.original.json"
        backup.write_bytes(item["raw"])
        os.chmod(backup, 0o600)
        receipt["repairs"].append(
            {
                "runner_class_id": class_id,
                "runner_request_id": request_id,
                "prior_state": item["record"]["state"],
                "terminal_state": item["terminal_state"],
                "workflow_run_id": item["spec"]["workflow_run_id"],
                "github_job_id": item["spec"]["github_job_id"],
                "github_job_conclusion": item["proof"]["github_job_conclusion"],
                "controller_policy_sha256": item["record"]["controller_policy_sha256"],
                "workflow_blob_sha": item["record"]["workflow_blob_sha"],
                "matching_canary_transaction": str(item["transaction"]),
                "original_ledger_sha256": _sha256(item["raw"]),
                "backup_path": str(backup),
            }
        )
    receipt_path.write_bytes(_canonical(receipt))
    os.chmod(receipt_path, 0o600)

    if stale_authority_present:
        STALE_PRODUCTION_AUTHORITY.unlink()

    now = datetime.now(timezone.utc).isoformat()
    for item in prepared:
        repaired = dict(item["record"])
        repaired["state"] = item["terminal_state"]
        repaired["scheduler_state"] = (
            "GITHUB_JOB_COMPLETED_SUCCESS"
            if item["terminal_state"] == "COMPLETED"
            else "GITHUB_JOB_COMPLETED_FAILURE"
        )
        repaired["updated_at"] = now
        repaired["terminalization_provenance"] = {
            "mode": REPAIR_MODE,
            "workflow_run_id": item["spec"]["workflow_run_id"],
            "github_job_id": item["spec"]["github_job_id"],
            "github_job_conclusion": item["proof"]["github_job_conclusion"],
            "canary_source_head": CANARY_SOURCE_HEAD,
            "matching_canary_transaction": str(item["transaction"]),
            "repaired_at": now,
        }
        _atomic_rewrite_preserving_owner(item["path"], _canonical(repaired))

    production._assert_controller_ledgers_terminal(
        CONTROLLER_STATE_ROOT,
        root_policy,
    )

    receipt["phase"] = "COMMITTED"
    receipt["committed_at"] = datetime.now(timezone.utc).isoformat()
    for row in receipt["repairs"]:
        path = (
            CONTROLLER_STATE_ROOT
            / row["runner_class_id"]
            / f"scheduler-{row['runner_request_id']}.json"
        )
        row["repaired_ledger_sha256"] = _sha256(path.read_bytes())
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
        print("V3_MIGRATION_CANARY_LEDGER_REPAIR=ALREADY_TERMINAL")
    else:
        print("V3_MIGRATION_CANARY_LEDGER_REPAIR=PASS")
        print(f"LEDGER_REPAIR_RECEIPT={receipt}")
    print("V3_CONTROLLER_LEDGERS_TERMINAL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
