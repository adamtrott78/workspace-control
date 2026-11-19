import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "operator-bridge"
MATRIX = ROOT / "architecture/workspace-semantic-execution-operator-simulator-e2e-test-matrix.v0.1.json"
CATALOG = BRIDGE / "simulator/Scenarios/stage05-l0-l1-catalog.json"
PRODUCTION_SOLUTION = BRIDGE / "WorkspaceOperatorBridge.slnx"
SIMULATOR_SOLUTION = BRIDGE / "WorkspaceOperatorBridge.Simulator.slnx"
PRODUCTION_SOURCE = BRIDGE / "src"
PROTOCOL_COPY = BRIDGE / "protocol/browser_adapter_v1.schema.json"


class SimulatorStageFiveBoundaryTests(unittest.TestCase):
    def test_stage05_catalog_covers_every_frozen_l0_l1_test(self):
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

        expected = {
            item["id"]
            for item in matrix["tests"]
            if any(layer in {"L0", "L1"} for layer in item["layers"])
        }
        actual = {item["id"] for item in catalog["tests"]}

        self.assertEqual(expected, actual)
        self.assertEqual(36, len(actual))

    def test_production_solution_does_not_link_simulator_projects(self):
        production = PRODUCTION_SOLUTION.read_text(encoding="utf-8")
        simulator = SIMULATOR_SOLUTION.read_text(encoding="utf-8")

        self.assertNotIn("WorkspaceOperator.Simulator", production)
        self.assertNotIn("Simulator.Tests", production)
        self.assertIn("WorkspaceOperator.Simulator", simulator)
        self.assertIn("Simulator.Tests", simulator)

    def test_sim_human_submit_absent_from_production_source_and_protocol(self):
        production_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in PRODUCTION_SOURCE.rglob("*")
            if path.is_file() and path.suffix in {".cs", ".js", ".json"}
        )
        protocol = PROTOCOL_COPY.read_text(encoding="utf-8")

        self.assertNotIn("SIM_HUMAN_SUBMIT", production_text)
        self.assertNotIn("SIM_HUMAN_SUBMIT", protocol)
        self.assertNotIn("FaultInjector", production_text)

    def test_fake_worker_surface_is_simulator_only(self):
        surface = BRIDGE / "simulator/FakeWorker/index.html"
        self.assertTrue(surface.is_file())
        self.assertFalse((BRIDGE / "src/FakeWorker/index.html").exists())


if __name__ == "__main__":
    unittest.main()
