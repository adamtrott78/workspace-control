import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIREFOX = ROOT / "operator-bridge/src/FirefoxAdapter"
MANIFEST = FIREFOX / "manifest.json"
CORE = FIREFOX / "adapter_core.js"
BACKGROUND = FIREFOX / "background.js"


class FirefoxAdapterStageFourStaticTests(unittest.TestCase):
    def test_permission_allowlist_remains_exact(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            ["nativeMessaging", "tabs", "sessions"],
            manifest["permissions"],
        )
        self.assertNotIn("host_permissions", manifest)
        self.assertNotIn("content_scripts", manifest)

    def test_background_scripts_load_core_before_transport(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            ["adapter_core.js", "background.js"],
            manifest["background"]["scripts"],
        )

    def test_fixed_worker_start_url_is_not_command_supplied(self):
        source = CORE.read_text(encoding="utf-8")
        self.assertIn(
            'const WORKER_START_URL = "https://chatgpt.com/";',
            source,
        )
        self.assertIn("url: WORKER_START_URL", source)
        self.assertNotRegex(
            source,
            re.compile(r"url\s*:\s*payload\.", re.IGNORECASE),
        )

    def test_sessions_metadata_key_is_private_and_content_free(self):
        source = CORE.read_text(encoding="utf-8")
        self.assertIn("sessions.setTabValue", source)
        self.assertIn("sessions.getTabValue", source)
        for forbidden in (
            "packet_text:",
            "clipboard_content:",
            "raw_url:",
            "credential:",
            "token:",
            "cookie:",
            "password:",
        ):
            self.assertNotIn(forbidden, source.lower())

    def test_no_forbidden_browser_automation_apis(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in FIREFOX.glob("*.js")
        )
        for forbidden in (
            "browser.scripting",
            "executeScript",
            "browser.webNavigation",
            "browser.webRequest",
            "browser.cookies",
            "browser.clipboard",
            "document.querySelector",
            "document.body",
            "innerText",
            "textContent",
            "sendMessageToTab",
        ):
            self.assertNotIn(forbidden, combined)

    def test_background_protocol_does_not_emit_raw_url_property(self):
        source = BACKGROUND.read_text(encoding="utf-8")
        self.assertNotRegex(
            source,
            re.compile(r"\burl\s*:", re.IGNORECASE),
        )
        self.assertNotIn("tab.url", source)
        self.assertNotIn("changeInfo.url", source)


if __name__ == "__main__":
    unittest.main()
