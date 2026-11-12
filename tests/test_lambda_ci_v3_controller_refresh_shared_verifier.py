import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
REFRESH = ROOT / "scripts" / "lambda_ci_v3_controller_refresh.py"
OPERATOR = ROOT / "scripts" / "lambda_ci_v3_padataset_cpu_canary_live.sh"


class ControllerRefreshSharedVerifierRegressionTests(unittest.TestCase):
    def test_controller_refresh_uses_shared_effective_generation_verifier(self):
        text = REFRESH.read_text(encoding="utf-8")
        self.assertIn("reconciler.verify_installed(manifest_path)", text)
        self.assertIn("effective installed generation invalid", text)
        self.assertNotIn("def _verify_base_non_controller(", text)

    def test_padataset_operator_still_checks_controller_specific_provenance(self):
        text = OPERATOR.read_text(encoding="utf-8")
        self.assertIn("--verify-active", text)
        self.assertIn('--expected-source-head "$SOURCE_HEAD"', text)
        self.assertIn('--base-source-head "$BASE_SOURCE_HEAD"', text)
        self.assertIn("CONTROLLER_OVERRIDE_BINDING=PASS", text)

    def test_preflight_failure_occurs_before_fresh_canary_authority(self):
        text = OPERATOR.read_text(encoding="utf-8")
        verify = text.index("CONTROLLER_OVERRIDE_BINDING=PASS")
        authority = text.index("CANARY_AUTHORITY_CREATED=PASS")
        apply_tx = text.index("--apply-canary")
        self.assertLess(verify, authority)
        self.assertLess(authority, apply_tx)


if __name__ == "__main__":
    unittest.main()
