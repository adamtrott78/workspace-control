from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'architecture/workspace-semantic-execution-research-iterate-e1-review.v0.2.json'
PROCEDURE = ROOT / 'architecture/workspace-semantic-execution-research-iterate-e1-procedure.v0.2.md'
IMPLEMENTATION_HEAD = "65bdef0e3572c5cfed8b8e59298ce86fc15b59af"

def git(spec: str) -> str:
    return subprocess.check_output(['git','rev-parse',spec], cwd=ROOT, text=True).strip()

def test_e1_v02_review_binds_corrected_implementation() -> None:
    r=json.loads(REVIEW.read_text(encoding='utf-8'))
    assert r['status']=='VALIDATED_IMPLEMENTATION_REVIEW_CANDIDATE_NOT_AUTHORITY'
    assert r['implementation']['head']==IMPLEMENTATION_HEAD
    assert r['implementation']['validation']=={'workspace_control_run':3173,'semantic_execution_run':475,'operator_bridge_run':746,'result':'SUCCESS'}
    for path, blob in r['implementation']['exact_bindings'].items():
        assert git(f'{IMPLEMENTATION_HEAD}:{path}') == blob
    assert r['implementation']['live_fixture_staging_repair']['literal_backslash_n_remaining'] is False

def test_e1_v02_review_keeps_workspace_shell_read_only() -> None:
    r=json.loads(REVIEW.read_text(encoding='utf-8'))
    w=r['workspace_shell_probe']
    assert w['literal_prefixes']==['@Workspace Shell','@github']
    assert w['allowed_tool']=='workspace_shell_inspect'
    assert w['prohibited_tools']==['workspace_shell_exec','workspace_shell_run_reviewed_helper']
    assert w['authority_widening'] is False
    assert w['expected_values_disclosed_in_worker_packet'] is False

def test_e1_v02_review_grants_zero_live_authority() -> None:
    r=json.loads(REVIEW.read_text(encoding='utf-8'))
    assert r['authority_gate']['live_attempt_authorized'] is False
    assert r['authority_gate']['fresh_one_shot_authority_required'] is True
    assert r['authority_gate']['no_silent_retry'] is True

def test_e1_v02_procedure_pins_refresh_and_launch_to_same_authority_sha() -> None:
    text=PROCEDURE.read_text(encoding='utf-8')
    assert text.count('<E1_AUTHORITY_SHA>') == 2
    assert 'wop status <E1_AUTHORITY_SHA>' in text
    assert 'wop e1 <E1_AUTHORITY_SHA>' in text
    assert 'Ctrl+Space -> Ctrl+V -> Enter' in text
