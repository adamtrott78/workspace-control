#!/usr/bin/env python3
"""Transactional live refresh of the shared v3 controller binary.

This is deliberately narrower than a substrate reinstall. It preserves the
installed policy/config/runtime generation, quiesces the currently-active
controller set, replaces only the shared controller executable plus its
root-owned attestation receipt, verifies the effective generation, and restores
exactly the prior controller topology. Root services stay active throughout.
"""

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

BASE_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = Path("/etc/workspace-ci/v3/root-policy.json")
CONTROLLER_BINARY = Path("/opt/workspace-ci/v3/controller/lambda-ci-controller-v3")
CONTROLLER_REFRESH = Path("/var/lib/workspace-ci/v3/controller-refresh/active.json")
PROVISIONER_STATE = Path("/var/lib/workspace-ci/v3/provisioner")
PROVISIONER_UNIT = "workspace-ci-v3-provisioner.service"
RECONCILER_UNIT = "workspace-ci-v3-reconciler.service"
TX_ROOT = Path("/var/lib/workspace-ci/v3/padataset-scientific/controller-repair/transactions")
AUTH_CONSUMED = Path("/var/lib/workspace-ci/v3/padataset-scientific/controller-repair/authority-consumption")
TARGET_CLASS = "padataset-scientific-single-gpu-v1"
ACTIVE_PROVISION_STATES = {"RESERVED","PREPARING","ACCEPTED","RUNNING"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
MODE = "V3_INACTIVE_CONTROLLER_BINARY_OVERRIDE"

class ControllerRepairError(RuntimeError):
    pass

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def canonical(v: Any) -> bytes:
    return (json.dumps(v, indent=2, sort_keys=True) + "\n").encode()

def load(path: Path) -> tuple[dict[str,Any],bytes]:
    raw=path.read_bytes()
    value=json.loads(raw)
    if not isinstance(value,dict):
        raise ControllerRepairError(f"expected object: {path}")
    return value,raw

def exact_repo(expected: str) -> Path:
    if SHA40.fullmatch(expected) is None:
        raise ControllerRepairError("expected head invalid")
    repo=Path(__file__).resolve().parents[1]
    head=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
    if head!=expected:
        raise ControllerRepairError(f"source head mismatch: {head} != {expected}")
    dirty=subprocess.check_output(["git","-C",str(repo),"status","--porcelain=v1","--untracked-files=normal"],text=True)
    if dirty.strip():
        raise ControllerRepairError("source checkout dirty")
    return repo

def systemd(unit: str) -> dict[str,str]:
    p=subprocess.run(
        ["systemctl","show",unit,
         "-p","LoadState","-p","ActiveState","-p","SubState",
         "-p","MainPID","-p","NRestarts","-p","InvocationID",
         "-p","UnitFileState","--no-pager"],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,
    )
    if p.returncode:
        raise ControllerRepairError(
            f"systemctl show failed: {unit}: {p.stderr.strip()[:512]}"
        )
    out={}
    for line in p.stdout.splitlines():
        if "=" in line:
            k,v=line.split("=",1); out[k]=v
    return out

def ctl(*args: str) -> None:
    p=subprocess.run(["systemctl",*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if p.returncode:
        raise ControllerRepairError(
            f"systemctl {' '.join(args)} failed: {p.stderr.strip()[:512]}"
        )

def wait_state(unit: str, expected: str, timeout: float=15.0) -> None:
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if systemd(unit).get("ActiveState")==expected:
            return
        time.sleep(.1)
    raise ControllerRepairError(f"{unit} did not reach {expected}")

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
        os.chown(tmp,0,0)
        os.replace(tmp,path)
        dfd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    finally:
        try: tmp.unlink()
        except FileNotFoundError: pass

def atomic_json(path: Path, value: dict[str,Any]) -> None:
    ensure_dir(path.parent)
    atomic_file(path,canonical(value),0o600)

def controller_units(root: dict[str,Any]) -> dict[str,str]:
    classes=root.get("runner_classes")
    if not isinstance(classes,dict) or TARGET_CLASS not in classes:
        raise ControllerRepairError("installed runner class set invalid")
    return {
        cid:f"workspace-ci-v3-controller@{cid}.service"
        for cid in sorted(classes)
    }

def snapshot_controllers(units: dict[str,str]) -> dict[str,dict[str,str]]:
    return {cid:systemd(unit) for cid,unit in units.items()}

def require_root_services() -> None:
    p=systemd(PROVISIONER_UNIT)
    if p.get("ActiveState")!="active" or p.get("SubState")!="running":
        raise ControllerRepairError("shared provisioner must be active/running")
    r=systemd(RECONCILER_UNIT)
    if r.get("ActiveState")!="active" or r.get("SubState")!="exited":
        raise ControllerRepairError("reconciler must be active/exited")

def require_no_live_provisioner_records() -> None:
    if not PROVISIONER_STATE.exists():
        return
    for p in sorted(PROVISIONER_STATE.glob("*.json")):
        if p.name.startswith("_"):
            continue
        value=json.loads(p.read_text())
        if value.get("state") in ACTIVE_PROVISION_STATES or value.get("resource_hold") is True:
            raise ControllerRepairError(
                f"live provisioner record blocks controller refresh: {p.name}"
            )

def require_no_transients(classes: dict[str,str]) -> None:
    p=subprocess.run(
        ["systemctl","list-units","--all","--type=service","--plain","--no-legend","--no-pager"],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,
    )
    if p.returncode:
        raise ControllerRepairError("cannot enumerate transient units")
    prefixes=tuple(f"workspace-ci-v3-{cid}-" for cid in classes)
    for line in p.stdout.splitlines():
        fields=line.split()
        if not fields or not fields[0].startswith(prefixes):
            continue
        st=systemd(fields[0])
        if st.get("ActiveState") in {"active","activating","reloading"}:
            raise ControllerRepairError(
                f"live transient blocks controller refresh: {fields[0]}"
            )

def build_candidate(repo: Path, go_bin: str) -> bytes:
    go=Path(go_bin)
    if not go.is_file():
        raise ControllerRepairError("go binary missing")
    with tempfile.TemporaryDirectory(prefix="wc-v3-controller-repair-build-") as raw:
        output=Path(raw)/"lambda-ci-controller-v3"
        p=subprocess.run(
            [
                str(go),"-C",str(repo/"controller/lambda-ci-controller"),
                "build","-mod=readonly","-trimpath","-o",str(output),"./v3",
            ],
            text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,
        )
        if p.returncode:
            raise ControllerRepairError(
                "controller build failed: "+p.stderr.strip()[-2048:]
            )
        return output.read_bytes()

def validate_authority(path: Path, expected: dict[str,Any]) -> tuple[dict[str,Any],bytes]:
    st=path.stat()
    if (
        not stat.S_ISREG(st.st_mode)
        or st.st_uid!=0 or st.st_gid!=0
        or stat.S_IMODE(st.st_mode)!=0o600
    ):
        raise ControllerRepairError("authority metadata invalid")
    value,raw=load(path)
    required={
        "schema_version","authority","operation","authorization_id",
        "issued_at","expires_at",*expected
    }
    if set(value)!=required:
        raise ControllerRepairError("authority keys drift")
    if (
        value["schema_version"]!=1
        or value["authority"]!="workspace-control-operator"
        or value["operation"]!="REFRESH_V3_CONTROLLER_BINARY_LIVE_V1"
    ):
        raise ControllerRepairError("authority identity invalid")
    aid=value["authorization_id"]
    if (
        not isinstance(aid,str)
        or UUID_RE.fullmatch(aid) is None
        or str(uuid.UUID(aid))!=aid
    ):
        raise ControllerRepairError("authorization id invalid")
    for k,v in expected.items():
        if value.get(k)!=v:
            raise ControllerRepairError(f"authority binding mismatch: {k}")
    def parse(v: Any) -> datetime:
        if not isinstance(v,str):
            raise ControllerRepairError("authority time invalid")
        d=datetime.fromisoformat(v.replace("Z","+00:00"))
        if d.tzinfo is None:
            raise ControllerRepairError("authority time must be aware")
        return d.astimezone(timezone.utc)
    issued=parse(value["issued_at"]); expires=parse(value["expires_at"])
    now=datetime.now(timezone.utc)
    if not (issued<=now<=expires) or (expires-issued).total_seconds()>1800:
        raise ControllerRepairError("authority validity invalid")
    return value,raw

def consume(value: dict[str,Any], raw: bytes) -> None:
    ensure_dir(AUTH_CONSUMED)
    p=AUTH_CONSUMED/f"{value['authorization_id']}.json"
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"wb") as h:
        h.write(canonical({
            "schema_version":1,
            "authorization_id":value["authorization_id"],
            "operation":value["operation"],
            "authority_sha256":sha(raw),
            "consumed_at":datetime.now(timezone.utc).isoformat(),
        }))
        h.flush(); os.fsync(h.fileno())
    os.chown(p,0,0)

def verify_topology(
    before: dict[str,dict[str,str]],
    after: dict[str,dict[str,str]],
    active_before: list[str],
) -> dict[str,int]:
    deltas={}
    for cid,state in before.items():
        now=after[cid]
        if cid in active_before:
            if now.get("ActiveState")!="active" or now.get("SubState")!="running":
                raise ControllerRepairError(
                    f"controller did not restore active/running: {cid}"
                )
        elif now.get("ActiveState")!="inactive":
            raise ControllerRepairError(
                f"inactive controller unexpectedly activated: {cid}"
            )
        if now.get("UnitFileState")!=state.get("UnitFileState"):
            raise ControllerRepairError(
                f"controller enablement changed: {cid}"
            )
        before_n=int(state.get("NRestarts") or "0")
        after_n=int(now.get("NRestarts") or "0")
        delta=after_n-before_n
        deltas[cid]=delta
        if delta<0:
            raise ControllerRepairError(
                f"controller restart counter regressed: {cid}"
            )
        if before_n==0 and delta!=0:
            raise ControllerRepairError(
                f"previously-stable controller restarted during refresh: {cid}"
            )
        if before_n>0 and delta>1:
            raise ControllerRepairError(
                f"pre-existing restarting controller exceeded bounded restart delta: {cid}"
            )
    return deltas

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--expected-head",required=True)
    ap.add_argument("--authorization-receipt",type=Path,required=True)
    ap.add_argument("--go-bin",required=True)
    args=ap.parse_args()

    if os.geteuid()!=0:
        raise ControllerRepairError("controller repair requires root")
    repo=exact_repo(args.expected_head)

    reconciler.verify_installed(BASE_MANIFEST)
    manifest,manifest_raw=load(BASE_MANIFEST)
    root,_=load(ROOT_POLICY)
    units=controller_units(root)
    before=snapshot_controllers(units)
    active_before=[cid for cid,s in before.items() if s.get("ActiveState")=="active"]
    if TARGET_CLASS not in active_before:
        raise ControllerRepairError("scientific controller must be active before refresh")
    require_root_services()

    current_binary=CONTROLLER_BINARY.read_bytes()
    current_sha=sha(current_binary)
    candidate_binary=build_candidate(repo,args.go_bin)
    candidate_sha=sha(candidate_binary)
    if current_sha==candidate_sha:
        raise ControllerRepairError("candidate controller is already installed")

    previous_refresh,previous_refresh_raw=load(CONTROLLER_REFRESH)
    if previous_refresh.get("mode")!=MODE or previous_refresh.get("phase")!="ACTIVE":
        raise ControllerRepairError("current controller refresh receipt invalid")
    if previous_refresh.get("controller_binary_sha256")!=current_sha:
        raise ControllerRepairError("current controller refresh digest mismatch")

    base_sha=sha(manifest_raw)
    root_policy_sha=manifest.get("root_policy_sha256")
    base_head=manifest.get("source_head")
    if not isinstance(base_head,str) or SHA40.fullmatch(base_head) is None:
        raise ControllerRepairError("base manifest source head invalid")
    if not isinstance(root_policy_sha,str) or SHA64.fullmatch(root_policy_sha) is None:
        raise ControllerRepairError("root policy digest invalid")

    expected={
        "source_head":args.expected_head,
        "base_source_head":base_head,
        "base_install_manifest_sha256":base_sha,
        "root_policy_sha256":root_policy_sha,
        "current_controller_sha256":current_sha,
        "candidate_controller_sha256":candidate_sha,
        "previous_controller_refresh_sha256":sha(previous_refresh_raw),
        "previous_controller_source_head":previous_refresh.get("controller_source_head"),
    }
    authority,authority_raw=validate_authority(args.authorization_receipt,expected)

    # Quiesce before consuming authority; then prove there is no live root work
    # that could observe the shared executable changing.
    for cid in active_before:
        ctl("stop",units[cid]); wait_state(units[cid],"inactive")
    require_root_services()
    require_no_live_provisioner_records()
    require_no_transients(units)

    consume(authority,authority_raw)

    ensure_dir(TX_ROOT)
    txdir=TX_ROOT/f"refresh-{uuid.uuid4()}"; ensure_dir(txdir)
    txpath=txdir/"receipt.json"
    atomic_file(txdir/"previous-controller",current_binary,0o755)
    atomic_file(txdir/"previous-controller-refresh.json",previous_refresh_raw,0o600)

    refresh_receipt={
        "schema_version":1,
        "mode":MODE,
        "phase":"ACTIVE",
        "transaction_id":txdir.name.removeprefix("refresh-"),
        "receipt_path":str(txpath),
        "base_source_head":base_head,
        "controller_source_head":args.expected_head,
        "base_install_manifest_sha256":base_sha,
        "root_policy_sha256":root_policy_sha,
        "previous_controller_sha256":current_sha,
        "controller_binary_sha256":candidate_sha,
        "non_controller_generation_equivalent":True,
        "live_controller_repair":True,
        "authorization_id":authority["authorization_id"],
    }
    tx={
        "schema_version":1,
        "mode":"V3_LIVE_CONTROLLER_BINARY_REPAIR_TRANSACTION",
        "phase":"PREPARED",
        "source_head":args.expected_head,
        "authorization_id":authority["authorization_id"],
        "authority_sha256":sha(authority_raw),
        "current_controller_sha256":current_sha,
        "candidate_controller_sha256":candidate_sha,
        "previous_controller_refresh_sha256":sha(previous_refresh_raw),
        "controller_snapshot_before":before,
        "active_controller_set_before":active_before,
        "provisioner_before":systemd(PROVISIONER_UNIT),
        "reconciler_before":systemd(RECONCILER_UNIT),
    }
    atomic_json(txpath,tx)

    modified=False
    try:
        atomic_file(CONTROLLER_BINARY,candidate_binary,0o755)
        atomic_json(CONTROLLER_REFRESH,refresh_receipt)
        modified=True

        reconciler.verify_installed(BASE_MANIFEST)
        require_root_services()

        for cid in active_before:
            ctl("start",units[cid]); wait_state(units[cid],"active")

        after=snapshot_controllers(units)
        deltas=verify_topology(before,after,active_before)
        require_root_services()

        # Do not require post-restore scheduler emptiness: restoring the
        # scientific controller is expected to revive the already-queued smoke.
        reconciler.verify_installed(BASE_MANIFEST)

        tx.update({
            "phase":"COMMITTED_ACTIVE_CONTROLLER_REPAIR",
            "controller_refresh_sha256":sha(CONTROLLER_REFRESH.read_bytes()),
            "controller_snapshot_after":after,
            "controller_restart_deltas":deltas,
            "provisioner_after":systemd(PROVISIONER_UNIT),
            "reconciler_after":systemd(RECONCILER_UNIT),
            "completed_at":datetime.now(timezone.utc).isoformat(),
        })
        atomic_json(txpath,tx)
        print("V3_LIVE_CONTROLLER_BINARY_REPAIR=PASS")
        print(f"TRANSACTION_RECEIPT={txpath}")
        print(f"CONTROLLER_SHA256={candidate_sha}")
        return 0
    except BaseException as exc:
        try:
            for cid in units:
                if systemd(units[cid]).get("ActiveState")=="active":
                    subprocess.run(["systemctl","stop",units[cid]],check=False)
            if modified:
                atomic_file(CONTROLLER_BINARY,current_binary,0o755)
                atomic_file(CONTROLLER_REFRESH,previous_refresh_raw,0o600)
            reconciler.verify_installed(BASE_MANIFEST)
            for cid in active_before:
                subprocess.run(["systemctl","start",units[cid]],check=False)
                wait_state(units[cid],"active")
            rollback_after=snapshot_controllers(units)
            verify_topology(before,rollback_after,active_before)
            require_root_services()
            reconciler.verify_installed(BASE_MANIFEST)
            tx.update({
                "phase":"ROLLED_BACK_PREVIOUS_CONTROLLER",
                "rollback_completed":True,
                "rollback_controller_snapshot_after":rollback_after,
                "rollback_provisioner_after":systemd(PROVISIONER_UNIT),
                "rollback_reconciler_after":systemd(RECONCILER_UNIT),
            })
        except BaseException as rollback:
            tx.update({
                "phase":"ROLLBACK_INCOMPLETE",
                "rollback_completed":False,
                "rollback_error":str(rollback),
            })
        tx["failure"]=str(exc)
        tx["failed_at"]=datetime.now(timezone.utc).isoformat()
        atomic_json(txpath,tx)
        raise

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except ControllerRepairError as exc:
        print(f"ERROR: {exc}",file=__import__("sys").stderr)
        raise SystemExit(1)
