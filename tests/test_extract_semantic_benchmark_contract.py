from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "active" / "workspace-extract-semantic-benchmark-v1.json"
CONTRACT = ROOT / "architecture" / "extract-semantic-benchmark-contract.v0.1.md"
CORPUS = ROOT / "architecture" / "extract-semantic-benchmark-corpus.v0.1.json"
SCHEMA = ROOT / "schemas" / "extract_semantic_benchmark.v0.1.schema.json"
PILOT = ROOT / "architecture" / "extract-semantic-benchmark-pilot-annotations.v0.1.json"
SOURCE_MANIFEST = ROOT / "architecture" / "extract-semantic-benchmark-source-manifest.v0.1.json"


def test_semantic_benchmark_uses_fresh_heldout_papers() -> None:
    data = json.loads(CORPUS.read_text())
    dev = set(data["development_corpus_exclusions"]["legacy_wave1_arxiv_ids"])
    pilot = {p["arxiv_id"] for p in data["pilot_papers"]}
    acceptance = {p["arxiv_id"] for p in data["acceptance_papers"]}

    assert len(pilot) == 2
    assert len(acceptance) == 8
    assert not (pilot & acceptance)
    assert not (dev & pilot)
    assert not (dev & acceptance)


def test_acceptance_papers_are_not_development_inputs() -> None:
    data = json.loads(CORPUS.read_text())
    policy = data["contamination_policy"]

    assert policy["active_extract_may_use_acceptance_papers_for_development"] is False
    assert policy["active_extract_may_read_acceptance_gold"] is False
    assert policy["active_extract_may_run_acceptance_evaluation_before_architecture_freeze"] is False


def test_contract_does_not_require_13_of_13() -> None:
    text = CONTRACT.read_text()

    assert "No rule requires 13/13" in text
    assert "development data" in text
    assert "eight fresh papers" in text.lower()
    assert "unsupported-claim rate" in text
    assert "macro-average CORE obligation recall" in text


def test_schema_requires_source_first_exact_provenance() -> None:
    data = json.loads(SCHEMA.read_text())
    paper_required = set(data["$defs"]["paper"]["required"])
    obligation_required = set(data["$defs"]["obligation"]["required"])

    assert {"source_sha256", "page_count", "source_pdf_url"} <= paper_required
    assert {"normalized_claim", "support_mode", "quotes", "importance"} <= obligation_required
    assert data["$defs"]["annotation_provenance"]["properties"]["source_first"]["const"] is True
    assert data["$defs"]["annotation_provenance"]["properties"]["extract_outputs_viewed"]["const"] is False


def test_task_keeps_research_engine_read_only() -> None:
    data = json.loads(TASK.read_text())
    repos = {r["name"]: r for r in data["repositories"]}

    assert repos["research-engine"]["intent"] == "read"
    assert repos["research-engine"]["allowed_mutation_scope"] == []
    assert data["current_stage"] == "freeze_benchmark_contract_and_holdout_corpus"


def test_pilot_annotations_are_source_first_and_not_acceptance_gold() -> None:
    data = json.loads(PILOT.read_text())

    assert data["constraints"]["source_first"] is True
    assert data["constraints"]["local_extract_outputs_viewed"] is False
    assert data["constraints"]["acceptance_score_eligible"] is False
    assert len(data["papers"]) == 2
    assert all(p["source_sha256"] is None for p in data["papers"])
    assert sum(len(p["obligations"]) for p in data["papers"]) >= 10
    assert any(
        o["support_mode"] == "COMPOSITE"
        for p in data["papers"]
        for o in p["obligations"]
    )
    assert any(
        o["type"] == "LIMITATION"
        for p in data["papers"]
        for o in p["obligations"]
    )


def test_source_manifest_freezes_all_ten_exact_pdfs() -> None:
    corpus = json.loads(CORPUS.read_text())
    manifest = json.loads(SOURCE_MANIFEST.read_text())
    papers = manifest["papers"]

    assert manifest["status"] == "SOURCE_IDENTITIES_FROZEN"
    assert len(papers) == 10
    assert sum(p["split"] == "PILOT" for p in papers) == 2
    assert sum(p["split"] == "ACCEPTANCE" for p in papers) == 8

    corpus_papers = {
        p["benchmark_paper_id"]: p
        for p in corpus["pilot_papers"] + corpus["acceptance_papers"]
    }
    for p in papers:
        assert len(p["source_pdf_sha256"]) == 64
        assert p["source_pdf_bytes"] > 0
        assert p["page_count"] == len(p["pages"]) > 0
        cp = corpus_papers[p["benchmark_paper_id"]]
        assert cp["source_sha256"] == p["source_pdf_sha256"]
        assert cp["page_count"] == p["page_count"]
        assert cp["source_identity_status"] == "FROZEN"
