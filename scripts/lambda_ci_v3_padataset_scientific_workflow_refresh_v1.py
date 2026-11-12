#!/usr/bin/env python3
"""One-shot live refresh of only PADataset scientific trusted-workflow authority."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import tempfile
import uuid
from typing import Any

import lambda_ci_v3_reconciler as candidate

BASE_MANIFEST = pathlib.Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
TARGET_CLASS = candidate.PADATASET_SCIENTIFIC_TARGET_CLASS
TARGET_UNIT = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
TARGET_POLICY = pathlib.Path("/etc/workspace-ci/v3/controllers") / f"{TARGET_CLASS}.json"
SCIENTIFIC_ACTIVE = candidate.PADATASET_SCIENTIFIC_ACTIVE_RECEIPT
REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_ACTIVE_RECEIPT
INSTALLED_RECONCILER = candidate.RECONCILER_SCRIPT
RECONCILER_OVERRIDE = candidate.RECONCILER_OVERRIDE_ACTIVE_RECEIPT
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
SCIENTIFIC_ROOT = pathlib.Path("/var/lib/workspace-ci/v3/padataset-scientific")
TX_ROOT = SCIENTIFIC_ROOT / "workflow-refresh" / "transactions"
AUTHORITY_ROOT = SCIENTIFIC_ROOT / "authority-consumption"
OLD_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_BLOB
NEW_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_BLOB
PAD_MAIN = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_PAD_MAIN
WORKFLOW_PATH = candidate.PADATASET_SCIENTIFIC_WORKFLOW_PATH
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
AUTHORITY_MAX_SECONDS = 30 * 60
PREFLIGHT_MAX_SECONDS = 15 * 60

class RefreshError(RuntimeError):
    pass

def canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def load(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RefreshError(f"{path}: expected JSON object")
    return value, raw

def parse_time(raw: Any, label: str) -> datetime:
    if not isinstance(raw, str):
        raise RefreshError(f"{label} missing")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RefreshError(f"{label} invalid") from exc
    if value.tzinfo is None:
        raise RefreshError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)

def require_root_private(path: pathlib.Path) -> bytes:
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or st.st_gid != 0:
        raise RefreshError(f"root-private file metadata invalid: {path}")
    if stat.S_IMODE(st.st_mode) != 0o600:
        raise RefreshError(f"root-private file mode invalid: {path}")
    return path.read_bytes()

def exact_repo(repo: pathlib.Path, expected: str) -> pathlib.Path:
    if SHA40.fullmatch(expected) is None:
        raise RefreshError("expected source head invalid")
    head = subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
    if head != expected:
        raise RefreshError(f"source head mismatch: {head} != {expected}")
    dirty = subprocess.check_output(["git","-C",str(repo),"status","--porcelain=v1","--untracked-files=normal"],text=True)
    if dirty.strip():
        raise RefreshError("source checkout is dirty")
    return repo.resolve()

def systemd(unit: str) -> dict[str,str]:
    proc = subprocess.run(
        ["systemctl","show",unit,"-p","LoadState","-p","ActiveState","-p","SubState","-p","MainPID","-p","NRestarts","-p","InvocationID","-p","UnitFileState","--no-pager"],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,
    )
    if proc.returncode:
        raise RefreshError(f"systemctl show failed: {unit}: {proc.stderr.strip()[:512]}")
    out={}
    for line in proc.stdout.splitlines():
        if "=" in line:
            k,v=line.split("=",1); out[k]=v
    return out

def run_systemctl(*args: str) -> None:
    proc=subprocess.run(["systemctl",*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if proc.returncode:
        raise RefreshError(f"systemctl {' '.join(args)} failed: {proc.stderr.strip()[:512]}")

def controller_snapshots() -> dict[str,dict[str,str]]:
    root,_=load(ROOT_POLICY)
    classes=root.get("runner_classes")
    if not isinstance(classes,dict) or TARGET_CLASS not in classes:
        raise RefreshError("installed class set invalid")
    return {
        cid:systemd(f"workspace-ci-v3-controller@{cid}.service")
        for cid in sorted(classes) if cid != TARGET_CLASS
    }

def require_snapshot_same(before: dict[str,dict[str,str]], after: dict[str,dict[str,str]]) -> None:
    fields=("LoadState","ActiveState","SubState","MainPID","NRestarts","InvocationID","UnitFileState")
    if set(before)!=set(after):
        raise RefreshError("non-target controller set changed")
    for cid in before:
        for field in fields:
            if before[cid].get(field)!=after[cid].get(field):
                raise RefreshError(f"non-target controller changed: {cid} {field}")

def require_roots() -> None:
    p=systemd(PROVISIONER_UNIT)
    if p.get("ActiveState")!="active" or p.get("SubState")!="running":
        raise RefreshError("shared provisioner is not active/running")
    r=systemd(RECONCILER_UNIT)
    if r.get("ActiveState")!="active" or r.get("SubState")!="exited" or r.get("MainPID") not in {"","0"}:
        raise RefreshError("reconciler must be active/exited with no running process")

def ensure_dir(path: pathlib.Path) -> None:
    path.mkdir(parents=True,exist_ok=True)
    os.chown(path,0,0); os.chmod(path,0o700)

def atomic_file(path: pathlib.Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=f".{path.name}.",dir=str(path.parent))
    tmp=pathlib.Path(name)
    try:
        with os.fdopen(fd,"wb") as h:
            os.fchmod(h.fileno(),mode); h.write(raw); h.flush(); os.fsync(h.fileno())
        os.chown(tmp,0,0); os.replace(tmp,path)
        dfd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    finally:
        try: tmp.unlink()
        except FileNotFoundError: pass

def atomic_json(path: pathlib.Path, value: dict[str,Any]) -> None:
    ensure_dir(path.parent); atomic_file(path,canonical(value),0o600)

def validate_preflight(path: pathlib.Path) -> tuple[dict[str,Any],bytes]:
    raw=require_root_private(path)
    value=json.loads(raw)
    required={
        "schema_version":1,
        "mode":"PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_PREFLIGHT",
        "repository":"adamtrott78/PADataset",
        "padataset_main_sha":PAD_MAIN,
        "workflow_path":WORKFLOW_PATH,
        "workflow_blob_sha":NEW_BLOB,
        "scale_set_name":candidate.PADATASET_SCIENTIFIC_TARGET_SCALE_SET,
        "scale_set_id":5,
        "assigned_jobs":0,
        "running_jobs":0,
        "active_workflow_runs":0,
    }
    if not isinstance(value,dict):
        raise RefreshError("preflight must be object")
    for k,v in required.items():
        if value.get(k)!=v:
            raise RefreshError(f"preflight mismatch: {k}")
    allowed=set(required)|{"confirmed_at"}
    if set(value)!=allowed:
        raise RefreshError("preflight keys drift")
    age=(datetime.now(timezone.utc)-parse_time(value["confirmed_at"],"confirmed_at")).total_seconds()
    if age<0 or age>PREFLIGHT_MAX_SECONDS:
        raise RefreshError("workflow refresh preflight is stale")
    return value,raw

def validate_authority(path: pathlib.Path, expected: dict[str,Any]) -> tuple[dict[str,Any],bytes]:
    raw=require_root_private(path)
    value=json.loads(raw)
    required={"schema_version","authority","operation","authorization_id","issued_at","expires_at",*expected.keys()}
    if not isinstance(value,dict) or set(value)!=required:
        raise RefreshError("authority keys drift")
    if value["schema_version"]!=1 or value["authority"]!="workspace-control-operator" or value["operation"]!="REFRESH_PADATASET_SCIENTIFIC_WORKFLOW_V1":
        raise RefreshError("authority identity invalid")
    aid=value["authorization_id"]
    if not isinstance(aid,str) or UUID_RE.fullmatch(aid) is None or str(uuid.UUID(aid))!=aid:
        raise RefreshError("authorization id invalid")
    for k,v in expected.items():
        if value.get(k)!=v:
            raise RefreshError(f"authority binding mismatch: {k}")
    issued=parse_time(value["issued_at"],"issued_at"); expires=parse_time(value["expires_at"],"expires_at"); now=datetime.now(timezone.utc)
    if not (issued<=now<=expires) or (expires-issued).total_seconds()>AUTHORITY_MAX_SECONDS:
        raise RefreshError("authority validity window invalid")
    return value,raw

def consume_authority(value: dict[str,Any], raw: bytes) -> pathlib.Path:
    ensure_dir(AUTHORITY_ROOT)
    marker=AUTHORITY_ROOT/f"{value['authorization_id']}.json"
    record={"schema_version":1,"authorization_id":value["authorization_id"],"operation":value["operation"],"authority_sha256":sha(raw),"consumed_at":datetime.now(timezone.utc).isoformat()}
    fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"wb") as h:
        h.write(canonical(record)); h.flush(); os.fsync(h.fileno())
    os.chown(marker,0,0)
    return marker

def current_reconciler_override(manifest: dict[str,Any], manifest_raw: bytes, actual_sha: str) -> tuple[dict[str,Any],bytes]:
    value,raw=load(RECONCILER_OVERRIDE)
    entries={str(e["destination"]):e for e in manifest["entries"]}
    entry=entries[str(INSTALLED_RECONCILER)]
    required={
        "schema_version":1,"mode":"V3_RECONCILER_OVERRIDE","phase":"ACTIVE",
        "base_source_head":manifest.get("source_head"),
        "base_install_manifest_sha256":sha(manifest_raw),
        "base_reconciler_sha256":entry.get("sha256"),
        "reconciler_sha256":actual_sha,
        "reconciler_mode":str(entry.get("mode")),
        "root_policy_sha256":manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent":True,
    }
    for k,v in required.items():
        if value.get(k)!=v:
            raise RefreshError(f"current reconciler override mismatch: {k}")
    return value,raw

def policy_digest(policy: dict[str,Any]) -> str:
    payload={
        k:v for k,v in policy.items()
        if k not in {"control_plane_generation_sha256","controller_policy_sha256"}
    }
    raw=json.dumps(
        payload,
        sort_keys=True,
        separators=(",",":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def build_refreshed_policy(current: dict[str,Any]) -> dict[str,Any]:
    workflows=current.get("trusted_workflows")
    if not isinstance(workflows,list) or len(workflows)!=1:
        raise RefreshError("current trusted workflow set invalid")
    workflow=workflows[0]
    required={
        "route_id":"scientific-single-gpu",
        "path":WORKFLOW_PATH,
        "default_branch":"main",
        "blob_sha":OLD_BLOB,
        "compile_time_job_key":"padataset-scientific",
        "compile_time_top_level_job_count":1,
        "allowed_events":["issue_comment"],
        "allowed_actor_logins":["adamtrott78"],
    }
    if workflow!=required:
        raise RefreshError("current workflow binding is not the accepted predecessor")
    refreshed=copy.deepcopy(current)
    refreshed_workflow=copy.deepcopy(workflow)
    refreshed_workflow["blob_sha"]=NEW_BLOB
    refreshed["trusted_workflows"]=[refreshed_workflow]
    refreshed["controller_policy_sha256"]=policy_digest(refreshed)
    return refreshed

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root",type=pathlib.Path,required=True)
    parser.add_argument("--expected-head",required=True)
    parser.add_argument("--preflight-confirmation",type=pathlib.Path,required=True)
    parser.add_argument("--authorization-receipt",type=pathlib.Path,required=True)
    args=parser.parse_args()
    if os.geteuid()!=0:
        raise RefreshError("workflow refresh requires root")
    repo=exact_repo(args.repo_root,args.expected_head)
    require_roots()

    # Candidate verifier must accept the currently installed predecessor state.
    candidate.verify_installed(BASE_MANIFEST)

    target_before=systemd(TARGET_UNIT)
    if target_before.get("ActiveState")!="active" or target_before.get("SubState")!="running" or target_before.get("UnitFileState")!="enabled":
        raise RefreshError("scientific target controller is not active/running/enabled")
    others_before=controller_snapshots()

    preflight,preflight_raw=validate_preflight(args.preflight_confirmation)
    scientific,scientific_raw=load(SCIENTIFIC_ACTIVE)
    if scientific.get("phase")!="ACTIVE" or scientific.get("trusted_workflow_blob_sha")!=OLD_BLOB:
        raise RefreshError("scientific activation predecessor binding invalid")
    if REFRESH_ACTIVE.exists():
        raise RefreshError("scientific workflow refresh already exists")

    current_policy,current_policy_raw=load(TARGET_POLICY)
    if current_policy.get("controller_policy_sha256")!=scientific.get("target_controller_policy_sha256"):
        raise RefreshError("current target policy digest binding mismatch")
    refreshed_policy=build_refreshed_policy(current_policy)
    refreshed_policy_raw=canonical(refreshed_policy)

    manifest,manifest_raw=load(BASE_MANIFEST)
    old_rec=INSTALLED_RECONCILER.read_bytes()
    old_rec_sha=sha(old_rec)
    _,old_rec_override_raw=current_reconciler_override(manifest,manifest_raw,old_rec_sha)
    new_rec=(repo/"scripts/lambda_ci_v3_reconciler.py").read_bytes()
    new_rec_sha=sha(new_rec)
    rec_blob=subprocess.check_output(["git","-C",str(repo),"hash-object","scripts/lambda_ci_v3_reconciler.py"],text=True).strip()
    entries={str(e["destination"]):e for e in manifest["entries"]}
    rec_entry=entries[str(INSTALLED_RECONCILER)]
    new_rec_override={
        "schema_version":1,"mode":"V3_RECONCILER_OVERRIDE","phase":"ACTIVE",
        "base_source_head":manifest.get("source_head"),
        "base_install_manifest_sha256":sha(manifest_raw),
        "base_reconciler_sha256":rec_entry.get("sha256"),
        "reconciler_sha256":new_rec_sha,
        "reconciler_mode":str(rec_entry.get("mode")),
        "reconciler_source_head":args.expected_head,
        "reconciler_git_blob":rec_blob,
        "root_policy_sha256":manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent":True,
    }

    expected_authority={
        "source_head":args.expected_head,
        "scientific_active_receipt_sha256":sha(scientific_raw),
        "preflight_confirmation_sha256":sha(preflight_raw),
        "previous_workflow_blob_sha":OLD_BLOB,
        "workflow_blob_sha":NEW_BLOB,
        "padataset_main_sha":PAD_MAIN,
        "previous_controller_policy_sha256":current_policy["controller_policy_sha256"],
        "controller_policy_sha256":refreshed_policy["controller_policy_sha256"],
        "target_class_id":TARGET_CLASS,
    }
    authority,authority_raw=validate_authority(args.authorization_receipt,expected_authority)

    refresh={
        "schema_version":1,
        "mode":"V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH",
        "phase":"ACTIVE",
        "source_head":args.expected_head,
        "scientific_active_receipt_sha256":sha(scientific_raw),
        "target_class_id":TARGET_CLASS,
        "workflow_path":WORKFLOW_PATH,
        "previous_workflow_blob_sha":OLD_BLOB,
        "workflow_blob_sha":NEW_BLOB,
        "padataset_main_sha":PAD_MAIN,
        "previous_controller_policy_sha256":current_policy["controller_policy_sha256"],
        "controller_policy_sha256":refreshed_policy["controller_policy_sha256"],
        "controller_policy_file_sha256":sha(refreshed_policy_raw),
    }

    ensure_dir(TX_ROOT)
    tx_id=str(uuid.uuid4()); tx_dir=TX_ROOT/f"refresh-{tx_id}"; ensure_dir(tx_dir)
    tx_path=tx_dir/"receipt.json"
    backups={
        "policy":current_policy_raw,
        "reconciler":old_rec,
        "reconciler_override":old_rec_override_raw,
    }
    tx={
        "schema_version":1,"mode":"V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_TRANSACTION",
        "phase":"PREPARED","source_head":args.expected_head,
        "authorization_id":authority["authorization_id"],
        "authority_sha256":sha(authority_raw),
        "preflight_confirmation_sha256":sha(preflight_raw),
        "previous_workflow_blob_sha":OLD_BLOB,"workflow_blob_sha":NEW_BLOB,
        "target_controller_before":target_before,
        "existing_controller_snapshot":others_before,
    }
    atomic_json(tx_path,tx)
    consume_authority(authority,authority_raw)

    target_stopped=False
    try:
        run_systemctl("stop",TARGET_UNIT); target_stopped=True
        stopped=systemd(TARGET_UNIT)
        if stopped.get("ActiveState")!="inactive":
            raise RefreshError("scientific controller did not stop")

        atomic_file(TARGET_POLICY,refreshed_policy_raw,0o644)
        atomic_json(REFRESH_ACTIVE,refresh)
        atomic_json(RECONCILER_OVERRIDE,new_rec_override)
        atomic_file(INSTALLED_RECONCILER,new_rec,int(str(rec_entry.get("mode")),8))

        candidate.verify_installed(BASE_MANIFEST)
        proc=subprocess.run(
            ["/usr/bin/python3",str(INSTALLED_RECONCILER),"--verify-installed","--manifest",str(BASE_MANIFEST)],
            text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,
        )
        if proc.returncode:
            raise RefreshError("installed reconciler verification failed: "+proc.stderr.strip()[:1024])

        run_systemctl("start",TARGET_UNIT); target_stopped=False
        target_after=systemd(TARGET_UNIT)
        if target_after.get("ActiveState")!="active" or target_after.get("SubState")!="running" or target_after.get("UnitFileState")!="enabled":
            raise RefreshError("scientific controller did not return active/running/enabled")
        require_roots()
        others_after=controller_snapshots(); require_snapshot_same(others_before,others_after)
        candidate.verify_installed(BASE_MANIFEST)

        tx.update({
            "phase":"COMMITTED_ACTIVE_WORKFLOW_REFRESH",
            "refresh_receipt_sha256":sha(REFRESH_ACTIVE.read_bytes()),
            "controller_policy_file_sha256":sha(TARGET_POLICY.read_bytes()),
            "reconciler_sha256":sha(INSTALLED_RECONCILER.read_bytes()),
            "target_controller_after":target_after,
            "existing_controller_snapshot_after":others_after,
            "completed_at":datetime.now(timezone.utc).isoformat(),
        })
        atomic_json(tx_path,tx)
        print("PADATASET_SCIENTIFIC_WORKFLOW_REFRESH=PASS")
        print(f"TRANSACTION_RECEIPT={tx_path}")
        return 0
    except BaseException as exc:
        try:
            if not target_stopped:
                subprocess.run(["systemctl","stop",TARGET_UNIT],check=False)
            atomic_file(TARGET_POLICY,backups["policy"],0o644)
            try: REFRESH_ACTIVE.unlink()
            except FileNotFoundError: pass
            atomic_file(RECONCILER_OVERRIDE,backups["reconciler_override"],0o600)
            atomic_file(INSTALLED_RECONCILER,backups["reconciler"],int(str(rec_entry.get("mode")),8))
            subprocess.run(["systemctl","start",TARGET_UNIT],check=False)
            tx["phase"]="ROLLED_BACK_PREVIOUS_WORKFLOW"; tx["rollback_completed"]=True
        except BaseException as rollback_exc:
            tx["phase"]="ROLLBACK_INCOMPLETE"; tx["rollback_completed"]=False; tx["rollback_error"]=str(rollback_exc)
        tx["failure"]=str(exc); tx["failed_at"]=datetime.now(timezone.utc).isoformat()
        atomic_json(tx_path,tx)
        raise

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except RefreshError as exc:
        print(f"ERROR: {exc}",file=__import__("sys").stderr)
        raise SystemExit(1)
