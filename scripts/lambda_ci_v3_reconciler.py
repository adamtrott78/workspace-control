#!/usr/bin/env python3
"""Install and attest the Lambda CI v3 substrate without activation authority.

The APPLY_INACTIVE transaction is deliberately narrower than migration/cutover:
it may create v3 Unix identities, directories, immutable binaries, compiled
policy projections, and systemd definitions. It never starts/enables/restarts a
v3 class controller, never edits a workflow, never touches a v2 unit/scale set,
and never clears containment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
from typing import Any

import lambda_ci_policy_compiler as compiler
import lambda_ci_v3_control_planes as planes


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION_PATH = pathlib.Path("architecture/lambda-ci-v3-migration-plan.v1.json")
OVERLAY_PATH = pathlib.Path("architecture/lambda-ci-deployment-overlay.v1.json")
V3_CONFIG_ROOT = pathlib.Path("/etc/workspace-ci/v3")
V3_CONTROLLER_BINARY = pathlib.Path(
    "/opt/workspace-ci/v3/controller/lambda-ci-controller-v3"
)
V3_PROVISIONER_ROOT = pathlib.Path("/opt/workspace-ci/v3/provisioner")
V3_RECONCILER_ROOT = pathlib.Path("/opt/workspace-ci/v3/reconciler")
V3_CACHE_ROOT = pathlib.Path("/opt/workspace-ci/v3/cache-manager")
V3_CANARY_ROOT = pathlib.Path("/opt/workspace-ci/v3/canary")
V3_PAYLOAD_ROOT = pathlib.Path("/opt/workspace-ci/v3/payload")
V3_STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/controller/state")
V3_CREDENTIAL_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/credentials")
V3_SOCKET_GROUP = "workspace-ci-v3-provisioner"

MANAGED_SYSTEMD = {
    "workspace-ci-v3-provisioner.service":
        "systemd/workspace-ci-v3-provisioner.service",
    "workspace-ci-v3-controller@.service":
        "systemd/workspace-ci-v3-controller@.service",
    "workspace-ci-v3-reconciler.service":
        "systemd/workspace-ci-v3-reconciler.service",
}


class ReconcileError(RuntimeError):
    pass


def _json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReconcileError(f"{path}: expected JSON object")
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _project_groups(migration: dict[str, Any]) -> dict[str, str]:
    groups = migration["controller_identity"]["project_credential_groups"]
    if set(groups) != {"workspace-control", "padataset", "research-engine"}:
        raise ReconcileError("project credential group set drifted")
    if len(set(groups.values())) != len(groups):
        raise ReconcileError("project credential groups must be unique")
    return dict(groups)


def render_sysusers(
    compiled: dict[str, Any],
    migration: dict[str, Any],
) -> str:
    groups = _project_groups(migration)
    classes = compiled["root_projection"]["runner_classes"]
    users: dict[str, str] = {}
    broker_users: dict[str, tuple[str, str]] = {}
    lines = [
        "# Generated from compiled Lambda CI v3 root policy.\n",
        f"g {V3_SOCKET_GROUP} -\n",
    ]
    for group in sorted(groups.values()):
        lines.append(f"g {group} -\n")
    for class_id, policy in sorted(classes.items()):
        user = policy["controller_peer"]["unix_user"]
        project = policy["project_id"]
        if user in users:
            raise ReconcileError(
                f"controller Unix user {user} reused by {users[user]} and {class_id}"
            )
        users[user] = class_id
        home = V3_STATE_ROOT / class_id
        lines.append(
            f'u {user} - "Workspace CI v3 {class_id}" {home} /usr/sbin/nologin\n'
        )
        lines.append(f"m {user} {V3_SOCKET_GROUP}\n")
        lines.append(f"m {user} {groups[project]}\n")

        broker = policy.get("payload_broker_identity")
        if broker is not None:
            if not isinstance(broker, dict) or set(broker) != {"user", "group"}:
                raise ReconcileError(f"{class_id}: payload broker identity invalid")
            broker_user = str(broker["user"])
            broker_group = str(broker["group"])
            if broker_user == policy["project_runner_identity"]["user"]:
                raise ReconcileError(
                    f"{class_id}: payload broker user equals runner user"
                )
            if broker_group != policy["project_runner_identity"]["group"]:
                raise ReconcileError(
                    f"{class_id}: payload broker group differs from runner group"
                )
            if broker_user in users:
                raise ReconcileError(
                    f"{class_id}: payload broker user collides with controller user"
                )
            prior = broker_users.get(broker_user)
            current = (project, broker_group)
            if prior is not None and prior != current:
                raise ReconcileError(
                    f"payload broker Unix user {broker_user} reused across identities"
                )
            broker_users[broker_user] = current

    if len(users) != 9:
        raise ReconcileError(f"expected nine unique class users, got {len(users)}")

    for broker_user, (project, broker_group) in sorted(broker_users.items()):
        lines.append(
            f'u {broker_user} - "Workspace CI v3 offline payload {project}" '
            "- /usr/sbin/nologin\n"
        )
        lines.append(f"m {broker_user} {broker_group}\n")
    return "".join(lines)

def render_tmpfiles(
    compiled: dict[str, Any],
    migration: dict[str, Any],
) -> str:
    groups = _project_groups(migration)
    classes = compiled["root_projection"]["runner_classes"]
    lines = [
        "# Generated Lambda CI v3 disjoint runtime/state layout.\n",
        "d /run/workspace-ci/v3 0711 root root -\n",
        "d /run/workspace-ci/v3/provisioner 0700 root root -\n",
        "d /run/workspace-ci/v3/provisioner/jit 0700 root root -\n",
        "d /run/workspace-ci-v3-payload 0711 root root -\n",
        "d /var/lib/workspace-ci/v3 0711 root root -\n",
        "d /var/lib/workspace-ci/v3/provisioner 0700 root root -\n",
        "d /var/lib/workspace-ci/v3/migration 0700 root root -\n",
        "d /var/lib/workspace-ci/v3/migration-authority 0700 root root -\n",
        "d /var/lib/workspace-ci/v3/controller 0711 root root -\n",
        "d /var/lib/workspace-ci/v3/controller/state 0711 root root -\n",
        "d /var/lib/workspace-ci/v3/credentials 0711 root root -\n",
    ]
    for project, group in sorted(groups.items()):
        lines.append(
            f"d /var/lib/workspace-ci/v3/credentials/{project} 0750 root {group} -\n"
        )
    for class_id, policy in sorted(classes.items()):
        user = policy["controller_peer"]["unix_user"]
        lines.append(
            f"d /var/lib/workspace-ci/v3/controller/state/{class_id} "
            f"0700 {user} {user} -\n"
        )
    return "".join(lines)


def render_controller_dropin(
    class_id: str,
    policy: dict[str, Any],
    migration: dict[str, Any],
) -> str:
    groups = _project_groups(migration)
    project = policy["project_id"]
    user = policy["controller_peer"]["unix_user"]
    credential_env = V3_CREDENTIAL_ROOT / project / "controller.env"
    return (
        "[Service]\n"
        f"User={user}\n"
        f"Group={groups[project]}\n"
        f"SupplementaryGroups={V3_SOCKET_GROUP}\n"
        f"EnvironmentFile=-{credential_env}\n"
    )


def _write(
    stage: pathlib.Path,
    destination: pathlib.Path,
    raw: bytes,
    mode: int,
    entries: list[dict[str, Any]],
) -> None:
    if not destination.is_absolute():
        raise ReconcileError(f"managed destination is not absolute: {destination}")
    target = stage / destination.relative_to("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    target.chmod(mode)
    entries.append({
        "destination": str(destination),
        "sha256": _sha256(raw),
        "mode": f"{mode:04o}",
    })


def _installed_overlay(
    compiled: dict[str, Any],
    base: dict[str, Any],
) -> dict[str, Any]:
    model = planes.ReconciliationPlaneModel(compiled=compiled, overlay=base)
    after = model.install_generation()
    model.assert_no_activation_delta(base, after)
    for class_id, state in after["classes"].items():
        if state["install_state"] != "INSTALLED":
            raise ReconcileError(f"{class_id}: install state not INSTALLED")
        if state["controller_state"] != base["classes"][class_id]["controller_state"]:
            raise ReconcileError(f"{class_id}: controller activation delta")
    return after


def _source_files(repo_root: pathlib.Path) -> list[tuple[pathlib.Path, pathlib.Path, int]]:
    return [
        (
            repo_root / "scripts/lambda_ci_v3_provisioner.py",
            V3_PROVISIONER_ROOT / "lambda_ci_v3_provisioner.py",
            0o755,
        ),
        (
            repo_root / "scripts/lambda_ci_v3_spec.py",
            V3_PROVISIONER_ROOT / "lambda_ci_v3_spec.py",
            0o644,
        ),
        (
            repo_root / "scripts/lambda_ci_runtime.py",
            V3_PROVISIONER_ROOT / "lambda_ci_runtime.py",
            0o644,
        ),
        (
            repo_root / "scripts/lambda_ci_multirepo.py",
            V3_PROVISIONER_ROOT / "lambda_ci_multirepo.py",
            0o644,
        ),
        (
            repo_root / "scripts/lambda_ci_cuda_oom_probe.py",
            V3_PROVISIONER_ROOT / "trusted-probes/lambda_ci_cuda_oom_probe.py",
            0o555,
        ),
        (
            repo_root / "scripts/lambda_ci_dual_timeout_probe.py",
            V3_PROVISIONER_ROOT / "trusted-probes/lambda_ci_dual_timeout_probe.py",
            0o555,
        ),
        (
            repo_root / "scripts/lambda_ci_dual_cuda_oom_probe.py",
            V3_PROVISIONER_ROOT / "trusted-probes/lambda_ci_dual_cuda_oom_probe.py",
            0o555,
        ),
        (
            repo_root / "scripts/lambda_ci_trusted_cache.py",
            V3_CACHE_ROOT / "lambda_ci_trusted_cache.py",
            0o555,
        ),
        (
            repo_root / "scripts/lambda_ci_v3_canary_probe.py",
            V3_CANARY_ROOT / "lambda_ci_v3_canary_probe.py",
            0o555,
        ),
        (
            repo_root / "scripts/lambda_ci_v3_payload_broker.py",
            V3_PAYLOAD_ROOT / "lambda_ci_v3_payload_broker.py",
            0o555,
        ),
        (
            repo_root / "scripts/lambda_ci_v3_payload_exec.py",
            V3_PAYLOAD_ROOT / "lambda_ci_v3_payload_exec.py",
            0o555,
        ),
        (
            repo_root / "scripts/lambda_ci_v3_reconciler.py",
            V3_RECONCILER_ROOT / "lambda_ci_v3_reconciler.py",
            0o755,
        ),
        (
            repo_root / "scripts/lambda_ci_v3_root_activation.py",
            V3_RECONCILER_ROOT / "lambda_ci_v3_root_activation.py",
            0o555,
        ),
        (
            repo_root / "scripts/lambda_ci_policy_compiler.py",
            V3_RECONCILER_ROOT / "lambda_ci_policy_compiler.py",
            0o644,
        ),
        (
            repo_root / "scripts/lambda_ci_v3_control_planes.py",
            V3_RECONCILER_ROOT / "lambda_ci_v3_control_planes.py",
            0o644,
        ),
    ]


def build_stage(
    repo_root: pathlib.Path,
    stage: pathlib.Path,
    *,
    controller_binary: bytes,
    base_overlay: dict[str, Any] | None = None,
    source_head: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    stage.mkdir(parents=True, exist_ok=True)
    compiled = compiler.compile_policy(repo_root)
    migration = _json(repo_root / MIGRATION_PATH)
    if migration["side_by_side_paths"]["root_socket"] != "/run/workspace-ci/v3/provisioner.sock":
        raise ReconcileError("migration root socket drifted")
    if migration["side_by_side_paths"]["controller_binary"] != str(V3_CONTROLLER_BINARY):
        raise ReconcileError("migration controller binary drifted")
    if len(compiled["root_projection"]["runner_classes"]) != 9:
        raise ReconcileError("compiled runner class count is not nine")

    if base_overlay is None:
        base_overlay = _json(repo_root / OVERLAY_PATH)
    overlay = _installed_overlay(compiled, base_overlay)

    entries: list[dict[str, Any]] = []
    _write(
        stage,
        V3_CONFIG_ROOT / "root-policy.json",
        _canonical(compiled["root_projection"]),
        0o644,
        entries,
    )
    _write(
        stage,
        V3_CONFIG_ROOT / "executor-actions.json",
        _canonical(compiled["executor_projection"]),
        0o644,
        entries,
    )
    _write(
        stage,
        V3_CONFIG_ROOT / "compatibility-matrix.json",
        _canonical(compiled["compatibility_matrix"]),
        0o644,
        entries,
    )
    _write(
        stage,
        V3_CONFIG_ROOT / "deployment-overlay.json",
        _canonical(overlay),
        0o644,
        entries,
    )
    _write(
        stage,
        V3_CONFIG_ROOT / "migration-plan.json",
        _canonical(migration),
        0o644,
        entries,
    )

    for class_id, policy in sorted(compiled["controller_projections"].items()):
        _write(
            stage,
            V3_CONFIG_ROOT / "controllers" / f"{class_id}.json",
            _canonical(policy),
            0o644,
            entries,
        )
        root_policy = compiled["root_projection"]["runner_classes"][class_id]
        _write(
            stage,
            pathlib.Path(
                f"/etc/systemd/system/workspace-ci-v3-controller@{class_id}.service.d/identity.conf"
            ),
            render_controller_dropin(class_id, root_policy, migration).encode(),
            0o644,
            entries,
        )

    _write(
        stage,
        pathlib.Path("/etc/sysusers.d/workspace-ci-v3.conf"),
        render_sysusers(compiled, migration).encode(),
        0o644,
        entries,
    )
    _write(
        stage,
        pathlib.Path("/etc/tmpfiles.d/workspace-ci-v3.conf"),
        render_tmpfiles(compiled, migration).encode(),
        0o644,
        entries,
    )

    for unit, source in sorted(MANAGED_SYSTEMD.items()):
        _write(
            stage,
            pathlib.Path("/etc/systemd/system") / unit,
            (repo_root / source).read_bytes(),
            0o644,
            entries,
        )

    for source, destination, mode in _source_files(repo_root):
        _write(stage, destination, source.read_bytes(), mode, entries)

    if not controller_binary:
        raise ReconcileError("controller binary is empty")
    _write(stage, V3_CONTROLLER_BINARY, controller_binary, 0o755, entries)

    manifest = {
        "schema_version": 1,
        "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
        "source_head": source_head,
        "catalog_generation_sha256": compiled["catalog_generation_sha256"],
        "root_policy_sha256": compiled["root_projection"]["root_policy_sha256"],
        "runner_class_count": 9,
        "controller_state": "INACTIVE",
        "route_state": "DISABLED",
        "entries": sorted(entries, key=lambda item: item["destination"]),
    }
    _write(
        stage,
        V3_CONFIG_ROOT / "install-manifest.json",
        _canonical(manifest),
        0o644,
        [],
    )
    return {
        "compiled": compiled,
        "migration": migration,
        "overlay": overlay,
        "manifest": manifest,
    }


def verify_installed(manifest_path: pathlib.Path) -> None:
    manifest = _json(manifest_path)
    if manifest.get("mode") != "V3_SUBSTRATE_INSTALL_INACTIVE":
        raise ReconcileError("installed manifest mode invalid")
    if manifest.get("runner_class_count") != 9:
        raise ReconcileError("installed manifest runner class count invalid")
    for entry in manifest.get("entries", []):
        path = pathlib.Path(entry["destination"])
        if not path.is_file():
            raise ReconcileError(f"managed artifact missing: {path}")
        raw = path.read_bytes()
        if _sha256(raw) != entry["sha256"]:
            raise ReconcileError(f"managed artifact digest drift: {path}")
        if stat.S_IMODE(path.stat().st_mode) != int(entry["mode"], 8):
            raise ReconcileError(f"managed artifact mode drift: {path}")


def _git_exact_head(repo_root: pathlib.Path, expected: str) -> None:
    head = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if head != expected:
        raise ReconcileError(f"source head mismatch: {head} != {expected}")
    dirty = subprocess.check_output(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=no"],
        text=True,
    )
    if dirty.strip():
        raise ReconcileError("source tree has tracked modifications")


def _assert_v3_inactive(class_ids: list[str]) -> None:
    units = [
        "workspace-ci-v3-provisioner.service",
        "workspace-ci-v3-reconciler.service",
        *[f"workspace-ci-v3-controller@{class_id}.service" for class_id in class_ids],
    ]
    for unit in units:
        proc = subprocess.run(
            ["systemctl", "is-active", "--quiet", unit],
            check=False,
        )
        if proc.returncode == 0:
            raise ReconcileError(f"refusing inactive install while {unit} is active")


def _build_controller(repo_root: pathlib.Path, output: pathlib.Path, go_bin: str) -> bytes:
    subprocess.run(
        [
            go_bin,
            "-C",
            str(repo_root / "controller/lambda-ci-controller"),
            "build",
            "-mod=readonly",
            "-trimpath",
            "-o",
            str(output),
            "./v3",
        ],
        check=True,
    )
    return output.read_bytes()


def _atomic_copy(stage: pathlib.Path, destination: pathlib.Path) -> None:
    for source in sorted(path for path in stage.rglob("*") if path.is_file()):
        relative = source.relative_to(stage)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + f".tmp.{os.getpid()}")
        shutil.copyfile(source, tmp)
        os.chmod(tmp, stat.S_IMODE(source.stat().st_mode))
        os.replace(tmp, target)


def apply_inactive(
    repo_root: pathlib.Path,
    *,
    expected_head: str,
    go_bin: str,
) -> dict[str, Any]:
    if os.geteuid() != 0:
        raise ReconcileError("APPLY_INACTIVE requires root")
    _git_exact_head(repo_root, expected_head)
    compiled = compiler.compile_policy(repo_root)
    class_ids = sorted(compiled["root_projection"]["runner_classes"])
    _assert_v3_inactive(class_ids)

    installed_overlay_path = V3_CONFIG_ROOT / "deployment-overlay.json"
    base_overlay = (
        _json(installed_overlay_path)
        if installed_overlay_path.is_file()
        else _json(repo_root / OVERLAY_PATH)
    )

    with tempfile.TemporaryDirectory(prefix="workspace-ci-v3-install-") as raw:
        temp = pathlib.Path(raw)
        binary = _build_controller(repo_root, temp / "lambda-ci-controller-v3", go_bin)
        stage = temp / "stage"
        result = build_stage(
            repo_root,
            stage,
            controller_binary=binary,
            base_overlay=base_overlay,
            source_head=expected_head,
        )
        _atomic_copy(stage, pathlib.Path("/"))

    subprocess.run(
        ["systemd-sysusers", "/etc/sysusers.d/workspace-ci-v3.conf"],
        check=True,
    )
    subprocess.run(
        ["systemd-tmpfiles", "--create", "/etc/tmpfiles.d/workspace-ci-v3.conf"],
        check=True,
    )
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    verify_installed(V3_CONFIG_ROOT / "install-manifest.json")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--stage-dir", type=pathlib.Path)
    parser.add_argument("--controller-binary", type=pathlib.Path)
    parser.add_argument("--apply-inactive", action="store_true")
    parser.add_argument("--expected-source-head")
    parser.add_argument("--go-bin", default="go")
    parser.add_argument("--verify-installed", action="store_true")
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    if args.verify_installed:
        manifest = args.manifest or (V3_CONFIG_ROOT / "install-manifest.json")
        verify_installed(manifest)
        print("V3_INSTALLED_GENERATION_VERIFY=PASS")
        return 0

    if args.apply_inactive:
        if not args.expected_source_head:
            raise ReconcileError("--apply-inactive requires --expected-source-head")
        result = apply_inactive(
            args.repo_root.resolve(),
            expected_head=args.expected_source_head,
            go_bin=args.go_bin,
        )
        print("V3_SUBSTRATE_INSTALL_INACTIVE=PASS")
        print(f"CATALOG_GENERATION_SHA256={result['compiled']['catalog_generation_sha256']}")
        return 0

    if args.stage_dir:
        if args.controller_binary is None:
            raise ReconcileError("--stage-dir requires --controller-binary")
        result = build_stage(
            args.repo_root.resolve(),
            args.stage_dir.resolve(),
            controller_binary=args.controller_binary.read_bytes(),
        )
        print("V3_SUBSTRATE_STAGE=PASS")
        print(f"MANAGED_FILES={len(result['manifest']['entries'])}")
        return 0

    compiled = compiler.compile_policy(args.repo_root.resolve())
    migration = _json(args.repo_root.resolve() / MIGRATION_PATH)
    print(json.dumps({
        "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
        "catalog_generation_sha256": compiled["catalog_generation_sha256"],
        "runner_classes": sorted(compiled["root_projection"]["runner_classes"]),
        "sysusers": render_sysusers(compiled, migration).splitlines(),
        "tmpfiles": render_tmpfiles(compiled, migration).splitlines(),
        "activation_authority": "NONE",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
