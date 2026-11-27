"""Offline E4-0 token-economy replay contract."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = (
    ROOT / "benchmarks" / "workspace-semantic-execution"
    / "token_economy_e4_0_replay_v1.py"
)


def _load():
    spec = importlib.util.spec_from_file_location(
        "token_economy_e4_0_replay_v1",
        HARNESS,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TokenEconomyReplayTests(unittest.TestCase):
    def test_replay_is_zero_model_and_preserves_identity(self) -> None:
        report = _load().build_report()
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(report["codex_calls"], 0)
        self.assertEqual(report["paid_api_calls"], 0)
        self.assertGreaterEqual(len(report["cases"]), 4)
        for row in report["cases"]:
            self.assertTrue(row["canonical_identity_preserved"])
            self.assertEqual(row["context_mode"], "REF_ONLY")
            self.assertEqual(row["reasoning_profile"], "ECONOMY")
            self.assertEqual(row["communication_mode"], "MACHINE_MINIMAL")
            self.assertEqual(row["max_output_tokens"], 500)
            self.assertLess(row["compact_bytes"], row["legacy_full_bytes"])
            self.assertGreater(row["bytes_saved"], 0)
            self.assertGreater(row["reduction_fraction"], 0)

    def test_aggregate_compact_rendering_materially_reduces_bytes(self) -> None:
        totals = _load().build_report()["totals"]
        self.assertLess(totals["compact_bytes"], totals["legacy_full_bytes"])
        self.assertGreater(totals["bytes_saved"], 0)
        self.assertGreater(totals["reduction_fraction"], 0.20)


if __name__ == "__main__":
    unittest.main()
