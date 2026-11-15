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
        self.assertIn("stage10-ut04", workflow)
        self.assertIn("stage10-ut05", workflow)
        self.assertIn("stage10-ut06", workflow)
        self.assertIn("stage10-ut07", workflow)
        self.assertIn("stage10-ut08", workflow)
        self.assertIn("stage10-ut10", workflow)
        self.assertIn("stage10-ut12", workflow)
        self.assertIn("STAGE10_SCHEDULER_HOTKEY: Ctrl+Space", workflow)
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
        stage10 = workflow.split("  stage10-usability:", 1)[1].split(
            "\n  target-performance:", 1
        )[0]
        self.assertNotIn("actions/checkout@", stage10)
        self.assertNotIn("actions/setup-dotnet@", stage10)
        self.assertNotIn("actions/setup-node@", stage10)
        self.assertIn("git fetch --force --no-tags --prune --depth=1", stage10)
        self.assertIn("STAGE10_RUNNER_PREREQS=PASS", stage10)
        self.assertIn("STAGE10_RUNNER_TOOLCHAIN_BOUND=PASS", stage10)
        self.assertIn("RUNNER_TOOL_CACHE", stage10)
        self.assertIn("GITHUB_PATH", stage10)
        self.assertIn('".dotnet\\dotnet.exe"', stage10)
        self.assertIn("STAGE10_PRIOR_EXACT_HEAD_VALIDATION=PASS", stage10)
        self.assertIn("actions/runs/$($candidate.id)/jobs", stage10)
        self.assertNotIn("    needs: validation\n", stage10)

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

    def test_stage10_ut04_allows_ready_work_with_multiple_sent_unconfirmed(self):
        harness = (
            ROOT / "operator-bridge" / "integration" / "UsabilityHarness.cs"
        ).read_text(encoding="utf-8")
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage10-usability.ps1"
        ).read_text(encoding="utf-8")
        workflow = (
            ROOT / ".github" / "workflows" / "operator-bridge-validation.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('case "UT-04":', harness)
        self.assertIn('"ut04-pending-01"', harness)
        self.assertIn('"ut04-pending-02"', harness)
        self.assertIn("MultipleSentUnconfirmedWithReadyObserved", harness)
        self.assertIn("MaxSentUnconfirmed", harness)
        self.assertIn("Ut04BackgroundAcksApplied", harness)
        self.assertIn(
            "action.ActionId == _awaitingActionId",
            harness,
        )
        self.assertNotIn(
            "var pending = _world.Actions.Actions.FirstOrDefault(action =>\n"
            "            action.Status == SimActionStatus.AwaitingDurableAck);",
            harness,
        )
        self.assertIn("multiple_sent_unconfirmed_with_ready_observed", harness)
        self.assertIn("max_sent_unconfirmed", harness)
        self.assertIn('"UT-04"', script)
        self.assertIn('$TrialId -eq "UT-04"', script)
        self.assertIn("stage10-ut04", workflow)
        self.assertNotIn("SendKeys", harness)
        self.assertNotIn("KeyboardEvent", harness)
        self.assertNotIn("MouseEvent", harness)

    def test_stage10_ut05_and_ut12_are_bounded_and_content_free(self):
        harness = (
            ROOT / "operator-bridge" / "integration" / "UsabilityHarness.cs"
        ).read_text(encoding="utf-8")
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage10-usability.ps1"
        ).read_text(encoding="utf-8")
        workflow = (
            ROOT / ".github" / "workflows" / "operator-bridge-validation.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('case "UT-05":', harness)
        self.assertIn('"ut05-judgment-01"', harness)
        self.assertIn('"OPEN_JUDGMENT_GATE"', harness)
        self.assertIn("UsabilityOperatorSurface", harness)
        self.assertIn("JUDGMENT_DECISION_APPLIED", harness)
        self.assertIn("Ut05JudgmentClipboardWrites == 0", harness)
        self.assertIn("Ut05JudgmentBrowserEffects == 0", harness)
        self.assertIn("ut05_exact_gate_observed", harness)
        self.assertIn("TopMostOperatorDialogOwner", harness)
        self.assertIn("TopMost = true", harness)
        self.assertIn("MessageBox.Show(", harness)
        self.assertIn("STAGE10_HOTKEY_RECEIVED", harness)
        self.assertIn("STAGE10_JUDGMENT_OPENING", harness)
        self.assertIn("STAGE10_JUDGMENT_DECISION", harness)
        self.assertNotIn("SetForegroundWindow", harness)
        self.assertNotIn("GetForegroundWindow", harness)
        self.assertIn('case "UT-12":', harness)
        self.assertIn('"ut12-pending-01"', harness)
        self.assertIn("ApplyUt12BackgroundAckIfReady", harness)
        self.assertIn("TimeSpan.FromSeconds(3)", harness)
        self.assertIn("Ut12BackgroundAcksApplied == 1", harness)
        self.assertIn("Ut12NoWorkClipboardWrites == 0", harness)
        self.assertIn("Ut12NoWorkBrowserEffects == 0", harness)
        self.assertIn("Ut12BackgroundAckClipboardWrites == 0", harness)
        self.assertIn("Ut12BackgroundAckBrowserEffects == 0", harness)
        self.assertIn("bridge_browser_focus_commands", harness)
        self.assertIn('"UT-05"', script)
        self.assertIn('"UT-12"', script)
        self.assertIn('$TrialId -eq "UT-05"', script)
        self.assertIn('$TrialId -eq "UT-12"', script)
        self.assertIn("STAGE10_BUILD_CACHE=", script)
        self.assertIn("STAGE10_WEB_EXT_CACHE=", script)
        self.assertIn("web-ext-10.8.0", script)
        self.assertIn("WaitForExit(120000)", script)
        self.assertNotIn("$npmExitCode = $npmProcess.ExitCode", script)
        self.assertIn("$stagedMetadata.version -ne \"10.8.0\"", script)
        self.assertIn("build_fingerprint=", script)
        self.assertIn("[System.BitConverter]::ToString", script)
        self.assertNotIn("[Convert]::ToHexString", script)
        self.assertIn("ls-tree -r HEAD", script)
        self.assertIn("--prefer-offline", script)
        self.assertIn("stage10-ut05", workflow)
        self.assertIn("stage10-ut12", workflow)
        self.assertNotIn("SendKeys", harness)
        self.assertNotIn("KeyboardEvent", harness)
        self.assertNotIn("MouseEvent", harness)

    def test_stage10_ut06_ut07_ut08_recovery_trials_use_durable_authority(self):
        harness = (
            ROOT / "operator-bridge" / "integration" / "UsabilityHarness.cs"
        ).read_text(encoding="utf-8")
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage10-usability.ps1"
        ).read_text(encoding="utf-8")
        workflow = (
            ROOT / ".github" / "workflows" / "operator-bridge-validation.yml"
        ).read_text(encoding="utf-8")

        for trial in ("UT-06", "UT-07", "UT-08"):
            self.assertIn(f'case "{trial}":', harness)
            self.assertIn(f'"{trial}"', script)
            self.assertIn(f'$TrialId -eq "{trial}"', script)
            self.assertIn(
                "stage10-" + trial.lower().replace("ut-", "ut"),
                workflow,
            )

        self.assertIn("RecoveryCoordinator", harness)
        self.assertIn("RecoverySignal.ManagedTabClosed", harness)
        self.assertIn("RecoverySignal.OperatorReportedAuthRefresh", harness)
        self.assertIn("RecoverySignal.SystemResumeOrHelperColdStart", harness)
        self.assertIn("InitializeAsync()", harness)
        self.assertIn("_ut08RecoveryRehydrated", harness)
        self.assertIn("MarkManualAuthReturnedAsync", harness)
        self.assertIn("ProveNoAuthAutomation", harness)
        self.assertIn("RecoveryInstructionSteps <= 3", harness)
        self.assertIn("RecoveryClipboardWrites == 0", harness)
        self.assertIn("RecoveryBrowserEffects == 0", harness)
        self.assertIn("_recoveryAuthority.AdvanceCount == 2", harness)
        self.assertIn("SimActionStatus.Superseded", harness)
        self.assertIn("service_actions_expected_durable_acks", harness)
        self.assertIn("recovery_authority_generation_advances", harness)
        self.assertIn("ut08_recovery_rehydrated", harness)
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
