import copy
import json
import pathlib
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
import sys
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lambda_ci_reconciler as reconciler


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


REGISTRY = load_json("architecture/lambda-ci-project-registry.v1.json")
RESEARCH = load_json("architecture/lambda-ci-project-research-engine.v2.json")
PAD = load_json("architecture/lambda-ci-project-padataset.v1.json")
WORKSPACE = load_json("architecture/lambda-ci-project-workspace-control.v1.json")


class ReconcilerActivationDeltaTests(unittest.TestCase):
    def activation_target(self):
        registry = copy.deepcopy(REGISTRY)
        manifests = {
            "research-engine": copy.deepcopy(RESEARCH),
            "padataset": copy.deepcopy(PAD),
            "workspace-control": copy.deepcopy(WORKSPACE),
        }
        registry["projects"]["workspace-control"]["activation_state"] = "ACTIVE"
        workspace = manifests["workspace-control"]
        workspace["status"] = "ACTIVE"
        workspace["routes"]["control-validation"]["activation_state"] = "ACTIVE"
        return registry, manifests

    def make_apply_fixture(self, root):
        target_registry, manifests = self.activation_target()
        installed_registry = copy.deepcopy(REGISTRY)

        registry_path = root / "registry.json"
        registry_path.write_text(
            json.dumps(installed_registry, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        projects_dir = root / "projects"
        projects_dir.mkdir()
        for project_id, manifest in manifests.items():
            current = copy.deepcopy(manifest)
            if project_id == "workspace-control":
                current = copy.deepcopy(WORKSPACE)
            (projects_dir / f"{project_id}.json").write_text(
                json.dumps(current, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        controllers_dir = root / "controllers"
        controllers_dir.mkdir()
        controller_state_root = root / "controller-state"
        state_dir = root / "reconciler-state"
        dropins = root / "dropins"
        dropins.mkdir()

        stable = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
            "MainPID": "100",
            "InvocationID": "stable",
        }
        research_cpu = {
            **stable,
            "ActiveState": "inactive",
            "SubState": "dead",
            "ExecMainStatus": "1",
            "MainPID": "0",
            "NRestarts": "12411",
            "InvocationID": "research-cpu-failed-generation",
        }

        def snapshot(service):
            if service == "workspace-ci-controller@research-engine-cpu.service":
                return dict(research_cpu)
            return dict(stable)

        def dropin(project_id, lane, subnet):
            path = dropins / f"{project_id}-{lane}.conf"
            body = f"[Service]\nIPAddressDeny={subnet}\n".encode("utf-8")
            return path, body

        with mock.patch.object(
            reconciler,
            "controller_network_dropin",
            side_effect=dropin,
        ):
            for project_id in ("padataset", "research-engine"):
                manifest = manifests[project_id]
                for lane in target_registry["projects"][project_id]["lanes"]:
                    (controllers_dir / f"{project_id}-{lane}.env").write_bytes(
                        reconciler.render_controller_env(manifest, lane).encode("utf-8")
                    )
                    path, body = dropin(project_id, lane, "192.0.2.0/24")
                    path.write_bytes(body)

        request_id = "22222222-2222-4222-8222-222222222222"
        validated = {
            "request": {
                "request_id": request_id,
                "dry_run": False,
                "registry": {"sha256": "registry-target"},
                "project_manifests": [
                    {"project_id": k, "sha256": f"manifest-{k}"}
                    for k in sorted(manifests)
                ],
            },
            "source": {"commit_sha": "b" * 40},
            "registry": target_registry,
            "manifests": manifests,
            "plan": reconciler.plan_reconciliation(
                target_registry, manifests
            ),
        }
        return {
            "target_registry": target_registry,
            "manifests": manifests,
            "registry_path": registry_path,
            "projects_dir": projects_dir,
            "controllers_dir": controllers_dir,
            "controller_state_root": controller_state_root,
            "state_dir": state_dir,
            "dropin": dropin,
            "snapshot": snapshot,
            "stable": stable,
            "research_cpu": research_cpu,
            "validated": validated,
            "request_id": request_id,
        }

    def test_workspace_activation_restarts_only_workspace_controller(self):
        target_registry, manifests = self.activation_target()
        installed_registry = copy.deepcopy(REGISTRY)
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            controllers_dir = root / "controllers"
            controllers_dir.mkdir()
            dropins = root / "dropins"
            dropins.mkdir()

            def dropin(project_id, lane, subnet):
                path = dropins / f"{project_id}-{lane}.conf"
                body = f"[Service]\nIPAddressDeny={subnet}\n".encode("utf-8")
                return path, body

            with mock.patch.object(
                reconciler,
                "controller_network_dropin",
                side_effect=dropin,
            ):
                # Materialize the exact existing controller configuration for
                # every already-active sibling. workspace-control remains
                # absent because it is not installed yet.
                for project_id in ("padataset", "research-engine"):
                    manifest = manifests[project_id]
                    for lane in target_registry["projects"][project_id]["lanes"]:
                        (controllers_dir / f"{project_id}-{lane}.env").write_bytes(
                            reconciler.render_controller_env(manifest, lane).encode("utf-8")
                        )
                        path, body = dropin(project_id, lane, "192.0.2.0/24")
                        path.write_bytes(body)

                delta = reconciler.controller_reconciliation_delta(
                    installed_registry=installed_registry,
                    target_registry=target_registry,
                    manifests=manifests,
                    controllers_dir=controllers_dir,
                    local_subnet="192.0.2.0/24",
                )

            restarted = [x["service"] for x in delta if x["restart_required"]]
            preserved = [x["service"] for x in delta if not x["restart_required"]]
            self.assertEqual(
                restarted,
                ["workspace-ci-controller@workspace-control-cpu.service"],
            )
            self.assertEqual(
                preserved,
                [
                    "workspace-ci-controller@padataset-cpu.service",
                    "workspace-ci-controller@padataset-gpu.service",
                    "workspace-ci-controller@research-engine-cpu.service",
                    "workspace-ci-controller@research-engine-gpu.service",
                ],
            )

    def test_existing_controller_config_drift_is_explicit_restart_delta(self):
        target_registry, manifests = self.activation_target()
        installed_registry = copy.deepcopy(REGISTRY)
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            controllers_dir = root / "controllers"
            controllers_dir.mkdir()
            dropins = root / "dropins"
            dropins.mkdir()

            def dropin(project_id, lane, subnet):
                path = dropins / f"{project_id}-{lane}.conf"
                body = f"[Service]\nIPAddressDeny={subnet}\n".encode("utf-8")
                return path, body

            with mock.patch.object(
                reconciler,
                "controller_network_dropin",
                side_effect=dropin,
            ):
                for project_id in ("padataset", "research-engine"):
                    manifest = manifests[project_id]
                    for lane in target_registry["projects"][project_id]["lanes"]:
                        (controllers_dir / f"{project_id}-{lane}.env").write_bytes(
                            reconciler.render_controller_env(manifest, lane).encode("utf-8")
                        )
                        path, body = dropin(project_id, lane, "192.0.2.0/24")
                        path.write_bytes(body)
                # Deliberately drift only research-engine GPU config.
                (controllers_dir / "research-engine-gpu.env").write_text(
                    "DRIFT=1\n", encoding="utf-8"
                )

                delta = reconciler.controller_reconciliation_delta(
                    installed_registry=installed_registry,
                    target_registry=target_registry,
                    manifests=manifests,
                    controllers_dir=controllers_dir,
                    local_subnet="192.0.2.0/24",
                )

            restarted = [x["service"] for x in delta if x["restart_required"]]
            self.assertEqual(
                restarted,
                [
                    "workspace-ci-controller@research-engine-gpu.service",
                    "workspace-ci-controller@workspace-control-cpu.service",
                ],
            )

    def test_apply_activation_preserves_unchanged_sibling_service_snapshots(self):
        target_registry, manifests = self.activation_target()
        installed_registry = copy.deepcopy(REGISTRY)
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            registry_path = root / "registry.json"
            registry_path.write_text(
                json.dumps(installed_registry, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            projects_dir = root / "projects"
            projects_dir.mkdir()
            for project_id, manifest in manifests.items():
                current = copy.deepcopy(manifest)
                if project_id == "workspace-control":
                    current = copy.deepcopy(WORKSPACE)
                (projects_dir / f"{project_id}.json").write_text(
                    json.dumps(current, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            controllers_dir = root / "controllers"
            controllers_dir.mkdir()
            controller_state_root = root / "controller-state"
            state_dir = root / "reconciler-state"
            dropins = root / "dropins"
            dropins.mkdir()

            sibling_services = [
                "workspace-ci-controller@padataset-cpu.service",
                "workspace-ci-controller@padataset-gpu.service",
                "workspace-ci-controller@research-engine-cpu.service",
                "workspace-ci-controller@research-engine-gpu.service",
            ]
            stable = {
                "LoadState": "loaded",
                "ActiveState": "active",
                "SubState": "running",
                "UnitFileState": "enabled",
                "NRestarts": "0",
                "ExecMainStatus": "0",
                "MainPID": "100",
                "InvocationID": "stable",
            }
            research_cpu = {
                **stable,
                "ActiveState": "inactive",
                "SubState": "dead",
                "ExecMainStatus": "1",
                "MainPID": "0",
                "NRestarts": "12411",
                "InvocationID": "research-cpu-failed-generation",
            }

            def snapshot(service):
                if service == "workspace-ci-controller@research-engine-cpu.service":
                    return dict(research_cpu)
                return dict(stable)

            def dropin(project_id, lane, subnet):
                path = dropins / f"{project_id}-{lane}.conf"
                body = f"[Service]\nIPAddressDeny={subnet}\n".encode("utf-8")
                return path, body

            # Existing active siblings have exact current config.
            with mock.patch.object(
                reconciler,
                "controller_network_dropin",
                side_effect=dropin,
            ):
                for project_id in ("padataset", "research-engine"):
                    manifest = manifests[project_id]
                    for lane in target_registry["projects"][project_id]["lanes"]:
                        (controllers_dir / f"{project_id}-{lane}.env").write_bytes(
                            reconciler.render_controller_env(manifest, lane).encode("utf-8")
                        )
                        path, body = dropin(project_id, lane, "192.0.2.0/24")
                        path.write_bytes(body)

                calls = []

                def fake_run(argv, check=True):
                    calls.append(list(argv))
                    return types.SimpleNamespace(returncode=0, stdout="", stderr="")

                request_id = "11111111-1111-4111-8111-111111111111"
                validated = {
                    "request": {
                        "request_id": request_id,
                        "dry_run": False,
                        "registry": {"sha256": "r"},
                        "project_manifests": [
                            {"project_id": k, "sha256": k}
                            for k in sorted(manifests)
                        ],
                    },
                    "source": {"commit_sha": "a" * 40},
                    "registry": target_registry,
                    "manifests": manifests,
                    "plan": reconciler.plan_reconciliation(
                        target_registry, manifests
                    ),
                }

                with (
                    mock.patch.object(reconciler, "primary_local_subnet", return_value="192.0.2.0/24"),
                    mock.patch.object(reconciler, "_service_snapshot", side_effect=snapshot),
                    mock.patch.object(reconciler, "_ensure_project_identity"),
                    mock.patch.object(reconciler, "_ensure_project_roots"),
                    mock.patch.object(reconciler, "_service_enabled", return_value=False),
                    mock.patch.object(reconciler, "_service_active", return_value=True),
                    mock.patch.object(reconciler, "_run", side_effect=fake_run),
                    mock.patch.object(reconciler.os, "chown"),
                    mock.patch.object(
                        reconciler.pwd,
                        "getpwnam",
                        return_value=types.SimpleNamespace(pw_uid=1000),
                    ),
                    mock.patch.object(
                        reconciler.grp,
                        "getgrnam",
                        return_value=types.SimpleNamespace(gr_gid=1000),
                    ),
                ):
                    receipt = reconciler.apply_reconciliation(
                        validated,
                        registry_path=registry_path,
                        projects_dir=projects_dir,
                        controllers_dir=controllers_dir,
                        state_dir=state_dir,
                        controller_state_root=controller_state_root,
                    )

            restart_calls = [
                c for c in calls
                if len(c) >= 3 and c[:2] == ["systemctl", "restart"]
            ]
            self.assertEqual(
                restart_calls,
                [[
                    "systemctl",
                    "restart",
                    "workspace-ci-controller@workspace-control-cpu.service",
                ]],
            )
            self.assertEqual(
                receipt["controller_services_restarted"],
                ["workspace-ci-controller@workspace-control-cpu.service"],
            )
            self.assertEqual(
                receipt["controller_services_preserved"],
                sibling_services,
            )
            self.assertEqual(
                receipt["preserved_controller_services_before"],
                receipt["preserved_controller_services_after"],
            )
            self.assertEqual(
                receipt["preserved_controller_services_after"][
                    "workspace-ci-controller@research-engine-cpu.service"
                ]["NRestarts"],
                "12411",
            )


    def test_interrupted_apply_resumes_original_pending_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            fx = self.make_apply_fixture(root)
            first_calls = []

            def first_run(argv, check=True):
                first_calls.append(list(argv))
                if argv == [
                    "systemctl",
                    "restart",
                    "workspace-ci-controller@workspace-control-cpu.service",
                ]:
                    raise reconciler.ReconcileError("synthetic interruption before restart")
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")

            common = (
                mock.patch.object(
                    reconciler,
                    "primary_local_subnet",
                    return_value="192.0.2.0/24",
                ),
                mock.patch.object(
                    reconciler,
                    "controller_network_dropin",
                    side_effect=fx["dropin"],
                ),
                mock.patch.object(
                    reconciler,
                    "_service_snapshot",
                    side_effect=fx["snapshot"],
                ),
                mock.patch.object(reconciler, "_ensure_project_identity"),
                mock.patch.object(reconciler, "_ensure_project_roots"),
                mock.patch.object(reconciler, "_service_enabled", return_value=False),
                mock.patch.object(reconciler, "_service_active", return_value=True),
                mock.patch.object(reconciler.os, "chown"),
                mock.patch.object(
                    reconciler.pwd,
                    "getpwnam",
                    return_value=types.SimpleNamespace(pw_uid=1000),
                ),
                mock.patch.object(
                    reconciler.grp,
                    "getgrnam",
                    return_value=types.SimpleNamespace(gr_gid=1000),
                ),
            )
            with (*common, mock.patch.object(reconciler, "_run", side_effect=first_run)):
                with self.assertRaisesRegex(
                    reconciler.ReconcileError,
                    "synthetic interruption before restart",
                ):
                    reconciler.apply_reconciliation(
                        fx["validated"],
                        registry_path=fx["registry_path"],
                        projects_dir=fx["projects_dir"],
                        controllers_dir=fx["controllers_dir"],
                        state_dir=fx["state_dir"],
                        controller_state_root=fx["controller_state_root"],
                    )

            stored = json.loads(
                (
                    fx["state_dir"]
                    / "receipts"
                    / f"{fx['request_id']}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(stored["status"], "IN_PROGRESS")
            self.assertEqual(
                stored["transaction"]["controller_services_planned_for_restart"],
                ["workspace-ci-controller@workspace-control-cpu.service"],
            )
            self.assertEqual(
                stored["transaction"]["controller_services_restarted"],
                [],
            )
            self.assertEqual(
                json.loads(fx["registry_path"].read_text(encoding="utf-8"))[
                    "projects"
                ]["workspace-control"]["activation_state"],
                "ACTIVE",
            )
            self.assertTrue(
                (
                    fx["controllers_dir"] / "workspace-control-cpu.env"
                ).is_file()
            )

            second_calls = []

            def second_run(argv, check=True):
                second_calls.append(list(argv))
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")

            common2 = (
                mock.patch.object(
                    reconciler,
                    "primary_local_subnet",
                    return_value="192.0.2.0/24",
                ),
                mock.patch.object(
                    reconciler,
                    "controller_network_dropin",
                    side_effect=fx["dropin"],
                ),
                mock.patch.object(
                    reconciler,
                    "_service_snapshot",
                    side_effect=fx["snapshot"],
                ),
                mock.patch.object(reconciler, "_ensure_project_identity"),
                mock.patch.object(reconciler, "_ensure_project_roots"),
                mock.patch.object(reconciler, "_service_enabled", return_value=False),
                mock.patch.object(reconciler, "_service_active", return_value=True),
                mock.patch.object(reconciler.os, "chown"),
                mock.patch.object(
                    reconciler.pwd,
                    "getpwnam",
                    return_value=types.SimpleNamespace(pw_uid=1000),
                ),
                mock.patch.object(
                    reconciler.grp,
                    "getgrnam",
                    return_value=types.SimpleNamespace(gr_gid=1000),
                ),
            )
            with (*common2, mock.patch.object(reconciler, "_run", side_effect=second_run)):
                receipt = reconciler.apply_reconciliation(
                    fx["validated"],
                    registry_path=fx["registry_path"],
                    projects_dir=fx["projects_dir"],
                    controllers_dir=fx["controllers_dir"],
                    state_dir=fx["state_dir"],
                    controller_state_root=fx["controller_state_root"],
                )

            restart_calls = [
                call
                for call in second_calls
                if call[:2] == ["systemctl", "restart"]
            ]
            self.assertEqual(
                restart_calls,
                [[
                    "systemctl",
                    "restart",
                    "workspace-ci-controller@workspace-control-cpu.service",
                ]],
            )
            self.assertEqual(receipt["status"], "COMPLETED")
            self.assertEqual(
                receipt["controller_services_restarted"],
                ["workspace-ci-controller@workspace-control-cpu.service"],
            )

    def test_resume_fails_on_preserved_sibling_generation_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            fx = self.make_apply_fixture(root)

            def first_run(argv, check=True):
                if argv == [
                    "systemctl",
                    "restart",
                    "workspace-ci-controller@workspace-control-cpu.service",
                ]:
                    raise reconciler.ReconcileError("synthetic interruption before restart")
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")

            with (
                mock.patch.object(
                    reconciler,
                    "primary_local_subnet",
                    return_value="192.0.2.0/24",
                ),
                mock.patch.object(
                    reconciler,
                    "controller_network_dropin",
                    side_effect=fx["dropin"],
                ),
                mock.patch.object(
                    reconciler,
                    "_service_snapshot",
                    side_effect=fx["snapshot"],
                ),
                mock.patch.object(reconciler, "_ensure_project_identity"),
                mock.patch.object(reconciler, "_ensure_project_roots"),
                mock.patch.object(reconciler, "_service_enabled", return_value=False),
                mock.patch.object(reconciler, "_service_active", return_value=True),
                mock.patch.object(reconciler, "_run", side_effect=first_run),
                mock.patch.object(reconciler.os, "chown"),
                mock.patch.object(
                    reconciler.pwd,
                    "getpwnam",
                    return_value=types.SimpleNamespace(pw_uid=1000),
                ),
                mock.patch.object(
                    reconciler.grp,
                    "getgrnam",
                    return_value=types.SimpleNamespace(gr_gid=1000),
                ),
            ):
                with self.assertRaisesRegex(
                    reconciler.ReconcileError,
                    "synthetic interruption before restart",
                ):
                    reconciler.apply_reconciliation(
                        fx["validated"],
                        registry_path=fx["registry_path"],
                        projects_dir=fx["projects_dir"],
                        controllers_dir=fx["controllers_dir"],
                        state_dir=fx["state_dir"],
                        controller_state_root=fx["controller_state_root"],
                    )

            second_calls = []

            def second_run(argv, check=True):
                second_calls.append(list(argv))
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")

            def drifted_snapshot(service):
                value = fx["snapshot"](service)
                if service == "workspace-ci-controller@padataset-cpu.service":
                    value["InvocationID"] = "drifted-between-attempts"
                return value

            with (
                mock.patch.object(
                    reconciler,
                    "primary_local_subnet",
                    return_value="192.0.2.0/24",
                ),
                mock.patch.object(
                    reconciler,
                    "controller_network_dropin",
                    side_effect=fx["dropin"],
                ),
                mock.patch.object(
                    reconciler,
                    "_service_snapshot",
                    side_effect=drifted_snapshot,
                ),
                mock.patch.object(reconciler, "_run", side_effect=second_run),
                mock.patch.object(reconciler.os, "chown"),
            ):
                with self.assertRaisesRegex(
                    reconciler.ReconcileError,
                    "resume preserved controller service identity/state changed.*padataset-cpu",
                ):
                    reconciler.apply_reconciliation(
                        fx["validated"],
                        registry_path=fx["registry_path"],
                        projects_dir=fx["projects_dir"],
                        controllers_dir=fx["controllers_dir"],
                        state_dir=fx["state_dir"],
                        controller_state_root=fx["controller_state_root"],
                    )

            self.assertFalse(
                any(call[:2] == ["systemctl", "restart"] for call in second_calls)
            )

    def test_resume_rejects_malformed_stored_transaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            fx = self.make_apply_fixture(root)

            def first_run(argv, check=True):
                if argv == [
                    "systemctl",
                    "restart",
                    "workspace-ci-controller@workspace-control-cpu.service",
                ]:
                    raise reconciler.ReconcileError("synthetic interruption before restart")
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")

            with (
                mock.patch.object(
                    reconciler,
                    "primary_local_subnet",
                    return_value="192.0.2.0/24",
                ),
                mock.patch.object(
                    reconciler,
                    "controller_network_dropin",
                    side_effect=fx["dropin"],
                ),
                mock.patch.object(
                    reconciler,
                    "_service_snapshot",
                    side_effect=fx["snapshot"],
                ),
                mock.patch.object(reconciler, "_ensure_project_identity"),
                mock.patch.object(reconciler, "_ensure_project_roots"),
                mock.patch.object(reconciler, "_service_enabled", return_value=False),
                mock.patch.object(reconciler, "_service_active", return_value=True),
                mock.patch.object(reconciler, "_run", side_effect=first_run),
                mock.patch.object(reconciler.os, "chown"),
                mock.patch.object(
                    reconciler.pwd,
                    "getpwnam",
                    return_value=types.SimpleNamespace(pw_uid=1000),
                ),
                mock.patch.object(
                    reconciler.grp,
                    "getgrnam",
                    return_value=types.SimpleNamespace(gr_gid=1000),
                ),
            ):
                with self.assertRaises(reconciler.ReconcileError):
                    reconciler.apply_reconciliation(
                        fx["validated"],
                        registry_path=fx["registry_path"],
                        projects_dir=fx["projects_dir"],
                        controllers_dir=fx["controllers_dir"],
                        state_dir=fx["state_dir"],
                        controller_state_root=fx["controller_state_root"],
                    )

            receipt_path = (
                fx["state_dir"] / "receipts" / f"{fx['request_id']}.json"
            )
            stored = json.loads(receipt_path.read_text(encoding="utf-8"))
            del stored["transaction"]["controller_services_planned_for_restart"]
            receipt_path.write_text(json.dumps(stored), encoding="utf-8")

            with (
                mock.patch.object(
                    reconciler,
                    "primary_local_subnet",
                    return_value="192.0.2.0/24",
                ),
                mock.patch.object(reconciler.os, "chown"),
            ):
                with self.assertRaisesRegex(
                    reconciler.ReconcileError,
                    "transaction is malformed",
                ):
                    reconciler.apply_reconciliation(
                        fx["validated"],
                        registry_path=fx["registry_path"],
                        projects_dir=fx["projects_dir"],
                        controllers_dir=fx["controllers_dir"],
                        state_dir=fx["state_dir"],
                        controller_state_root=fx["controller_state_root"],
                    )


if __name__ == "__main__":
    unittest.main()
