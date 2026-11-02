import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_v3_production_cutover_live.sh"


class ProductionCutoverLiveOperatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SCRIPT.read_text(encoding="utf-8")

    def test_shell_syntax_is_valid(self):
        proc = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_exact_three_production_routes_are_pinned(self):
        required = {
            'WC_OLD_BLOB="524e01916e1a826efd1edb4792023973d7b3c73c"',
            'PAD_CPU_OLD_BLOB="5e6a1d4a47ecdfa8b40d3bea23fa8739cc12cd9e"',
            'PAD_GPU_OLD_BLOB="3e0c79dc1b8bed7b1480cc745c478c190a3c7da4"',
            'WC_TARGET_CLASS="workspace-control-control-small-v1"',
            'PAD_CPU_TARGET_CLASS="padataset-cpu-public-v1"',
            'PAD_GPU_TARGET_CLASS="padataset-gpu-single-public-v1"',
            'WC_TARGET_SCALE_SET="lambda-workspace-control-control-small"',
            'PAD_CPU_TARGET_SCALE_SET="lambda-padataset-cpu-public"',
            'PAD_GPU_TARGET_SCALE_SET="lambda-padataset-gpu-single-public"',
        }
        for value in required:
            self.assertIn(value, self.text)

    def test_all_v3_classes_are_inactive_and_boot_disabled_before_authority(self):
        classes = (
            "workspace-control-control-small-v1",
            "padataset-cpu-public-v1",
            "padataset-gpu-single-public-v1",
            "research-cpu-public-v1",
            "research-gpu-single-public-v1",
            "research-gpu-single-runtime-v1",
            "research-model-single-offline-v1",
            "research-model-dual-offline-v1",
            "research-model-dual-public-v1",
        )
        for class_id in classes:
            self.assertIn(class_id, self.text)
        loop = self.text.index("for class_id in \\\n  workspace-control-control-small-v1")
        authority = self.text.index("PRODUCTION_AUTHORITY_CREATED=PASS")
        self.assertLess(loop, authority)
        self.assertIn(
            'require_inactive "workspace-ci-v3-controller@$class_id.service"',
            self.text[loop:authority],
        )
        self.assertIn(
            'require_not_enabled "workspace-ci-v3-controller@$class_id.service"',
            self.text[loop:authority],
        )

    def test_verifier_and_runtime_bindings_precede_authority(self):
        authority = self.text.index("PRODUCTION_AUTHORITY_CREATED=PASS")
        self.assertLess(
            self.text.index("PRODUCTION_RECONCILER_BINDING=PASS"),
            authority,
        )
        self.assertLess(
            self.text.index("PRODUCTION_RUNTIME_REFRESH_BINDING=PASS"),
            authority,
        )
        self.assertIn(
            'reconciler_source_head"]==os.environ["EXPECTED_HEAD"]',
            self.text,
        )
        self.assertIn(
            'EXPECTED_RUNTIME_SOURCE_HEAD="e1a2d44bf24a3a7bf53d77baf0fc6170e4af0f15"',
            self.text,
        )

    def test_authority_is_after_scale_set_and_workflow_preflights(self):
        authority = self.text.index("PRODUCTION_AUTHORITY_CREATED=PASS")
        for marker in (
            "PRODUCTION_SCALE_SET_PREFLIGHT=PASS",
            "PRODUCTION_GENERATION_FREEZE=PASS",
            "PRODUCTION_WORKFLOW_OLD_BLOB=PASS",
            "PREFLIGHT_NO_ACTIVE_WORKFLOW_RUN=PASS",
            "PADATASET_VALIDATION_PR=PASS",
        ):
            self.assertLess(self.text.index(marker), authority, marker)

    def test_no_workflow_retarget_before_generation_exclusion(self):
        prepare = self.text.index(
            'echo "PRODUCTION_GENERATION_EXCLUSION=ACTIVE'
        )
        first_update = self.text.index(
            'WC_COMMIT_SHA="$(update_workflow'
        )
        self.assertLess(prepare, first_update)
        self.assertIn(
            '--prepare \\\n    --generation-dir "$GENERATION"',
            self.text[:first_update],
        )

    def test_activation_requires_exact_workflow_confirmation(self):
        retarget = self.text.index("PRODUCTION_WORKFLOW_RETARGET=PASS")
        activate = self.text.index("PRODUCTION_V3_ACTIVATION=PASS")
        self.assertLess(retarget, activate)
        segment = self.text[retarget:activate]
        self.assertIn(
            '"mode":"V3_PRODUCTION_WORKFLOW_CUTOVER_CONFIRMED"',
            segment,
        )
        self.assertIn("--workflow-confirmation", segment)

    def test_three_real_production_validations_precede_commit(self):
        commit = self.text.index("PRODUCTION_V3_COMMIT=PASS")
        segment = self.text[:commit]
        self.assertIn(
            '"/workspace-control-validate $OPERATOR_HEAD"',
            segment,
        )
        self.assertIn('"/lambda-ci-cpu $PAD_VALIDATION_SHA"', segment)
        self.assertIn('"/lambda-ci-gpu $PAD_VALIDATION_SHA"', segment)
        self.assertIn(
            'runner.startswith(os.environ["SCALE_SET"]+"-")',
            segment,
        )
        self.assertIn("POST_VALIDATION_RESOURCE_DRAIN=PASS", segment)
        self.assertIn(
            '"mode":"V3_PRODUCTION_VALIDATION_CONFIRMED"',
            segment,
        )

    def test_rollback_restores_workflows_then_uses_root_transaction(self):
        start = self.text.index("rollback_transaction()")
        end = self.text.index("on_exit()", start)
        segment = self.text[start:end]
        restore = segment.index("restore_workflow")
        root = segment.index("--rollback")
        self.assertLess(restore, root)
        self.assertIn("cancel_validation_runs", segment)
        self.assertIn("write_rollback_confirmation", segment)
        self.assertIn("RECOVERY_FAIL_CLOSED", segment)

    def test_credentials_are_kept_only_for_committed_production_or_unresolved_rollback(self):
        self.assertIn(
            'if [ "$ROLLBACK_DONE" -eq 1 ] || [ -z "$TX_RECEIPT" ]; then',
            self.text,
        )
        self.assertIn(
            'remove_staged_credentials',
            self.text,
        )
        self.assertIn(
            'CUTOVER_COMMITTED=1',
            self.text,
        )

    def test_post_commit_keeps_all_research_v3_classes_inactive(self):
        post = self.text.index("POST_COMMIT_EFFECTIVE_GENERATION_VERIFY=PASS")
        tail = self.text[post:]
        for class_id in (
            "research-cpu-public-v1",
            "research-gpu-single-public-v1",
            "research-gpu-single-runtime-v1",
            "research-model-single-offline-v1",
            "research-model-dual-offline-v1",
            "research-model-dual-public-v1",
        ):
            self.assertIn(class_id, tail)
        self.assertIn(
            "POST_COMMIT_V2_CONTROLLERS_RETIRED_OR_GATED=PASS",
            tail,
        )
        self.assertIn("V3_PRODUCTION_CUTOVER_ACCEPTED=PASS", tail)


if __name__ == "__main__":
    unittest.main()
