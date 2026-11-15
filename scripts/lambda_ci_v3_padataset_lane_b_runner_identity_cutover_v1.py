#!/usr/bin/env python3
"""Drained transactional cutover for PADataset lane-B runner identity.

The only accepted root-envelope semantic delta is lane B moving from
ci-padataset:ci-padataset to ci-padataset-2:ci-padataset, plus the matching
trusted lane-B workflow blob update. The host must be quiescent. Lane A and all
non-target controllers remain running; lane B is restarted only to reload its
trusted-workflow policy. UID-scoped pgrep/pkill safety is preserved.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import grp
import json
import os
import pathlib
import pwd
import re
import subprocess
import uuid
from typing import Any

import lambda_ci_policy_compiler as compiler
import lambda_ci_v3_reconciler as reconciler
import lambda_ci_v3_padataset_scientific_activation_v1 as base

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE_MANIFEST = pathlib.Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
EXECUTOR_ACTIONS = pathlib.Path("/etc/workspace-ci/v3/executor-actions.json")
COMPATIBILITY_MATRIX = pathlib.Path("/etc/workspace-ci/v3/compatibility-matrix.json")
DEPLOYMENT_OVERLAY = pathlib.Path("/etc/workspace-ci/v3/deployment-overlay.json")
SYSUSERS = pathlib.Path("/etc/sysusers.d/workspace-ci-v3.conf")
TMPFILES = pathlib.Path("/etc/tmpfiles.d/workspace-ci-v3.conf")
MIGRATION_PLAN_REL = pathlib.Path("architecture/lambda-ci-v3-migration-plan.v1.json")

TARGET_CLASS = reconciler.PADATASET_SCIENTIFIC_DUAL_TARGET_CLASS
TARGET_ROUTE = reconciler.PADATASET_SCIENTIFIC_DUAL_TARGET_ROUTE
TARGET_POLICY = pathlib.Path("/etc/workspace-ci/v3/controllers") / f"{TARGET_CLASS}.json"
TARGET_DROPIN = (
    pathlib.Path("/etc/systemd/system")
    / f"workspace-ci-v3-controller@{TARGET_CLASS}.service.d"
    / "identity.conf"
)
TARGET_UNIT = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
ACTIVE_RECEIPT = reconciler.PADATASET_SCIENTIFIC_DUAL_ACTIVE_RECEIPT
RECONCILER_INSTALLED = reconciler.RECONCILER_SCRIPT
RECONCILER_OVERRIDE = reconciler.RECONCILER_OVERRIDE_ACTIVE_RECEIPT
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
INSTALLED_RUNTIME = pathlib.Path("/opt/workspace-ci/v3/provisioner/lambda_ci_runtime.py")
SHARED_PROJECT_ROOT_MODES = {
    pathlib.Path("/srv/workspace-ci/padataset/jobs"): 0o750,
    pathlib.Path("/srv/workspace-ci/padataset/staging-cache"): 0o710,
    pathlib.Path("/srv/workspace-ci/padataset/logs"): 0o710,
}

STATE_ROOT = pathlib.Path(
    "/var/lib/workspace-ci/v3/padataset-scientific/lane-b-runner-identity"
)
TX_ROOT = STATE_ROOT / "transactions"
AUTHORITY_ROOT = STATE_ROOT / "authority-consumption"

OPERATION = "CUTOVER_PADATASET_LANE_B_RUNNER_IDENTITY_V1"
CURRENT_IDENTITY = {"user": "ci-padataset", "group": "ci-padataset"}
CANDIDATE_IDENTITY = {"user": "ci-padataset-2", "group": "ci-padataset"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class RunnerIdentityCutoverError(RuntimeError):
    pass


def _load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerIdentityCutoverError(f"{path}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise RunnerIdentityCutoverError(f"{path}: expected object")
    return value


def _verify_predecessor_installed() -> None:
    proc = subprocess.run(
        [
            "/usr/bin/python3",
            str(RECONCILER_INSTALLED),
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
        raise RunnerIdentityCutoverError(
            "live predecessor verification failed: "
            + (proc.stderr.strip() or proc.stdout.strip())[:1024]
        )


def _class_semantic(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(value)
        for key, value in row.items()
        if key not in {"control_plane_generation_sha256", "root_envelope_sha256"}
    }


def _validate_identity_delta(
    current_root: dict[str, Any],
    candidate_root: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    if current_root.get("host_resource_policy") != candidate_root.get("host_resource_policy"):
        raise RunnerIdentityCutoverError("host resource policy drift")
    if current_root.get("upstream_pins") != candidate_root.get("upstream_pins"):
        raise RunnerIdentityCutoverError("upstream pin drift")

    old_classes = current_root.get("runner_classes")
    new_classes = candidate_root.get("runner_classes")
    if not isinstance(old_classes, dict) or not isinstance(new_classes, dict):
        raise RunnerIdentityCutoverError("runner class maps missing")
    if set(old_classes) != set(new_classes):
        raise RunnerIdentityCutoverError("runner class set drift")
    if TARGET_CLASS not in old_classes:
        raise RunnerIdentityCutoverError("lane-B class missing")

    previous: dict[str, str] = {}
    current: dict[str, str] = {}

    for class_id in sorted(old_classes):
        old = old_classes[class_id]
        new = new_classes[class_id]
        previous[class_id] = str(old.get("root_envelope_sha256", ""))
        current[class_id] = str(new.get("root_envelope_sha256", ""))

        if class_id != TARGET_CLASS:
            if _class_semantic(old) != _class_semantic(new):
                raise RunnerIdentityCutoverError(
                    f"non-target runner class changed: {class_id}"
                )
            if previous[class_id] != current[class_id]:
                raise RunnerIdentityCutoverError(
                    f"non-target root envelope changed: {class_id}"
                )
            continue

        old_sem = _class_semantic(old)
        new_sem = _class_semantic(new)
        if old_sem.get("project_runner_identity") != CURRENT_IDENTITY:
            raise RunnerIdentityCutoverError(
                "live lane-B runner identity is not predecessor"
            )
        if new_sem.get("project_runner_identity") != CANDIDATE_IDENTITY:
            raise RunnerIdentityCutoverError(
                "candidate lane-B runner identity mismatch"
            )

        old_systemd = copy.deepcopy(old_sem.get("systemd_common"))
        new_systemd = copy.deepcopy(new_sem.get("systemd_common"))
        if not isinstance(old_systemd, dict) or not isinstance(new_systemd, dict):
            raise RunnerIdentityCutoverError("lane-B systemd common envelope missing")
        if old_systemd.get("User") != CURRENT_IDENTITY["user"]:
            raise RunnerIdentityCutoverError("live lane-B systemd User mismatch")
        if old_systemd.get("Group") != CURRENT_IDENTITY["group"]:
            raise RunnerIdentityCutoverError("live lane-B systemd Group mismatch")
        if new_systemd.get("User") != CANDIDATE_IDENTITY["user"]:
            raise RunnerIdentityCutoverError("candidate lane-B systemd User mismatch")
        if new_systemd.get("Group") != CANDIDATE_IDENTITY["group"]:
            raise RunnerIdentityCutoverError("candidate lane-B systemd Group mismatch")

        normalized = copy.deepcopy(new_sem)
        normalized["project_runner_identity"] = copy.deepcopy(CURRENT_IDENTITY)
        normalized["systemd_common"] = copy.deepcopy(new_systemd)
        normalized["systemd_common"]["User"] = CURRENT_IDENTITY["user"]
        if normalized != old_sem:
            raise RunnerIdentityCutoverError(
                "lane-B candidate contains changes beyond runner UID specialization"
            )
        if previous[class_id] == current[class_id]:
            raise RunnerIdentityCutoverError(
                "lane-B root envelope did not change after identity specialization"
            )

    return previous, current


def _repair_shared_project_roots() -> None:
    owner = pwd.getpwnam("ci-padataset")
    group = grp.getgrnam("ci-padataset")
    lane_b = pwd.getpwnam("ci-padataset-2")

    if lane_b.pw_gid != group.gr_gid:
        raise RunnerIdentityCutoverError(
            "lane-B primary group no longer matches shared PADataset group"
        )

    for path, expected_mode in SHARED_PROJECT_ROOT_MODES.items():
        if not path.is_dir():
            raise RunnerIdentityCutoverError(
                f"shared PADataset runtime root missing: {path}"
            )
        st = path.stat()
        if st.st_uid != owner.pw_uid or st.st_gid != group.gr_gid:
            raise RunnerIdentityCutoverError(
                f"shared PADataset runtime root ownership mismatch: {path}"
            )
        mode = st.st_mode & 0o777
        if mode not in {0o700, expected_mode}:
            raise RunnerIdentityCutoverError(
                f"unexpected shared PADataset runtime root mode {mode:04o}: {path}"
            )
        os.chmod(path, expected_mode)


def _verify_shared_project_roots() -> None:
    owner = pwd.getpwnam("ci-padataset")
    group = grp.getgrnam("ci-padataset")
    lane_b = pwd.getpwnam("ci-padataset-2")

    if lane_b.pw_gid != group.gr_gid:
        raise RunnerIdentityCutoverError(
            "lane-B primary group no longer matches shared PADataset group"
        )

    for path, expected_mode in SHARED_PROJECT_ROOT_MODES.items():
        st = path.stat()
        if st.st_uid != owner.pw_uid or st.st_gid != group.gr_gid:
            raise RunnerIdentityCutoverError(
                f"shared PADataset runtime root ownership mismatch: {path}"
            )
        if (st.st_mode & 0o777) != expected_mode:
            raise RunnerIdentityCutoverError(
                f"shared PADataset runtime root mode must be "
                f"{expected_mode:04o}: {path}"
            )


def _verify_uid_guards() -> None:
    source = INSTALLED_RUNTIME.read_text(encoding="utf-8")
    for token in (
        'run(["pgrep", "-u", str(row.pw_uid)], check=False)',
        'f"existing project process detected for {user}; refusing concurrency"',
        'run(["pkill", "-KILL", "-u", str(uid)], check=False)',
    ):
        if token not in source:
            raise RunnerIdentityCutoverError(
                "UID-scoped runtime safety guard changed or missing"
            )


def _candidate_artifacts(
    repo_root: pathlib.Path,
    compiled: dict[str, Any],
    live_overlay: dict[str, Any],
) -> dict[pathlib.Path, tuple[bytes, int]]:
    overlay = copy.deepcopy(live_overlay)
    lane_a = overlay.get("classes", {}).get(reconciler.PADATASET_SCIENTIFIC_TARGET_CLASS)
    lane_b = overlay.get("classes", {}).get(TARGET_CLASS)
    route_a = overlay.get("routes", {}).get(reconciler.PADATASET_SCIENTIFIC_TARGET_ROUTE)
    route_b = overlay.get("routes", {}).get(TARGET_ROUTE)
    if (
        not isinstance(lane_a, dict)
        or lane_a.get("controller_state") != "ACTIVE"
        or not isinstance(lane_b, dict)
        or lane_b.get("controller_state") != "ACTIVE"
        or not isinstance(route_a, dict)
        or route_a.get("admission_state") != "ENABLED"
        or not isinstance(route_b, dict)
        or route_b.get("admission_state") != "ENABLED"
    ):
        raise RunnerIdentityCutoverError("dual scientific topology is not ACTIVE")
    overlay["catalog_generation_sha256"] = compiled["catalog_generation_sha256"]

    migration = _load(repo_root / MIGRATION_PLAN_REL)
    target_policy = compiled["controller_projections"][TARGET_CLASS]
    target_root = compiled["root_projection"]["runner_classes"][TARGET_CLASS]
    return {
        ROOT_POLICY: (base._canonical(compiled["root_projection"]), 0o644),
        EXECUTOR_ACTIONS: (base._canonical(compiled["executor_projection"]), 0o644),
        COMPATIBILITY_MATRIX: (base._canonical(compiled["compatibility_matrix"]), 0o644),
        DEPLOYMENT_OVERLAY: (base._canonical(overlay), 0o644),
        SYSUSERS: (reconciler.render_sysusers(compiled, migration).encode(), 0o644),
        TMPFILES: (reconciler.render_tmpfiles(compiled, migration).encode(), 0o644),
        TARGET_POLICY: (base._canonical(target_policy), 0o644),
        TARGET_DROPIN: (
            reconciler.render_controller_dropin(TARGET_CLASS, target_root, migration).encode(),
            0o644,
        ),
    }


def _updated_dual_receipt(
    *,
    existing: dict[str, Any],
    source_head: str,
    padataset_main_sha: str,
    compiled: dict[str, Any],
    artifacts: dict[pathlib.Path, tuple[bytes, int]],
) -> dict[str, Any]:
    if existing.get("phase") != "ACTIVE":
        raise RunnerIdentityCutoverError("dual-lane active receipt is not ACTIVE")
    if existing.get("target_class_id") != TARGET_CLASS:
        raise RunnerIdentityCutoverError("dual-lane active receipt target mismatch")

    updated = copy.deepcopy(existing)
    updated["source_head"] = source_head
    updated["catalog_generation_sha256"] = compiled["catalog_generation_sha256"]
    updated["root_policy_sha256"] = compiled["root_projection"]["root_policy_sha256"]
    updated["root_envelope_sha256"] = {
        class_id: row["root_envelope_sha256"]
        for class_id, row in sorted(compiled["root_projection"]["runner_classes"].items())
    }
    updated["target_controller_policy_sha256"] = compiled[
        "controller_projections"
    ][TARGET_CLASS]["controller_policy_sha256"]
    updated["trusted_workflow_blob_sha"] = reconciler.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_BLOB
    updated["padataset_main_sha"] = padataset_main_sha

    overrides = updated.get("managed_artifact_overrides")
    additions = updated.get("managed_artifact_additions")
    if not isinstance(overrides, dict) or not isinstance(additions, dict):
        raise RunnerIdentityCutoverError("dual-lane managed artifact maps missing")
    for destination in reconciler.PADATASET_SCIENTIFIC_DUAL_OVERRIDE_DESTINATIONS:
        raw, _mode = artifacts[pathlib.Path(destination)]
        overrides[destination]["sha256"] = base._sha(raw)
    for destination in reconciler.PADATASET_SCIENTIFIC_DUAL_ADDITION_DESTINATIONS:
        raw, _mode = artifacts[pathlib.Path(destination)]
        additions[destination]["sha256"] = base._sha(raw)
    return updated


def _verify_runner_user() -> None:
    try:
        row = pwd.getpwnam(CANDIDATE_IDENTITY["user"])
        group = grp.getgrnam(CANDIDATE_IDENTITY["group"])
    except KeyError as exc:
        raise RunnerIdentityCutoverError(
            "lane-B runner user/group was not materialized"
        ) from exc
    if row.pw_gid != group.gr_gid:
        raise RunnerIdentityCutoverError(
            "lane-B runner primary group is not ci-padataset"
        )
    if row.pw_shell != "/usr/sbin/nologin":
        raise RunnerIdentityCutoverError("lane-B runner shell is not nologin")


def _consume_authority(value: dict[str, Any], raw: bytes) -> None:
    base._ensure_private_dir(AUTHORITY_ROOT)
    path = AUTHORITY_ROOT / f"{value['authorization_id']}.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(
            base._canonical(
                {
                    "schema_version": 1,
                    "authorization_id": value["authorization_id"],
                    "operation": value["operation"],
                    "authority_sha256": base._sha(raw),
                    "consumed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        )
        handle.flush()
        os.fsync(handle.fileno())
    os.chown(path, 0, 0)


def _prepare(
    *,
    repo_root: pathlib.Path,
    expected_head: str,
    padataset_main_sha: str,
    systemd: Any,
) -> dict[str, Any]:
    if SHA40.fullmatch(expected_head) is None or SHA40.fullmatch(padataset_main_sha) is None:
        raise RunnerIdentityCutoverError("source SHA invalid")
    repo_root = base._exact_repo(repo_root, expected_head)

    _verify_predecessor_installed()
    base._require_provisioner_active(systemd)
    base._require_provisioner_socket()
    base._require_quiescent(systemd)
    _verify_uid_guards()

    live_root = _load(ROOT_POLICY)
    live_overlay = _load(DEPLOYMENT_OVERLAY)
    dual_raw = ACTIVE_RECEIPT.read_bytes()
    dual = _load(ACTIVE_RECEIPT)
    if dual.get("phase") != "ACTIVE":
        raise RunnerIdentityCutoverError("dual-lane topology is not active")
    if live_root.get("root_policy_sha256") != dual.get("root_policy_sha256"):
        raise RunnerIdentityCutoverError("live root policy/dual receipt drift")

    live_target = _load(TARGET_POLICY)
    workflows = live_target.get("trusted_workflows")
    if not isinstance(workflows, list) or len(workflows) != 1:
        raise RunnerIdentityCutoverError("live lane-B trusted workflow set invalid")
    if workflows[0].get("blob_sha") != dual.get("trusted_workflow_blob_sha"):
        raise RunnerIdentityCutoverError("live lane-B workflow/receipt drift")

    compiled = compiler.compile_policy(repo_root)
    previous, current = _validate_identity_delta(live_root, compiled["root_projection"])
    candidate_workflows = compiled["controller_projections"][TARGET_CLASS].get(
        "trusted_workflows"
    )
    if (
        not isinstance(candidate_workflows, list)
        or len(candidate_workflows) != 1
        or candidate_workflows[0].get("blob_sha")
        != reconciler.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_BLOB
    ):
        raise RunnerIdentityCutoverError("candidate lane-B workflow binding drift")

    artifacts = _candidate_artifacts(repo_root, compiled, live_overlay)
    updated_dual = _updated_dual_receipt(
        existing=dual,
        source_head=expected_head,
        padataset_main_sha=padataset_main_sha,
        compiled=compiled,
        artifacts=artifacts,
    )
    expected_authority = {
        "source_head": expected_head,
        "padataset_main_sha": padataset_main_sha,
        "target_workflow_blob_sha": reconciler.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_BLOB,
        "current_root_policy_sha256": live_root["root_policy_sha256"],
        "candidate_root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "dual_active_receipt_sha256": base._sha(dual_raw),
        "target_class_id": TARGET_CLASS,
        "current_target_root_envelope_sha256": previous[TARGET_CLASS],
        "candidate_target_root_envelope_sha256": current[TARGET_CLASS],
        "current_runner_identity": CURRENT_IDENTITY,
        "candidate_runner_identity": CANDIDATE_IDENTITY,
    }
    return {
        "repo_root": repo_root,
        "live_root": live_root,
        "compiled": compiled,
        "artifacts": artifacts,
        "updated_dual": updated_dual,
        "expected_authority": expected_authority,
    }


def cutover(
    *,
    repo_root: pathlib.Path,
    expected_head: str,
    padataset_main_sha: str,
    authority_path: pathlib.Path,
    systemd: Any | None = None,
) -> pathlib.Path:
    if os.geteuid() != 0:
        raise RunnerIdentityCutoverError("runner-identity cutover requires root")
    systemd = systemd or base.RealSystemd()
    prepared = _prepare(
        repo_root=repo_root,
        expected_head=expected_head,
        padataset_main_sha=padataset_main_sha,
        systemd=systemd,
    )

    try:
        authority, authority_raw = base._load_authority(
            authority_path,
            operation=OPERATION,
            expected=prepared["expected_authority"],
        )
    except base.ScientificActivationError as exc:
        raise RunnerIdentityCutoverError(str(exc)) from exc

    live_root = prepared["live_root"]
    compiled = prepared["compiled"]
    artifacts = prepared["artifacts"]
    updated_dual = prepared["updated_dual"]

    class_ids = sorted(live_root["runner_classes"])
    non_target = [x for x in class_ids if x != TARGET_CLASS]
    non_target_before = base._controller_snapshot(systemd, non_target)
    target_before = systemd.show(TARGET_UNIT)
    if target_before.get("ActiveState") != "active":
        raise RunnerIdentityCutoverError("lane-B controller is not active")

    manifest_raw = BASE_MANIFEST.read_bytes()
    manifest = _load(BASE_MANIFEST)
    candidate_reconciler = (
        prepared["repo_root"] / "scripts/lambda_ci_v3_reconciler.py"
    ).read_bytes()
    reconciler_override = base._new_reconciler_override(
        source_head=expected_head,
        base_manifest=manifest,
        base_manifest_raw=manifest_raw,
        candidate_raw=candidate_reconciler,
    )

    base._ensure_private_dir(STATE_ROOT)
    base._ensure_private_dir(TX_ROOT)
    base._ensure_private_dir(AUTHORITY_ROOT)
    tx_dir = TX_ROOT / f"cutover-{uuid.uuid4()}"
    base._ensure_private_dir(tx_dir)
    mutation_paths = [
        *sorted(artifacts, key=str),
        RECONCILER_INSTALLED,
        RECONCILER_OVERRIDE,
        ACTIVE_RECEIPT,
    ]
    backups = base._backup_paths(tx_dir, mutation_paths)
    tx_path = tx_dir / "receipt.json"
    tx = {
        "schema_version": 1,
        "mode": "V3_PADATASET_LANE_B_RUNNER_IDENTITY_CUTOVER",
        "phase": "PREPARED",
        "source_head": expected_head,
        "padataset_main_sha": padataset_main_sha,
        "authorization_id": authority["authorization_id"],
        "authority_sha256": base._sha(authority_raw),
        "previous_root_policy_sha256": live_root["root_policy_sha256"],
        "candidate_root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "target_controller_before": target_before,
        "non_target_controller_snapshot_before": non_target_before,
        "backups": backups,
    }
    base._atomic_json(tx_path, tx)
    _consume_authority(authority, authority_raw)

    target_stopped = False
    provisioner_stopped = False
    try:
        systemd.stop(TARGET_UNIT)
        target_stopped = True
        systemd.stop(PROVISIONER_UNIT)
        provisioner_stopped = True
        base._require_quiescent(systemd)

        for path, (raw, mode) in artifacts.items():
            base._atomic_file(path, raw, mode)
        base._atomic_file(RECONCILER_INSTALLED, candidate_reconciler, 0o755)
        base._atomic_json(RECONCILER_OVERRIDE, reconciler_override)
        base._atomic_json(ACTIVE_RECEIPT, updated_dual)

        base._run_root_tool(["systemd-sysusers", str(SYSUSERS)])
        base._run_root_tool(["systemd-tmpfiles", "--create", str(TMPFILES)])
        _repair_shared_project_roots()
        base._run_root_tool(["systemctl", "daemon-reload"])
        _verify_runner_user()
        _verify_shared_project_roots()
        _verify_uid_guards()

        systemd.start(PROVISIONER_UNIT)
        provisioner_stopped = False
        base._require_provisioner_active(systemd)
        base._require_provisioner_socket()
        systemd.start(TARGET_UNIT)
        target_stopped = False

        target_after = systemd.show(TARGET_UNIT)
        if (
            target_after.get("ActiveState") != "active"
            or target_after.get("SubState") != "running"
        ):
            raise RunnerIdentityCutoverError("lane-B controller failed to restart")
        non_target_after = base._controller_snapshot(systemd, non_target)
        base._require_controller_snapshot_preserved(
            non_target_before,
            non_target_after,
        )
        reconciler.verify_installed(BASE_MANIFEST)

        live_after = _load(ROOT_POLICY)
        lane_b = live_after["runner_classes"][TARGET_CLASS]
        if lane_b.get("project_runner_identity") != CANDIDATE_IDENTITY:
            raise RunnerIdentityCutoverError("live lane-B runner identity did not cut over")
        if lane_b.get("systemd_common", {}).get("User") != "ci-padataset-2":
            raise RunnerIdentityCutoverError("live lane-B systemd User did not cut over")

        tx["phase"] = "COMMITTED_ACTIVE"
        tx["target_controller_after"] = target_after
        tx["non_target_controller_snapshot_after"] = non_target_after
        tx["dual_active_receipt_sha256"] = base._sha_file(ACTIVE_RECEIPT)
        tx["completed_at"] = datetime.now(timezone.utc).isoformat()
        base._atomic_json(tx_path, tx)
        return tx_path
    except BaseException as exc:
        try:
            if not provisioner_stopped:
                systemd.stop(PROVISIONER_UNIT)
            if not target_stopped:
                systemd.stop(TARGET_UNIT)
            base._restore_paths(backups)
            base._run_root_tool(["systemctl", "daemon-reload"])
            systemd.start(PROVISIONER_UNIT)
            systemd.start(TARGET_UNIT)
            _verify_predecessor_installed()
            tx["phase"] = "ROLLED_BACK"
            tx["rollback_completed"] = True
        except BaseException as rollback_exc:
            tx["phase"] = "ROLLBACK_INCOMPLETE"
            tx["rollback_completed"] = False
            tx["rollback_error"] = str(rollback_exc)
        tx["failure"] = str(exc)
        tx["failed_at"] = datetime.now(timezone.utc).isoformat()
        base._atomic_json(tx_path, tx)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--padataset-main-sha", required=True)
    parser.add_argument("--authorization-receipt", type=pathlib.Path)
    parser.add_argument("--print-authority-bindings", action="store_true")
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise RunnerIdentityCutoverError("runner-identity cutover requires root")

    if args.print_authority_bindings:
        if args.authorization_receipt is not None:
            raise RunnerIdentityCutoverError(
                "--authorization-receipt is invalid with --print-authority-bindings"
            )
        prepared = _prepare(
            repo_root=args.repo_root,
            expected_head=args.expected_head,
            padataset_main_sha=args.padataset_main_sha,
            systemd=base.RealSystemd(),
        )
        print(json.dumps(prepared["expected_authority"], indent=2, sort_keys=True))
        return 0

    if args.authorization_receipt is None:
        raise RunnerIdentityCutoverError(
            "cutover requires --authorization-receipt"
        )
    receipt = cutover(
        repo_root=args.repo_root,
        expected_head=args.expected_head,
        padataset_main_sha=args.padataset_main_sha,
        authority_path=args.authorization_receipt,
    )
    print("PADATASET_LANE_B_RUNNER_IDENTITY_CUTOVER=PASS")
    print("LANE_A_RUNNER_USER=ci-padataset")
    print("LANE_B_RUNNER_USER=ci-padataset-2")
    print("LANE_B_PRIMARY_GROUP=ci-padataset")
    print("UID_SCOPED_GUARDS=PRESERVED")
    print("SHARED_PADATASET_JOBS=0750 ci-padataset:ci-padataset")
    print("SHARED_PADATASET_STAGING_CACHE=0710 ci-padataset:ci-padataset")
    print("SHARED_PADATASET_LOGS=0710 ci-padataset:ci-padataset")
    print(f"TRANSACTION_RECEIPT={receipt}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RunnerIdentityCutoverError, base.ScientificActivationError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
