#!/usr/bin/env python3
"""One-shot operator transaction for post-outage v3 root recovery.

This wrapper intentionally does only two authority-bounded operations:
1. install the repository-validated refresh-aware root-activation helper using
   the transactional live updater; and
2. mint a fresh, exact installed-manifest-bound ACTIVATE_V3_ROOT_SERVICES
   authority receipt and invoke the installed activation helper.

It never reuses prior root authority, never enables services, never activates a
class controller, and never mutates workflows, routes, scale sets, v2 state, or
Research GPU containment.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import uuid


UPDATER_REL = Path("scripts/lambda_ci_v3_root_reactivation_helper_live_update_v1.py")
INSTALLED_ACTIVATOR = Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py")
INSTALL_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
ROOT_POLICY = Path("/etc/workspace-ci/v3/root-policy.json")
MIGRATION_ROOT = Path("/var/lib/workspace-ci/v3/migration")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class RecoveryError(RuntimeError):
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
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_json(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise RecoveryError(f"expected JSON object: {path}")
    return value, raw


def require_root_file(path: Path, mode: int) -> None:
    if not path.is_file() or path.is_symlink():
        raise RecoveryError(f"required root file missing or symlinked: {path}")
    st = path.stat()
    if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != mode:
        raise RecoveryError(
            f"root file metadata mismatch: {path}: "
            f"uid={st.st_uid} gid={st.st_gid} mode={stat.S_IMODE(st.st_mode):04o}"
        )


def require_private_root_dir(path: Path) -> None:
    if not path.is_dir() or path.is_symlink():
        raise RecoveryError(f"required private root directory missing: {path}")
    st = path.stat()
    if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o700:
        raise RecoveryError(
            f"private root directory metadata mismatch: {path}: "
            f"uid={st.st_uid} gid={st.st_gid} mode={stat.S_IMODE(st.st_mode):04o}"
        )


def exact_repo(expected_head: str) -> Path:
    cwd = Path.cwd().resolve()
    proc = run(["git", "-c", f"safe.directory={cwd}", "rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        raise RecoveryError("could not resolve repository root")
    repo = Path(proc.stdout.strip()).resolve()
    git = ["git", "-c", f"safe.directory={repo}", "-C", str(repo)]

    head = run(git + ["rev-parse", "HEAD"])
    if head.returncode != 0 or head.stdout.strip() != expected_head:
        observed = head.stdout.strip() if head.stdout else "<unavailable>"
        raise RecoveryError(f"checkout HEAD mismatch: {observed} != {expected_head}")

    status = run(git + ["status", "--porcelain=v1", "--untracked-files=normal"])
    if status.returncode != 0:
        raise RecoveryError("git status failed")
    if status.stdout.strip():
        raise RecoveryError("checkout is dirty")
    return repo


def write_authority(path: Path, payload: dict) -> None:
    raw = canonical(payload)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(path, 0, 0)
        os.chmod(path, 0o600)
        dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        raise RecoveryError("post-outage root recovery must run as root")
    if SHA_RE.fullmatch(args.expected_head) is None:
        raise RecoveryError("--expected-head must be a full lowercase Git SHA")

    repo = exact_repo(args.expected_head)
    updater = repo / UPDATER_REL
    if not updater.is_file():
        raise RecoveryError(f"root-reactivation updater missing: {updater}")

    print("POST_OUTAGE_V3_ROOT_RECOVERY=BEGIN")
    print(f"EXPECTED_HEAD={args.expected_head}")

    update = run(
        [sys.executable, str(updater), "--expected-head", args.expected_head],
        cwd=repo,
    )
    if update.returncode != 0:
        raise RecoveryError(
            f"transactional root-reactivation helper update failed rc={update.returncode}"
        )
    print("POST_OUTAGE_HELPER_UPDATE=PASS")

    require_root_file(INSTALL_MANIFEST, 0o644)
    require_root_file(ROOT_POLICY, 0o644)
    require_root_file(INSTALLED_ACTIVATOR, 0o555)
    require_private_root_dir(MIGRATION_ROOT)

    manifest, manifest_raw = load_json(INSTALL_MANIFEST)
    root_policy, _ = load_json(ROOT_POLICY)
    source_head = manifest.get("source_head")
    if not isinstance(source_head, str) or SHA_RE.fullmatch(source_head) is None:
        raise RecoveryError("installed manifest source_head invalid")

    root_policy_sha = root_policy.get("root_policy_sha256")
    if not isinstance(root_policy_sha, str) or len(root_policy_sha) != 64:
        raise RecoveryError("installed root policy digest invalid")
    if manifest.get("root_policy_sha256") != root_policy_sha:
        raise RecoveryError("installed manifest/root policy digest mismatch")

    now = datetime.now(timezone.utc)
    authorization_id = str(uuid.uuid4())
    authority = {
        "schema_version": 1,
        "authority": "workspace-control-operator",
        "operation": "ACTIVATE_V3_ROOT_SERVICES",
        "authorization_id": authorization_id,
        "source_head": source_head,
        "install_manifest_sha256": sha256(manifest_raw),
        "root_policy_sha256": root_policy_sha,
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
    }
    authority_path = MIGRATION_ROOT / f"root-reactivation-authority-{authorization_id}.json"
    write_authority(authority_path, authority)
    print("FRESH_ROOT_ACTIVATION_AUTHORITY=PASS")
    print(f"AUTHORIZATION_ID={authorization_id}")
    print(f"AUTHORIZATION_RECEIPT={authority_path}")

    activation = run(
        [
            str(INSTALLED_ACTIVATOR),
            "--activate",
            "--authorization-receipt",
            str(authority_path),
        ]
    )
    if activation.returncode != 0:
        raise RecoveryError(
            "v3 root activation failed; authority/transaction evidence is preserved "
            f"for diagnosis (rc={activation.returncode})"
        )

    print("POST_OUTAGE_V3_ROOT_RECOVERY=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RecoveryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
