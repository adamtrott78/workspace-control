#!/usr/bin/env python3
"""Transactional live update for refresh-aware v3 root reactivation.

Mutates exactly the reviewed root-activation helper plus its narrow active
override attestation:

  /opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py
  /var/lib/workspace-ci/v3/root-reactivation-helper/active.json

It does not start/stop/enable any service, mutate any controller binary, alter
the install manifest, change controller-refresh state, consume activation
authority, or touch workflows/routes/scale sets/credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile


BASE_SOURCE_HEAD = "09c46818252991f6a55aaeedbcf046c554e2ffee"
SOURCE_REL = "scripts/lambda_ci_v3_root_activation.py"
EXPECTED_CANDIDATE_GIT_BLOB = "3f617c8d85b3dabf1a6b9b2b82edc0feb1f1b930"
INSTALLED = Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py")
INSTALL_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
BACKUP_ROOT = Path("/var/lib/workspace-ci/v3/migration")
HELPER_OVERRIDE_ROOT = Path("/var/lib/workspace-ci/v3/root-reactivation-helper")
ACTIVE_RECEIPT = HELPER_OVERRIDE_ROOT / "active.json"


class UpdateError(RuntimeError):
    pass


def run(argv: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise UpdateError(
            f"command failed rc={proc.returncode}: {' '.join(argv)}: {proc.stderr.strip()}"
        )
    return proc


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def require_root_mode(path: Path, expected_mode: int) -> None:
    if not path.is_file() or path.is_symlink():
        raise UpdateError(f"installed artifact missing or symlinked: {path}")
    st = path.stat()
    if (
        st.st_uid != 0
        or st.st_gid != 0
        or stat.S_IMODE(st.st_mode) != expected_mode
    ):
        raise UpdateError(
            f"installed artifact metadata mismatch: {path}: "
            f"uid={st.st_uid} gid={st.st_gid} "
            f"mode={stat.S_IMODE(st.st_mode):04o} "
            f"expected_uid=0 expected_gid=0 expected_mode={expected_mode:04o}"
        )


def load_manifest_contract(manifest_raw: bytes, base_raw: bytes) -> tuple[dict, dict, int]:
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateError("installed v3 manifest is invalid JSON") from exc
    if not isinstance(manifest, dict):
        raise UpdateError("installed v3 manifest is not an object")
    if manifest.get("mode") != "V3_SUBSTRATE_INSTALL_INACTIVE":
        raise UpdateError("installed v3 manifest mode mismatch")
    if manifest.get("source_head") != BASE_SOURCE_HEAD:
        raise UpdateError("installed v3 manifest source head mismatch")

    entries = [
        entry
        for entry in manifest.get("entries", [])
        if isinstance(entry, dict) and entry.get("destination") == str(INSTALLED)
    ]
    if len(entries) != 1:
        raise UpdateError("installed helper manifest entry missing or duplicated")
    entry = entries[0]

    try:
        expected_mode = int(str(entry.get("mode")), 8)
    except ValueError as exc:
        raise UpdateError("installed helper manifest mode invalid") from exc
    if expected_mode != 0o555:
        raise UpdateError(
            f"reviewed inactive-substrate helper mode drift: {expected_mode:04o} != 0555"
        )

    base_sha = sha256_bytes(base_raw)
    if entry.get("sha256") != base_sha:
        raise UpdateError("installed helper manifest digest does not match reviewed base helper")
    return manifest, entry, expected_mode


def write_root_file_atomic(path: Path, raw: bytes, *, mode: int) -> None:
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    try:
        tmp.write_bytes(raw)
        os.chown(tmp, 0, 0)
        os.chmod(tmp, mode)
        with tmp.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def prepare_override_root() -> bool:
    if HELPER_OVERRIDE_ROOT.exists():
        st = HELPER_OVERRIDE_ROOT.stat()
        if (
            not stat.S_ISDIR(st.st_mode)
            or st.st_uid != 0
            or st.st_gid != 0
            or stat.S_IMODE(st.st_mode) != 0o700
        ):
            raise UpdateError("root-reactivation helper override root metadata mismatch")
        if ACTIVE_RECEIPT.exists():
            raise UpdateError("root-reactivation helper active override already exists")
        if any(HELPER_OVERRIDE_ROOT.iterdir()):
            raise UpdateError("root-reactivation helper override root is not empty")
        return False

    HELPER_OVERRIDE_ROOT.mkdir(mode=0o700)
    os.chown(HELPER_OVERRIDE_ROOT, 0, 0)
    os.chmod(HELPER_OVERRIDE_ROOT, 0o700)
    return True


def load_candidate_module(path: Path):
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(
            "lambda_ci_v3_root_activation_live_verify",
            path,
        )
        if spec is None or spec.loader is None:
            raise UpdateError("could not create activation-helper import spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            sys.path.remove(str(path.parent))
        except ValueError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise UpdateError("must run as root")
    if len(args.expected_head) != 40 or any(c not in "0123456789abcdef" for c in args.expected_head):
        raise UpdateError("--expected-head must be a full lowercase Git SHA")

    repo_hint = Path.cwd().resolve()
    repo = Path(
        run(
            ["git", "-c", f"safe.directory={repo_hint}", "rev-parse", "--show-toplevel"]
        ).stdout.strip()
    ).resolve()
    git = ["git", "-c", f"safe.directory={repo}", "-C", str(repo)]

    observed = run(git + ["rev-parse", "HEAD"]).stdout.strip()
    if observed != args.expected_head:
        raise UpdateError(f"checkout HEAD mismatch: {observed} != {args.expected_head}")
    if run(git + ["status", "--porcelain=v1", "--untracked-files=normal"]).stdout.strip():
        raise UpdateError("checkout is dirty")

    candidate = repo / SOURCE_REL
    candidate_blob = run(["git", "hash-object", str(candidate)]).stdout.strip()
    if candidate_blob != EXPECTED_CANDIDATE_GIT_BLOB:
        raise UpdateError("candidate root-activation helper blob mismatch")

    base_raw = subprocess.check_output(
        git + ["show", f"{BASE_SOURCE_HEAD}:{SOURCE_REL}"]
    )
    candidate_raw = candidate.read_bytes()

    require_root_mode(INSTALL_MANIFEST, 0o644)
    manifest_raw = INSTALL_MANIFEST.read_bytes()
    manifest, helper_entry, expected_mode = load_manifest_contract(manifest_raw, base_raw)

    require_root_mode(INSTALLED, expected_mode)
    installed_sha = sha256_bytes(INSTALLED.read_bytes())
    if installed_sha != helper_entry.get("sha256"):
        raise UpdateError(
            "installed root-activation helper does not match reviewed inactive-substrate prestate"
        )

    print("V3_ROOT_REACTIVATION_HELPER_PRESTATE=PASS")
    print("INSTALLED_UID=0")
    print("INSTALLED_GID=0")
    print(f"INSTALLED_MODE={expected_mode:04o}")
    print(f"INSTALLED_SHA256={installed_sha}")

    update_dir = BACKUP_ROOT / f"root-reactivation-helper-update-{args.expected_head}"
    if update_dir.exists():
        raise UpdateError(f"update directory already exists: {update_dir}")
    update_dir.mkdir(mode=0o700)
    os.chown(update_dir, 0, 0)
    os.chmod(update_dir, 0o700)

    backup = update_dir / "previous-root-activation.py"
    shutil.copy2(INSTALLED, backup)
    os.chown(backup, 0, 0)
    os.chmod(backup, expected_mode)

    tmp = INSTALLED.with_name(INSTALLED.name + f".candidate.{os.getpid()}")
    replaced = False
    committed = False
    override_root_created = False
    override_written = False
    try:
        tmp.write_bytes(candidate_raw)
        os.chown(tmp, 0, 0)
        os.chmod(tmp, expected_mode)
        os.replace(tmp, INSTALLED)
        replaced = True

        require_root_mode(INSTALLED, expected_mode)
        candidate_sha = sha256_bytes(INSTALLED.read_bytes())
        if candidate_sha != sha256_bytes(candidate_raw):
            raise UpdateError("installed helper digest mismatch after replacement")

        override_root_created = prepare_override_root()
        active_override = {
            "schema_version": 1,
            "mode": "V3_ROOT_REACTIVATION_HELPER_OVERRIDE",
            "phase": "ACTIVE",
            "base_source_head": BASE_SOURCE_HEAD,
            "helper_source_head": args.expected_head,
            "base_install_manifest_sha256": sha256_bytes(manifest_raw),
            "base_helper_sha256": helper_entry.get("sha256"),
            "helper_sha256": candidate_sha,
            "helper_git_blob": EXPECTED_CANDIDATE_GIT_BLOB,
            "helper_mode": str(helper_entry.get("mode")),
            "root_policy_sha256": manifest.get("root_policy_sha256"),
            "non_helper_generation_equivalent": True,
        }
        write_root_file_atomic(ACTIVE_RECEIPT, canonical(active_override), mode=0o600)
        override_written = True

        module = load_candidate_module(INSTALLED)
        effective = module.verify_effective_installed_generation(INSTALL_MANIFEST)
        if not isinstance(effective, dict):
            raise UpdateError("effective generation did not report reviewed live overrides")
        helper_override = effective.get("root_activation_helper_override")
        if not isinstance(helper_override, dict):
            raise UpdateError("active root-reactivation helper override was not attested")
        if helper_override.get("helper_source_head") != args.expected_head:
            raise UpdateError("active root-reactivation helper override source head mismatch")

        controller_source_head = effective.get("controller_source_head")
        receipt = update_dir / "receipt.json"
        receipt_payload = {
            "schema_version": 1,
            "mode": "V3_ROOT_REACTIVATION_HELPER_UPDATE",
            "phase": "ACTIVE",
            "validated_head": args.expected_head,
            "base_source_head": BASE_SOURCE_HEAD,
            "base_install_manifest_sha256": sha256_bytes(manifest_raw),
            "previous_helper_sha256": installed_sha,
            "installed_helper_sha256": candidate_sha,
            "installed_helper_mode": f"{expected_mode:04o}",
            "active_override_receipt": str(ACTIVE_RECEIPT),
            "controller_override_source_head": controller_source_head,
        }
        write_root_file_atomic(receipt, canonical(receipt_payload), mode=0o600)
        committed = True

        print("V3_ROOT_REACTIVATION_HELPER_UPDATE=PASS")
        print(f"VALIDATED_HEAD={args.expected_head}")
        print(f"INSTALLED_SHA256={candidate_sha}")
        print(f"INSTALLED_MODE={expected_mode:04o}")
        if controller_source_head is not None:
            print(f"CONTROLLER_OVERRIDE_SOURCE_HEAD={controller_source_head}")
        print(f"ACTIVE_OVERRIDE_RECEIPT={ACTIVE_RECEIPT}")
        print(f"UPDATE_RECEIPT={receipt}")
        return 0
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        if replaced and not committed:
            shutil.copy2(backup, INSTALLED)
            os.chown(INSTALLED, 0, 0)
            os.chmod(INSTALLED, expected_mode)
        if override_written and not committed:
            try:
                ACTIVE_RECEIPT.unlink()
            except FileNotFoundError:
                pass
        if override_root_created and not committed:
            try:
                HELPER_OVERRIDE_ROOT.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
