import importlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "workspace-shell"
sys.path.insert(0, str(PLUGIN / "root"))
job_launcher = importlib.import_module("job_launcher")


class WorkspaceShellMultirepoResearchTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((PLUGIN / "config" / "profiles.v1.json").read_text())

    def test_padataset_profile_matrix_is_fail_closed(self):
        for profile in ("git-read", "file-list", "file-read", "file-hash", "research-bounded"):
            job_launcher.assert_target_profile("PADataset", profile)
        with self.assertRaisesRegex(Exception, "TARGET_PROFILE_DENIED"):
            job_launcher.assert_target_profile("PADataset", "validation-bounded")
        with self.assertRaisesRegex(Exception, "TARGET_PROFILE_DENIED"):
            job_launcher.assert_target_profile("workspace-control", "research-bounded")
        with self.assertRaisesRegex(Exception, "TARGET_PROFILE_DENIED"):
            job_launcher.assert_target_profile("unknown", "git-read")

    def test_evidence_profiles_are_read_only_and_bounded(self):
        listing = job_launcher.resolve_profile(
            self.manifest,
            "file-list",
            ["results", "-maxdepth", "4", "-type", "f", "-name", "*.csv", "-print"],
        )
        self.assertEqual(listing["executable"], "/usr/bin/find")
        self.assertFalse(listing["write_scratch"])

        reader = job_launcher.resolve_profile(
            self.manifest,
            "file-read",
            ["-c", "65536", "--", "results/example.csv"],
        )
        self.assertEqual(reader["executable"], "/usr/bin/head")
        self.assertFalse(reader["write_scratch"])

        hasher = job_launcher.resolve_profile(
            self.manifest,
            "file-hash",
            ["results/example.csv"],
        )
        self.assertEqual(hasher["executable"], "/usr/bin/sha256sum")
        self.assertFalse(hasher["write_scratch"])

        with self.assertRaisesRegex(Exception, "PROFILE_ARGV_DENIED"):
            job_launcher.resolve_profile(
                self.manifest,
                "file-read",
                ["-c", "65537", "--", "results/example.csv"],
            )

    def test_research_profile_is_sandbox_copy_only(self):
        resolved = job_launcher.resolve_profile(
            self.manifest,
            "research-bounded",
            ["experiments/pa_eval_osr_one.py", "--help"],
        )
        self.assertEqual(resolved["executable"], "/usr/bin/python3")
        self.assertTrue(resolved["write_scratch"])
        self.assertEqual(resolved["argv"][:2], ["-B", "experiments/pa_eval_osr_one.py"])
        self.assertEqual(self.manifest["profiles"]["research-bounded"]["network"], "deny")
        with self.assertRaisesRegex(Exception, "PROFILE_ARGV_DENIED"):
            job_launcher.resolve_profile(
                self.manifest,
                "research-bounded",
                ["papers/not-authorized.py"],
            )

    def test_install_and_upgrade_pin_padataset_snapshot(self):
        render = (PLUGIN / "install" / "render_install.py").read_text()
        self.assertIn('padataset_root = "/srv/workspace-shell/PADataset"', render)
        self.assertIn('"PADataset": padataset_root', render)

        upgrade = (PLUGIN / "install" / "upgrade_multirepo_padataset_v1.sh").read_text()
        self.assertIn("17e1147614f27702e43565089d618182ff71c5af", upgrade)
        self.assertIn('PAD_ROOT="${PADATASET_CHECKOUT:-$HOME/adamArchives/Adam/varMax/PADataset}"', upgrade)
        self.assertIn("no runtime mutation performed", upgrade)
        self.assertIn("/srv/workspace-shell/PADataset", upgrade)
        self.assertIn("attempting rollback", upgrade)


if __name__ == "__main__":
    unittest.main()
