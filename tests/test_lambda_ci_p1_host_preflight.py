import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_p1_host_preflight.py"


class P1HostPreflightHelperTests(unittest.TestCase):
    def test_helper_is_read_only_and_ignores_only_untracked_files(self):
        raw = SCRIPT.read_text(encoding="utf-8")

        self.assertIn('"status", "--porcelain", "--untracked-files=no"', raw)
        self.assertIn('"ls-files", "--others", "--exclude-standard"', raw)
        self.assertIn("NO_INSTALL_RESTART_RECONCILE_ACTIVATE_TRIGGER_PERFORMED=true", raw)

        forbidden_fragments = [
            '["systemctl", "start"',
            '["systemctl", "stop"',
            '["systemctl", "restart"',
            '["systemctl", "enable"',
            '["systemctl", "disable"',
            'subprocess.run(["install"',
            'subprocess.run(["cp"',
            'subprocess.run(["mv"',
            'subprocess.run(["rm"',
            ".write_text(",
            ".write_bytes(",
            ".mkdir(",
            ".unlink(",
            "os.remove(",
            "os.rename(",
            "os.replace(",
        ]
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, raw, fragment)

    def test_helper_never_reads_credential_contents(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("TOKEN_PATHS", raw)
        self.assertIn("owner_group_mode(path)", raw)
        self.assertNotIn("path.read_text(encoding=\"utf-8\")", raw.split("TOKEN_PATHS", 1)[1].split("INSTALLED_FILES", 1)[0])


if __name__ == "__main__":
    unittest.main()
