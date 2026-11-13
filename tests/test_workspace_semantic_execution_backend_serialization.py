"""Deterministic durable WorkGraph serialization tests."""
from __future__ import annotations

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
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(
            [item["process_id"] for item in payload["processes"]],
            ["complete", "waiting"],
        )

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

    def test_codec_does_not_use_pickle(self):
        source = (
            SRC
            / "workspace_semantic_execution"
            / "adapters"
            / "serialization.py"
        ).read_text().lower()
        self.assertNotIn("pickle", source)


if __name__ == "__main__":
    unittest.main()
