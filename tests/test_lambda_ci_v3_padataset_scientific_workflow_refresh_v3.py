import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    ROOT / "scripts/lambda_ci_v3_padataset_scientific_workflow_refresh_v3.py"
).read_text()
LAUNCHER = (ROOT / "scripts/mth602_activate_lanea_refresh_v3.py").read_text()


class PADatasetScientificWorkflowRefreshV3Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(
            HELPER,
            "lambda_ci_v3_padataset_scientific_workflow_refresh_v3.py",
            "exec",
        )
        compile(LAUNCHER, "mth602_activate_lanea_refresh_v3.py", "exec")

    def test_exact_v2_to_v3_transition_is_frozen(self):
        for marker in (
            '"bca2eabe3afe70ec3115391e5a6c24daefd1498b"',
            '"ea5d844c494013eb2322686d7345b5a1b15443c4"',
            '"51073327c688d243961a0caabbb5358cc065ced1"',
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v2_receipt_before_v3(self):
        for marker in (
            "_padataset_scientific_workflow_refresh_v3",
            "workflow refresh v3 requires v2 predecessor",
            "scientific_workflow_refresh_v3",
            "scientific_workflow_effective_refresh",
        ):
            self.assertIn(marker, REC)
        block = REC[
            REC.index("scientific_workflow_refresh_v2 ="):
            REC.index("scientific_dual_workflow_refresh =")
        ]
        self.assertIn(
            "_padataset_scientific_workflow_refresh_v3(\n"
            "            scientific_workflow_refresh_v2",
            block,
        )
        self.assertIn(
            "scientific_workflow_refresh_v3\n"
            "        if scientific_workflow_refresh_v3 is not None",
            block,
        )

    def test_dual_lane_predecessor_remains_immutable_lane_a_v1(self):
        block = REC[
            REC.index("def _padataset_scientific_dual_lane_override"):
            REC.index("def _padataset_scientific_dual_lane_workflow_refresh")
        ]
        self.assertIn(
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_ACTIVE_RECEIPT.read_bytes()",
            block,
        )
        self.assertNotIn(
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT.read_bytes()",
            block,
        )
        self.assertNotIn(
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT.read_bytes()",
            block,
        )

    def test_effective_v3_digest_is_used_for_lane_a_managed_addition(self):
        block = REC[
            REC.index("for destination, binding in scientific_additions.items():"):
            REC.index("for destination, binding in dual_additions.items():")
        ]
        self.assertIn("scientific_workflow_effective_refresh is not None", block)
        self.assertIn(
            'expected_addition_sha = scientific_workflow_effective_refresh[',
            block,
        )

    def test_helper_receipt_bindings_are_exact(self):
        lines = set(HELPER.splitlines())
        for marker in (
            "TARGET_CLASS = candidate.PADATASET_SCIENTIFIC_TARGET_CLASS",
            "PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT",
            "REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT",
            "OLD_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_BLOB",
            "NEW_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_BLOB",
            "PAD_MAIN = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_PAD_MAIN",
        ):
            self.assertIn(marker, lines)

    def test_helper_requires_exact_v2_predecessor_and_rolls_back_to_v2(self):
        for marker in (
            '!= "V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2"',
            "candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_BLOB",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            "does not match refresh v2",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V2",
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3=PASS",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn("PRIOR_REFRESH_ACTIVE.unlink", HELPER)

    def test_helper_is_lane_a_only_and_fail_closed(self):
        for marker in (
            '"assigned_jobs": 0',
            '"running_jobs": 0',
            '"active_workflow_runs": 0',
            "require_target_quiescent()",
            'base.run_systemctl("stop", TARGET_UNIT)',
            'base.run_systemctl("start", TARGET_UNIT)',
            "require_snapshot_same(others_before, others_after)",
            "candidate.verify_installed(BASE_MANIFEST)",
            "O_EXCL",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn('run_systemctl("stop", PROVISIONER_UNIT)', HELPER)

    def test_launcher_proves_provider_zero_work_before_sudo(self):
        for marker in (
            'EXPECTED_PAD_MAIN = "51073327c688d243961a0caabbb5358cc065ced1"',
            'EXPECTED_WORKFLOW_BLOB = "ea5d844c494013eb2322686d7345b5a1b15443c4"',
            'WORKFLOW_FILE = "lambda-ci-scientific.yml"',
            '"queued", "in_progress"',
            "LANEA_PROVIDER_ZERO_WORK=PASS",
            'run(["sudo", "-v"])',
            "MTH602_LANEA_REFRESH_V3_POSTVERIFY=PASS",
            "helper.require_target_quiescent()",
            "PADATASET_SCIENTIFIC_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, LAUNCHER)
        self.assertLess(
            LAUNCHER.index("provider_zero_work()"),
            LAUNCHER.index('run(["sudo", "-v"])'),
        )
        self.assertNotIn("shell=True", LAUNCHER)
        self.assertNotIn("os.system(", LAUNCHER)


if __name__ == "__main__":
    unittest.main()
