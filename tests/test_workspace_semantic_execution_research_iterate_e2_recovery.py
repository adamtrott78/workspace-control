"""E2 recovery-canary regression tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
CANARY = ROOT / "benchmarks/workspace-semantic-execution/research_iterate_e2_recovery_canary_v1.py"
sys.path.insert(0, str(SRC))

spec = importlib.util.spec_from_file_location("e2_recovery_canary", CANARY)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class E2RecoveryCanaryTests(unittest.TestCase):
    def test_worker_session_and_runtime_loss_recover_from_durable_state(self) -> None:
        report = module.run_e2_recovery_canary()

        self.assertEqual(report["result"], "PASS")
        self.assertTrue(report["worker_process_loss_injected"])
        self.assertEqual(report["process_generation"], {"before": 0, "after": 1})
        self.assertTrue(report["session_loss_injected"])
        self.assertEqual(report["session_generation"], {"before": 0, "after": 1})
        self.assertTrue(report["old_operator_action_staled"])
        self.assertTrue(report["late_old_candidate_rejected_without_mutation"])
        self.assertTrue(report["orchestrator_runtime_restarted"])
        self.assertTrue(report["durable_state_rehydrated_without_chat_memory"])
        self.assertTrue(report["replacement_session_created"])
        self.assertTrue(report["replacement_packet_recompiled_from_typed_state"])
        self.assertTrue(report["replacement_worker_completed"])
        self.assertTrue(report["final_rehydration_completed"])
        self.assertFalse(report["manual_state_relay"])
        self.assertFalse(report["chat_transcript_in_durable_graph"])


if __name__ == "__main__":
    unittest.main()
