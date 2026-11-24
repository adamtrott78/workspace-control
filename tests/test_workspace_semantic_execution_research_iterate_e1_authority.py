from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUTH=ROOT/'architecture/workspace-semantic-execution-research-iterate-e1-authority.v0.1.json'
REVIEW_HEAD='1e3569f8b46cfaee4a9f8b9d6ef751d6d367e5aa'

def git(spec: str) -> str:
    return subprocess.check_output(['git','rev-parse',spec],cwd=ROOT,text=True).strip()

def authority() -> dict:
    return json.loads(AUTH.read_text(encoding='utf-8'))

def test_e1_authority_is_exactly_one_pending_attempt() -> None:
    a=authority()
    assert a['status']=='PENDING_OPERATOR_WOP_E1_EXECUTION'
    assert a['approval_basis']['approved_scope']=='EXACTLY_ONE_E1_LIVE_ATTEMPT'
    assert a['approval_basis']['standing_or_future_authority_inferred'] is False
    assert a['attempt_contract']['attempts_authorized']==1
    assert a['attempt_contract']['consumed'] is False
    assert a['attempt_contract']['reusable'] is True
    assert a['attempt_contract']['no_silent_retry'] is True

def test_e1_authority_binds_reviewed_execution_bytes() -> None:
    a=authority(); b=a['execution_bindings']
    assert b['source_parent_head']==REVIEW_HEAD
    assert b['candidate_baseline']=='8aacc7eebbbafabcb20b372aa53b88350a44e633'
    for path, blob in b.items():
        if path in {'source_parent_head','candidate_baseline','operator-bridge/src_tree'}: continue
        assert git(f'{REVIEW_HEAD}:{path}') == blob
    assert git(f'{REVIEW_HEAD}:operator-bridge/src') == b['operator-bridge/src_tree']

def test_e1_authority_workspace_shell_is_read_only() -> None:
    w=authority()['workspace_shell_authority']
    assert w['allowed_tool']=='workspace_shell_inspect'
    assert w['exact_args']['operation']=='runtime_inventory'
    assert w['prohibited_tools']==['workspace_shell_exec','workspace_shell_run_reviewed_helper']
    assert w['privileged_execution'] is False
    assert w['authority_widening'] is False

def test_e1_authority_requires_same_exact_sha_for_refresh_and_launch() -> None:
    l=authority()['launch_contract']
    assert l['wop_driver_refresh_required_once'] is True
    assert l['exact_authority_sha_required_for_refresh_and_launch'] is True
    assert l['branch_must_remain_at_authority_commit_before_launch'] is True

def test_e1_authority_preserves_manual_a7_loop() -> None:
    a=authority()
    assert a['accepted_frontend']['operator_loop']=='Ctrl+Space -> Ctrl+V -> Enter'
    assert a['operator_service_contract']['manual_instant_service_points']==4
    assert a['retained_prohibitions']['automatic_typing'] is False
    assert a['retained_prohibitions']['automatic_submission'] is False
