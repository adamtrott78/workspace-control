import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    ROOT / "scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v5.py"
).read_text()


class PADatasetScientificDualWorkflowRefreshV5Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(
            HELPER,
            "lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v5.py",
            "exec",
        )

    def test_exact_v4_to_v5_transition_is_frozen(self):
        for marker in (
            '"650a529aeee51b53234a84b3afea8743cc527688"',
            '"ba549b4d1560b18a9e40ef531387bc1accc90d43"',
            '"b0cbf6c1436e18cb5b793596dd790560bd2cec08"',
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V5_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v4_receipt_before_v5(self):
        for marker in (
            "_padataset_scientific_dual_lane_workflow_refresh_v5",
            "workflow refresh v5 requires v4 predecessor",
            "scientific_dual_workflow_refresh_v5",
            "scientific_dual_effective_refresh",
        ):
            self.assertIn(marker, REC)
        self.assertLess(
            REC.index("scientific_dual_workflow_refresh_v5"),
            REC.index("scientific_dual_effective_refresh"),
        )

    def test_helper_preserves_v4_and_rolls_back_to_v4(self):
        for marker in (
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4_ACTIVE_RECEIPT",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V5_ACTIVE_RECEIPT",
            "REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V5",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V5_PREFLIGHT",
            "prior_refresh_receipt_sha256",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V4",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V5=PASS",
            "O_EXCL",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn("PRIOR_REFRESH_ACTIVE.unlink", HELPER)

    def test_helper_receipt_bindings_are_exact(self):
        lines = set(HELPER.splitlines())
        self.assertIn(
            "PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V5_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "OLD_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4_BLOB",
            lines,
        )
        self.assertIn(
            "NEW_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V5_BLOB",
            lines,
        )
        self.assertIn(
            "PAD_MAIN = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V5_PAD_MAIN",
            lines,
        )

    def test_helper_requires_exact_v4_predecessor_lineage(self):
        for marker in (
            '!= "V3_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4"',
            "candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_BLOB",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            'prior_refresh.get("controller_policy_sha256")',
            "does not match refresh v4",
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

    def test_v5_remains_fallback_preference_over_v4(self):
        block = REC[
            REC.index("scientific_dual_workflow_refresh_v5 ="):
            REC.index("scientific_overrides =")
        ]
        v5 = block.index("scientific_dual_workflow_refresh_v5", 1)
        v4 = block.rindex("scientific_dual_workflow_refresh_v4")
        self.assertLess(v5, v4)


if __name__ == "__main__":
    unittest.main()
