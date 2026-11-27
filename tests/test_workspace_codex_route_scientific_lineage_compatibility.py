from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lambda_ci_v3_reconciler as reconciler  # noqa: E402


class CodexRouteScientificLineageCompatibilityTests(unittest.TestCase):
    def test_live_lane_b_base_and_v9_successor_are_exact(self):
        self.assertEqual(
            reconciler.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_BLOB,
            "6280a6e7b2ad8cc379277fa320e8839a94f360ec",
        )
        self.assertEqual(
            reconciler.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_BLOB,
            "6753795041090a5331a80354f59945be006ac889",
        )

    def test_live_lane_a_v4_successor_is_exact(self):
        self.assertEqual(
            reconciler.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V4_BLOB,
            "39190413abbd801bd6d25c2166ac36a7a69968fb",
        )

    def test_full_attested_refresh_chain_is_present(self):
        for version in range(2, 5):
            self.assertTrue(
                hasattr(
                    reconciler,
                    f"_padataset_scientific_workflow_refresh_v{version}",
                )
            )
        self.assertTrue(
            hasattr(reconciler, "_padataset_scientific_dual_lane_workflow_refresh")
        )
        for version in range(2, 10):
            self.assertTrue(
                hasattr(
                    reconciler,
                    f"_padataset_scientific_dual_lane_workflow_refresh_v{version}",
                )
            )

    def test_codex_route_layer_remains_present_after_science_lineage_rebase(self):
        self.assertTrue(
            hasattr(reconciler, "_workspace_control_codex_route_override")
        )
        self.assertTrue(
            hasattr(
                reconciler,
                "_verify_workspace_control_codex_route_effective_state",
            )
        )
        self.assertEqual(
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_INITIAL_BLOB,
            "520da69cfb9b28c81fb1121a16c12d3715892cc7",
        )
        self.assertEqual(
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_BLOB,
            "b17526353acb531010fce019337f7b3080ba235b",
        )
        self.assertEqual(
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_REFRESH_V2_BLOB,
            "683d2aa85ec455f853ef2a99dd07d8fe5242cc65",
        )
        self.assertEqual(
            reconciler.WORKSPACE_CONTROL_CODEX_WORKFLOW_BLOB,
            "80da66083ec77e0d542caf97c11a3fe55f13b3dd",
        )
        self.assertTrue(
            hasattr(reconciler, "_workspace_control_codex_workflow_refresh")
        )
        self.assertTrue(
            hasattr(reconciler, "_workspace_control_codex_workflow_refresh_v2")
        )
        self.assertTrue(
            hasattr(reconciler, "_workspace_control_codex_workflow_refresh_v3")
        )

    def test_source_selects_effective_science_refresh_before_codex_overlay(self):
        src = (SCRIPTS / "lambda_ci_v3_reconciler.py").read_text()
        self.assertIn("scientific_workflow_effective_refresh", src)
        self.assertIn("scientific_dual_effective_refresh", src)
        self.assertIn(
            "_padataset_scientific_dual_lane_workflow_refresh_v9(",
            src,
        )
        self.assertIn(
            "_verify_workspace_control_codex_route_effective_state(",
            src,
        )


if __name__ == "__main__":
    unittest.main()
