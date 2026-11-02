#!/usr/bin/env python3
"""Transactional live update for refresh-aware v3 root reactivation.

Mutates exactly:
  /opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py

It does not start/stop/enable any service, mutate any controller binary, alter
the install manifest, change controller-refresh state, consume authority, or
touch workflows/routes/scale sets/credentials. It only installs the reviewed
root-activation helper and proves the current effective v3 generation is valid.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile


BASE_SOURCE_HEAD = "09c46818252991f6a55aaeedbcf046c554e2ffee"
SOURCE_REL = "scripts/lambda_ci_v3_root_activation.py"
EXPECTED_CANDIDATE_GIT_BLOB = "eed5c2ddac6c901b31d5b98b33d7ae0c297a0dbb"
INSTALLED = Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py")
INSTALL_MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
BACKUP_ROOT = Path("/var/lib/workspace-ci/v3/migration")


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


def require_root_0755(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise UpdateError(f"installed helper missing or symlinked: {path}")
    st = path.stat()
    if st.st_uid != 0 or st.st_gid != 0 or stat.S_IMODE(st.st_mode) != 0o755:
        raise UpdateError(f"installed helper metadata mismatch: {path}")


def load_candidate_module(path: Path):
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location("lambda_ci_v3_root_activation_live_verify", path)
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

    require_root_0755(INSTALLED)
    if sha256_bytes(INSTALLED.read_bytes()) != sha256_bytes(base_raw):
        raise UpdateError(
            "installed root-activation helper does not match reviewed inactive-substrate prestate"
        )

    if not INSTALL_MANIFEST.is_file():
        raise UpdateError("v3 install manifest missing")

    update_dir = BACKUP_ROOT / f"root-reactivation-helper-update-{args.expected_head}"
    if update_dir.exists():
        raise UpdateError(f"update directory already exists: {update_dir}")
    update_dir.mkdir(mode=0o700)
    backup = update_dir / "previous-root-activation.py"
    shutil.copy2(INSTALLED, backup)
    os.chown(backup, 0, 0)
    os.chmod(backup, 0o755)

    tmp = INSTALLED.with_name(INSTALLED.name + f".candidate.{os.getpid()}")
    replaced = False
    committed = False
    try:
        tmp.write_bytes(candidate_raw)
        os.chown(tmp, 0, 0)
        os.chmod(tmp, 0o755)
        os.replace(tmp, INSTALLED)
        replaced = True

        require_root_0755(INSTALLED)
        if sha256_bytes(INSTALLED.read_bytes()) != sha256_bytes(candidate_raw):
            raise UpdateError("installed helper digest mismatch after replacement")

        module = load_candidate_module(INSTALLED)
        override = module.verify_effective_installed_generation(INSTALL_MANIFEST)
        if not isinstance(override, dict):
            raise UpdateError(
                "expected active controller override was not observed after helper update"
            )
        if override.get("phase") != "ACTIVE":
            raise UpdateError("effective controller override is not ACTIVE")

        receipt = update_dir / "receipt.txt"
        receipt.write_text(
            "\n".join(
                [
                    "V3_ROOT_REACTIVATION_HELPER_UPDATE=PASS",
                    f"VALIDATED_HEAD={args.expected_head}",
                    f"INSTALLED_SHA256={sha256_bytes(INSTALLED.read_bytes())}",
                    f"CONTROLLER_OVERRIDE_SOURCE_HEAD={override.get('controller_source_head')}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        os.chown(receipt, 0, 0)
        os.chmod(receipt, 0o600)
        committed = True

        print("V3_ROOT_REACTIVATION_HELPER_UPDATE=PASS")
        print(f"VALIDATED_HEAD={args.expected_head}")
        print(f"INSTALLED_SHA256={sha256_bytes(INSTALLED.read_bytes())}")
        print(f"CONTROLLER_OVERRIDE_SOURCE_HEAD={override.get('controller_source_head')}")
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
            os.chmod(INSTALLED, 0o755)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
