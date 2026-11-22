import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    ROOT / "scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v7.py"
).read_text()


class PADatasetScientificDualWorkflowRefreshV7Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(
            HELPER,
            "lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v7.py",
            "exec",
        )

    def test_exact_v6_to_v7_transition_is_frozen(self):
        for marker in (
            '"5e8abef47f7a59eab3d715836658c0e9067de187"',
            '"85dc8f289a972dddbb1a838d5596def6d872118b"',
            '"af4b221f6e6014ce2047e41d9c4e91f511d9fe84"',
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V7_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v6_receipt_before_v7(self):
        for marker in (
            "_padataset_scientific_dual_lane_workflow_refresh_v7",
            "workflow refresh v7 requires v6 predecessor",
            "scientific_dual_workflow_refresh_v7",
            "scientific_dual_effective_refresh",
        ):
            self.assertIn(marker, REC)
        self.assertLess(
            REC.index("scientific_dual_workflow_refresh_v7"),
            REC.index("scientific_dual_effective_refresh"),
        )

    def test_helper_preserves_v6_and_rolls_back_to_v6(self):
        for marker in (
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V6_ACTIVE_RECEIPT",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V7_ACTIVE_RECEIPT",
            "REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V7",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V7_PREFLIGHT",
            "prior_refresh_receipt_sha256",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V6",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V7=PASS",
            "O_EXCL",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn("PRIOR_REFRESH_ACTIVE.unlink", HELPER)

    def test_helper_receipt_bindings_are_exact(self):
        lines = set(HELPER.splitlines())
        self.assertIn(
            "PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V6_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V7_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "OLD_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V6_BLOB",
            lines,
        )
        self.assertIn(
            "NEW_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V7_BLOB",
            lines,
        )
        self.assertIn(
            "PAD_MAIN = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V7_PAD_MAIN",
            lines,
        )

    def test_helper_requires_exact_v6_predecessor_lineage(self):
        for marker in (
            '!= "V3_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V6"',
            "candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V5_BLOB",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            'prior_refresh.get("controller_policy_sha256")',
            "does not match refresh v6",
        ):
            self.assertIn(marker, HELPER)

    def test_helper_requires_zero_work_and_changes_only_lane_b(self):
        for marker in (
            '"assigned_jobs": 0',
            '"running_jobs": 0',
            '"active_workflow_runs": 0',
            "require_target_quiescent()",
            'base.run_systemctl("stop", TARGET_UNIT)',
            'base.run_systemctl("start", TARGET_UNIT)',
            "require_snapshot_same(others_before, others_after)",
            "candidate.verify_installed(BASE_MANIFEST)",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn('run_systemctl("stop", PROVISIONER_UNIT)', HELPER)
        self.assertNotIn('run_systemctl("restart"', HELPER)

    def test_v7_is_effective_preference_over_v6(self):
        block = REC[
            REC.index("scientific_dual_effective_refresh ="):
            REC.index("scientific_overrides =")
        ]
        self.assertIn("scientific_dual_workflow_refresh_v7", block)
        self.assertIn("scientific_dual_workflow_refresh_v6", block)
        self.assertLess(
            block.index("scientific_dual_workflow_refresh_v7"),
            block.index("scientific_dual_workflow_refresh_v6"),
        )


if __name__ == "__main__":
    unittest.main()
