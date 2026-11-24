"""Real-workflow canary: map Research Engine orchestration into the generic kernel."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
KERNEL_PATH = ROOT / "benchmarks/workspace-semantic-execution/kernel_reference_v1.py"
FIXTURE_PATH = ROOT / "benchmarks/workspace-semantic-execution/research_engine_kernel_canary_v1.json"

spec = importlib.util.spec_from_file_location("kernel_reference_v1", KERNEL_PATH)
kernel = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(kernel)

FIXTURE = json.loads(FIXTURE_PATH.read_text())


def build_graph() -> dict:
    return kernel.new_graph(
        [
            kernel.new_process(
                node["process_id"],
                dependencies=node["dependencies"],
            )
            for node in FIXTURE["nodes"]
        ]
    )


def complete_node(graph: dict, process_id: str) -> dict:
    generation = graph["processes"][process_id]["generation"]
    lease = f"lease:{process_id}"
    worker = f"worker:{process_id}"
    graph = kernel.claim(
        graph,
        process_id,
        worker_id=worker,
        lease_id=lease,
        expected_generation=generation,
    )
    graph = kernel.start(
        graph,
        process_id,
        lease_id=lease,
        expected_generation=generation,
    )
    graph = kernel.record_effect(
        graph,
        process_id,
        action_id=f"replay:{process_id}",
        idempotency_key=f"replay:{process_id}",
        target_ref=f"research-engine:{process_id}",
        effect_hash=f"replay-hash:{process_id}",
        executor_id="research-engine-frozen-replay",
        observed_at="fixture:T1",
        lease_id=lease,
        expected_generation=generation,
    )
    graph = kernel.propose_terminal(
        graph,
        process_id,
        lease_id=lease,
        expected_generation=generation,
    )
    graph = kernel.begin_validation(graph, process_id)
    return kernel.record_validation(
        graph,
        process_id,
        validator_id="research-engine-frozen-shape-validator",
        passed=True,
        evidence_ref=(
            "research-engine@"
            + FIXTURE["source"]["commit_sha"]
            + ":src/research_engine/orchestration.py"
        ),
        observed_at="fixture:T2",
    )


class ResearchEngineKernelCanaryTests(unittest.TestCase):
    def test_fixture_is_bound_to_exact_research_engine_source(self):
        source = FIXTURE["source"]
        self.assertEqual(source["repository"], "adamtrott78/research-engine")
        self.assertEqual(
            source["commit_sha"],
            "1031861c03b2af8cff5cf72939bbbc83a95e65a4",
        )
        self.assertEqual(source["path"], "src/research_engine/orchestration.py")

    def test_real_executor_tier_shape_is_preserved(self):
        tiers = FIXTURE["executor_tiers"]
        self.assertEqual(tiers["ACQUIRE"], "DETERMINISTIC")
        self.assertEqual(tiers["DISCOVERY"], "CHEAP")
        self.assertEqual(tiers["EXTRACT"], "STANDARD")
        self.assertEqual(tiers["SYNTHESIZE"], "STRONG")
        self.assertEqual(tiers["HUMAN_REVIEW"], "HUMAN")

    def test_screen_fanout_and_checkpoint_fanin_are_enforced(self):
        graph = build_graph()

        with self.assertRaises(kernel.KernelContractError):
            kernel.claim(
                graph,
                "re:acquire:paper1",
                worker_id="early",
                lease_id="early",
                expected_generation=0,
            )

        graph = complete_node(graph, "re:discovery")
        graph = complete_node(graph, "re:screen")

        graph = complete_node(graph, "re:acquire:paper1")
        graph = complete_node(graph, "re:extract:paper1")
        graph = complete_node(graph, "re:verify:paper1")

        with self.assertRaises(kernel.KernelContractError):
            kernel.claim(
                graph,
                "re:checkpoint",
                worker_id="too-early",
                lease_id="too-early",
                expected_generation=0,
            )

        graph = complete_node(graph, "re:acquire:paper2")
        graph = complete_node(graph, "re:extract:paper2")
        graph = complete_node(graph, "re:verify:paper2")
        graph = complete_node(graph, "re:checkpoint")

        self.assertEqual(graph["processes"]["re:checkpoint"]["state"], "COMPLETED")

    def test_novelty_parallelism_and_human_gate_replay(self):
        graph = build_graph()
        ordered_prefix = [
            "re:discovery",
            "re:screen",
            "re:acquire:paper1",
            "re:extract:paper1",
            "re:verify:paper1",
            "re:acquire:paper2",
            "re:extract:paper2",
            "re:verify:paper2",
            "re:checkpoint",
            "re:synthesize",
            "re:gap",
        ]
        for process_id in ordered_prefix:
            graph = complete_node(graph, process_id)

        # Both novelty searches become independently claimable after GAP_GENERATE.
        graph_one = kernel.claim(
            graph,
            "re:novelty:g1:0",
            worker_id="novelty-0",
            lease_id="novelty-0",
            expected_generation=0,
        )
        graph_two = kernel.claim(
            graph,
            "re:novelty:g1:1",
            worker_id="novelty-1",
            lease_id="novelty-1",
            expected_generation=0,
        )
        self.assertEqual(
            graph_one["processes"]["re:novelty:g1:0"]["state"],
            "CLAIMED",
        )
        self.assertEqual(
            graph_two["processes"]["re:novelty:g1:1"]["state"],
            "CLAIMED",
        )

        graph = complete_node(graph, "re:novelty:g1:0")
        with self.assertRaises(kernel.KernelContractError):
            kernel.claim(
                graph,
                "re:arbitrate:g1",
                worker_id="early-arb",
                lease_id="early-arb",
                expected_generation=0,
            )

        graph = complete_node(graph, "re:novelty:g1:1")
        graph = complete_node(graph, "re:arbitrate:g1")

        graph = kernel.claim(
            graph,
            "re:human-review",
            worker_id="gate-controller",
            lease_id="gate-controller",
            expected_generation=0,
        )
        graph = kernel.start(
            graph,
            "re:human-review",
            lease_id="gate-controller",
            expected_generation=0,
        )
        graph = kernel.wait_external(
            graph,
            "re:human-review",
            wait_key="human-review:research-engine",
            lease_id="gate-controller",
            expected_generation=0,
        )
        gate = graph["processes"]["re:human-review"]
        self.assertEqual(gate["state"], "WAITING_EXTERNAL")
        self.assertIsNone(gate["worker_id"])
        self.assertIsNone(gate["lease_id"])
        self.assertEqual(gate["reasoning_quanta"], 0)

    def test_full_machine_prefix_reaches_human_gate_without_dependency_violation(self):
        graph = build_graph()
        machine_order = [
            "re:discovery",
            "re:screen",
            "re:acquire:paper1",
            "re:extract:paper1",
            "re:verify:paper1",
            "re:acquire:paper2",
            "re:extract:paper2",
            "re:verify:paper2",
            "re:checkpoint",
            "re:synthesize",
            "re:gap",
            "re:novelty:g1:0",
            "re:novelty:g1:1",
            "re:arbitrate:g1",
        ]
        for process_id in machine_order:
            graph = complete_node(graph, process_id)

        for process_id in machine_order:
            self.assertEqual(graph["processes"][process_id]["state"], "COMPLETED")

        human = graph["processes"]["re:human-review"]
        self.assertEqual(human["state"], "READY")
        self.assertTrue(
            all(
                graph["processes"][dep]["state"] == "COMPLETED"
                for dep in human["dependencies"]
            )
        )


if __name__ == "__main__":
    unittest.main()
