import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "lambda_ci_v3_post_outage_root_recovery_v1.py"


class PostOutageRootRecoveryContractTests(unittest.TestCase):
    def test_wrapper_is_exact_bounded_and_fresh_authority_only(self):
        text = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("POST_OUTAGE_V3_ROOT_RECOVERY=BEGIN", text)
        self.assertIn("POST_OUTAGE_V3_ROOT_RECOVERY=PASS", text)
        self.assertIn("lambda_ci_v3_root_reactivation_helper_live_update_v1.py", text)
        self.assertIn("ACTIVATE_V3_ROOT_SERVICES", text)
        self.assertIn("uuid.uuid4()", text)
        self.assertIn("timedelta(minutes=10)", text)
        self.assertIn("O_EXCL", text)
        self.assertIn("--authorization-receipt", text)
        self.assertIn("--activate", text)
        self.assertNotIn("14e58009-7bf3-43d1-8ad8-7616e70edaa3", text)
        self.assertNotIn("systemctl", text)
        self.assertNotIn("ACTIVATE_ONE_V3_CANARY", text)
        self.assertNotIn("workflow", text.lower().split("never mutates workflows")[0])

    def test_wrapper_requires_exact_clean_checkout_and_root(self):
        text = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("os.geteuid() != 0", text)
        self.assertIn('["rev-parse", "HEAD"]', text)
        self.assertIn('["status", "--porcelain=v1", "--untracked-files=normal"]', text)
        self.assertIn("checkout HEAD mismatch", text)
        self.assertIn("checkout is dirty", text)

    def test_wrapper_preserves_activation_failure_evidence(self):
        text = WRAPPER.read_text(encoding="utf-8")
        self.assertIn(
            "authority/transaction evidence is preserved for diagnosis",
            text,
        )
        self.assertNotIn("unlink(authority_path", text)


if __name__ == "__main__":
    unittest.main()
