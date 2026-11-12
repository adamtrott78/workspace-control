import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OperatorBridgeStageTenUsabilityTests(unittest.TestCase):
    def test_usability_harness_is_test_only_and_manual_input_preserved(self):
        production = (
            ROOT / "operator-bridge" / "WorkspaceOperatorBridge.slnx"
        ).read_text(encoding="utf-8")
        integration = (
            ROOT / "operator-bridge" / "integration" / "Program.cs"
        ).read_text(encoding="utf-8")
        server = (
            ROOT / "operator-bridge" / "integration" / "FakeWorkerLoopbackServer.cs"
        ).read_text(encoding="utf-8")
        harness = (
            ROOT / "operator-bridge" / "integration" / "UsabilityHarness.cs"
        ).read_text(encoding="utf-8")
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage10-usability.ps1"
        ).read_text(encoding="utf-8")

        self.assertNotIn("UsabilityHarness", production)
        self.assertIn("--usability-trial", integration)
        self.assertIn("[STAThread]", integration)
        self.assertIn("private static int Main(string[] args)", integration)
        self.assertIn("RunAsync(args).GetAwaiter().GetResult()", integration)
        self.assertNotIn("private static async Task<int> Main", integration)
        self.assertIn("WindowsFormsSynchronizationContext", harness)
        self.assertIn("SynchronizationContext.SetSynchronizationContext", harness)
        self.assertGreater(
            harness.index("SynchronizationContext.SetSynchronizationContext"),
            harness.index("public UsabilityApplicationContext("),
        )
        self.assertGreater(
            harness.index("SynchronizationContext.SetSynchronizationContext"),
            harness.index("hub.WaitForConnectionAsync"),
        )
        self.assertIn("STAGE10_HOTKEY_REGISTRATION_NOT_CONFIRMED", harness)
        self.assertIn("hotkey_registered = context.HotkeyRegistered", harness)
        self.assertIn("bridge_enabled = context.BridgeEnabled", harness)
        self.assertLess(
            harness.index("using var context = new UsabilityApplicationContext"),
            harness.index('evidence_class = "STAGE10_USABILITY_READY"'),
        )
        self.assertIn("EARLY_STARTUP_", harness)
        self.assertIn("WinFormsClipboardWriter", harness)
        self.assertIn("clipboard_failed_dispatches", harness)
        self.assertIn("last_dispatch_outcome", harness)
        self.assertIn("DispatchOutcome.ClipboardFailed", harness)
        self.assertIn("_awaitingHumanSubmit", harness)
        self.assertIn("_awaitingActionId", harness)
        self.assertIn("HandoffBlockedPresses", harness)
        self.assertIn("HandoffRefocuses", harness)
        self.assertIn("SimActionStatus.AwaitingDurableAck", harness)
        self.assertIn("FocusTargetAsync", harness)
        self.assertIn("handoff_refocuses", harness)
        self.assertIn("safely_recovered_repeat_presses", harness)
        self.assertIn(
            "Volatile.Read(ref _awaitingHumanSubmit) != 0",
            harness,
        )
        self.assertIn(
            "Volatile.Write(ref _awaitingHumanSubmit, 0)",
            harness,
        )
        self.assertNotIn("BusyPresses == 0", harness)
        self.assertIn("WindowsHotkeyRegistrar", harness)
        self.assertIn("IPAddress.Loopback", server)
        self.assertNotIn("IPAddress.Any", server)
        self.assertIn('event.key === "Enter"', server)
        self.assertIn('fetch("/submit"', server)
        self.assertIn("PENDING_OPERATOR_COUNTS_AND_RATINGS", harness)
        self.assertIn("wrong_worker_dispatches", harness)
        self.assertIn("wrong_packet_dispatches", harness)
        self.assertIn("Ctrl+V", script)
        self.assertIn("SchedulerHotkey", script)
        self.assertIn('"--scheduler-hotkey"', harness)
        self.assertNotIn("SendKeys", harness)
        self.assertNotIn("KeyboardEvent", harness)
        self.assertNotIn("MouseEvent", harness)

    def test_workflow_has_opt_in_interactive_stage10_trials(self):
        workflow = (
            ROOT / ".github" / "workflows" / "operator-bridge-validation.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("stage10-usability:", workflow)
        self.assertIn("stage10-ut11", workflow)
        self.assertIn("stage10-ut01", workflow)
        self.assertIn("stage10-ut02", workflow)
        self.assertIn("stage10-ut03", workflow)
        self.assertIn("stage10-ut10", workflow)
        self.assertIn("STAGE10_SCHEDULER_HOTKEY: Ctrl+Space", workflow)
        self.assertIn("needs: validation", workflow)
        self.assertIn(
            "runs-on: [self-hosted, windows, x64, workspace-operator-target]",
            workflow,
        )
        self.assertIn("run-stage10-usability.ps1", workflow)
        self.assertIn(
            "Stage 10 usability runner must be launched interactively",
            workflow,
        )
        self.assertIn("operator-bridge-stage10-usability-", workflow)

    def test_stage10_ut03_interruption_trial_is_explicit_and_bounded(self):
        harness = (
            ROOT / "operator-bridge" / "integration" / "UsabilityHarness.cs"
        ).read_text(encoding="utf-8")
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage10-usability.ps1"
        ).read_text(encoding="utf-8")
        workflow = (
            ROOT / ".github" / "workflows" / "operator-bridge-validation.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('case "UT-03":', harness)
        self.assertIn('world.Queue("ut03-06"', harness)
        self.assertIn("InterruptionPromptsIssued", harness)
        self.assertIn("interruption_prompts_required", harness)
        self.assertIn("interruption_prompts_issued", harness)
        self.assertIn("InterruptionPromptsIssued == 5", harness)
        self.assertIn('"UT-03"', script)
        self.assertIn('$TrialId -eq "UT-03"', script)
        self.assertIn("stage10-ut03", workflow)
        self.assertNotIn("SendKeys", harness)
        self.assertNotIn("KeyboardEvent", harness)
        self.assertNotIn("MouseEvent", harness)

    def test_stage10_wrapper_uses_structured_objective_result_not_windows_exit_code(self):
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage10-usability.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn('resultObject.result -ne "OBJECTIVE_PASS"', script)
        self.assertIn("structured result is authoritative", script)
        self.assertNotIn(
            'if ($runner.ExitCode -ne 0) {\n    throw "Stage 10 usability harness reported objective failure."',
            script,
        )

    def test_usability_adapter_keeps_least_privilege_and_fake_worker_only(self):
        manifest = (
            ROOT
            / "operator-bridge"
            / "usability"
            / "FirefoxProfile"
            / "extension"
            / "manifest.json"
        ).read_text(encoding="utf-8")
        background = (
            ROOT
            / "operator-bridge"
            / "usability"
            / "FirefoxProfile"
            / "extension"
            / "background.js"
        ).read_text(encoding="utf-8")

        self.assertIn('"nativeMessaging"', manifest)
        self.assertIn('"tabs"', manifest)
        self.assertIn('"sessions"', manifest)
        self.assertNotIn("host_permissions", manifest)
        self.assertNotIn("content_scripts", manifest)
        self.assertIn("http://127.0.0.1:8765/fake-worker.html", background)
        self.assertNotIn("chatgpt.com", background.lower())
        self.assertNotIn("querySelector", background)
        self.assertNotIn("executeScript", background)

    def test_simulator_packet_carries_only_test_identity_and_hash(self):
        ports = (
            ROOT / "operator-bridge" / "integration" / "HarnessPorts.cs"
        ).read_text(encoding="utf-8")
        self.assertIn("worker_slot_id=", ports)
        self.assertIn("session_generation=", ports)
        self.assertIn("payload_sha256=", ports)
        self.assertNotIn("response_text", ports.lower())
        self.assertNotIn("credential", ports.lower())


if __name__ == "__main__":
    unittest.main()
