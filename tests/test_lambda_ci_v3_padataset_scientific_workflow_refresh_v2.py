import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    ROOT / "scripts/lambda_ci_v3_padataset_scientific_workflow_refresh_v2.py"
).read_text()
LAUNCHER = (
    ROOT / "scripts/mth602_activate_lanea_l2o_v2.py"
).read_text()


class PADatasetScientificWorkflowRefreshV2Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(
            HELPER,
            "lambda_ci_v3_padataset_scientific_workflow_refresh_v2.py",
            "exec",
        )
        compile(LAUNCHER, "mth602_activate_lanea_l2o_v2.py", "exec")

    def test_operator_launcher_is_exact_and_non_generic(self):
        for marker in (
            'p.add_argument("--expected-head", required=True)',
            '"source_head": args.expected_head',
            '"--expected-head", args.expected_head',
            'EXPECTED_PAD_MAIN = "34e150ae4fe349889a054aa2c12d33393cf64f66"',
            'EXPECTED_WORKFLOW_BLOB = "bca2eabe3afe70ec3115391e5a6c24daefd1498b"',
            'EXPECTED_CONFIRM = "MERGE_PR39_AND_ACTIVATE_GPU0_L2O"',
            'EXPECTED_PROVIDER_CONFIRM = "PROVIDER_LANEA_QUEUE_ZERO_VERIFIED"',
            'p.add_argument("--padataset-root", type=pathlib.Path, required=True)',
            'p.add_argument("--provider-queue-confirm", required=True)',
            'local_padataset_preflight(args.padataset_root)',
            '"active_workflow_runs": 0',
            '"assigned_jobs": 0',
            '"running_jobs": 0',
            "candidate.verify_installed",
            "refresh.require_target_quiescent",
            "MTH602_LANEA_L2O_REFRESH_V2_POSTVERIFY=PASS",
        ):
            self.assertIn(marker, LAUNCHER)
        self.assertNotIn("shell=True", LAUNCHER)
        self.assertNotIn("os.system(", LAUNCHER)
        self.assertNotIn("gh api", LAUNCHER)
        self.assertNotIn('["gh"', LAUNCHER)
        self.assertNotIn("api.github.com", LAUNCHER)
        self.assertNotIn("GH_TOKEN", LAUNCHER)

    def test_effective_v2_digest_is_used_for_lane_a_managed_addition(self):
        block = REC[
            REC.index("for destination, binding in scientific_additions.items():"):
            REC.index("for destination, binding in dual_additions.items():")
        ]
        self.assertIn("scientific_workflow_effective_refresh is not None", block)
        self.assertIn(
            'expected_addition_sha = scientific_workflow_effective_refresh[',
            block,
        )
        self.assertNotIn(
            'expected_addition_sha = scientific_workflow_refresh[',
            block,
        )

    def test_rollback_is_postverified_before_marking_complete(self):
        for marker in (
            "rollback lane-A controller did not return active/running/enabled",
            "candidate.verify_installed(BASE_MANIFEST)",
            "require_snapshot_same(others_before, rollback_others)",
            '"rollback_target_controller_after"',
            '"rollback_existing_controller_snapshot_after"',
        ):
            self.assertIn(marker, HELPER)

    def test_exact_v1_to_v2_transition_is_frozen(self):
        for marker in (
            '"4cf390ec334b0569dbfc2399ff86c2d892f97586"',
            '"bca2eabe3afe70ec3115391e5a6c24daefd1498b"',
            '"34e150ae4fe349889a054aa2c12d33393cf64f66"',
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v1_receipt_before_v2(self):
        for marker in (
            "_padataset_scientific_workflow_refresh_v2",
            "workflow refresh v2 requires v1 predecessor",
            "scientific_workflow_refresh_v2",
            "scientific_workflow_effective_refresh",
        ):
            self.assertIn(marker, REC)
        self.assertLess(
            REC.index("scientific_workflow_refresh_v2 ="),
            REC.index("scientific_workflow_effective_refresh ="),
        )

    def test_dual_lane_predecessor_still_binds_immutable_lane_a_v1_receipt(self):
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

    def test_helper_preserves_v1_and_rolls_back_to_v1(self):
        for marker in (
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_ACTIVE_RECEIPT",
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT",
            "REFRESH_PADATASET_SCIENTIFIC_WORKFLOW_V2",
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_PREFLIGHT",
            "prior_refresh_receipt_sha256",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V1",
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2=PASS",
            "O_EXCL",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn("PRIOR_REFRESH_ACTIVE.unlink", HELPER)

    def test_helper_receipt_bindings_are_exact(self):
        lines = set(HELPER.splitlines())
        self.assertIn(
            "TARGET_CLASS = candidate.PADATASET_SCIENTIFIC_TARGET_CLASS",
            lines,
        )
        self.assertIn(
            "PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT",
            lines,
        )
        self.assertIn(
            "OLD_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_BLOB",
            lines,
        )
        self.assertIn(
            "NEW_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_BLOB",
            lines,
        )
        self.assertIn(
            "PAD_MAIN = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_PAD_MAIN",
            lines,
        )

    def test_helper_requires_exact_v1_predecessor_lineage(self):
        for marker in (
            '!= "V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH"',
            "candidate.PADATASET_SCIENTIFIC_WORKFLOW_BLOB",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            'prior_refresh.get("controller_policy_sha256")',
            "does not match refresh v1",
        ):
            self.assertIn(marker, HELPER)

    def test_helper_requires_zero_lane_a_work_and_changes_only_lane_a(self):
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

    def test_v2_is_effective_for_lane_a_without_rebinding_dual_predecessor(self):
        block = REC[
            REC.index("scientific_workflow_refresh_v2 ="):
            REC.index("scientific_dual_workflow_refresh =")
        ]
        self.assertIn(
            "scientific_workflow_refresh_v2\n"
            "        if scientific_workflow_refresh_v2 is not None",
            block,
        )
        self.assertIn(
            "_padataset_scientific_dual_lane_override(\n"
            "            scientific_override,\n"
            "            scientific_workflow_refresh,",
            block,
        )


if __name__ == "__main__":
    unittest.main()
