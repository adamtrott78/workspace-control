"""Claim-bearing E3-C2 exact bounded no-model soak execution."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))
HARNESS = (
    ROOT / "benchmarks" / "workspace-semantic-execution"
    / "research_iterate_e3_c2_soak_v1.py"
)

spec = importlib.util.spec_from_file_location("e3_c2_soak", HARNESS)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class E3C2BoundedSoakTests(unittest.TestCase):
    def test_exact_frozen_1000_cycle_no_model_soak(self):
        summary, report = module.run_e3_c2_soak()
        print("E3_C2_SUMMARY=" + module.json.dumps(
            summary, sort_keys=True, separators=(",", ":")
        ))
        print("E3_C2_REPORT=" + module.json.dumps(
            report, sort_keys=True, separators=(",", ":")
        ))

        self.assertEqual(summary["result"], "PASS")
        self.assertEqual(summary["bounds"]["cycles"], 1000)
        self.assertEqual(summary["bounds"]["sample_every_cycles"], 10)
        self.assertEqual(summary["bounds"]["warmup_cycles"], 100)
        self.assertEqual(summary["model_calls"], 0)
        self.assertEqual(summary["human_service_cycles"], 0)
        self.assertFalse(summary["gpu_use"])
        self.assertFalse(summary["padataset_access"])
        self.assertEqual(summary["recovery_cycles_completed"], 1000)
        self.assertEqual(summary["failures"], [])
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["sampling"]["sample_count"], 103)


if __name__ == "__main__":
    unittest.main()
