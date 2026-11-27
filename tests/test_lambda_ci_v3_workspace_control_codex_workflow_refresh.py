from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


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

    def test_refresh_is_single_use_authority_bound_and_rollback_safe(self):
        for marker in (
            "REFRESH_WORKSPACE_CONTROL_CODEX_WORKFLOW_V1",
            "require_target_quiescent()",
            "consume_authority(authority, authority_raw)",
            "os.O_EXCL",
            'run_systemctl("stop", TARGET_UNIT)',
            'run_systemctl("start", TARGET_UNIT)',
            "require_snapshot_same(others_before, others_after)",
            "COMMITTED_ACTIVE_CODEX_WORKFLOW_REFRESH",
            "ROLLED_BACK_PREVIOUS_CODEX_WORKFLOW",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn('run_systemctl("stop", PROVISIONER_UNIT)', HELPER)
        self.assertNotIn('run_systemctl("restart"', HELPER)

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
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_BLOB,
            refresh.NEW_BLOB,
        )


if __name__ == "__main__":
    unittest.main()
