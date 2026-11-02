#!/usr/bin/env python3
"""One-time fail-closed repair for orphaned production-validation v3 ledgers.

A rolled-back production validation can stop the v3 controller after GitHub has
already reached a terminal job conclusion but before that terminal scheduler event
is durably persisted. Production preflight must continue to reject arbitrary
nonterminal history. This helper terminalizes only exact, previously observed,
fully rolled-back production-validation jobs with independent GitHub terminal proof.
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

TARGET_CLASS = "workspace-control-control-small-v1"
TARGET_ROUTE = "workspace-control:control-validation"
TARGET_REPOSITORY = "adamtrott78/workspace-control"
REPAIR_MODE = "V3_ROLLED_BACK_PRODUCTION_VALIDATION_LEDGER_TERMINALIZATION"
REPAIR_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/ledger-repair")
CONTROLLER_STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/controller/state")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
ALLOWED_PRETERMINAL_STATES = {"ACCEPTED", "RUNNING"}

KNOWN_HISTORY = (
    {
        "workflow_run_id": 41466656949,
        "github_job_id": 125349219134,
        "github_job_conclusion": "cancelled",
        "source_head": "559c6186b44f17d4b83cb9267d554b355cda2ef7",
        "production_generation_sha256": "dd381c8748df079fb5e3d3479ba9f6fd8b8223579358bf58f5984fbe33a09ced",
        "transaction_id": "c4c11247-0883-4eab-91fd-3b5306b23de6",
    },
    {
        "workflow_run_id": 41487908880,
        "github_job_id": 125422978205,
        "github_job_conclusion": "failure",
        "source_head": "dd91ab09db74948354afcc538224490f0fa95a13",
        "production_generation_sha256": "b93a3cd050900c3d99e05e316e018cfc8b0cb8eb4208f4a077edcaefe3c72fe8",
        "transaction_id": "dcdc0961-9b16-45da-8473-d0ddd3595fb2",
    },
)

STALE_AUTHORITY_ID = "ba50aba4-3a3f-4923-b302-d3d518277ad1"
STALE_AUTHORITY = (
    pathlib.Path("/var/lib/workspace-ci/v3/migration")
    / f"root-production-cutover-authority-{STALE_AUTHORITY_ID}.json"
)
STALE_AUTHORITY_MARKER = (
    pathlib.Path("/var/lib/workspace-ci/v3/migration-authority")
    / f"{STALE_AUTHORITY_ID}.json"
)


class RepairError(RuntimeError):
    pass


def _load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RepairError(f"{path}: expected JSON object")
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_exact_head(repo_root: pathlib.Path, expected: str) -> None:
    actual = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != expected:
        raise RepairError(f"source head mismatch: {actual} != {expected}")
    dirty = subprocess.check_output(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=no"],
        text=True,
    )
    if dirty.strip():
        raise RepairError("source tree has tracked modifications")


def _unit_enabled(unit: str) -> bool:
    return subprocess.run(
        ["systemctl", "is-enabled", "--quiet", unit], check=False
    ).returncode == 0


def _assert_runtime_boundary(
    systemd: migration.Systemd,
    *,
    repo_root: pathlib.Path,
    root_policy: dict[str, Any],
) -> None:
    if not systemd.active(migration.V3_RECONCILER_UNIT):
        raise RepairError("v3 reconciler is not active")
    if not systemd.active(migration.V3_PROVISIONER_UNIT):
        raise RepairError("v3 provisioner is not active")
    if _unit_enabled(migration.V3_RECONCILER_UNIT):
        raise RepairError("v3 reconciler unexpectedly boot-enabled")
    if _unit_enabled(migration.V3_PROVISIONER_UNIT):
        raise RepairError("v3 provisioner unexpectedly boot-enabled")
    for unit in migration.v3_controller_units(root_policy):
        if systemd.active(unit):
            raise RepairError(f"v3 class controller active during repair: {unit}")
        if _unit_enabled(unit):
            raise RepairError(f"v3 class controller boot-enabled during repair: {unit}")
    migration._assert_research_gpu_containment(systemd)
    registry = compiler.load_inputs(repo_root)["registry"]
    migration._assert_generation_drained(
        systemd,
        registry=registry,
        root_policy=root_policy,
        require_legacy_empty=False,
        require_v3_empty=True,
        state_root=migration.V3_PROVISIONER_STATE,
    )


def _validate_proofs(payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    if set(payload) != {"schema_version", "jobs"} or payload["schema_version"] != 1:
        raise RepairError("GitHub proof envelope invalid")
    jobs = payload["jobs"]
    if not isinstance(jobs, list) or len(jobs) != len(KNOWN_HISTORY):
        raise RepairError("GitHub proof set invalid")
    expected = {int(item["github_job_id"]): item for item in KNOWN_HISTORY}
    out: dict[int, dict[str, Any]] = {}
    for proof in jobs:
        if not isinstance(proof, dict):
            raise RepairError("GitHub proof row invalid")
        required = {
            "repository", "workflow_run_id", "workflow_run_status",
            "workflow_run_conclusion", "github_job_id", "github_job_status",
            "github_job_conclusion",
        }
        if set(proof) != required:
            raise RepairError("GitHub proof row key set invalid")
        job_id = int(proof["github_job_id"])
        spec = expected.get(job_id)
        if spec is None:
            raise RepairError(f"unexpected GitHub job proof: {job_id}")
        if proof["repository"] != TARGET_REPOSITORY:
            raise RepairError(f"{job_id}: repository mismatch")
        if int(proof["workflow_run_id"]) != int(spec["workflow_run_id"]):
            raise RepairError(f"{job_id}: workflow run mismatch")
        if proof["workflow_run_status"] != "completed" or proof["github_job_status"] != "completed":
            raise RepairError(f"{job_id}: GitHub evidence is nonterminal")
        if proof["workflow_run_conclusion"] != spec["github_job_conclusion"]:
            raise RepairError(f"{job_id}: workflow conclusion mismatch")
        if proof["github_job_conclusion"] != spec["github_job_conclusion"]:
            raise RepairError(f"{job_id}: job conclusion mismatch")
        out[job_id] = proof
    if set(out) != set(expected):
        raise RepairError("GitHub proof set incomplete")
    return out


def _nonterminal_ledgers(
    state_root: pathlib.Path, root_policy: dict[str, Any]
) -> dict[tuple[str, int], tuple[pathlib.Path, dict[str, Any], bytes]]:
    classes = root_policy.get("runner_classes")
    if not isinstance(classes, dict):
        raise RepairError("root policy runner class set invalid")
    found: dict[tuple[str, int], tuple[pathlib.Path, dict[str, Any], bytes]] = {}
    for class_id in sorted(classes):
        class_root = state_root / class_id
        if not class_root.exists():
            continue
        if class_root.is_symlink() or not class_root.is_dir():
            raise RepairError(f"{class_id}: controller state root invalid")
        for path in sorted(class_root.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                raise RepairError(f"{class_id}: controller ledger entry invalid")
            raw = path.read_bytes()
            record = json.loads(raw)
            if not isinstance(record, dict) or record.get("schema_version") != 1:
                raise RepairError(f"{class_id}: controller ledger schema invalid")
            request_id = record.get("runner_request_id")
            if not isinstance(request_id, int) or request_id <= 0:
                raise RepairError(f"{class_id}: controller ledger identity invalid")
            if record.get("state") in production.TERMINAL_CONTROLLER_STATES:
                continue
            found[(class_id, request_id)] = (path, record, raw)
    return found


def _validate_transaction(spec: dict[str, Any], record: dict[str, Any]) -> pathlib.Path:
    path = (
        migration.MIGRATION_ROOT
        / str(spec["transaction_id"])
        / "transaction.json"
    )
    if not path.is_file():
        raise RepairError(f"production rollback transaction missing: {path}")
    tx = _load(path)
    required = {
        "schema_version": 1,
        "mode": "V3_PRODUCTION_GENERATION_CUTOVER",
        "transaction_id": spec["transaction_id"],
        "source_head": spec["source_head"],
        "production_generation_sha256": spec["production_generation_sha256"],
        "phase": "ROLLED_BACK_LEGACY_RESTORED",
    }
    for key, expected in required.items():
        if tx.get(key) != expected:
            raise RepairError(
                f"{spec['github_job_id']}: production transaction binding mismatch: {key}"
            )
    policies = tx.get("controller_policy_sha256")
    if not isinstance(policies, dict) or policies.get(TARGET_CLASS) != record.get(
        "controller_policy_sha256"
    ):
        raise RepairError(
            f"{spec['github_job_id']}: controller policy binding mismatch"
        )
    bindings = tx.get("workflow_bindings")
    if not isinstance(bindings, dict):
        raise RepairError(f"{spec['github_job_id']}: workflow bindings missing")
    route = bindings.get(TARGET_ROUTE)
    if not isinstance(route, dict) or route.get("new_blob_sha") != record.get(
        "workflow_blob_sha"
    ):
        raise RepairError(
            f"{spec['github_job_id']}: workflow blob binding mismatch"
        )
    return path


def _terminal_state(conclusion: str) -> str:
    return {
        "success": "COMPLETED",
        "failure": "FAILED",
        "cancelled": "CANCELED",
    }[conclusion]


def _assert_stale_authority_unconsumed() -> bool:
    if STALE_AUTHORITY_MARKER.exists():
        raise RepairError("failed prepare authority unexpectedly has consumption marker")
    for path in migration.MIGRATION_ROOT.glob("*/transaction.json"):
        try:
            value = _load(path)
        except Exception:
            continue
        if value.get("authorization_id") == STALE_AUTHORITY_ID:
            raise RepairError(
                f"failed prepare authority unexpectedly bound to transaction: {path}"
            )
    if not STALE_AUTHORITY.exists():
        return False
    st = STALE_AUTHORITY.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise RepairError("failed prepare authority is not a regular file")
    if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o600:
        raise RepairError("failed prepare authority metadata invalid")
    return True


def _atomic_rewrite(path: pathlib.Path, raw: bytes) -> None:
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o600:
        raise RepairError("controller ledger metadata invalid")
    tmp = path.with_name(path.name + f".repair.{os.getpid()}.tmp")
    try:
        with tmp.open("wb") as handle:
            os.chmod(tmp, 0o600)
            os.fchown(handle.fileno(), st.st_uid, st.st_gid)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
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
        raise RepairError("production-validation ledger repair requires root")
    _git_exact_head(repo_root, expected_source_head)
    proofs = _validate_proofs(_load(github_proof_path))
    root_policy = _load(ROOT_POLICY)
    live = systemd or migration.RealSystemd()
    _assert_runtime_boundary(live, repo_root=repo_root, root_policy=root_policy)

    nonterminal = _nonterminal_ledgers(CONTROLLER_STATE_ROOT, root_policy)
    if not nonterminal:
        production._assert_controller_ledgers_terminal(
            CONTROLLER_STATE_ROOT, root_policy
        )
        return None

    known = {
        (TARGET_CLASS, int(item["github_job_id"])): item
        for item in KNOWN_HISTORY
    }
    unknown = sorted(set(nonterminal) - set(known))
    if unknown:
        rendered = ", ".join(
            f"{class_id}/{request_id}:{nonterminal[(class_id, request_id)][1].get('state')}"
            for class_id, request_id in unknown
        )
        raise RepairError(
            "unknown nonterminal controller ledger blocks bounded repair: " + rendered
        )

    claims = set(migration.v3_resource_claims())
    prepared: list[dict[str, Any]] = []
    for key in sorted(nonterminal):
        path, record, raw = nonterminal[key]
        spec = known[key]
        proof = proofs[int(spec["github_job_id"])]
        if record.get("state") not in ALLOWED_PRETERMINAL_STATES:
            raise RepairError(
                f"{key}: nonterminal state is not safely repairable: {record.get('state')}"
            )
        if record.get("github_job_id") != spec["github_job_id"]:
            raise RepairError(f"{key}: github_job_id mismatch")
        if record.get("workflow_run_id") != spec["workflow_run_id"]:
            raise RepairError(f"{key}: workflow_run_id mismatch")
        if record.get("request_id") in claims:
            raise RepairError(f"{key}: live provisioner resource claim remains")
        if re.fullmatch(
            r"[0-9a-f]{64}", str(record.get("controller_policy_sha256", ""))
        ) is None:
            raise RepairError(f"{key}: controller policy digest invalid")
        if re.fullmatch(
            r"[0-9a-f]{40}", str(record.get("workflow_blob_sha", ""))
        ) is None:
            raise RepairError(f"{key}: workflow blob digest invalid")
        tx_path = _validate_transaction(spec, record)
        prepared.append(
            {
                "key": key,
                "path": path,
                "record": record,
                "raw": raw,
                "spec": spec,
                "proof": proof,
                "transaction": tx_path,
                "terminal_state": _terminal_state(
                    str(spec["github_job_conclusion"])
                ),
            }
        )

    stale_authority = _assert_stale_authority_unconsumed()

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
        "stale_unconsumed_production_authority_id": (
            STALE_AUTHORITY_ID if stale_authority else None
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
                "github_job_conclusion": item["proof"]["github_job_conclusion"],
                "rolled_back_production_transaction": str(item["transaction"]),
                "original_ledger_sha256": _sha256(item["raw"]),
                "backup_path": str(backup),
            }
        )
    receipt_path.write_bytes(_canonical(receipt))
    os.chmod(receipt_path, 0o600)

    if stale_authority:
        STALE_AUTHORITY.unlink()

    now = datetime.now(timezone.utc).isoformat()
    for item in prepared:
        repaired = dict(item["record"])
        repaired["state"] = item["terminal_state"]
        repaired["scheduler_state"] = (
            "GITHUB_JOB_" + str(item["proof"]["github_job_conclusion"]).upper()
        )
        repaired["updated_at"] = now
        repaired["terminalization_provenance"] = {
            "mode": REPAIR_MODE,
            "workflow_run_id": item["spec"]["workflow_run_id"],
            "github_job_id": item["spec"]["github_job_id"],
            "github_job_conclusion": item["proof"]["github_job_conclusion"],
            "rolled_back_production_transaction": str(item["transaction"]),
            "repaired_at": now,
        }
        _atomic_rewrite(item["path"], _canonical(repaired))

    production._assert_controller_ledgers_terminal(
        CONTROLLER_STATE_ROOT, root_policy
    )

    receipt["phase"] = "COMMITTED"
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
        print("V3_PRODUCTION_VALIDATION_LEDGER_REPAIR=ALREADY_TERMINAL")
    else:
        print("V3_PRODUCTION_VALIDATION_LEDGER_REPAIR=PASS")
        print(f"LEDGER_REPAIR_RECEIPT={receipt}")
    print("V3_CONTROLLER_LEDGERS_TERMINAL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
