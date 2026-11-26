"""Deterministic durable WorkGraph serialization tests."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    GraphCodecError,
    decode_work_graph,
    dumps_work_graph,
    encode_work_graph,
    loads_work_graph,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    EffectReceipt,
    ProcessState,
    ValidationResult,
    WorkContract,
    WorkDisposition,
)


def rich_graph():
    graph = DomainKernel.create_graph(
        [
            DomainKernel.create_process("complete"),
            DomainKernel.create_process("waiting"),
        ]
    )

    graph = DomainKernel.claim(
        graph,
        "complete",
        worker_id="W1",
        lease_id="L1",
        expected_generation=0,
    )
    graph = DomainKernel.start(
        graph,
        "complete",
        lease_id="L1",
        expected_generation=0,
    )
    graph = DomainKernel.record_effect(
        graph,
        "complete",
        receipt=EffectReceipt(
            action_id="A1",
            idempotency_key="I1",
            target_ref="target:1",
            effect_hash="hash:1",
            executor_id="executor:1",
            generation=0,
            observed_at="T1",
        ),
        lease_id="L1",
        expected_generation=0,
    )
    graph = DomainKernel.propose_terminal(
        graph,
        "complete",
        lease_id="L1",
        expected_generation=0,
    )
    graph = DomainKernel.begin_validation(graph, "complete")
    graph = DomainKernel.record_validation(
        graph,
        "complete",
        result=ValidationResult(
            validator_id="V1",
            passed=True,
            evidence_ref="evidence:1",
            observed_at="T2",
        ),
    )

    graph = DomainKernel.claim(
        graph,
        "waiting",
        worker_id="W2",
        lease_id="L2",
        expected_generation=0,
    )
    graph = DomainKernel.start(
        graph,
        "waiting",
        lease_id="L2",
        expected_generation=0,
    )
    graph = DomainKernel.wait_external(
        graph,
        "waiting",
        wait_key="experiment:E1",
        lease_id="L2",
        expected_generation=0,
    )
    graph.graph_history.append(
        {
            "event": "codec-test",
            "nested": ("a", 2, {"tuple": ("x", "y")}),
        }
    )
    return graph


class GraphCodecTests(unittest.TestCase):
    def test_round_trip_preserves_exact_domain_graph(self):
        graph = rich_graph()
        encoded = encode_work_graph(graph)
        decoded = decode_work_graph(encoded)

        self.assertEqual(decoded, graph)
        self.assertEqual(
            decoded.processes["complete"].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            decoded.processes["waiting"].state,
            ProcessState.WAITING_EXTERNAL,
        )
        self.assertEqual(
            decoded.processes["waiting"].wait_key,
            "experiment:E1",
        )

    def test_dumps_is_byte_deterministic(self):
        graph = rich_graph()
        first = dumps_work_graph(graph)
        second = dumps_work_graph(graph)

        self.assertEqual(first, second)
        self.assertEqual(loads_work_graph(first), graph)
        payload = json.loads(first)
        self.assertEqual(payload["schema_version"], 9)
        self.assertEqual(
            [item["process_id"] for item in payload["processes"]],
            ["complete", "waiting"],
        )

    def test_schema_v2_preserves_work_contract_and_disposition(self):
        contract = WorkContract(
            objective="Synthesize exact evidence",
            mandatory_constraints=("no writes",),
            provenance_refs=("git:repo@sha",),
            authority_refs=("scope:read-only",),
            validator_contracts=("validator:exact",),
            output_schema_refs=("schema:summary-v1",),
        )
        graph = DomainKernel.create_graph(
            [
                DomainKernel.create_process(
                    "contracted",
                    work_contract=contract,
                )
            ]
        )
        graph = DomainKernel.claim(
            graph,
            "contracted",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.start(
            graph,
            "contracted",
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.classify_work(
            graph,
            "contracted",
            disposition=WorkDisposition.INTRINSICALLY_DIFFICULT,
            reason="coupled reasoning requires stronger executor",
            lease_id="L",
            expected_generation=0,
        )

        decoded = loads_work_graph(dumps_work_graph(graph))
        process = decoded.processes["contracted"]

        self.assertEqual(decoded, graph)
        self.assertEqual(process.work_contract, contract)
        self.assertEqual(
            process.disposition,
            WorkDisposition.INTRINSICALLY_DIFFICULT,
        )
        self.assertEqual(
            process.disposition_reason,
            "coupled reasoning requires stronger executor",
        )
        self.assertEqual(process.state, ProcessState.READY_TO_RESUME)

    def test_schema_v1_legacy_graph_remains_decodable(self):
        graph = rich_graph()
        payload = encode_work_graph(graph)
        payload["schema_version"] = 1
        for process in payload["processes"]:
            process.pop("work_contract", None)
            process.pop("disposition", None)
            process.pop("disposition_reason", None)

        decoded = decode_work_graph(payload)

        self.assertEqual(decoded, graph)
        self.assertTrue(
            all(
                process.work_contract is None
                for process in decoded.processes.values()
            )
        )
        self.assertTrue(
            all(
                process.disposition == WorkDisposition.UNCLASSIFIED
                for process in decoded.processes.values()
            )
        )

    def test_schema_v4_legacy_graph_remains_decodable_without_packet_sources(self):
        graph = rich_graph()
        payload = encode_work_graph(graph)
        payload["schema_version"] = 4
        payload.pop("packet_sources", None)

        decoded = decode_work_graph(payload)

        self.assertEqual(decoded, graph)
        self.assertEqual(decoded.packet_sources, {})

    def test_schema_v5_legacy_graph_remains_decodable_without_worker_results(self):
        graph = rich_graph()
        payload = encode_work_graph(graph)
        payload["schema_version"] = 5
        payload.pop("worker_results", None)

        decoded = decode_work_graph(payload)

        self.assertEqual(decoded, graph)
        self.assertEqual(decoded.worker_results, {})

    def test_schema_v6_legacy_graph_remains_decodable_without_publication_targets(self):
        graph = rich_graph()
        payload = encode_work_graph(graph)
        payload["schema_version"] = 6
        for source in payload.get("packet_sources", []):
            source.pop("result_publication", None)

        decoded = decode_work_graph(payload)

        self.assertEqual(decoded, graph)
        for source in decoded.packet_sources.values():
            self.assertIsNone(source.result_publication)

    def test_schema_v7_legacy_graph_remains_decodable_without_scheduler_dispatches(self):
        graph = rich_graph()
        payload = encode_work_graph(graph)
        payload["schema_version"] = 7
        payload.pop("scheduler_dispatches", None)

        decoded = decode_work_graph(payload)

        self.assertEqual(decoded, graph)
        self.assertEqual(decoded.scheduler_dispatches, {})

    def test_unknown_schema_version_fails_closed(self):
        payload = encode_work_graph(rich_graph())
        payload["schema_version"] = 999
        with self.assertRaises(GraphCodecError):
            decode_work_graph(payload)

    def test_corrupt_receipt_key_fails_closed(self):
        payload = encode_work_graph(rich_graph())
        complete = next(
            item
            for item in payload["processes"]
            if item["process_id"] == "complete"
        )
        complete["effect_receipts"][0]["idempotency_key"] = "WRONG"
        with self.assertRaises(GraphCodecError):
            decode_work_graph(payload)

    def test_codec_does_not_import_pickle(self):
        path = (
            SRC
            / "workspace_semantic_execution"
            / "adapters"
            / "serialization.py"
        )
        tree = ast.parse(path.read_text(), filename=str(path))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        self.assertNotIn("pickle", imported)


if __name__ == "__main__":
    unittest.main()
