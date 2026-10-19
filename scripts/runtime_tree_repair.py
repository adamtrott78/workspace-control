#!/usr/bin/env python3
"""Reversible repair for a cryptographically proven expanded-runtime drift set."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import stat
import sys
from typing import Any

import runtime_tree_projection as projection


def file_sha256(path: pathlib.Path) -> str:
    return projection.sha256_file(path)


def load_candidate(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "candidate_extras",
        "reference_only",
        "type_mismatches",
        "non_pycache_extras",
    }
    if set(data) != required:
        raise RuntimeError("candidate evidence keys drift")
    for key in required:
        if not isinstance(data[key], list):
            raise RuntimeError(f"candidate evidence {key} is not a list")
    if data["reference_only"]:
        raise RuntimeError("candidate evidence has reference-only paths")
    if data["type_mismatches"]:
        raise RuntimeError("candidate evidence has type mismatches")
    if data["non_pycache_extras"]:
        raise RuntimeError("candidate evidence has non-pycache extras")
    return data


def safe_rel(value: str) -> pathlib.PurePosixPath:
    rel = pathlib.PurePosixPath(value)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts:
        raise RuntimeError(f"unsafe candidate path: {value!r}")
    return rel


def candidate_roots(values: list[str]) -> list[str]:
    candidate = {safe_rel(value).as_posix() for value in values}
    if len(candidate) != len(values):
        raise RuntimeError("candidate path list contains duplicates")

    roots: list[str] = []
    for rel in sorted(candidate):
        pure = pathlib.PurePosixPath(rel)
        if "__pycache__" not in pure.parts:
            raise RuntimeError(f"candidate path is not under __pycache__: {rel}")
        parents = [
            pathlib.PurePosixPath(*pure.parts[:index]).as_posix()
            for index in range(1, len(pure.parts))
        ]
        if not any(parent in candidate for parent in parents):
            roots.append(rel)
    return roots


def actual_digest(
    records: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, int]]:
    return projection.projected_digest(records, set())


def validate_projection(
    *,
    live_root: pathlib.Path,
    candidate_path: pathlib.Path,
    expected_files: int,
    expected_directories: int,
    expected_symlinks: int,
    expected_bytes: int,
    expected_digest: str,
    expected_extra_files: int,
    expected_extra_directories: int,
    expected_extra_symlinks: int,
    required_uid: int,
    required_gid: int,
) -> dict[str, Any]:
    candidate = load_candidate(candidate_path)
    extras = candidate["candidate_extras"]
    roots = candidate_roots(extras)

    live, live_counts = projection.scan_tree(
        live_root,
        hash_regular_files=True,
    )
    extra_set = set(extras)

    missing = sorted(extra_set - set(live))
    if missing:
        raise RuntimeError(
            f"candidate paths missing from live tree: {len(missing)}"
        )

    extra_counts = {
        "file_count": sum(
            live[rel]["kind"] == "file" for rel in extra_set
        ),
        "directory_count": sum(
            live[rel]["kind"] == "directory" for rel in extra_set
        ),
        "symlink_count": sum(
            live[rel]["kind"] == "symlink" for rel in extra_set
        ),
    }

    if extra_counts != {
        "file_count": expected_extra_files,
        "directory_count": expected_extra_directories,
        "symlink_count": expected_extra_symlinks,
    }:
        raise RuntimeError(
            f"candidate extra counts drift: {extra_counts!r}"
        )

    projected_digest, projected = projection.projected_digest(
        live,
        extra_set,
    )

    expected_projected = {
        "file_count": expected_files,
        "directory_count": expected_directories,
        "symlink_count": expected_symlinks,
        "materialized_bytes": expected_bytes,
    }
    for key, expected in expected_projected.items():
        if projected[key] != expected:
            raise RuntimeError(
                f"projected {key} mismatch: {projected[key]} != {expected}"
            )

    if projected_digest != expected_digest:
        raise RuntimeError(
            f"projected digest mismatch: {projected_digest}"
        )

    retained = [
        item for rel, item in live.items()
        if rel not in extra_set
    ]
    wrong_owner = [
        item["path"] for item in retained
        if item["uid"] != required_uid or item["gid"] != required_gid
    ]
    if wrong_owner:
        raise RuntimeError(
            f"retained ownership drift: {len(wrong_owner)} path(s)"
        )

    if (
        live_counts["root_uid"] != required_uid
        or live_counts["root_gid"] != required_gid
    ):
        raise RuntimeError("runtime root ownership drift")

    if int(live_counts["root_mode"]) & 0o222:
        raise RuntimeError("runtime root is writable")

    if projected["writable_retained_before_projection"] != 0:
        raise RuntimeError(
            "retained write bits exist; path-only repair is not authorized"
        )

    pre_digest, pre_counts = actual_digest(live)

    return {
        "candidate_evidence_sha256": file_sha256(candidate_path),
        "candidate_extra_count": len(extra_set),
        "candidate_extra_counts": extra_counts,
        "candidate_roots": roots,
        "pre_actual_digest": pre_digest,
        "pre_actual_counts": pre_counts,
        "projected_digest": projected_digest,
        "projected_counts": projected,
    }


def rollback_moves(
    *,
    live_root: pathlib.Path,
    quarantine_root: pathlib.Path,
    roots: list[str],
) -> None:
    for rel in reversed(roots):
        src = quarantine_root / "payload" / rel
        dst = live_root / rel
        if not src.exists() and not src.is_symlink():
            raise RuntimeError(
                f"rollback source missing from quarantine: {rel}"
            )
        if dst.exists() or dst.is_symlink():
            raise RuntimeError(
                f"rollback destination already exists: {rel}"
            )
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.rename(src, dst)


def apply_repair(
    *,
    live_root: pathlib.Path,
    candidate_path: pathlib.Path,
    quarantine_root: pathlib.Path,
    expected_files: int,
    expected_directories: int,
    expected_symlinks: int,
    expected_bytes: int,
    expected_digest: str,
    expected_extra_files: int,
    expected_extra_directories: int,
    expected_extra_symlinks: int,
    required_uid: int = 0,
    required_gid: int = 0,
) -> dict[str, Any]:
    if quarantine_root.exists() or quarantine_root.is_symlink():
        raise RuntimeError("quarantine root already exists")

    proof = validate_projection(
        live_root=live_root,
        candidate_path=candidate_path,
        expected_files=expected_files,
        expected_directories=expected_directories,
        expected_symlinks=expected_symlinks,
        expected_bytes=expected_bytes,
        expected_digest=expected_digest,
        expected_extra_files=expected_extra_files,
        expected_extra_directories=expected_extra_directories,
        expected_extra_symlinks=expected_extra_symlinks,
        required_uid=required_uid,
        required_gid=required_gid,
    )

    quarantine_root.mkdir(parents=True, mode=0o700)
    payload = quarantine_root / "payload"
    payload.mkdir(mode=0o700)

    if live_root.stat().st_dev != quarantine_root.stat().st_dev:
        raise RuntimeError(
            "quarantine must be on the same filesystem for atomic rename"
        )

    manifest = {
        "schema_version": 1,
        "live_root": str(live_root),
        "candidate_evidence": str(candidate_path),
        "candidate_evidence_sha256": proof["candidate_evidence_sha256"],
        "candidate_roots": proof["candidate_roots"],
        "pre_actual_digest": proof["pre_actual_digest"],
        "pre_actual_counts": proof["pre_actual_counts"],
        "expected": {
            "file_count": expected_files,
            "directory_count": expected_directories,
            "symlink_count": expected_symlinks,
            "materialized_bytes": expected_bytes,
            "tree_digest_sha256": expected_digest,
            "extra_file_count": expected_extra_files,
            "extra_directory_count": expected_extra_directories,
            "extra_symlink_count": expected_extra_symlinks,
        },
        "state": "PREPARED",
    }
    manifest_path = quarantine_root / "repair-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    moved: list[str] = []
    try:
        for rel in proof["candidate_roots"]:
            src = live_root / rel
            dst = payload / rel
            if not src.exists() and not src.is_symlink():
                raise RuntimeError(f"candidate root disappeared: {rel}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.rename(src, dst)
            moved.append(rel)

        after, after_counts = projection.scan_tree(
            live_root,
            hash_regular_files=True,
        )
        after_digest, actual = actual_digest(after)

        expected_actual = {
            "file_count": expected_files,
            "directory_count": expected_directories,
            "symlink_count": expected_symlinks,
            "materialized_bytes": expected_bytes,
        }
        for key, expected in expected_actual.items():
            if actual[key] != expected:
                raise RuntimeError(
                    f"post-repair {key} mismatch: {actual[key]} != {expected}"
                )
        if after_digest != expected_digest:
            raise RuntimeError(
                f"post-repair digest mismatch: {after_digest}"
            )

        if (
            after_counts["root_uid"] != required_uid
            or after_counts["root_gid"] != required_gid
        ):
            raise RuntimeError("post-repair root ownership drift")
        if int(after_counts["root_mode"]) & 0o222:
            raise RuntimeError("post-repair runtime root is writable")

        wrong_owner = [
            item["path"] for item in after.values()
            if item["uid"] != required_uid or item["gid"] != required_gid
        ]
        if wrong_owner:
            raise RuntimeError(
                f"post-repair ownership drift: {len(wrong_owner)} path(s)"
            )
        if actual["writable_retained_before_projection"] != 0:
            raise RuntimeError("post-repair writable inode detected")

        manifest["state"] = "APPLIED_LOCAL_PROOF_PASS"
        manifest["post_actual_digest"] = after_digest
        manifest["post_actual_counts"] = actual
        manifest["moved_roots"] = moved
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        return {
            "decision": "PASS",
            "manifest_path": str(manifest_path),
            "manifest_sha256": file_sha256(manifest_path),
            "candidate_root_count": len(moved),
            "post_actual_digest": after_digest,
            "post_actual_counts": actual,
        }
    except Exception:
        if moved:
            rollback_moves(
                live_root=live_root,
                quarantine_root=quarantine_root,
                roots=moved,
            )
        raise


def rollback_repair(
    *,
    manifest_path: pathlib.Path,
    required_uid: int = 0,
    required_gid: int = 0,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise RuntimeError("unsupported repair manifest")

    live_root = pathlib.Path(manifest["live_root"])
    quarantine_root = manifest_path.parent
    roots = list(manifest.get("moved_roots") or manifest["candidate_roots"])

    rollback_moves(
        live_root=live_root,
        quarantine_root=quarantine_root,
        roots=roots,
    )

    after, after_counts = projection.scan_tree(
        live_root,
        hash_regular_files=True,
    )
    after_digest, actual = actual_digest(after)

    if after_digest != manifest["pre_actual_digest"]:
        raise RuntimeError(
            f"rollback digest mismatch: {after_digest}"
        )

    pre_counts = manifest["pre_actual_counts"]
    for key in (
        "file_count",
        "directory_count",
        "symlink_count",
        "materialized_bytes",
    ):
        if actual[key] != pre_counts[key]:
            raise RuntimeError(
                f"rollback {key} mismatch: {actual[key]} != {pre_counts[key]}"
            )

    if (
        after_counts["root_uid"] != required_uid
        or after_counts["root_gid"] != required_gid
    ):
        raise RuntimeError("rollback root ownership drift")

    manifest["state"] = "ROLLED_BACK"
    manifest["rollback_actual_digest"] = after_digest
    manifest["rollback_actual_counts"] = actual
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "decision": "PASS",
        "state": "ROLLED_BACK",
        "actual_digest": after_digest,
        "manifest_sha256": file_sha256(manifest_path),
    }


def cli() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)

    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("--live-root", required=True)
    apply_parser.add_argument("--candidate-evidence", required=True)
    apply_parser.add_argument("--quarantine-root", required=True)
    apply_parser.add_argument("--expected-files", type=int, required=True)
    apply_parser.add_argument("--expected-directories", type=int, required=True)
    apply_parser.add_argument("--expected-symlinks", type=int, required=True)
    apply_parser.add_argument("--expected-bytes", type=int, required=True)
    apply_parser.add_argument("--expected-digest", required=True)
    apply_parser.add_argument("--expected-extra-files", type=int, required=True)
    apply_parser.add_argument("--expected-extra-directories", type=int, required=True)
    apply_parser.add_argument("--expected-extra-symlinks", type=int, required=True)

    rollback_parser = sub.add_parser("rollback")
    rollback_parser.add_argument("--manifest", required=True)

    args = parser.parse_args()

    try:
        if args.action == "apply":
            result = apply_repair(
                live_root=pathlib.Path(args.live_root),
                candidate_path=pathlib.Path(args.candidate_evidence),
                quarantine_root=pathlib.Path(args.quarantine_root),
                expected_files=args.expected_files,
                expected_directories=args.expected_directories,
                expected_symlinks=args.expected_symlinks,
                expected_bytes=args.expected_bytes,
                expected_digest=args.expected_digest,
                expected_extra_files=args.expected_extra_files,
                expected_extra_directories=args.expected_extra_directories,
                expected_extra_symlinks=args.expected_extra_symlinks,
            )
            print(
                f"CANDIDATE_ROOT_COUNT={result['candidate_root_count']}"
            )
            print(f"REPAIR_MANIFEST={result['manifest_path']}")
            print(f"REPAIR_MANIFEST_SHA256={result['manifest_sha256']}")
            print(f"POST_REPAIR_TREE_DIGEST={result['post_actual_digest']}")
            print("REVERSIBLE_RUNTIME_REPAIR=PASS")
            return 0

        result = rollback_repair(
            manifest_path=pathlib.Path(args.manifest),
        )
        print(f"ROLLBACK_TREE_DIGEST={result['actual_digest']}")
        print(f"ROLLBACK_MANIFEST_SHA256={result['manifest_sha256']}")
        print("REVERSIBLE_RUNTIME_ROLLBACK=PASS")
        return 0
    except Exception as exc:
        print(f"ERROR_TYPE={type(exc).__name__}")
        print(f"ERROR={exc}")
        if args.action == "apply":
            print("REVERSIBLE_RUNTIME_REPAIR=FAILED")
        else:
            print("REVERSIBLE_RUNTIME_ROLLBACK=FAILED")
        return 10


if __name__ == "__main__":
    raise SystemExit(cli())
