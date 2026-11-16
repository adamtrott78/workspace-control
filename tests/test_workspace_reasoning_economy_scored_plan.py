"""Frozen scored-replicate plan checks for Reasoning Economy."""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks" / "workspace-semantic-execution"
PLAN = json.loads(
    (BASE / "economics" / "scored_replicate_plan_v1.json").read_text(
        encoding="utf-8"
    )
)
RUNSET = json.loads(
    (BASE / "resumable_reasoning_matrix_runset_v1.json").read_text(
        encoding="utf-8"
    )
)
ISOLATION = json.loads(
    (BASE / "evaluator_isolation_v1.json").read_text(
        encoding="utf-8"
    )
)


class ScoredReplicatePlanTests(unittest.TestCase):
    def test_plan_matches_frozen_runset_comparison_cells(self):
        expected = set()
        scored = next(
            item
            for item in RUNSET["execution_stages"]
            if item["id"] == "scored_replicates"
        )
        for comparison in scored["comparison_plan"]:
            for phenotype in comparison["phenotypes"]:
                code = phenotype.split("_", 1)[0]
                for pair in comparison["pairs"]:
                    for arm in pair:
                        expected.add((code, arm))

        observed = {
            (cell["phenotype_code"], cell["arm"])
            for cell in PLAN["cells"]
        }
        self.assertEqual(observed, expected)
        self.assertEqual(len(observed), 18)

    def test_plan_binds_screening_source_and_is_not_launch_authority(self):
        screening = next(
            item
            for item in RUNSET["execution_stages"]
            if item["id"] == "protocol_screening"
        )
        manifest = screening["screening_completion_manifest"]

        self.assertEqual(PLAN["source_checkpoint_sha"], manifest["source_checkpoint_sha"])
        self.assertEqual(PLAN["screening_run_count"], manifest["run_count"])
        self.assertTrue(PLAN["claim_bearing"])
        self.assertEqual(PLAN["status"], "FROZEN_NOT_LAUNCHED")
        self.assertFalse(PLAN["launch_gate"]["allowed_to_launch"])
        self.assertEqual(
            PLAN["launch_gate"]["calibrated_allowance_relationship"],
            "UNKNOWN",
        )
        self.assertEqual(
            PLAN["launch_gate"]["evaluator_isolation"],
            ISOLATION["status"],
        )
        self.assertNotEqual(
            PLAN["launch_gate"]["evaluator_isolation"],
            PLAN["evaluator_isolation_contract"]["required_live_status"],
        )
        self.assertTrue(
            PLAN["evaluator_isolation_contract"][
                "required_for_claim_bearing_launch"
            ]
        )
        self.assertEqual(PLAN["summary"]["run_files_materialized"], 0)
        self.assertEqual(PLAN["summary"]["model_invocations_authorized"], 0)

    def test_exactly_fifty_four_unique_runs_are_planned(self):
        runs = [
            run
            for cell in PLAN["cells"]
            for run in cell["runs"]
        ]
        self.assertEqual(len(PLAN["cells"]), 18)
        self.assertEqual(len(runs), 54)
        self.assertEqual(
            len({run["run_id"] for run in runs}),
            54,
        )
        self.assertEqual(
            len({run["state_path"] for run in runs}),
            54,
        )
        self.assertTrue(
            all(cell["replicate_count"] == 3 for cell in PLAN["cells"])
        )
        self.assertTrue(
            all(
                run["state_path"].startswith(
                    "benchmarks/workspace-semantic-execution/runs/matrix-v1/"
                )
                for run in runs
            )
        )

    def test_matched_work_items_align_across_policies(self):
        by_phenotype = {}
        for cell in PLAN["cells"]:
            ids = {
                run["matched_work_item_id"]
                for run in cell["runs"]
            }
            previous = by_phenotype.setdefault(
                cell["phenotype_code"],
                ids,
            )
            self.assertEqual(ids, previous)
            self.assertEqual(len(ids), 3)

    def test_plan_contains_no_evaluator_oracle_payload(self):
        serialized = json.dumps(PLAN).lower()
        self.assertNotIn("oracle_path", serialized)
        self.assertNotIn("expected_hypothesis", serialized)
        self.assertNotIn("interpretation_hint", serialized)
        self.assertNotIn("seed_hex", serialized)
        self.assertNotIn("seal_nonce_hex", serialized)
        self.assertNotIn(".sealed.json", serialized)


if __name__ == "__main__":
    unittest.main()
