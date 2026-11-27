"""Offline Token Economy replay acceptance."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
BENCH = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "token_economy_replay_v1.py"
)


def _load():
    spec = importlib.util.spec_from_file_location(
        "token_economy_replay_v1",
        BENCH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TokenEconomyReplayTests(unittest.TestCase):
    def test_research_iterate_replay_preserves_identity_and_reduces_input(self):
        report = _load().run_replay()
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(len(report["cases"]), 4)
        for row in report["cases"]:
            self.assertTrue(row["canonical_identity_preserved"])
            self.assertEqual(row["context_mode"], "REF_ONLY")
            self.assertGreater(
                row["full_worker_text_bytes"],
                row["compact_worker_text_bytes"],
            )
            self.assertGreater(row["byte_reduction"], 0)
        aggregate = report["aggregate"]
        self.assertGreater(
            aggregate["full_worker_text_bytes"],
            aggregate["compact_worker_text_bytes"],
        )
        self.assertGreater(aggregate["byte_reduction_fraction"], 0.0)
        self.assertIn("offline input-size proxy", report["token_claim"])


if __name__ == "__main__":
    unittest.main()
