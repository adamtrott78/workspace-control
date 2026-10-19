#!/usr/bin/env python3
"""Read-only projection proof for an accepted immutable runtime tree.

The reference tree is used only as a pathname/type oracle. All projected bytes,
modes, sizes, symlink targets, ownership checks, and the final digest come from
the existing live tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import stat
import sys
from typing import Any


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def kind_for_mode(mode: int) -> str:
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISREG(mode):
        return "file"
    return "special"


def scan_tree(
    root: pathlib.Path,
    *,
    hash_regular_files: bool,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not root.is_dir():
        raise RuntimeError(f"tree root is not a directory: {root}")

    root_stat = root.lstat()
    records: dict[str, dict[str, Any]] = {}
    counts = {
        "file_count": 0,
        "directory_count": 1,
        "symlink_count": 0,
        "materialized_bytes": 0,
        "root_uid": root_stat.st_uid,
        "root_gid": root_stat.st_gid,
        "root_mode": stat.S_IMODE(root_stat.st_mode),
    }

    for path in sorted(
        root.rglob("*"),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        rel = path.relative_to(root).as_posix()
        st = path.lstat()
        kind = kind_for_mode(st.st_mode)
        if kind == "special":
            raise RuntimeError(f"special inode detected: {rel}")

        record: dict[str, Any] = {
            "path": rel,
            "kind": kind,
            "mode": stat.S_IMODE(st.st_mode),
            "uid": st.st_uid,
            "gid": st.st_gid,
        }

        if kind == "file":
            counts["file_count"] += 1
            counts["materialized_bytes"] += st.st_size
            record["size"] = st.st_size
            if hash_regular_files:
                record["sha256"] = sha256_file(path)
        elif kind == "directory":
            counts["directory_count"] += 1
        else:
            counts["symlink_count"] += 1
            record["target"] = os.readlink(path)

        records[rel] = record

    return records, counts


def projected_digest(
    live: dict[str, dict[str, Any]],
    excluded: set[str],
) -> tuple[str, dict[str, int]]:
    tree_hash = hashlib.sha256()
    counts = {
        "file_count": 0,
        "directory_count": 1,
        "symlink_count": 0,
        "materialized_bytes": 0,
        "non_root_owned_retained": 0,
        "writable_retained_before_projection": 0,
    }

    for rel in sorted(live):
        if rel in excluded:
            continue

        item = live[rel]
        kind = item["kind"]

        if item["uid"] != 0 or item["gid"] != 0:
            counts["non_root_owned_retained"] += 1

        if kind == "directory":
            counts["directory_count"] += 1
            mode = int(item["mode"]) & ~0o222
            if int(item["mode"]) & 0o222:
                counts["writable_retained_before_projection"] += 1
            tree_hash.update(f"D\0{rel}\0{mode:o}\n".encode())
            continue

        if kind == "symlink":
            counts["symlink_count"] += 1
            tree_hash.update(
                f"L\0{rel}\0{item['target']}\n".encode()
            )
            continue

        counts["file_count"] += 1
        counts["materialized_bytes"] += int(item["size"])
        mode = int(item["mode"]) & ~0o222
        if int(item["mode"]) & 0o222:
            counts["writable_retained_before_projection"] += 1
        tree_hash.update(
            (
                f"F\0{rel}\0{mode:o}\0{item['size']}\0"
                f"{item['sha256']}\n"
            ).encode()
        )

    return tree_hash.hexdigest(), counts


def write_json(path: pathlib.Path, value: Any) -> str:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return sha256_file(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-root", required=True)
    parser.add_argument("--reference-root", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--expected-files", required=True, type=int)
    parser.add_argument("--expected-directories", required=True, type=int)
    parser.add_argument("--expected-symlinks", required=True, type=int)
    parser.add_argument("--expected-bytes", required=True, type=int)
    parser.add_argument("--expected-digest", required=True)
    args = parser.parse_args()

    live_root = pathlib.Path(args.live_root)
    reference_root = pathlib.Path(args.reference_root)
    evidence_dir = pathlib.Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=False)

    live, live_counts = scan_tree(
        live_root,
        hash_regular_files=True,
    )
    reference, reference_counts = scan_tree(
        reference_root,
        hash_regular_files=False,
    )

    live_paths = set(live)
    reference_paths = set(reference)

    candidate_extras = live_paths - reference_paths
    reference_only = reference_paths - live_paths

    type_mismatches = sorted(
        rel
        for rel in live_paths & reference_paths
        if live[rel]["kind"] != reference[rel]["kind"]
    )

    extra_counts = {
        "file_count": sum(
            live[rel]["kind"] == "file"
            for rel in candidate_extras
        ),
        "directory_count": sum(
            live[rel]["kind"] == "directory"
            for rel in candidate_extras
        ),
        "symlink_count": sum(
            live[rel]["kind"] == "symlink"
            for rel in candidate_extras
        ),
    }

    non_pycache_extras = sorted(
        rel for rel in candidate_extras
        if "__pycache__" not in pathlib.PurePosixPath(rel).parts
    )

    digest, projected = projected_digest(
        live,
        candidate_extras,
    )

    root_projected_mode = int(live_counts["root_mode"]) & ~0o222
    root_owner_ok = (
        live_counts["root_uid"] == 0
        and live_counts["root_gid"] == 0
    )

    expected = {
        "file_count": args.expected_files,
        "directory_count": args.expected_directories,
        "symlink_count": args.expected_symlinks,
        "materialized_bytes": args.expected_bytes,
        "tree_digest_sha256": args.expected_digest,
    }

    candidate_gate = (
        reference_counts["file_count"] == args.expected_files
        and reference_counts["directory_count"]
        == args.expected_directories
        and reference_counts["symlink_count"]
        == args.expected_symlinks
        and not reference_only
        and not type_mismatches
        and extra_counts["file_count"]
        == live_counts["file_count"] - args.expected_files
        and extra_counts["directory_count"]
        == live_counts["directory_count"]
        - args.expected_directories
        and extra_counts["symlink_count"]
        == live_counts["symlink_count"] - args.expected_symlinks
        and not non_pycache_extras
    )

    projection_gate = (
        projected["file_count"] == args.expected_files
        and projected["directory_count"]
        == args.expected_directories
        and projected["symlink_count"] == args.expected_symlinks
        and projected["materialized_bytes"] == args.expected_bytes
        and digest == args.expected_digest
        and projected["non_root_owned_retained"] == 0
        and root_owner_ok
    )

    summary = {
        "schema_version": 1,
        "operation": "read_only_runtime_tree_projection",
        "live_root": str(live_root),
        "reference_root": str(reference_root),
        "live_counts": live_counts,
        "reference_counts": reference_counts,
        "candidate_extra_counts": extra_counts,
        "candidate_extra_count": len(candidate_extras),
        "reference_only_count": len(reference_only),
        "type_mismatch_count": len(type_mismatches),
        "non_pycache_extra_count": len(non_pycache_extras),
        "projected": {
            **projected,
            "root_projected_mode": root_projected_mode,
            "root_owner_ok": root_owner_ok,
            "tree_digest_sha256": digest,
        },
        "expected": expected,
        "candidate_gate": candidate_gate,
        "projection_gate": projection_gate,
        "live_runtime_mutated": False,
        "decision": (
            "PASS"
            if candidate_gate and projection_gate
            else "REJECT"
        ),
    }

    live_manifest = [
        live[rel]
        for rel in sorted(live)
    ]
    candidate = {
        "candidate_extras": sorted(candidate_extras),
        "reference_only": sorted(reference_only),
        "type_mismatches": type_mismatches,
        "non_pycache_extras": non_pycache_extras,
    }

    manifest_sha = write_json(
        evidence_dir / "live-tree-evidence.json",
        live_manifest,
    )
    candidate_sha = write_json(
        evidence_dir / "candidate-path-difference.json",
        candidate,
    )
    summary_sha = write_json(
        evidence_dir / "projection-summary.json",
        summary,
    )

    print(f"LIVE_FILE_COUNT={live_counts['file_count']}")
    print(
        "LIVE_DIRECTORY_COUNT="
        f"{live_counts['directory_count']}"
    )
    print(f"LIVE_SYMLINK_COUNT={live_counts['symlink_count']}")
    print(
        "REFERENCE_FILE_COUNT="
        f"{reference_counts['file_count']}"
    )
    print(
        "REFERENCE_DIRECTORY_COUNT="
        f"{reference_counts['directory_count']}"
    )
    print(
        "REFERENCE_SYMLINK_COUNT="
        f"{reference_counts['symlink_count']}"
    )
    print(
        "CANDIDATE_EXTRA_FILES="
        f"{extra_counts['file_count']}"
    )
    print(
        "CANDIDATE_EXTRA_DIRECTORIES="
        f"{extra_counts['directory_count']}"
    )
    print(
        "CANDIDATE_EXTRA_SYMLINKS="
        f"{extra_counts['symlink_count']}"
    )
    print(f"REFERENCE_ONLY_COUNT={len(reference_only)}")
    print(f"TYPE_MISMATCH_COUNT={len(type_mismatches)}")
    print(
        "NON_PYCACHE_EXTRA_COUNT="
        f"{len(non_pycache_extras)}"
    )
    print(
        "PROJECTED_FILE_COUNT="
        f"{projected['file_count']}"
    )
    print(
        "PROJECTED_DIRECTORY_COUNT="
        f"{projected['directory_count']}"
    )
    print(
        "PROJECTED_SYMLINK_COUNT="
        f"{projected['symlink_count']}"
    )
    print(
        "PROJECTED_MATERIALIZED_BYTES="
        f"{projected['materialized_bytes']}"
    )
    print(f"PROJECTED_TREE_DIGEST={digest}")
    print(
        "NON_ROOT_OWNED_RETAINED="
        f"{projected['non_root_owned_retained']}"
    )
    print(
        "WRITABLE_RETAINED_BEFORE_PROJECTION="
        f"{projected['writable_retained_before_projection']}"
    )
    print(f"LIVE_EVIDENCE_SHA256={manifest_sha}")
    print(f"CANDIDATE_EVIDENCE_SHA256={candidate_sha}")
    print(f"SUMMARY_SHA256={summary_sha}")
    print(
        "RECOVERY_PROJECTION="
        + ("PASS" if summary["decision"] == "PASS" else "REJECT")
    )
    print("LIVE_RUNTIME_MUTATED=false")

    return 0 if summary["decision"] == "PASS" else 10


if __name__ == "__main__":
    raise SystemExit(main())
