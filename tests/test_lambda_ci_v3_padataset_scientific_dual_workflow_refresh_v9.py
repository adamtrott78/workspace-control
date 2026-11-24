import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    ROOT / "scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v9.py"
).read_text()


class PADatasetScientificDualWorkflowRefreshV9Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(
            HELPER,
            "lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v9.py",
            "exec",
        )

    def test_exact_v7_to_v8_transition_is_frozen(self):
        for marker in (
            '"85dc8f289a972dddbb1a838d5596def6d872118b"',
            '"8375dd0a0733b01de38f677dee58a373d3adcb48"',
            '"51073327c688d243961a0caabbb5358cc065ced1"',
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v7_receipt_before_v8(self):
        for marker in (
            "_padataset_scientific_dual_lane_workflow_refresh_v9",
            "workflow refresh v9 requires v8 predecessor",
            "scientific_dual_workflow_refresh_v9",
            "scientific_dual_effective_refresh",
        ):
            self.assertIn(marker, REC)
        self.assertLess(
            REC.index("scientific_dual_workflow_refresh_v9"),
            REC.index("scientific_dual_effective_refresh"),
        )

    def test_helper_preserves_v7_and_rolls_back_to_v7(self):
        for marker in (
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT",
            "REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V8",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_PREFLIGHT",
            "prior_refresh_receipt_sha256",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V8",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9=PASS",
            "O_EXCL",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn("PRIOR_REFRESH_ACTIVE.unlink", HELPER)

    def test_helper_receipt_bindings_are_exact(self):
        lines = set(HELPER.splitlines())
        self.assertIn(
            "PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "OLD_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_BLOB",
            lines,
        )
        self.assertIn(
            "NEW_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_BLOB",
            lines,
        )
        self.assertIn(
            "PAD_MAIN = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_PAD_MAIN",
            lines,
        )

    def test_helper_requires_exact_v7_predecessor_lineage(self):
        for marker in (
            '!= "V3_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V7"',
            "candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V6_BLOB",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            'prior_refresh.get("controller_policy_sha256")',
            "does not match refresh v8",
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

    def test_v8_is_effective_preference_over_v7(self):
        block = REC[
            REC.index("scientific_dual_workflow_refresh_v9 ="):
            REC.index("scientific_overrides =")
        ]
        self.assertIn(
            "scientific_dual_workflow_refresh_v9\n"
            "        if scientific_dual_workflow_refresh_v9 is not None",
            block,
        )
        self.assertIn("scientific_dual_workflow_refresh_v7", block)


    def test_live_lane_a_v2_is_effective_without_rebinding_dual_predecessor(self):
        for marker in (
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT",
            "_padataset_scientific_workflow_refresh_v2",
            "scientific_workflow_effective_refresh",
        ):
            self.assertIn(marker, REC)

        addition_block = REC[
            REC.index("for destination, binding in scientific_additions.items():"):
            REC.index("for destination, binding in dual_additions.items():")
        ]
        self.assertIn("scientific_workflow_effective_refresh is not None", addition_block)
        self.assertIn(
            'expected_addition_sha = scientific_workflow_effective_refresh[',
            addition_block,
        )
        self.assertNotIn(
            'expected_addition_sha = scientific_workflow_refresh[',
            addition_block,
        )

        dual_block = REC[
            REC.index("def _padataset_scientific_dual_lane_override"):
            REC.index("def _padataset_scientific_dual_lane_workflow_refresh")
        ]
        self.assertIn(
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_ACTIVE_RECEIPT.read_bytes()",
            dual_block,
        )
        self.assertNotIn(
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT.read_bytes()",
            dual_block,
        )



if __name__ == "__main__":
    unittest.main()

    def test_exact_control_matrix_lane_b_transition(self):
        self.assertIn('"8375dd0a0733b01de38f677dee58a373d3adcb48"', REC)
        self.assertIn('"6753795041090a5331a80354f59945be006ac889"', REC)
        self.assertIn('"7cfe0ab61cc16785f4d267273b48a63361c595dd"', REC)
        self.assertIn("PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V8_ACTIVE_RECEIPT", HELPER)
        self.assertIn("PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT", HELPER)
        self.assertIn("PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V8_BLOB", HELPER)
        self.assertIn("PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_BLOB", HELPER)
