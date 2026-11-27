from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lambda_ci_policy_compiler as compiler  # noqa: E402
import lambda_ci_v3_reconciler as reconciler  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "codex_workflow_refresh",
    SCRIPTS / "lambda_ci_v3_workspace_control_codex_workflow_refresh_v1.py",
)
refresh = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["codex_workflow_refresh"] = refresh
spec.loader.exec_module(refresh)

HELPER = (
    SCRIPTS / "lambda_ci_v3_workspace_control_codex_workflow_refresh_v1.py"
).read_text(encoding="utf-8")
REC = (SCRIPTS / "lambda_ci_v3_reconciler.py").read_text(encoding="utf-8")


def inactive_state() -> dict[str, str]:
    return {
        "ActiveState": "inactive",
        "SubState": "dead",
        "MainPID": "0",
        "NRestarts": "0",
        "InvocationID": "inactive-id",
        "UnitFileState": "enabled",
        "LoadState": "loaded",
    }


def active_state() -> dict[str, str]:
    return {
        "ActiveState": "active",
        "SubState": "running",
        "MainPID": "123",
        "NRestarts": "0",
        "InvocationID": "active-id",
        "UnitFileState": "enabled",
        "LoadState": "loaded",
    }


class WorkspaceControlCodexWorkflowRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        compiled = compiler.compile_policy(ROOT)
        cls.current = compiled["controller_projections"][refresh.TARGET_CLASS]

    def predecessor_policy(self) -> dict:
        value = copy.deepcopy(self.current)
        by_route = {
            row["route_id"]: row
            for row in value["trusted_workflows"]
        }
        by_route["codex-bootstrap"]["blob_sha"] = refresh.OLD_BLOB
        value["controller_policy_sha256"] = refresh.policy_digest(value)
        return value

    def test_exact_old_and_new_workflow_lineage(self):
        self.assertEqual(
            refresh.OLD_BLOB,
            "520da69cfb9b28c81fb1121a16c12d3715892cc7",
        )
        self.assertEqual(
            refresh.NEW_BLOB,
            "b17526353acb531010fce019337f7b3080ba235b",
        )
        self.assertNotEqual(refresh.OLD_BLOB, refresh.NEW_BLOB)

    def test_refresh_changes_only_codex_blob_and_controller_digest(self):
        before = self.predecessor_policy()
        after = refresh.build_refreshed_policy(before)
        before_routes = {
            row["route_id"]: row
            for row in before["trusted_workflows"]
        }
        after_routes = {
            row["route_id"]: row
            for row in after["trusted_workflows"]
        }
        self.assertEqual(
            before_routes["control-validation"],
            after_routes["control-validation"],
        )
        self.assertEqual(
            before_routes["codex-bootstrap"]["blob_sha"],
            refresh.OLD_BLOB,
        )
        self.assertEqual(
            after_routes["codex-bootstrap"]["blob_sha"],
            refresh.NEW_BLOB,
        )
        changed = {
            key
            for key in set(before) | set(after)
            if before.get(key) != after.get(key)
        }
        self.assertEqual(
            changed,
            {"trusted_workflows", "controller_policy_sha256"},
        )

    def test_final_quiescence_rejects_work_after_predecessor_checks_before_write(self):
        events: list[str] = []
        mutation_state = {"started": False}
        late_work = {"present": False}

        def stop(*_args):
            events.append("stop")

        def inactive():
            events.append("inactive")
            return inactive_state()

        def quiescence():
            events.append("quiescence")
            if late_work["present"]:
                raise refresh.RefreshError("late target work appeared")

        def predecessor(**_kwargs):
            events.append("predecessor")
            late_work["present"] = True

        with (
            mock.patch.object(refresh, "run_systemctl", side_effect=stop),
            mock.patch.object(
                refresh,
                "require_target_inactive",
                side_effect=inactive,
            ),
            mock.patch.object(
                refresh,
                "require_target_quiescent",
                side_effect=quiescence,
            ),
            mock.patch.object(
                refresh,
                "require_predecessor_unchanged",
                side_effect=predecessor,
            ),
            mock.patch.object(refresh, "atomic_file") as atomic_file,
        ):
            with self.assertRaisesRegex(
                refresh.RefreshError,
                "late target work appeared",
            ):
                refresh.stop_target_close_quiescence_and_write_first_policy(
                    root_policy_raw=b"root",
                    active_route_raw=b"active",
                    policy_raw=b"policy",
                    reconciler_raw=b"reconciler",
                    reconciler_override_raw=b"override",
                    others_before={},
                    refreshed_policy_raw=b"new-policy",
                    mutation_state=mutation_state,
                )

        self.assertEqual(
            events,
            ["stop", "inactive", "quiescence", "predecessor", "quiescence"],
        )
        self.assertFalse(mutation_state["started"])
        atomic_file.assert_not_called()


    def test_pre_mutation_failure_recovery_writes_no_managed_files(self):
        expected_target = active_state()
        expected_others = {"sibling": active_state()}
        with (
            mock.patch.object(refresh, "require_target_inactive"),
            mock.patch.object(refresh, "require_predecessor_unchanged"),
            mock.patch.object(refresh, "run_systemctl") as systemctl,
            mock.patch.object(
                refresh,
                "verify_predecessor_restored",
                return_value=(expected_target, expected_others),
            ),
            mock.patch.object(refresh, "atomic_file") as atomic_file,
            mock.patch.object(refresh, "atomic_json") as atomic_json,
        ):
            actual = refresh.recover_pre_mutation_failure(
                root_policy_raw=b"root",
                active_route_raw=b"active",
                policy_raw=b"policy",
                reconciler_raw=b"reconciler",
                reconciler_override_raw=b"override",
                others_before=expected_others,
            )

        self.assertEqual(actual, (expected_target, expected_others))
        systemctl.assert_called_once_with("start", refresh.TARGET_UNIT)
        atomic_file.assert_not_called()
        atomic_json.assert_not_called()

    def test_rollback_stop_failure_blocks_restore_and_cannot_attest(self):
        with (
            mock.patch.object(
                refresh,
                "systemd",
                return_value=active_state(),
            ),
            mock.patch.object(
                refresh,
                "run_systemctl",
                side_effect=refresh.RefreshError("stop failed"),
            ),
            mock.patch.object(refresh, "atomic_file") as atomic_file,
        ):
            with self.assertRaisesRegex(refresh.RefreshError, "stop failed"):
                refresh.rollback_after_mutation(
                    root_policy_raw=b"root",
                    active_route_raw=b"active",
                    policy_raw=b"policy",
                    reconciler_raw=b"reconciler",
                    reconciler_override_raw=b"override",
                    reconciler_mode=0o755,
                    others_before={},
                )
        atomic_file.assert_not_called()

    def test_rollback_start_failure_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            root_policy = root / "root.json"
            active_route = root / "active.json"
            target_policy = root / "policy.json"
            reconciler = root / "reconciler.py"
            override = root / "override.json"
            refresh_receipt = root / "refresh.json"

            root_policy.write_bytes(b"root-before")
            active_route.write_bytes(b"route-before")
            target_policy.write_bytes(b"mutated-policy")
            reconciler.write_bytes(b"mutated-reconciler")
            override.write_bytes(b"mutated-override")
            refresh_receipt.write_bytes(b"refresh")

            def atomic(path: Path, data: bytes, _mode: int):
                path.write_bytes(data)

            with (
                mock.patch.object(refresh, "ROOT_POLICY", root_policy),
                mock.patch.object(refresh, "ACTIVE_ROUTE", active_route),
                mock.patch.object(refresh, "TARGET_POLICY", target_policy),
                mock.patch.object(refresh, "INSTALLED_RECONCILER", reconciler),
                mock.patch.object(refresh, "RECONCILER_OVERRIDE", override),
                mock.patch.object(refresh, "REFRESH_ACTIVE", refresh_receipt),
                mock.patch.object(
                    refresh,
                    "systemd",
                    side_effect=[inactive_state(), inactive_state()],
                ),
                mock.patch.object(refresh, "atomic_file", side_effect=atomic),
                mock.patch.object(
                    refresh.candidate,
                    "verify_installed",
                ),
                mock.patch.object(
                    refresh,
                    "run_systemctl",
                    side_effect=refresh.RefreshError("start failed"),
                ),
            ):
                with self.assertRaisesRegex(
                    refresh.RefreshError,
                    "start failed",
                ):
                    refresh.rollback_after_mutation(
                        root_policy_raw=b"root-before",
                        active_route_raw=b"route-before",
                        policy_raw=b"policy-before",
                        reconciler_raw=b"reconciler-before",
                        reconciler_override_raw=b"override-before",
                        reconciler_mode=0o755,
                        others_before={},
                    )

            self.assertEqual(target_policy.read_bytes(), b"policy-before")
            self.assertEqual(reconciler.read_bytes(), b"reconciler-before")
            self.assertEqual(override.read_bytes(), b"override-before")
            self.assertFalse(refresh_receipt.exists())

    def test_rollback_proves_exact_restoration_and_runtime_invariants(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            root_policy = root / "root.json"
            active_route = root / "active.json"
            target_policy = root / "policy.json"
            reconciler = root / "reconciler.py"
            override = root / "override.json"
            refresh_receipt = root / "refresh.json"

            root_policy.write_bytes(b"root-before")
            active_route.write_bytes(b"route-before")
            target_policy.write_bytes(b"mutated-policy")
            reconciler.write_bytes(b"mutated-reconciler")
            override.write_bytes(b"mutated-override")
            refresh_receipt.write_bytes(b"refresh")

            sibling = {"sibling": active_state()}

            def atomic(path: Path, data: bytes, _mode: int):
                path.write_bytes(data)

            with (
                mock.patch.object(refresh, "ROOT_POLICY", root_policy),
                mock.patch.object(refresh, "ACTIVE_ROUTE", active_route),
                mock.patch.object(refresh, "TARGET_POLICY", target_policy),
                mock.patch.object(refresh, "INSTALLED_RECONCILER", reconciler),
                mock.patch.object(refresh, "RECONCILER_OVERRIDE", override),
                mock.patch.object(refresh, "REFRESH_ACTIVE", refresh_receipt),
                mock.patch.object(
                    refresh,
                    "systemd",
                    side_effect=[
                        inactive_state(),
                        inactive_state(),
                        active_state(),
                    ],
                ),
                mock.patch.object(refresh, "atomic_file", side_effect=atomic),
                mock.patch.object(refresh, "run_systemctl") as systemctl,
                mock.patch.object(refresh, "require_roots") as roots,
                mock.patch.object(
                    refresh,
                    "require_target_quiescent",
                ) as quiescent,
                mock.patch.object(
                    refresh,
                    "controller_snapshots",
                    return_value=sibling,
                ),
                mock.patch.object(
                    refresh.candidate,
                    "verify_installed",
                ) as verify,
            ):
                target_after, others_after = refresh.rollback_after_mutation(
                    root_policy_raw=b"root-before",
                    active_route_raw=b"route-before",
                    policy_raw=b"policy-before",
                    reconciler_raw=b"reconciler-before",
                    reconciler_override_raw=b"override-before",
                    reconciler_mode=0o755,
                    others_before=sibling,
                )

            self.assertEqual(target_after["ActiveState"], "active")
            self.assertEqual(others_after, sibling)
            self.assertEqual(target_policy.read_bytes(), b"policy-before")
            self.assertEqual(reconciler.read_bytes(), b"reconciler-before")
            self.assertEqual(override.read_bytes(), b"override-before")
            self.assertEqual(root_policy.read_bytes(), b"root-before")
            self.assertEqual(active_route.read_bytes(), b"route-before")
            self.assertFalse(refresh_receipt.exists())
            systemctl.assert_called_once_with("start", refresh.TARGET_UNIT)
            roots.assert_called_once_with()
            quiescent.assert_called_once_with()
            self.assertGreaterEqual(verify.call_count, 2)

    def test_single_use_authority_survives_failed_pre_mutation_recovery(self):
        with tempfile.TemporaryDirectory() as raw:
            authority_root = Path(raw) / "consumed"
            authority = {
                "authorization_id": "11111111-1111-1111-1111-111111111111",
                "operation": "REFRESH_WORKSPACE_CONTROL_CODEX_WORKFLOW_V1",
            }
            authority_raw = b"authority-receipt"

            def ensure(path: Path):
                path.mkdir(parents=True, exist_ok=True)

            with (
                mock.patch.object(refresh, "AUTHORITY_ROOT", authority_root),
                mock.patch.object(refresh, "ensure_dir", side_effect=ensure),
                mock.patch.object(os, "chown"),
            ):
                marker = refresh.consume_authority(authority, authority_raw)
                self.assertTrue(marker.exists())

                with (
                    mock.patch.object(refresh, "require_target_inactive"),
                    mock.patch.object(
                        refresh,
                        "require_predecessor_unchanged",
                    ),
                    mock.patch.object(
                        refresh,
                        "run_systemctl",
                        side_effect=refresh.RefreshError("restart failed"),
                    ),
                ):
                    with self.assertRaisesRegex(
                        refresh.RefreshError,
                        "restart failed",
                    ):
                        refresh.recover_pre_mutation_failure(
                            root_policy_raw=b"root",
                            active_route_raw=b"active",
                            policy_raw=b"policy",
                            reconciler_raw=b"reconciler",
                            reconciler_override_raw=b"override",
                            others_before={},
                        )

                self.assertTrue(marker.exists())
                with self.assertRaises(FileExistsError):
                    refresh.consume_authority(authority, authority_raw)

    def test_late_work_race_keeps_authority_consumed_and_recovery_write_free(self):
        with tempfile.TemporaryDirectory() as raw:
            authority_root = Path(raw) / "consumed"
            authority = {
                "authorization_id": "22222222-2222-2222-2222-222222222222",
                "operation": "REFRESH_WORKSPACE_CONTROL_CODEX_WORKFLOW_V1",
            }
            authority_raw = b"authority-receipt"
            mutation_state = {"started": False}
            late_work = {"present": False}

            def ensure(path: Path):
                path.mkdir(parents=True, exist_ok=True)

            def predecessor(**_kwargs):
                late_work["present"] = True

            def quiescence():
                if late_work["present"]:
                    raise refresh.RefreshError("late target work appeared")

            with (
                mock.patch.object(refresh, "AUTHORITY_ROOT", authority_root),
                mock.patch.object(refresh, "ensure_dir", side_effect=ensure),
                mock.patch.object(os, "chown"),
            ):
                marker_path = refresh.consume_authority(authority, authority_raw)
                self.assertTrue(marker_path.exists())

                with (
                    mock.patch.object(refresh, "run_systemctl") as systemctl,
                    mock.patch.object(refresh, "require_target_inactive"),
                    mock.patch.object(
                        refresh,
                        "require_target_quiescent",
                        side_effect=quiescence,
                    ),
                    mock.patch.object(
                        refresh,
                        "require_predecessor_unchanged",
                        side_effect=predecessor,
                    ),
                    mock.patch.object(refresh, "atomic_file") as atomic_file,
                    mock.patch.object(
                        refresh,
                        "verify_predecessor_restored",
                        return_value=(active_state(), {}),
                    ),
                ):
                    with self.assertRaisesRegex(
                        refresh.RefreshError,
                        "late target work appeared",
                    ):
                        refresh.stop_target_close_quiescence_and_write_first_policy(
                            root_policy_raw=b"root",
                            active_route_raw=b"active",
                            policy_raw=b"policy",
                            reconciler_raw=b"reconciler",
                            reconciler_override_raw=b"override",
                            others_before={},
                            refreshed_policy_raw=b"new-policy",
                            mutation_state=mutation_state,
                        )

                    self.assertFalse(mutation_state["started"])
                    refresh.recover_pre_mutation_failure(
                        root_policy_raw=b"root",
                        active_route_raw=b"active",
                        policy_raw=b"policy",
                        reconciler_raw=b"reconciler",
                        reconciler_override_raw=b"override",
                        others_before={},
                    )

                    atomic_file.assert_not_called()
                    self.assertEqual(
                        systemctl.call_args_list,
                        [
                            mock.call("stop", refresh.TARGET_UNIT),
                            mock.call("start", refresh.TARGET_UNIT),
                        ],
                    )

                self.assertTrue(marker_path.exists())
                with self.assertRaises(FileExistsError):
                    refresh.consume_authority(authority, authority_raw)

    def test_refresh_preserves_root_overlay_capacity_and_gpu_authority(self):
        for forbidden in (
            'atomic_file(ROOT_POLICY',
            'atomic_json(ROOT_POLICY',
            'atomic_file(candidate.WORKSPACE_CONTROL_CODEX_OVERLAY_DESTINATION',
            'atomic_json(candidate.WORKSPACE_CONTROL_CODEX_OVERLAY_DESTINATION',
            "max_active_runners",
            "reserved_project_slots",
            "CUDA_VISIBLE_DEVICES",
            "NVIDIA_VISIBLE_DEVICES",
            "/dev/nvidia",
        ):
            self.assertNotIn(forbidden, HELPER)

    def test_reconciler_layers_refresh_over_historical_route_receipt(self):
        for marker in (
            "WORKSPACE_CONTROL_CODEX_WORKFLOW_INITIAL_BLOB",
            "WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_ACTIVE_RECEIPT",
            "def _workspace_control_codex_workflow_refresh(",
            "workspace_codex_refresh",
            "workspace_codex_effective",
            "effective[\"workflow_blob_sha\"]",
        ):
            self.assertIn(marker, REC)
        self.assertLess(
            REC.index("_workspace_control_codex_route_override("),
            REC.index("_workspace_control_codex_workflow_refresh("),
        )

    def test_historical_route_receipt_and_current_effective_blob_remain_distinct(self):
        self.assertEqual(
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_INITIAL_BLOB,
            refresh.OLD_BLOB,
        )
        self.assertEqual(
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_BLOB,
            refresh.NEW_BLOB,
        )


if __name__ == "__main__":
    unittest.main()
