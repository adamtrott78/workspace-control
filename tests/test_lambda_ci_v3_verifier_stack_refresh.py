import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RECONCILER = ROOT / "scripts" / "lambda_ci_v3_reconciler.py"
ACTIVATOR = ROOT / "scripts" / "lambda_ci_v3_root_activation.py"
UPDATER = ROOT / "scripts" / "lambda_ci_v3_verifier_stack_live_update_v1.py"
WRAPPER = ROOT / "scripts" / "lambda_ci_v3_repair_research_gpu_and_resume_roots_v1.py"


class V3VerifierStackRefreshTests(unittest.TestCase):
    def test_reconciler_accepts_only_exact_attested_overrides(self):
        text=RECONCILER.read_text(encoding="utf-8")
        self.assertIn("V3_INACTIVE_CONTROLLER_BINARY_OVERRIDE",text)
        self.assertIn("V3_ROOT_REACTIVATION_HELPER_OVERRIDE",text)
        self.assertIn("V3_RECONCILER_OVERRIDE",text)
        self.assertIn("base_install_manifest_sha256",text)
        self.assertIn("non_controller_generation_equivalent",text)
        self.assertIn("non_helper_generation_equivalent",text)
        self.assertIn("non_reconciler_generation_equivalent",text)

    def test_root_activator_accepts_exact_reconciler_override(self):
        text=ACTIVATOR.read_text(encoding="utf-8")
        self.assertIn("RECONCILER_OVERRIDE_ACTIVE_RECEIPT",text)
        self.assertIn('"mode": "V3_RECONCILER_OVERRIDE"',text)
        self.assertIn('"non_reconciler_generation_equivalent": True',text)
        self.assertIn('effective["reconciler_override"]',text)

    def test_updater_is_two_file_transaction_only(self):
        text=UPDATER.read_text(encoding="utf-8")
        self.assertIn("V3_VERIFIER_STACK_LIVE_UPDATE=PASS",text)
        self.assertIn("activation.verify_effective_installed_generation(BASE_MANIFEST)",text)
        self.assertIn('"--verify-installed"',text)
        self.assertIn("RECONCILER_OVERRIDE",text)
        self.assertIn("HELPER_OVERRIDE",text)
        self.assertIn('"controller_override_mutated":False',text)
        self.assertIn('"class_controller_mutated":False',text)
        self.assertIn('"workflow_mutated":False',text)
        self.assertIn('"legacy_v2_mutated":False',text)
        self.assertIn("changed=True",text)
        self.assertNotIn("systemctl start",text)
        self.assertNotIn("systemctl stop",text)

    def test_recovery_wrapper_refreshes_verifier_before_new_authority(self):
        text=WRAPPER.read_text(encoding="utf-8")
        refresh=text.index("V3_VERIFIER_STACK_REFRESH=PASS")
        authority=text.index("authority_path = mint_root_authority()")
        activation=text.index("str(INSTALLED_ACTIVATOR)")
        self.assertLess(refresh,authority)
        self.assertLess(authority,activation)
        self.assertIn("repo = exact_repo(args.expected_head)",text)
        self.assertIn("updater = repo / VERIFIER_STACK_UPDATER_REL",text)
        self.assertIn("cwd=repo",text)
        self.assertIn('[sys.executable, "-B", str(updater)',text)
        self.assertIn('reconciler_state.get("SubState") == "exited"',text)
        self.assertIn('provisioner_state.get("SubState") == "running"',text)


if __name__=="__main__":
    unittest.main()
