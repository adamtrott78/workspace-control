import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERF = ROOT / "operator-bridge" / "performance"
PRODUCTION = ROOT / "operator-bridge" / "WorkspaceOperatorBridge.slnx"
INTEGRATION = ROOT / "operator-bridge" / "WorkspaceOperatorBridge.Integration.slnx"
WORKFLOW = ROOT / ".github" / "workflows" / "operator-bridge-validation.yml"
BUDGET = ROOT / "architecture" / "workspace-semantic-execution-operator-performance-budget.v0.1.md"
CONTRACT = ROOT / "benchmarks" / "workspace-semantic-execution" / "operator_ux_performance_v1.json"


class OperatorBridgeStageNinePerformanceTests(unittest.TestCase):
    def test_performance_harness_is_test_only(self):
        production = PRODUCTION.read_text(encoding="utf-8")
        integration = INTEGRATION.read_text(encoding="utf-8")
        self.assertNotIn("PerformanceHarness", production)
        self.assertIn("performance/WorkspaceOperator.PerformanceHarness.csproj", integration)

    def test_performance_extension_preserves_frozen_permissions_and_identity(self):
        manifest = json.loads(
            (PERF / "FirefoxProfile" / "extension" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(["nativeMessaging", "tabs", "sessions"], manifest["permissions"])
        self.assertEqual(
            "workspace-control-operator@adamtrott78.local",
            manifest["browser_specific_settings"]["gecko"]["id"],
        )
        self.assertNotIn("host_permissions", manifest)
        self.assertNotIn("content_scripts", manifest)

    def test_performance_background_has_no_fixture_seeding_or_content_automation(self):
        source = (PERF / "FirefoxProfile" / "extension" / "background.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("http://127.0.0.1:8765/fake-worker.html", source)
        for forbidden in (
            "seedSimulatorTabs",
            "SIM_HUMAN_SUBMIT",
            "executeScript",
            "document.querySelector",
            "innerText",
            "textContent",
            "KeyboardEvent",
            "MouseEvent",
            "browser.cookies",
        ):
            self.assertNotIn(forbidden, source)

    def test_harness_never_claims_ci_is_target_machine(self):
        source = (PERF / "Program.cs").read_text(encoding="utf-8")
        readme = (PERF / "README.md").read_text(encoding="utf-8")
        self.assertIn('"GITHUB_HOSTED_WINDOWS_CI"', source)
        self.assertIn("target_contract_complete = false", source)
        self.assertNotIn('"IMPLEMENTATION_GAP"', source)
        self.assertIn('"TARGET_COLD_FIREFOX_PARTIAL"', source)
        self.assertIn("fabricated timing evidence", readme)
        self.assertIn("60-second warm-up", readme)
        self.assertIn("120-second 1 Hz", readme)

    def test_harness_security_boundary_is_content_free(self):
        combined = "\n".join(
            [
                (PERF / "Program.cs").read_text(encoding="utf-8"),
                (PERF / "FirefoxProfile" / "extension" / "background.js").read_text(
                    encoding="utf-8"
                ),
            ]
        )
        lowered = combined.lower()
        self.assertIn("screenshots_collected = false", combined)
        for forbidden in (
            "queryselector",
            "accessibility tree",
            "cookies.sqlite",
            "logins.json",
            "key4.db",
            "localstorage",
            "indexeddb",
            "synthetic paste",
            "synthetic enter",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_ci_script_is_shortened_non_target_smoke(self):
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage09-ci.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn("--mode=ci", script)
        self.assertIn("--warmup-ms=250", script)
        self.assertIn("--sample-ms=1200", script)
        self.assertIn("--latency-scale=10", script)
        self.assertIn('evidence_class -ne "GITHUB_HOSTED_WINDOWS_CI"', script)
        self.assertIn("target_contract_complete", script)
        self.assertIn("web-ext@10.8.0", script)
        self.assertIn("STAGE09_CI_PREDECESSOR_FIREFOX_CLEANUP", script)
        self.assertIn("Stop-Process -Force", script)
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertIn(
            "unrelated same-name browser process is present",
            contract["trial_validity"]["reject_if"],
        )

    def test_frozen_contract_counts_and_budgets_are_unchanged(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        groups = {item["id"]: item for item in contract["scenario_groups"]}
        self.assertEqual(50, groups["LATENCY_REUSE"]["repetitions"])
        self.assertEqual(30, groups["LATENCY_RESTORE"]["repetitions"])
        self.assertEqual(30, groups["LATENCY_CREATE"]["repetitions"])
        self.assertEqual(10, groups["LATENCY_COLD_START"]["repetitions"])
        self.assertEqual(100, groups["LATENCY_LOCAL_PRIMITIVES"]["repetitions"])
        budgets = contract["frozen_budgets"]
        self.assertEqual(750, budgets["latency_ms"]["reuse_existing_worker_ready_for_paste_p95_max"])
        self.assertEqual(1536, budgets["resource"]["firefox_two_live_worker_tabs_working_set_mib_p95_max"])
        self.assertEqual(25, budgets["resource"]["discard_three_of_four_tabs_total_working_set_reduction_percent_min"])
        self.assertIn("Empirical results remain intentionally", BUDGET.read_text(encoding="utf-8"))

    def test_ci_workflow_runs_and_uploads_stage09_evidence(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Run Stage 09 account-free CI performance smoke", workflow)
        self.assertIn("Parse Stage 09 PowerShell target tooling", workflow)
        self.assertIn("prepare-stage09-target-profile.ps1", workflow)
        self.assertIn("run-stage09-target-firefox.ps1", workflow)
        self.assertIn("run-stage09-target-matrix.ps1", workflow)
        self.assertIn("stage09-ci-performance.json", workflow)
        self.assertIn("non-target content-free performance evidence", workflow)

    def test_target_matrix_is_exact_fail_closed_cross_browser_contract(self):
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage09-target-matrix.ps1"
        ).read_text(encoding="utf-8")
        validator = (
            PERF / "validate-stage09-target.py"
        ).read_text(encoding="utf-8")
        self.assertIn("$WarmupSeconds = 60", script)
        self.assertIn("$SteadySeconds = 120", script)
        self.assertIn("$BrowserResourceRepetitions = 3", script)
        self.assertIn("$DiscardRestoreRepetitions = 5", script)
        self.assertIn("$ReuseRepetitions = 50", script)
        self.assertIn("$RestoreRepetitions = 30", script)
        self.assertIn("$CreateRepetitions = 30", script)
        self.assertIn("$ColdStartRepetitions = 10", script)
        self.assertIn("$PrimitiveRepetitions = 100", script)
        self.assertIn('@("firefox", "chrome")', script)
        self.assertIn('@("chrome", "firefox")', script)
        self.assertIn("-ConfirmAcPower", script)
        self.assertIn("-ConfirmChromeMemorySaverDisabled", script)
        self.assertIn("pre-existing $name process is present", script)
        self.assertIn("sustained unrelated CPU exceeded 20 percent", script)
        self.assertIn("Initialize-FirefoxBaselineProfile", script)
        self.assertIn("browser.aboutwelcome.enabled", script)
        self.assertIn("browser.shell.checkDefaultBrowser", script)
        self.assertIn("browser.sessionstore.resume_from_crash", script)
        self.assertIn("termsofuse.bypassNotification", script)
        self.assertIn("New-ProcessOwnershipTracker", script)
        self.assertIn("Update-ProcessOwnershipTracker", script)
        self.assertIn("KnownPids", script)
        self.assertIn("Stop-TrackedProcessName", script)
        self.assertIn("-OwnershipTracker $tracker", script)
        self.assertIn("-PassThru", script)
        self.assertIn("unowned $($Tracker.Name) process appeared during measurement", script)
        self.assertIn('"TARGET_WINDOWS_OPERATOR_WORKSTATION"', script)
        self.assertIn("STAGE09_TARGET_EVIDENCE_VALID=PASS", validator)
        self.assertNotIn("querySelector", script)
        self.assertNotIn("cookies.sqlite", script)
        self.assertNotIn("logins.json", script)

    def test_ci_executes_target_matrix_plan_only_without_claiming_target_evidence(self):
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage09-ci.ps1"
        ).read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run-stage09-target-matrix.ps1", script)
        self.assertIn("-PlanOnly", script)
        self.assertIn('"TARGET_MATRIX_PLAN_ONLY"', script)
        self.assertIn("STAGE09_TARGET_MATRIX_PLAN_SMOKE=PASS", script)
        self.assertIn("stage09-target-plan.json", workflow)

    def test_target_matrix_temporarily_binds_exact_head_native_host_and_restores_it(self):
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage09-target-matrix.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn("native-host-exact-head.json", script)
        self.assertIn("path = $helperExe", script)
        self.assertIn("$originalNativeHostPath", script)
        self.assertIn("Set-Item -LiteralPath $nativeRegPath -Value $targetNativeManifest", script)
        self.assertIn("Set-Item -LiteralPath $nativeRegPath -Value $originalNativeHostPath", script)

    def test_workflow_has_opt_in_exact_head_self_hosted_target_job(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("repair_target_profile:", workflow)
        self.assertIn("run_target_preflight:", workflow)
        self.assertIn("run_target_benchmark:", workflow)
        self.assertIn("stage09-profile-repair", workflow)
        self.assertIn("target-profile-repair:", workflow)
        self.assertIn("STAGE09_TARGET_PROFILE_REPAIR=PASS", workflow)
        self.assertIn("-InteractiveInstall", workflow)
        self.assertIn("-VerifyOnly", workflow)
        self.assertIn("stage09-preflight", workflow)
        self.assertIn("target-preflight:", workflow)
        self.assertIn("-PreflightOnly", workflow)
        self.assertIn("stage09-preflight-diagnostics/**", workflow)
        self.assertIn("confirm_ac_power:", workflow)
        self.assertIn("confirm_chrome_memory_saver_disabled:", workflow)
        self.assertIn("runs-on: [self-hosted, windows, x64, workspace-operator-target]", workflow)
        self.assertIn("needs: validation", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.run_target_benchmark", workflow)
        self.assertIn("Target runner must be launched interactively", workflow)
        self.assertIn("operator-bridge-stage09-target-", workflow)

    def test_target_evidence_schema_requires_exact_frozen_execution_shape(self):
        schema = json.loads(
            (PERF / "stage09-target-evidence.schema.json").read_text(encoding="utf-8")
        )
        props = schema["properties"]
        self.assertEqual("TARGET_WINDOWS_OPERATOR_WORKSTATION", props["evidence_class"]["const"])
        self.assertTrue(props["target_contract_complete"]["const"])
        self.assertEqual(60, props["measurement"]["properties"]["warmup_seconds"]["const"])
        self.assertEqual(120, props["measurement"]["properties"]["steady_state_seconds"]["const"])
        reps = props["repetitions"]["properties"]
        self.assertEqual(3, reps["browser_resource"]["const"])
        self.assertEqual(5, reps["discard_restore"]["const"])
        self.assertEqual(50, reps["reuse"]["const"])
        self.assertEqual(30, reps["restore"]["const"])
        self.assertEqual(30, reps["create"]["const"])
        self.assertEqual(10, reps["cold_start"]["const"])
        self.assertEqual(100, reps["local_primitives"]["const"])
        self.assertEqual(0, props["blockers"]["maxItems"])

    def test_target_firefox_collector_fails_closed_and_never_claims_completion(self):
        script = (
            ROOT / "operator-bridge" / "tools" / "run-stage09-target-firefox.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn("Target measurement rejected: unrelated same-name Firefox process is present.", script)
        self.assertIn("--mode=target", script)
        self.assertIn("--warmup-ms=60000", script)
        self.assertIn("--sample-ms=120000", script)
        self.assertIn("--sample-interval-ms=1000", script)
        self.assertIn("--latency-scale=1", script)
        self.assertIn("$SkipLatency", script)
        self.assertIn("--skip-latency", script)
        self.assertIn("$SkipColdStart", script)
        self.assertIn('"TARGET_MODE_PARTIAL"', script)
        self.assertIn("--mode=cold-target", script)
        self.assertIn("--cold-count=10", script)
        self.assertIn('"TARGET_COLD_FIREFOX_PARTIAL"', script)
        self.assertIn("must not claim complete UX-09 acceptance", script)
        self.assertIn("$DiagnosticsDirectory", script)
        self.assertIn("TARGET_ADAPTER_PREFLIGHT_DIAGNOSTICS", script)
        self.assertIn("tracked_owned_firefox_ids", script)
        self.assertIn("runner_exit_code", script)
        self.assertIn("CloseMainWindow", script)
        self.assertIn("owned_by_collector", script)
        self.assertIn("runner.out.log", script)
        self.assertIn("fake-worker.err.log", script)
        self.assertNotIn("Stop-Process -Name firefox", script)

    def test_cold_start_launcher_is_fixed_profile_chrome_level_only(self):
        launcher = (
            ROOT / "operator-bridge" / "src" / "WorkspaceOperator" / "Windows" / "Firefox" / "FirefoxWorkerEnvironmentLauncher.cs"
        ).read_text(encoding="utf-8")
        tray = (
            ROOT / "operator-bridge" / "src" / "WorkspaceOperator" / "Windows" / "TrayApplicationContext.cs"
        ).read_text(encoding="utf-8")
        self.assertIn('ProfileName = "WorkspaceWorkers"', launcher)
        self.assertIn('ArgumentList.Add("-P")', launcher)
        self.assertIn("ArgumentList.Add(ProfileName)", launcher)
        self.assertIn('ArgumentList.Add("-no-remote")', launcher)
        self.assertNotIn("chatgpt.com", launcher.lower())
        self.assertNotIn("http://", launcher.lower())
        self.assertNotIn("https://", launcher.lower())
        self.assertIn("new FirefoxWorkerEnvironmentLauncher()", tray)
        self.assertIn("TimeSpan.FromSeconds(8)", tray)

    def test_cold_target_probe_uses_production_launcher_and_owned_pid(self):
        source = (PERF / "Program.cs").read_text(encoding="utf-8")
        self.assertIn('"cold-target"', source)
        self.assertIn("new FirefoxWorkerEnvironmentLauncher()", source)
        self.assertIn("recordingLauncher.LastProcessId", source)
        self.assertIn("TerminateOwnedFirefoxAsync(processId)", source)
        self.assertIn("CloseMainWindow()", source)
        self.assertIn("TimeSpan.FromSeconds(8)", source)
        self.assertIn('"TARGET_COLD_FIREFOX_PARTIAL"', source)
        self.assertNotIn('"IMPLEMENTATION_GAP"', source)


    def test_stage09_target_is_fake_worker_only_and_identity_fenced(self):
        manifest = json.loads(
            (PERF / "FirefoxProfile" / "extension" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        background = (
            PERF / "FirefoxProfile" / "extension" / "background.js"
        ).read_text(encoding="utf-8")
        hub = (
            ROOT
            / "operator-bridge"
            / "src"
            / "WorkspaceOperator"
            / "Ipc"
            / "BrowserCommandHub.cs"
        ).read_text(encoding="utf-8")
        harness = (PERF / "Program.cs").read_text(encoding="utf-8")
        builder = (PERF / "build-stage09-performance-xpi.ps1").read_text(
            encoding="utf-8"
        )
        prep = (PERF / "prepare-stage09-target-profile.ps1").read_text(
            encoding="utf-8"
        )
        matrix = (
            ROOT / "operator-bridge" / "tools" / "run-stage09-target-matrix.ps1"
        ).read_text(encoding="utf-8")
        collector = (
            ROOT / "operator-bridge" / "tools" / "run-stage09-target-firefox.ps1"
        ).read_text(encoding="utf-8")

        self.assertEqual("0.1.9", manifest["version"])
        self.assertLessEqual(len(manifest["name"]), 45)
        self.assertIn('const ADAPTER_VERSION = "0.1.9-perf";', background)
        self.assertIn("ADAPTER_IDENTITY_REJECTED", hub)
        self.assertIn('"adapter-preflight"', harness)
        self.assertIn('"0.1.9-perf"', harness)
        self.assertIn('"ADAPTER_IDENTITY_REJECTED"', harness)
        self.assertIn('"ADAPTER_CONNECTION_NOT_OBSERVED"', harness)
        self.assertIn('"IPC_SERVER_TEARDOWN_FAILED"', harness)
        self.assertIn("CaptureDiagnostics", harness)
        self.assertIn("Snapshot", harness)
        self.assertIn("UNSIGNED_MOZILLA_SIGNING_INPUT", builder)
        self.assertIn('https://chatgpt.com/', builder)
        self.assertIn("must not retain the production ChatGPT worker URL", builder)
        self.assertIn("Refusing to mutate an existing Firefox profile not owned by Stage 09", prep)
        self.assertIn("profiles.ini", prep)
        self.assertIn("STAGE09_TARGET_PROFILE_STALE_REGISTRATION_RECONCILED=PASS", prep)
        self.assertIn("STAGE09_TARGET_PROFILE_REFRESH_REGISTRATION_RECONCILED=PASS", prep)
        self.assertIn("outside Firefox Profiles", prep)
        self.assertIn("outside the owned Stage 09 path", prep)
        self.assertIn("Signed Stage 09 XPI retains the production ChatGPT worker URL", prep)
        self.assertIn("$InteractiveInstall", prep)
        self.assertIn("STAGE09_TARGET_PROFILE_INSTALL_UI_OPENED=PASS", prep)
        self.assertIn("STAGE09_TARGET_PROFILE_ADDON_STATE=", prep)
        self.assertIn("extensions.json", prep)
        self.assertIn("performance adapter is not active/enabled", prep)
        self.assertIn("Copy-Item -LiteralPath $xpi -Destination $canonicalXpi -Force", prep)
        self.assertNotIn('$extensions = Join-Path $profile "extensions"', prep)
        self.assertNotIn('$ExpectedExtensionId + ".xpi"', prep)
        self.assertIn("PerformanceSignedXpiPath", matrix)
        self.assertIn("prepare-stage09-target-profile.ps1", matrix)
        self.assertIn("TARGET_ADAPTER_PREFLIGHT", matrix)
        self.assertIn("$PreflightOnly", matrix)
        self.assertIn("STAGE09_TARGET_PREFLIGHT_ONLY=PASS", matrix)
        self.assertIn("stage09-preflight-diagnostics", matrix)
        self.assertIn("$PreflightOnly", collector)
        self.assertIn("preflight produced no result evidence", collector)
        self.assertIn("preflight emitted failing or invalid evidence", collector)

    def test_stage09_target_bootstrap_restores_machine_state(self):
        matrix = (
            ROOT / "operator-bridge" / "tools" / "run-stage09-target-matrix.ps1"
        ).read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")

        try_index = matrix.index(
            'try {\n  New-Item -Path "HKCU:\\Software\\Mozilla\\NativeMessagingHosts"'
        )
        native_set_index = matrix.index(
            "Set-Item -LiteralPath $nativeRegPath -Value $targetNativeManifest"
        )
        self.assertGreater(native_set_index, try_index)
        self.assertIn("$nativeRegExisted", matrix)
        self.assertIn("Remove-Item -LiteralPath $nativeRegPath -Recurse -Force", matrix)
        self.assertNotIn("HKCU:\\Software\\Policies\\Google", matrix)
        self.assertNotIn("HighEfficiencyModeEnabled", matrix)
        self.assertIn("Initialize-ChromeBenchmarkProfile", matrix)
        self.assertIn("performance_tuning", matrix)
        self.assertIn("high_efficiency_mode", matrix)
        self.assertIn("state = 0", matrix)
        self.assertIn('method = "fresh-user-data-local-state"', matrix)
        self.assertIn("PSExecutionPolicyPreference: Bypass", workflow)
        target_block = workflow.split("  target-performance:", 1)[1]
        self.assertIn("shell: powershell", target_block)
        self.assertNotIn("shell: pwsh", target_block)
        self.assertIn("stage09-performance-unsigned.xpi", workflow)


if __name__ == "__main__":
    unittest.main()
