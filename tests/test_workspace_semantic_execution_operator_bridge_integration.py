import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "architecture/workspace-semantic-execution-operator-simulator-e2e-test-matrix.v0.1.json"
CATALOG = ROOT / "operator-bridge/simulator/Scenarios/stage06-l2-l3-catalog.json"
PRODUCTION_SOLUTION = ROOT / "operator-bridge/WorkspaceOperatorBridge.slnx"
INTEGRATION_SOLUTION = ROOT / "operator-bridge/WorkspaceOperatorBridge.Integration.slnx"
SIM_MANIFEST = ROOT / "operator-bridge/simulator/FirefoxProfile/extension/manifest.json"
SIM_BACKGROUND = ROOT / "operator-bridge/simulator/FirefoxProfile/extension/background.js"
PROD_BACKGROUND = ROOT / "operator-bridge/src/FirefoxAdapter/background.js"
STAGE06_SCRIPT = ROOT / "operator-bridge/tools/run-stage06-firefox.ps1"


class StageSixIntegrationBoundaryTests(unittest.TestCase):
    def test_stage06_catalog_matches_frozen_required_gate_subset(self):
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        gates = {"CORE", "AUTHORITY", "ACK", "INPUT", "IDENTITY"}

        expected = {
            item["id"]
            for item in matrix["tests"]
            if item["gate"] in gates
            and any(layer in {"L2", "L3"} for layer in item["layers"])
        }
        actual = {item["id"] for item in catalog["tests"]}

        self.assertEqual(expected, actual)
        self.assertEqual(11, len(actual))

    def test_production_solution_remains_simulator_free(self):
        production = PRODUCTION_SOLUTION.read_text(encoding="utf-8")
        integration = INTEGRATION_SOLUTION.read_text(encoding="utf-8")
        self.assertNotIn("WorkspaceOperator.Simulator", production)
        self.assertNotIn("IntegrationHarness", production)
        self.assertIn("WorkspaceOperator.Simulator", integration)
        self.assertIn("IntegrationHarness", integration)

    def test_simulator_firefox_profile_keeps_same_permission_boundary(self):
        manifest = json.loads(SIM_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            ["nativeMessaging", "tabs", "sessions"],
            manifest["permissions"],
        )
        self.assertNotIn("host_permissions", manifest)
        self.assertNotIn("content_scripts", manifest)
        self.assertEqual(
            "workspace-control-operator@adamtrott78.local",
            manifest["browser_specific_settings"]["gecko"]["id"],
        )

    def test_fake_worker_override_exists_only_in_simulator_background(self):
        simulator = SIM_BACKGROUND.read_text(encoding="utf-8")
        production = PROD_BACKGROUND.read_text(encoding="utf-8")
        self.assertIn("workerStartUrl: fakeWorkerUrl", simulator)
        self.assertNotIn("workerStartUrl", production)
        self.assertNotIn("chatgpt.com", simulator.lower())

    def test_stage06_web_ext_is_exactly_pinned_and_test_only(self):
        script = STAGE06_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("web-ext@10.8.0", script)
        self.assertIn("STAGE06_WEB_EXT_VERSION=10.8.0", script)
        production_solution = PRODUCTION_SOLUTION.read_text(encoding="utf-8")
        self.assertNotIn("web-ext", production_solution.lower())

    def test_simulator_background_has_no_dom_or_synthetic_input_automation(self):
        source = SIM_BACKGROUND.read_text(encoding="utf-8")
        for forbidden in (
            "executeScript",
            "document.querySelector",
            "innerText",
            "textContent",
            "sendKeys",
            "dispatchEvent",
            "KeyboardEvent",
            "MouseEvent",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
