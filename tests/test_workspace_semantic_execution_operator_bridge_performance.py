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
        self.assertIn('"IMPLEMENTATION_GAP"', source)
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
        self.assertIn("stage09-ci-performance.json", workflow)
        self.assertIn("non-target content-free performance evidence", workflow)


if __name__ == "__main__":
    unittest.main()
