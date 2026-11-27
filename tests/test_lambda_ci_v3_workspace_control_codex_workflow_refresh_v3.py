from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lambda_ci_policy_compiler as compiler  # noqa: E402
import lambda_ci_v3_reconciler as reconciler  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "codex_workflow_refresh_v3",
    SCRIPTS / "lambda_ci_v3_workspace_control_codex_workflow_refresh_v3.py",
)
refresh = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["codex_workflow_refresh_v3"] = refresh
spec.loader.exec_module(refresh)

HELPER = (
    SCRIPTS / "lambda_ci_v3_workspace_control_codex_workflow_refresh_v3.py"
).read_text(encoding="utf-8")
REC = (SCRIPTS / "lambda_ci_v3_reconciler.py").read_text(encoding="utf-8")


class WorkspaceControlCodexWorkflowRefreshV3Tests(unittest.TestCase):
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

    def test_exact_v2_and_v3_workflow_lineage(self):
        self.assertEqual(
            refresh.OLD_BLOB,
            "683d2aa85ec455f853ef2a99dd07d8fe5242cc65",
        )
        self.assertEqual(
            refresh.NEW_BLOB,
            "21f1615b859496fa1919103b153374da85345c3e",
        )
        self.assertEqual(
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V2_BLOB,
            refresh.OLD_BLOB,
        )
        self.assertEqual(
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_BLOB,
            refresh.NEW_BLOB,
        )

    def test_v3_refresh_changes_only_codex_blob_and_policy_digest(self):
        before = self.predecessor_policy()
        after = refresh.build_refreshed_policy(before)
        before_routes = {
            row["route_id"]: row for row in before["trusted_workflows"]
        }
        after_routes = {
            row["route_id"]: row for row in after["trusted_workflows"]
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

    def test_v3_receipt_is_separate_and_binds_v2_receipt(self):
        self.assertNotEqual(refresh.PRIOR_REFRESH_ACTIVE, refresh.REFRESH_ACTIVE)
        self.assertEqual(
            refresh.PRIOR_REFRESH_ACTIVE,
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT,
        )
        self.assertEqual(
            refresh.REFRESH_ACTIVE,
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT,
        )
        for marker in (
            "REFRESH_WORKSPACE_CONTROL_CODEX_WORKFLOW_V3",
            '"mode": "V3_WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V3"',
            '"previous_refresh_receipt_sha256": sha(prior_refresh_raw)',
            "PRIOR_REFRESH_ACTIVE.read_bytes() != prior_refresh_raw",
        ):
            self.assertIn(marker, HELPER)

    def test_v3_final_quiescence_still_guards_first_managed_write(self):
        events: list[str] = []
        mutation_state = {"started": False}
        late = {"present": False}

        def stop(*_args):
            events.append("stop")

        def inactive():
            events.append("inactive")
            return {}

        def quiescence():
            events.append("quiescence")
            if late["present"]:
                raise refresh.RefreshError("late target work appeared")

        def predecessor(**_kwargs):
            events.append("predecessor")
            late["present"] = True

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
                    active_route_raw=b"route",
                    prior_refresh_raw=b"prior",
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

    def test_reconciler_layers_v3_over_v2(self):
        for marker in (
            "WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT",
            "def _workspace_control_codex_workflow_refresh_v3(",
            "workspace_codex_refresh_v3",
        ):
            self.assertIn(marker, REC)
        layer = REC.index("workspace_codex_refresh = (")
        v1_call = REC.index(
            "_workspace_control_codex_workflow_refresh(workspace_codex_route)",
            layer,
        )
        v2_call = REC.index(
            "_workspace_control_codex_workflow_refresh_v2(",
            layer,
        )
        v3_call = REC.index(
            "_workspace_control_codex_workflow_refresh_v3(",
            layer,
        )
        effective = REC.index("workspace_codex_effective = (", layer)
        self.assertLess(v1_call, v2_call)
        self.assertLess(v2_call, v3_call)
        self.assertLess(v3_call, effective)

    def test_v3_refresh_does_not_widen_root_capacity_or_gpu_authority(self):
        for forbidden in (
            'atomic_file(ROOT_POLICY',
            'atomic_json(ROOT_POLICY',
            "max_active_runners",
            "reserved_project_slots",
            "CUDA_VISIBLE_DEVICES",
            "NVIDIA_VISIBLE_DEVICES",
            "/dev/nvidia",
        ):
            self.assertNotIn(forbidden, HELPER)


if __name__ == "__main__":
    unittest.main()
