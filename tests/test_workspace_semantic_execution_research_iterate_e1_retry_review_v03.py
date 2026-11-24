from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'architecture/workspace-semantic-execution-research-iterate-e1-retry-review.v0.3.json'
PROCEDURE=ROOT/'architecture/workspace-semantic-execution-research-iterate-e1-retry-procedure.v0.3.md'
IMPLEMENTATION_HEAD="ad468737d57ed1e441d7676a52112f75a60d0fca"

def git(spec: str) -> str:
    return subprocess.check_output(['git','rev-parse',spec],cwd=ROOT,text=True).strip()

def test_retry_review_binds_exact_green_implementation() -> None:
    r=json.loads(REVIEW.read_text(encoding='utf-8'))
    assert r['status']=='VALIDATED_RETRY_REVIEW_CANDIDATE_NOT_AUTHORITY'
    assert r['implementation']['head']==IMPLEMENTATION_HEAD
    assert r['implementation']['validation']=={'workspace_control_run':3182,'semantic_execution_run':485,'operator_bridge_run':755,'result':'SUCCESS'}
    for path, blob in r['implementation']['exact_bindings'].items():
        assert git(f'{IMPLEMENTATION_HEAD}:{path}') == blob

def test_retry_review_does_not_mint_authority() -> None:
    r=json.loads(REVIEW.read_text(encoding='utf-8'))
    g=r['attempt_gate']
    assert g['live_attempt_authorized'] is False
    assert g['previous_authority_consumed'] is True
    assert g['fresh_operator_approval_required'] is True
    assert g['no_silent_retry'] is True

def test_retry_procedure_preserves_read_only_shell_and_human_loop() -> None:
    text=PROCEDURE.read_text(encoding='utf-8')
    assert 'Ctrl+Space -> Ctrl+V -> Enter' in text
    assert 'workspace_shell_inspect' in text
    assert 'grants no retry' in text
