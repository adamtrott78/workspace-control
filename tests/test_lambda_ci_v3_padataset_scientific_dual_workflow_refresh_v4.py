import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    ROOT / "scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v4.py"
).read_text()


class PADatasetScientificDualWorkflowRefreshV4Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(
            HELPER,
            "lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v4.py",
            "exec",
        )

    def test_exact_v3_to_v4_transition_is_frozen(self):
        for marker in (
            '"85e8deef5240e2d6d7db34318e6b2c35947a83f3"',
            '"650a529aeee51b53234a84b3afea8743cc527688"',
            '"6a3c17c27a401f059f9ded1287d274d766f61283"',
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v3_receipt_before_v4(self):
        for marker in (
            "_padataset_scientific_dual_lane_workflow_refresh_v4",
            "workflow refresh v4 requires v3 predecessor",
            "scientific_dual_workflow_refresh_v4",
            "scientific_dual_effective_refresh",
        ):
            self.assertIn(marker, REC)
        self.assertLess(
            REC.index("scientific_dual_workflow_refresh_v4"),
            REC.index("scientific_dual_effective_refresh"),
        )

    def test_helper_preserves_v3_and_rolls_back_to_v3(self):
        for marker in (
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4_ACTIVE_RECEIPT",
            "REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V4",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4_PREFLIGHT",
            "prior_refresh_receipt_sha256",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V3",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4=PASS",
            "O_EXCL",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn("PRIOR_REFRESH_ACTIVE.unlink", HELPER)

    def test_helper_receipt_bindings_are_exact(self):
        lines = set(HELPER.splitlines())
        self.assertIn(
            "PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "OLD_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_BLOB",
            lines,
        )
        self.assertIn(
            "NEW_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4_BLOB",
            lines,
        )
        self.assertIn(
            "PAD_MAIN = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V4_PAD_MAIN",
            lines,
        )

    def test_helper_requires_exact_v3_predecessor_lineage(self):
        for marker in (
            '!= "V3_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3"',
            "candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2_BLOB",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            'prior_refresh.get("controller_policy_sha256")',
            "does not match refresh v3",
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

    def test_v4_is_effective_preference_over_v3(self):
        block = REC[
            REC.index("scientific_dual_workflow_refresh_v4 ="):
            REC.index("scientific_overrides =")
        ]
        self.assertIn(
            "scientific_dual_workflow_refresh_v4\n"
            "        if scientific_dual_workflow_refresh_v4 is not None",
            block,
        )
        self.assertIn("scientific_dual_workflow_refresh_v3", block)


if __name__ == "__main__":
    unittest.main()
