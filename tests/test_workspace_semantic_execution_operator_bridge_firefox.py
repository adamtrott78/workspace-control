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
COMMAND_INSTALLER = ROOT / "operator-bridge/tools/install-wop-commands.ps1"
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

    def test_operator_dispatch_owns_new_tab_focus_and_blank_cleanup(self):
        source = CORE.read_text(encoding="utf-8")
        dev = DEV_RUNTIME.read_text(encoding="utf-8")
        stage12 = STAGE12.read_text(encoding="utf-8")
        self.assertNotIn("await this.prepareBootstrapSurface()", source)
        self.assertIn("const startupBlank = await this.findDisposableStartupBlankTab()", source)
        self.assertIn("url: this.workerStartUrl", source)
        self.assertIn("active: true", source)
        self.assertIn("await this.browser.windows.update(tab.windowId, { focused: true })", source)
        self.assertIn("await this.browser.tabs.remove(startupBlank.id)", source)
        self.assertNotIn("LEGACY_DEV_WORKER_URL", source)
        self.assertNotIn("--start-url", dev)
        self.assertNotIn("--start-url", stage12)

    def test_dedicated_firefox_launchers_clear_only_session_restore_artifacts(self):
        dev = DEV_RUNTIME.read_text(encoding="utf-8")
        stage12 = STAGE12.read_text(encoding="utf-8")
        for source in (dev, stage12):
            self.assertIn("function Reset-DedicatedFirefoxSessionState", source)
            self.assertIn('"sessionstore.jsonlz4"', source)
            self.assertIn('"sessionCheckpoints.json"', source)
            self.assertIn('"sessionstore-backups"', source)
            self.assertIn(
                "WORKSPACE_OPERATOR_FIREFOX_SESSION_STATE_RESET=PASS",
                source,
            )
            self.assertIn("Reset-DedicatedFirefoxSessionState $firefoxProfile", source)
            self.assertNotIn('"cookies.sqlite"', source)
            self.assertNotIn('"logins.json"', source)
            self.assertNotIn('"key4.db"', source)

    def test_dev_runtime_exposes_read_only_self_test(self):
        text = DEV_RUNTIME.read_text(encoding="utf-8")
        self.assertIn('"self-test"', text)
        self.assertIn("function Invoke-SelfTest", text)
        self.assertIn("WORKSPACE_OPERATOR_SELF_TEST=PASS", text)
        self.assertIn('"self-test" { Invoke-SelfTest }', text)

    def test_convenience_commands_use_existing_current_user_path_without_policy_mutation(self):
        text = COMMAND_INSTALLER.read_text(encoding="utf-8")
        self.assertIn('Microsoft\\WindowsApps', text)
        self.assertIn("Test-CommandDirectoryOnPath", text)
        self.assertIn("WORKSPACE_OPERATOR_COMMAND_PATH=PASS", text)
        self.assertIn("workspace-control-owned:wop-command-v2", text)
        self.assertIn("workspace-control-owned:wop-driver-v2", text)
        for command in (
            "wop",
            "wop-up",
            "wop-down",
            "wop-reset",
            "wop-status",
            "wop-self-test",
        ):
            self.assertIn(f'"{command}"', text)
        self.assertIn("DevCheckout", text)
        self.assertIn("workspace-operator-dev.ps1", text)
        self.assertIn("WORKSPACE_OPERATOR_COMMANDS_INSTALLED=PASS", text)
        self.assertIn("Remove-LegacyProfileBlock", text)
        self.assertIn("# BEGIN WORKSPACE OPERATOR COMMANDS V1", text)
        self.assertNotIn("Set-ExecutionPolicy", text)
        self.assertNotIn("[Environment]::SetEnvironmentVariable", text)
        self.assertNotIn("HKLM:", text)
        self.assertNotIn("Start-Service", text)
        self.assertNotIn("Register-ScheduledTask", text)
        self.assertNotIn("Invoke-Expression", text)
        self.assertIn("fetch --force --depth=1 origin workspace-semantic-execution-migration-v1", text)
        self.assertIn("WOP_EXACT_FETCH_FAILED", text)
        self.assertIn("WOP_CHECKOUT_TREE_UNAVAILABLE", text)

    def test_dedicated_firefox_launchers_suppress_session_restore(self):
        dev = DEV_RUNTIME.read_text(encoding="utf-8")
        stage12 = STAGE12.read_text(encoding="utf-8")
        for source in (dev, stage12):
            self.assertIn("--pref=browser.startup.page=0", source)
            self.assertIn(
                "--pref=browser.sessionstore.resume_from_crash=false",
                source,
            )
            self.assertIn("--keep-profile-changes", source)
            self.assertNotIn("--start-url", source)

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
