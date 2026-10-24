from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "architecture" / "research-methodology-outcome-partition-audit.v0.1.json"
SELF_STUDY = ROOT / "architecture" / "research-methodology-self-study.v0.1.json"
CANDIDATES = ROOT / "architecture" / "evidence-first-research-methodology.v0.2-candidates.md"
VALIDATOR = ROOT / "scripts" / "validate_research_outcome_partition.py"
RESULT = ROOT / "architecture" / "research-methodology-outcome-partition-result.v0.1.json"
PARTITION_SCHEMA = ROOT / "schemas" / "research_outcome_partition.v0.2-candidate.schema.json"


def _load_validator():
    spec = importlib.util.spec_from_file_location("partition_validator", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_outcome_partition_positive_control_detects_known_gap() -> None:
    module = _load_validator()
    audit = json.loads(AUDIT.read_text())
    result = module.classify(audit)

    assert result["verdict"] == "CANDIDATE_SUPPORTED"
    assert result["original"]["uncovered_count"] == 2
    assert result["original"]["overlap_count"] == 0
    assert result["corrected"]["uncovered_count"] == 0
    assert result["corrected"]["overlap_count"] == 0

    missing = result["original"]["uncovered_states"]
    assert all(state["controls_retained"] is True for state in missing)
    assert all(state["e1_supported"] is False for state in missing)
    assert all(state["e6_supported"] is False for state in missing)
    assert {state["sensitivity"] for state in missing} == {"ROBUST", "FRAGILE"}


def test_self_study_freezes_v01_and_selects_bounded_meta_experiment() -> None:
    data = json.loads(SELF_STUDY.read_text())

    assert data["selected_experiment_id"] == "exp-outcome-partition-audit-v1"
    assert data["experiment_candidates"][0]["cost_class"] == "LOW"
    assert data["experiment_candidates"][0]["decision_value"]["falsifiability"] == "HIGH"
    assert any(item["id"] == "inv-v01-immutability" for item in data["invariants"])
    assert "One meta-level only" in data["provenance"]["notes"]


def test_v02_candidates_are_non_governing_and_include_recursion_limit() -> None:
    text = CANDIDATES.read_text()

    assert "CANDIDATES ONLY / NOT GOVERNING METHOD" in text
    assert "Scientific outcome partition exhaustiveness" in text
    assert "Diagnostic depth before architecture commitment" in text
    assert "Contamination-aware architecture-selection validation" in text
    assert "Explicit steady-state overhead telemetry" in text
    assert "Recursion limit" in text


def test_outcome_partition_result_authorizes_candidate_only() -> None:
    result = json.loads(RESULT.read_text())
    schema = json.loads(PARTITION_SCHEMA.read_text())

    assert result["verdict"] == "CANDIDATE_SUPPORTED"
    assert result["observations"]["original_partition"]["uncovered_count"] == 2
    assert result["observations"]["corrected_partition"]["uncovered_count"] == 0
    assert "May draft a candidate" in result["authorization"]
    assert schema["properties"]["status"]["const"] == "CANDIDATE_NOT_GOVERNING"
    assert schema["properties"]["require_totality"]["const"] is True
    assert schema["properties"]["require_exclusivity"]["const"] is True
    assert schema["properties"]["validity_scope"]["const"] == "SCIENTIFIC_VALID_EXECUTIONS_ONLY"
