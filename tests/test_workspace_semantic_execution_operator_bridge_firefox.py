import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIREFOX = ROOT / "operator-bridge/src/FirefoxAdapter"
MANIFEST = FIREFOX / "manifest.json"
CORE = FIREFOX / "adapter_core.js"
BACKGROUND = FIREFOX / "background.js"
DEV_RUNTIME = ROOT / "operator-bridge/tools/workspace-operator-dev.ps1"
STAGE12 = ROOT / "operator-bridge/tools/run-stage12-real-instant.ps1"


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
        background = BACKGROUND.read_text(encoding="utf-8")
        self.assertIn(
            'const WORKER_START_URL = "https://chatgpt.com/?temporary-chat=true";',
            source,
        )
        self.assertIn(
            "this.workerStartUrl = options.workerStartUrl || WORKER_START_URL",
            source,
        )
        self.assertIn("url: this.workerStartUrl", source)
        self.assertNotIn("workerStartUrl", background)
        self.assertNotRegex(
            source,
            re.compile(r"url\s*:\s*payload\.", re.IGNORECASE),
        )

    def test_bootstrap_navigation_is_adapter_owned_and_launchers_do_not_use_start_url(self):
        source = CORE.read_text(encoding="utf-8")
        dev = DEV_RUNTIME.read_text(encoding="utf-8")
        stage12 = STAGE12.read_text(encoding="utf-8")
        self.assertIn("await this.prepareBootstrapSurface()", source)
        self.assertIn('tab.url === "about:newtab"', source)
        self.assertIn('tab.url === "about:blank"', source)
        self.assertIn("url: this.workerStartUrl", source)
        self.assertNotIn("--start-url", dev)
        self.assertNotIn("--start-url", stage12)

    def test_dev_runtime_prefers_graceful_managed_firefox_shutdown(self):
        text = DEV_RUNTIME.read_text(encoding="utf-8")
        self.assertIn("function Stop-ManagedFirefox", text)
        self.assertIn(".CloseMainWindow()", text)
        self.assertIn("WORKSPACE_OPERATOR_FIREFOX_SHUTDOWN=GRACEFUL", text)
        self.assertIn("WORKSPACE_OPERATOR_FIREFOX_SHUTDOWN=FORCED_FALLBACK", text)

    def test_dev_runtime_owns_exact_process_tree_before_workdir_cleanup(self):
        text = DEV_RUNTIME.read_text(encoding="utf-8")
        self.assertIn("function Get-RuntimeOwnedProcesses", text)
        self.assertIn("function Stop-RuntimeOwnedProcesses", text)
        self.assertIn("ParentProcessId", text)
        self.assertIn("State.work_dir", text)
        self.assertIn("State.helper_path", text)
        self.assertIn("WORKSPACE_OPERATOR_RUNTIME_PROCESS_CLEANUP=PASS", text)
        self.assertIn("DEV_RUNTIME_PROCESS_CLEANUP_FAILED", text)
        self.assertLess(
            text.index("Stop-RuntimeOwnedProcesses $state"),
            text.index("Try-RemoveTreeWithRetry ([string]$state.work_dir)"),
        )

    def test_verified_dead_runtime_can_defer_locked_workdir_residue(self):
        text = DEV_RUNTIME.read_text(encoding="utf-8")
        self.assertIn("function Try-RemoveTreeWithRetry", text)
        self.assertIn("cleanup-residue.jsonl", text)
        self.assertIn("WORKSPACE_OPERATOR_RUNTIME_RESIDUE=DEFERRED", text)
        self.assertIn("WORKSPACE_OPERATOR_RUNTIME_WORKDIR_CLEANUP=DEFERRED", text)
        self.assertIn("WORKSPACE_OPERATOR_DEV_OFFLINE=PASS", text)
        self.assertNotIn("DEV_RUNTIME_CLEANUP_FAILED:", text)
        self.assertLess(
            text.index("Try-RemoveTreeWithRetry ([string]$state.work_dir)"),
            text.index("Remove-Item -LiteralPath $statePath"),
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
