#!/usr/bin/env python3
"""Transactional runtime repair for the active PADataset scientific v3 lane."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
import uuid
from typing import Any

import lambda_ci_v3_reconciler as reconciler
import lambda_ci_v3_root_activation as activation

BASE_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = Path("/etc/workspace-ci/v3/root-policy.json")
INSTALLED_RUNTIME = Path("/opt/workspace-ci/v3/provisioner/lambda_ci_runtime.py")
RUNTIME_OVERRIDE = Path("/var/lib/workspace-ci/v3/runtime-refresh/active.json")
PROVISIONER_STATE = Path("/var/lib/workspace-ci/v3/provisioner")
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
TARGET_CLASS = "padataset-scientific-single-gpu-v1"
TARGET_UNIT = f"workspace-ci-v3-controller@{TARGET_CLASS}.service"
TX_ROOT = Path("/var/lib/workspace-ci/v3/padataset-scientific/runtime-repair/transactions")
AUTH_CONSUMED = Path("/var/lib/workspace-ci/v3/padataset-scientific/runtime-repair/authority-consumption")
ACTIVE_PROVISION_STATES = {"RESERVED", "PREPARING", "ACCEPTED", "RUNNING"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

class RepairError(RuntimeError):
    pass

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def canonical(v: Any) -> bytes:
    return (json.dumps(v, indent=2, sort_keys=True) + "\n").encode()

def load(path: Path) -> tuple[dict[str,Any],bytes]:
    raw=path.read_bytes()
    value=json.loads(raw)
    if not isinstance(value,dict):
        raise RepairError(f"expected object: {path}")
    return value,raw

def exact_repo(expected: str) -> Path:
    if SHA40.fullmatch(expected) is None:
        raise RepairError("expected head invalid")
    repo=Path(__file__).resolve().parents[1]
    head=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
    if head!=expected:
        raise RepairError(f"source head mismatch: {head} != {expected}")
    dirty=subprocess.check_output(["git","-C",str(repo),"status","--porcelain=v1","--untracked-files=normal"],text=True)
    if dirty.strip():
        raise RepairError("source checkout dirty")
    return repo

def systemd(unit: str) -> dict[str,str]:
    p=subprocess.run(["systemctl","show",unit,"-p","LoadState","-p","ActiveState","-p","SubState","-p","MainPID","-p","NRestarts","-p","InvocationID","-p","UnitFileState","--no-pager"],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if p.returncode:
        raise RepairError(f"systemctl show failed: {unit}: {p.stderr.strip()[:512]}")
    out={}
    for line in p.stdout.splitlines():
        if "=" in line:
            k,v=line.split("=",1); out[k]=v
    return out

def ctl(*args: str) -> None:
    p=subprocess.run(["systemctl",*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if p.returncode:
        raise RepairError(f"systemctl {' '.join(args)} failed: {p.stderr.strip()[:512]}")

def wait_state(unit: str, expected: str, timeout: float=15.0) -> None:
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if systemd(unit).get("ActiveState")==expected:
            return
        time.sleep(.1)
    raise RepairError(f"{unit} did not reach {expected}")

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True,exist_ok=True)
    os.chown(p,0,0); os.chmod(p,0o700)

def atomic_file(path: Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=f".{path.name}.",dir=str(path.parent))
    tmp=Path(name)
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

def atomic_json(path: Path, value: dict[str,Any]) -> None:
    ensure_dir(path.parent); atomic_file(path,canonical(value),0o600)

def controller_units(root: dict[str,Any]) -> dict[str,str]:
    classes=root.get("runner_classes")
    if not isinstance(classes,dict) or TARGET_CLASS not in classes:
        raise RepairError("installed runner class set invalid")
    return {cid:f"workspace-ci-v3-controller@{cid}.service" for cid in sorted(classes)}

def snapshot_controllers(units: dict[str,str]) -> dict[str,dict[str,str]]:
    return {cid:systemd(unit) for cid,unit in units.items()}

def require_no_live_provisioner_records() -> None:
    if not PROVISIONER_STATE.exists():
        return
    for p in sorted(PROVISIONER_STATE.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            value=json.loads(p.read_text())
        except Exception as exc:
            raise RepairError(f"invalid provisioner state {p.name}: {exc}") from exc
        if value.get("state") in ACTIVE_PROVISION_STATES or value.get("resource_hold") is True:
            raise RepairError(f"live provisioner record blocks runtime repair: {p.name}")

def require_no_transients(classes: dict[str,str]) -> None:
    p=subprocess.run(["systemctl","list-units","--all","--type=service","--plain","--no-legend","--no-pager"],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if p.returncode:
        raise RepairError("cannot enumerate transient units")
    prefixes=tuple(f"workspace-ci-v3-{cid}-" for cid in classes)
    for line in p.stdout.splitlines():
        fields=line.split()
        if not fields or not fields[0].startswith(prefixes):
            continue
        state=systemd(fields[0])
        if state.get("ActiveState") in {"active","activating","reloading"}:
            raise RepairError(f"live transient blocks runtime repair: {fields[0]}")

def validate_authority(path: Path, expected: dict[str,Any]) -> tuple[dict[str,Any],bytes]:
    st=path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or st.st_gid!=0 or stat.S_IMODE(st.st_mode)!=0o600:
        raise RepairError("authority metadata invalid")
    value,raw=load(path)
    required={"schema_version","authority","operation","authorization_id","issued_at","expires_at",*expected}
    if set(value)!=required:
        raise RepairError("authority keys drift")
    if value["schema_version"]!=1 or value["authority"]!="workspace-control-operator" or value["operation"]!="REPAIR_PADATASET_SCIENTIFIC_RUNTIME_V1":
        raise RepairError("authority identity invalid")
    aid=value["authorization_id"]
    if not isinstance(aid,str) or UUID_RE.fullmatch(aid) is None or str(uuid.UUID(aid))!=aid:
        raise RepairError("authorization id invalid")
    for k,v in expected.items():
        if value.get(k)!=v:
            raise RepairError(f"authority binding mismatch: {k}")
    def parse(v: Any) -> datetime:
        if not isinstance(v,str): raise RepairError("authority time invalid")
        d=datetime.fromisoformat(v.replace("Z","+00:00"))
        if d.tzinfo is None: raise RepairError("authority time must be aware")
        return d.astimezone(timezone.utc)
    issued=parse(value["issued_at"]); expires=parse(value["expires_at"]); now=datetime.now(timezone.utc)
    if not (issued<=now<=expires) or (expires-issued).total_seconds()>1800:
        raise RepairError("authority validity invalid")
    return value,raw

def consume(value: dict[str,Any], raw: bytes) -> None:
    ensure_dir(AUTH_CONSUMED)
    p=AUTH_CONSUMED/f"{value['authorization_id']}.json"
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"wb") as h:
        h.write(canonical({"schema_version":1,"authorization_id":value["authorization_id"],"operation":value["operation"],"authority_sha256":sha(raw),"consumed_at":datetime.now(timezone.utc).isoformat()}))
        h.flush(); os.fsync(h.fileno())
    os.chown(p,0,0)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--expected-head",required=True)
    ap.add_argument("--authorization-receipt",type=Path,required=True)
    args=ap.parse_args()
    if os.geteuid()!=0:
        raise RepairError("runtime repair requires root")
    repo=exact_repo(args.expected_head)

    # Candidate verifier must accept the current live generation before mutation.
    reconciler.verify_installed(BASE_MANIFEST)
    manifest,manifest_raw=load(BASE_MANIFEST)
    root,_=load(ROOT_POLICY)
    units=controller_units(root)
    before=snapshot_controllers(units)
    if before[TARGET_CLASS].get("ActiveState")!="active" or before[TARGET_CLASS].get("SubState")!="running":
        raise RepairError("scientific controller must be active/running before repair")
    provisioner_before=systemd(PROVISIONER_UNIT)
    if provisioner_before.get("ActiveState")!="active" or provisioner_before.get("SubState")!="running":
        raise RepairError("provisioner must be active/running before repair")

    current_runtime=INSTALLED_RUNTIME.read_bytes()
    candidate_runtime=(repo/"scripts/lambda_ci_runtime.py").read_bytes()
    current_sha=sha(current_runtime); candidate_sha=sha(candidate_runtime)
    if current_sha==candidate_sha:
        raise RepairError("candidate runtime is already installed")
    old_receipt_raw=RUNTIME_OVERRIDE.read_bytes() if RUNTIME_OVERRIDE.is_file() else None
    old_receipt_sha=sha(old_receipt_raw) if old_receipt_raw is not None else None

    expected={
        "source_head":args.expected_head,
        "current_runtime_sha256":current_sha,
        "candidate_runtime_sha256":candidate_sha,
        "previous_runtime_override_sha256":old_receipt_sha,
        "target_class_id":TARGET_CLASS,
    }
    authority,authority_raw=validate_authority(args.authorization_receipt,expected)

    entries={str(x["destination"]):x for x in manifest.get("entries",[]) if isinstance(x,dict) and "destination" in x}
    runtime_entry=entries.get(str(INSTALLED_RUNTIME))
    if not isinstance(runtime_entry,dict):
        raise RepairError("base runtime manifest entry missing")
    runtime_mode=int(str(runtime_entry["mode"]),8)
    if runtime_mode!=0o644:
        raise RepairError("runtime mode drift")

    active_before=[cid for cid,s in before.items() if s.get("ActiveState")=="active"]
    consume(authority,authority_raw)

    ensure_dir(TX_ROOT)
    txdir=TX_ROOT/f"repair-{uuid.uuid4()}"; ensure_dir(txdir)
    txpath=txdir/"receipt.json"
    atomic_file(txdir/"previous-runtime.py",current_runtime,runtime_mode)
    if old_receipt_raw is not None:
        atomic_file(txdir/"previous-runtime-override.json",old_receipt_raw,0o600)

    receipt={
        "schema_version":1,
        "mode":"V3_RUNTIME_OVERRIDE",
        "phase":"ACTIVE",
        "base_source_head":manifest.get("source_head"),
        "base_install_manifest_sha256":sha(manifest_raw),
        "base_runtime_sha256":runtime_entry.get("sha256"),
        "runtime_sha256":candidate_sha,
        "runtime_mode":str(runtime_entry.get("mode")),
        "runtime_source_head":args.expected_head,
        "runtime_git_blob":subprocess.check_output(["git","-C",str(repo),"hash-object","scripts/lambda_ci_runtime.py"],text=True).strip(),
        "root_policy_sha256":manifest.get("root_policy_sha256"),
        "non_runtime_generation_equivalent":True,
    }
    tx={
        "schema_version":1,
        "mode":"V3_PADATASET_SCIENTIFIC_RUNTIME_REPAIR_TRANSACTION",
        "phase":"PREPARED",
        "source_head":args.expected_head,
        "authorization_id":authority["authorization_id"],
        "authority_sha256":sha(authority_raw),
        "current_runtime_sha256":current_sha,
        "candidate_runtime_sha256":candidate_sha,
        "controller_snapshot_before":before,
        "provisioner_before":provisioner_before,
    }
    atomic_json(txpath,tx)

    modified=False
    try:
        # Quiesce every currently active controller so no class can race the
        # shared provisioner restart. Preserve the exact active set.
        for cid in active_before:
            ctl("stop",units[cid]); wait_state(units[cid],"inactive")

        require_no_live_provisioner_records()
        require_no_transients(units)

        ctl("stop",PROVISIONER_UNIT); wait_state(PROVISIONER_UNIT,"inactive")

        atomic_json(RUNTIME_OVERRIDE,receipt)
        atomic_file(INSTALLED_RUNTIME,candidate_runtime,runtime_mode)
        modified=True

        reconciler.verify_installed(BASE_MANIFEST)
        p=subprocess.run(["/usr/bin/python3","/opt/workspace-ci/v3/reconciler/lambda_ci_v3_reconciler.py","--verify-installed","--manifest",str(BASE_MANIFEST)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        if p.returncode:
            raise RepairError("installed reconciler rejected candidate runtime: "+p.stderr.strip()[:1024])

        ctl("start",PROVISIONER_UNIT); wait_state(PROVISIONER_UNIT,"active")
        activation.verify_provisioner_socket()

        for cid in active_before:
            ctl("start",units[cid]); wait_state(units[cid],"active")

        after=snapshot_controllers(units)
        restart_deltas={}
        for cid,state in before.items():
            now=after[cid]
            expected_active=cid in active_before
            if expected_active:
                if now.get("ActiveState")!="active" or now.get("SubState")!="running":
                    raise RepairError(f"controller did not restore active/running: {cid}")
            else:
                if now.get("ActiveState")!="inactive":
                    raise RepairError(f"inactive controller unexpectedly activated: {cid}")
            if now.get("UnitFileState")!=state.get("UnitFileState"):
                raise RepairError(f"controller enablement changed: {cid}")

            before_restarts=int(state.get("NRestarts") or "0")
            after_restarts=int(now.get("NRestarts") or "0")
            delta=after_restarts-before_restarts
            restart_deltas[cid]=delta
            if delta < 0:
                raise RepairError(f"controller restart counter regressed: {cid}")
            if before_restarts == 0 and delta != 0:
                raise RepairError(
                    f"previously-stable controller restarted during repair: {cid}"
                )
            if before_restarts > 0 and delta > 1:
                raise RepairError(
                    f"pre-existing restarting controller exceeded bounded restart delta: {cid}"
                )

        # Once controllers are restored, queued GitHub demand may legitimately
        # revive immediately. Emptiness is a pre-swap quiescence invariant, not
        # a post-restore invariant. The effective generation must still verify.
        reconciler.verify_installed(BASE_MANIFEST)

        tx.update({
            "phase":"COMMITTED_ACTIVE_RUNTIME_REPAIR",
            "runtime_override_sha256":sha(RUNTIME_OVERRIDE.read_bytes()),
            "controller_snapshot_after":after,
            "controller_restart_deltas":restart_deltas,
            "provisioner_after":systemd(PROVISIONER_UNIT),
            "completed_at":datetime.now(timezone.utc).isoformat(),
        })
        atomic_json(txpath,tx)
        print("PADATASET_SCIENTIFIC_RUNTIME_REPAIR=PASS")
        print(f"TRANSACTION_RECEIPT={txpath}")
        print(f"RUNTIME_SHA256={candidate_sha}")
        return 0
    except BaseException as exc:
        try:
            for cid in units:
                if systemd(units[cid]).get("ActiveState")=="active":
                    subprocess.run(["systemctl","stop",units[cid]],check=False)
            if systemd(PROVISIONER_UNIT).get("ActiveState")=="active":
                subprocess.run(["systemctl","stop",PROVISIONER_UNIT],check=False)
            if modified:
                atomic_file(INSTALLED_RUNTIME,current_runtime,runtime_mode)
                if old_receipt_raw is None:
                    try: RUNTIME_OVERRIDE.unlink()
                    except FileNotFoundError: pass
                else:
                    atomic_file(RUNTIME_OVERRIDE,old_receipt_raw,0o600)
            subprocess.run(["systemctl","start",PROVISIONER_UNIT],check=False)
            wait_state(PROVISIONER_UNIT,"active")
            for cid in active_before:
                subprocess.run(["systemctl","start",units[cid]],check=False)
                wait_state(units[cid],"active")

            rollback_after=snapshot_controllers(units)
            for cid,state in before.items():
                now=rollback_after[cid]
                if cid in active_before:
                    if now.get("ActiveState")!="active" or now.get("SubState")!="running":
                        raise RepairError(
                            f"rollback did not restore active controller: {cid}"
                        )
                elif now.get("ActiveState")!="inactive":
                    raise RepairError(
                        f"rollback activated previously-inactive controller: {cid}"
                    )
                if now.get("UnitFileState")!=state.get("UnitFileState"):
                    raise RepairError(
                        f"rollback changed controller enablement: {cid}"
                    )

            # Restored controllers may immediately resume queued work. Verify
            # the restored generation and controller topology, but do not
            # require post-restore scheduler emptiness.
            reconciler.verify_installed(BASE_MANIFEST)
            tx["phase"]="ROLLED_BACK_PREVIOUS_RUNTIME"
            tx["rollback_completed"]=True
            tx["rollback_controller_snapshot_after"]=rollback_after
            tx["rollback_provisioner_after"]=systemd(PROVISIONER_UNIT)
        except BaseException as rollback:
            tx["phase"]="ROLLBACK_INCOMPLETE"; tx["rollback_completed"]=False; tx["rollback_error"]=str(rollback)
        tx["failure"]=str(exc); tx["failed_at"]=datetime.now(timezone.utc).isoformat()
        atomic_json(txpath,tx)
        raise

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except RepairError as exc:
        print(f"ERROR: {exc}",file=__import__("sys").stderr)
        raise SystemExit(1)
