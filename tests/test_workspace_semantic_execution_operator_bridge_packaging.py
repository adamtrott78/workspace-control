import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "operator-bridge" / "packaging"
MANIFEST = ROOT / "operator-bridge" / "src" / "FirefoxAdapter" / "manifest.json"
WORKFLOW = ROOT / ".github" / "workflows" / "operator-bridge-validation.yml"


class OperatorBridgeStageEightPackagingTests(unittest.TestCase):
    def test_stage08_artifacts_exist(self):
        for name in (
            "STAGE08.md",
            "SIGNED-XPI-INSTALL.md",
            "build-package.ps1",
            "install.ps1",
            "rollback.ps1",
            "uninstall.ps1",
            "stage08-smoke.ps1",
        ):
            self.assertTrue((PACKAGING / name).is_file(), name)

    def test_builder_is_self_contained_win_x64_and_exact_sha_bound(self):
        source = (PACKAGING / "build-package.ps1").read_text(encoding="utf-8")
        self.assertIn("--runtime win-x64 --self-contained true", source)
        self.assertIn("SourceSha must equal the exact Git HEAD being packaged", source)
        self.assertIn("xpi_mode = $xpiMode", source)
        self.assertIn('"MOZILLA_SIGNED"', source)
        self.assertIn('"CI_UNSIGNED_FIXTURE"', source)
        self.assertNotIn("operator-bridge\\simulator", source.lower())
        self.assertNotIn("SIM_HUMAN_SUBMIT", source)

    def test_production_management_surface_is_per_user_only(self):
        combined = "\n".join(
            (PACKAGING / name).read_text(encoding="utf-8")
            for name in ("install.ps1", "rollback.ps1", "uninstall.ps1")
        )
        lowered = combined.lower()
        self.assertIn("hkcu:\\software\\mozilla\\nativemessaginghosts\\com.workspacecontrol.operator_bridge", lowered)
        self.assertIn("localappdata", lowered)
        for forbidden in (
            "hklm:",
            "programfiles",
            "runas",
            "start-process -verb",
            "new-service",
            "scheduledtask",
            "profiles.ini",
            "\\mozilla\\firefox\\profiles",
            "cookies.sqlite",
            "logins.json",
            "key4.db",
            "localstorage",
            "indexeddb",
            "sim_human_submit",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_installed_state_is_content_free(self):
        combined = "\n".join(
            (PACKAGING / name).read_text(encoding="utf-8")
            for name in ("install.ps1", "rollback.ps1", "uninstall.ps1")
        ).lower()
        for forbidden in (
            "packet_text",
            "clipboard_content",
            "raw_url",
            "page_content",
            "credential",
            "password",
            "cookie",
            "token",
        ):
            self.assertNotIn(forbidden, combined)

    def test_builder_and_firefox_manifest_preserve_frozen_identity(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            "workspace-control-operator@adamtrott78.local",
            manifest["browser_specific_settings"]["gecko"]["id"],
        )
        self.assertEqual(["nativeMessaging", "tabs", "sessions"], manifest["permissions"])

        builder = (PACKAGING / "build-package.ps1").read_text(encoding="utf-8")
        self.assertIn('"workspace-control-operator@adamtrott78.local"', builder)
        self.assertIn('"com.workspacecontrol.operator_bridge"', builder)
        self.assertIn('@("nativeMessaging", "tabs", "sessions")', builder)
        self.assertIn('"153.0"', builder)
        self.assertIn('"0.1.0"', builder)

    def test_production_package_excludes_smoke_and_builder(self):
        builder = (PACKAGING / "build-package.ps1").read_text(encoding="utf-8")
        management_copy = re.search(
            r'foreach \(\$name in @\((.*?)\)\)',
            builder,
            re.DOTALL,
        )
        self.assertIsNotNone(management_copy)
        copied = management_copy.group(1)
        self.assertIn('"install.ps1"', copied)
        self.assertIn('"uninstall.ps1"', copied)
        self.assertIn('"rollback.ps1"', copied)
        self.assertIn('"SIGNED-XPI-INSTALL.md"', copied)
        self.assertNotIn("stage08-smoke.ps1", copied)
        self.assertNotIn("build-package.ps1", copied)

    def test_signed_xpi_flow_is_manual_and_profile_safe(self):
        doc = (PACKAGING / "SIGNED-XPI-INSTALL.md").read_text(encoding="utf-8").lower()
        self.assertIn("mozilla-signed xpi", doc)
        self.assertIn("install add-on from file", doc)
        self.assertIn("firefox validates", doc)
        self.assertIn("manually", doc)
        self.assertIn("no automatic self-updater", doc)

    def test_workflow_runs_exact_head_stage08_smoke_and_uploads_evidence(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        expected_ref = "ref: $" + "{{ github.event.pull_request.head.sha || github.sha }}"
        self.assertIn(expected_ref, workflow)
        self.assertIn("Run Stage 08 per-user packaging/install/upgrade/rollback smoke", workflow)
        self.assertIn("stage08-packaging-evidence.json", workflow)
        self.assertIn("stage08-package-a.json", workflow)
        self.assertIn("stage08-package-b.json", workflow)


if __name__ == "__main__":
    unittest.main()
