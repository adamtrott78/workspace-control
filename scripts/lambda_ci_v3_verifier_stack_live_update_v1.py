#!/usr/bin/env python3
"""Transactional live refresh of the v3 installed-generation verifier stack.

Repairs the post-controller-refresh boot gap without rewriting the immutable
base install manifest. The only mutable installed artifacts are:
- lambda_ci_v3_reconciler.py
- lambda_ci_v3_root_activation.py

Both replacements are attested by exact root-owned ACTIVE override receipts.
The shared controller override remains untouched. All v3 root/class services
must be inactive before mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any

import lambda_ci_v3_root_activation as activation


BASE_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = Path("/etc/workspace-ci/v3/root-policy.json")
INSTALLED_RECONCILER = Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_reconciler.py")
INSTALLED_ACTIVATOR = Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py")
STATE_ROOT = Path("/var/lib/workspace-ci/v3")
RECONCILER_OVERRIDE = STATE_ROOT / "reconciler-refresh" / "active.json"
HELPER_OVERRIDE = STATE_ROOT / "root-reactivation-helper" / "active.json"
UPDATE_ROOT = STATE_ROOT / "migration"
ROOT_UNITS = (
    "workspace-ci-v3-reconciler.service",
    "workspace-ci-v3-provisioner.service",
)


class UpdateError(RuntimeError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise UpdateError(f"expected JSON object: {path}")
    return value, raw


def entry_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries=manifest.get("entries")
    if not isinstance(entries,list):
        raise UpdateError("install manifest entries missing")
    out={}
    for entry in entries:
        if not isinstance(entry,dict):
            raise UpdateError("install manifest entry invalid")
        destination=entry.get("destination")
        if not isinstance(destination,str) or destination in out:
            raise UpdateError("install manifest destination invalid/duplicate")
        out[destination]=entry
    return out


def active(unit: str) -> bool:
    return subprocess.run(
        ["systemctl","is-active","--quiet",unit],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def class_units() -> list[str]:
    policy,_=load(ROOT_POLICY)
    classes=policy.get("runner_classes")
    if not isinstance(classes,dict) or len(classes)!=9:
        raise UpdateError("installed root policy class set invalid")
    return [f"workspace-ci-v3-controller@{x}.service" for x in sorted(classes)]


def require_inactive() -> None:
    active_units=[u for u in [*ROOT_UNITS,*class_units()] if active(u)]
    if active_units:
        raise UpdateError("v3 units must be inactive before verifier refresh: "+",".join(active_units))


def exact_repo(expected_head: str) -> Path:
    repo=Path(__file__).resolve().parents[1]
    git=["git","-C",str(repo)]
    head=subprocess.check_output(git+["rev-parse","HEAD"],text=True).strip()
    if head!=expected_head:
        raise UpdateError(f"checkout HEAD mismatch: {head} != {expected_head}")
    dirty=subprocess.check_output(git+["status","--porcelain=v1","--untracked-files=normal"],text=True)
    if dirty.strip():
        raise UpdateError("checkout is dirty")
    return repo


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True,exist_ok=True)
    os.chown(path,0,0)
    os.chmod(path,0o700)


def atomic_file(path: Path, raw: bytes, mode: int) -> None:
    fd,name=tempfile.mkstemp(prefix=f".{path.name}.",dir=str(path.parent))
    tmp=Path(name)
    try:
        with os.fdopen(fd,"wb") as handle:
            os.fchmod(handle.fileno(),mode)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(tmp,0,0)
        os.replace(tmp,path)
        dfd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        try: tmp.unlink()
        except FileNotFoundError: pass


def atomic_json(path: Path, value: dict[str,Any]) -> None:
    ensure_dir(path.parent)
    atomic_file(path,canonical(value),0o600)


def git_blob(repo: Path, rel: str) -> str:
    return subprocess.check_output(["git","-C",str(repo),"hash-object",rel],text=True).strip()


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--expected-head",required=True)
    args=parser.parse_args()
    if os.geteuid()!=0:
        raise UpdateError("verifier-stack live update requires root")
    if len(args.expected_head)!=40:
        raise UpdateError("--expected-head must be full Git SHA")

    repo=exact_repo(args.expected_head)
    require_inactive()

    # Prove the currently installed effective generation before touching it.
    activation.verify_effective_installed_generation(BASE_MANIFEST)

    manifest,manifest_raw=load(BASE_MANIFEST)
    entries=entry_map(manifest)
    rec_entry=entries.get(str(INSTALLED_RECONCILER))
    helper_entry=entries.get(str(INSTALLED_ACTIVATOR))
    if rec_entry is None or helper_entry is None:
        raise UpdateError("base manifest does not manage verifier stack")

    if sha256(INSTALLED_RECONCILER.read_bytes()) != rec_entry.get("sha256"):
        raise UpdateError("installed reconciler prestate is not base-manifest exact")

    rec_mode=int(str(rec_entry.get("mode")),8)
    helper_mode=int(str(helper_entry.get("mode")),8)
    if rec_mode!=0o755 or helper_mode!=0o555:
        raise UpdateError("verifier-stack base modes are unexpected")

    candidate_rec=(repo/"scripts/lambda_ci_v3_reconciler.py").read_bytes()
    candidate_helper=(repo/"scripts/lambda_ci_v3_root_activation.py").read_bytes()
    candidate_rec_sha=sha256(candidate_rec)
    candidate_helper_sha=sha256(candidate_helper)
    base_manifest_sha=sha256(manifest_raw)

    previous_helper_raw=HELPER_OVERRIDE.read_bytes() if HELPER_OVERRIDE.is_file() else None
    previous_rec_raw=RECONCILER_OVERRIDE.read_bytes() if RECONCILER_OVERRIDE.is_file() else None
    old_rec=INSTALLED_RECONCILER.read_bytes()
    old_helper=INSTALLED_ACTIVATOR.read_bytes()

    rec_receipt={
        "schema_version":1,
        "mode":"V3_RECONCILER_OVERRIDE",
        "phase":"ACTIVE",
        "base_source_head":manifest.get("source_head"),
        "base_install_manifest_sha256":base_manifest_sha,
        "base_reconciler_sha256":rec_entry.get("sha256"),
        "reconciler_sha256":candidate_rec_sha,
        "reconciler_mode":str(rec_entry.get("mode")),
        "reconciler_source_head":args.expected_head,
        "reconciler_git_blob":git_blob(repo,"scripts/lambda_ci_v3_reconciler.py"),
        "root_policy_sha256":manifest.get("root_policy_sha256"),
        "non_reconciler_generation_equivalent":True,
    }
    helper_receipt={
        "schema_version":1,
        "mode":"V3_ROOT_REACTIVATION_HELPER_OVERRIDE",
        "phase":"ACTIVE",
        "base_source_head":manifest.get("source_head"),
        "base_install_manifest_sha256":base_manifest_sha,
        "base_helper_sha256":helper_entry.get("sha256"),
        "helper_sha256":candidate_helper_sha,
        "helper_mode":str(helper_entry.get("mode")),
        "helper_source_head":args.expected_head,
        "candidate_git_blob":git_blob(repo,"scripts/lambda_ci_v3_root_activation.py"),
        "root_policy_sha256":manifest.get("root_policy_sha256"),
        "non_helper_generation_equivalent":True,
    }

    changed=False
    try:
        atomic_json(RECONCILER_OVERRIDE,rec_receipt)
        atomic_json(HELPER_OVERRIDE,helper_receipt)
        # From this point onward, rollback both installed files on any exception,
        # including an fsync failure after an atomic replacement.
        changed=True
        atomic_file(INSTALLED_RECONCILER,candidate_rec,rec_mode)
        atomic_file(INSTALLED_ACTIVATOR,candidate_helper,helper_mode)

        # Repository verifier and installed verifier must agree after replacement.
        activation.verify_effective_installed_generation(BASE_MANIFEST)
        proc=subprocess.run(
            [
                sys.executable,
                str(INSTALLED_RECONCILER),
                "--verify-installed",
                "--manifest",
                str(BASE_MANIFEST),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode!=0:
            raise UpdateError(
                "installed reconciler self-verification failed rc="
                +str(proc.returncode)+": "+proc.stderr.strip()[:1024]
            )

        update_dir=UPDATE_ROOT/f"verifier-stack-update-{args.expected_head}"
        ensure_dir(update_dir)
        receipt={
            "schema_version":1,
            "mode":"V3_VERIFIER_STACK_LIVE_UPDATE",
            "phase":"ACTIVE",
            "source_head":args.expected_head,
            "base_install_manifest_sha256":base_manifest_sha,
            "reconciler_override":rec_receipt,
            "root_activation_helper_override":helper_receipt,
            "controller_override_mutated":False,
            "class_controller_mutated":False,
            "workflow_mutated":False,
            "legacy_v2_mutated":False,
        }
        atomic_json(update_dir/"receipt.json",receipt)
    except Exception:
        if changed:
            atomic_file(INSTALLED_RECONCILER,old_rec,rec_mode)
            atomic_file(INSTALLED_ACTIVATOR,old_helper,helper_mode)
        if previous_rec_raw is None:
            try: RECONCILER_OVERRIDE.unlink()
            except FileNotFoundError: pass
        else:
            atomic_file(RECONCILER_OVERRIDE,previous_rec_raw,0o600)
        if previous_helper_raw is None:
            try: HELPER_OVERRIDE.unlink()
            except FileNotFoundError: pass
        else:
            atomic_file(HELPER_OVERRIDE,previous_helper_raw,0o600)
        raise

    print("V3_VERIFIER_STACK_LIVE_UPDATE=PASS")
    print(f"VALIDATED_HEAD={args.expected_head}")
    print(f"RECONCILER_SHA256={candidate_rec_sha}")
    print(f"ROOT_ACTIVATION_HELPER_SHA256={candidate_helper_sha}")
    print(f"RECONCILER_OVERRIDE_RECEIPT={RECONCILER_OVERRIDE}")
    print(f"HELPER_OVERRIDE_RECEIPT={HELPER_OVERRIDE}")
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except UpdateError as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        raise SystemExit(1)
