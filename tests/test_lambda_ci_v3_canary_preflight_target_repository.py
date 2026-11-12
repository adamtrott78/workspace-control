import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "controller" / "lambda-ci-controller" / "cmd" / "v3-canary-preflight" / "main.go"


class V3CanaryPreflightTargetRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.text = PREFLIGHT.read_text(encoding="utf-8")

    def test_target_repository_is_not_hardcoded_at_client_creation(self):
        self.assertIn('targetURL := flag.String("target-url"', self.text)
        self.assertIn('targetClient := clientFor(\n\t\t*targetURL,', self.text)

    def test_target_url_is_attested(self):
        self.assertIn('V3_SCALE_SET_TARGET_URL=%s', self.text)


if __name__ == "__main__":
    unittest.main()
