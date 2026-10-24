from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "research_state.v1.schema.json"
METHODOLOGY = ROOT / "architecture" / "evidence-first-research-methodology.v0.1.md"
REPLAY = ROOT / "architecture" / "extract-research-replay.v0.1.md"


def test_research_state_schema_has_required_outer_loop_entities() -> None:
    data = json.loads(SCHEMA.read_text())
    assert data["$id"].endswith("/research_state.v1.schema.json")
    assert data["properties"]["hypotheses"]["items"]["$ref"] == "#/$defs/hypothesis"
    assert data["properties"]["mechanism_families"]["items"]["$ref"] == "#/$defs/mechanism_family"
    assert data["properties"]["experiment_candidates"]["items"]["$ref"] == "#/$defs/experiment_design"
    assert data["properties"]["scientific_results"]["items"]["$ref"] == "#/$defs/scientific_result"
    assert data["properties"]["belief_updates"]["items"]["$ref"] == "#/$defs/belief_update"
    assert data["properties"]["stopping_rules"]["items"]["$ref"] == "#/$defs/stopping_rule"
    assert data["properties"]["reopening_conditions"]["items"]["$ref"] == "#/$defs/reopening_condition"


def test_experiment_design_requires_predeclared_interpretation_and_decision_value() -> None:
    data = json.loads(SCHEMA.read_text())
    required = set(data["$defs"]["experiment_design"]["required"])
    assert {
        "target_uncertainty",
        "competing_hypothesis_ids",
        "discrimination_claim",
        "frozen_gates",
        "outcome_interpretations",
        "invalidation_conditions",
        "what_pass_authorizes",
        "decision_value",
    } <= required


def test_methodology_preserves_outer_inner_loop_and_shadow_boundary() -> None:
    text = METHODOLOGY.read_text()
    assert "Outer loop: scientific reasoning" in text
    assert "Inner loop: engineering execution" in text
    assert "Prospective shadow validation" in text
    assert "The shadow lane MUST NOT block the owning research task." in text
    assert "MechanismFamily" in text
    assert "StoppingRule and ReopeningCondition" in text
    assert "Ontology compatibility" in text


def test_replay_discloses_hindsight_and_mechanism_family_divergence() -> None:
    text = REPLAY.read_text()
    assert "HINDSIGHT-CONTAMINATED" in text
    assert "pairwise semantic redundancy certificate" in text
    assert "METHODOLOGY/HISTORY DIVERGENCE" in text
    assert "INVALID_EXPERIMENT / NOT_RUN" in text
    assert "Prospective shadow validation is required for actual validation." in text
