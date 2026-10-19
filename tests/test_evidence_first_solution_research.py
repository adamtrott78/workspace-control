#!/usr/bin/env python3
"""Regression tests for the shared evidence-first solution-research workflow."""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "workspace_control.py"
WORKFLOW = (
    ROOT
    / "workflows"
    / "evidence-first-solution-research.v1.json"
)
PROCEDURE = ROOT / "procedures" / "evidence_first_solution_research.md"
README = ROOT / "README.md"

spec = importlib.util.spec_from_file_location("workspace_control", SCRIPT)
workspace_control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace_control)

REPOS = json.loads((ROOT / "repos.json").read_text())["repositories"]


class EvidenceFirstSolutionResearchTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(WORKFLOW.read_text(encoding="utf-8"))

    def test_descriptor_passes_shared_semantic_validation(self):
        errors = workspace_control.validate_workflow_descriptor_v1_data(
            self.payload,
            WORKFLOW,
            REPOS,
        )
        self.assertEqual(errors, [])

    def test_workflow_preserves_research_before_heavyweight_work(self):
        stage_ids = [stage["id"] for stage in self.payload["stages"]]
        self.assertEqual(
            stage_ids,
            [
                "frame-problem",
                "recover-local-evidence",
                "research-external-solutions",
                "synthesize-architecture-families",
                "review-system-boundaries",
                "select-bounded-shortlist",
                "define-benchmark-contract",
                "handoff-to-implementation",
            ],
        )
        benchmark = next(
            stage
            for stage in self.payload["stages"]
            if stage["id"] == "define-benchmark-contract"
        )
        self.assertIn(
            "benchmark-before-heavyweight-work",
            benchmark["gates"],
        )

    def test_known_good_and_failed_approaches_are_first_class(self):
        procedure = PROCEDURE.read_text(encoding="utf-8")
        self.assertIn("known-good rollback baseline", procedure)
        self.assertIn("reuse / exclusion matrix", procedure)
        self.assertIn(
            "Do not rerun a failed approach merely under a new name",
            procedure,
        )

    def test_system_boundary_review_protects_accepted_validation_layers(self):
        procedure = PROCEDURE.read_text(encoding="utf-8")
        self.assertIn("Review system-boundary impact", procedure)
        self.assertIn(
            "preserve it as the known working baseline",
            procedure,
        )
        self.assertIn(
            "Do not optimize away a safety/verification layer",
            procedure,
        )

    def test_root_route_makes_workflow_discoverable_without_forcing_trivial_work(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn(
            "procedures/evidence_first_solution_research.md",
            readme,
        )
        self.assertIn(
            "workflows/evidence-first-solution-research.v1.json",
            readme,
        )
        self.assertIn(
            "it is not required for trivial fixes",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
