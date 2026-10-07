#!/usr/bin/env python3
"""Trusted content-addressed cache manager for workspace Lambda CI.

Promotion is intentionally a root-only operation. Candidate jobs may run the
read-only verifier against already promoted objects, but cannot acquire,
quarantine, or promote persistent content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1
IMPLEMENTATION_ID = "lambda-ci-trusted-cache-v1"
DEFAULT_STATE_ROOT = pathlib.Path("/var/lib/workspace-ci/cache-manager")
DEFAULT_TRUSTED_ROOT = pathlib.Path("/srv/workspace-ci/research-engine/trusted-cache")
PROJECT_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MUTABLE_REVISIONS = {"main", "master", "latest", "head", "trunk"}
UNSAFE_SUFFIXES = {".pkl", ".pickle", ".pt", ".pth"}
SECRET_NAMES = {
    ".env",
    "github-token",
    "credentials",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
    "jitconfig",
    "jit-config",
}
SECRET_MARKERS = (
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"github_pat_",
    b"ghp_",
    b"ACTIONS_RUNNER_INPUT_JITCONFIG=",
)


class CachePolicyError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CachePolicyError(f"JSON document must be an object: {path}")
    return value


def _require_root() -> None:
    if os.geteuid() != 0:
        raise CachePolicyError("trusted cache acquisition/promotion requires root")


def _safe_component(value: str, field: str) -> str:
    if not PROJECT_RE.fullmatch(value):
        raise CachePolicyError(f"{field} has invalid characters")
    return value


def validate_descriptor(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version",
        "project_id",
        "artifact_kind",
        "source",
        "license",
        "serialization",
        "recipe",
    }
    if set(value) != required:
        raise CachePolicyError(
            f"descriptor keys mismatch missing={sorted(required-set(value))} "
            f"extra={sorted(set(value)-required)}"
        )
    if value["schema_version"] != 1:
        raise CachePolicyError("unsupported descriptor schema_version")

    project_id = str(value["project_id"])
    _safe_component(project_id, "project_id")

    artifact_kind = str(value["artifact_kind"])
    if artifact_kind not in {"model", "runtime", "package", "test-fixture"}:
        raise CachePolicyError("artifact_kind is not authorized")

    source = value["source"]
    if not isinstance(source, dict) or set(source) != {
        "kind",
        "identifier",
        "immutable_revision",
    }:
        raise CachePolicyError("source identity must be exact")
    for key in ("kind", "identifier", "immutable_revision"):
        if not isinstance(source[key], str) or not source[key].strip():
            raise CachePolicyError(f"source.{key} must be non-empty")
    revision = source["immutable_revision"].strip()
    if revision.lower() in MUTABLE_REVISIONS:
        raise CachePolicyError("mutable source revision is forbidden")
    if artifact_kind == "model" and source["kind"] == "huggingface":
        if not GIT_SHA_RE.fullmatch(revision.lower()):
            raise CachePolicyError(
                "Hugging Face model promotion requires an exact 40-hex revision"
            )

    license_value = value["license"]
    if not isinstance(license_value, dict) or set(license_value) != {
        "id",
        "reviewed",
    }:
        raise CachePolicyError("license review identity is incomplete")
    if not isinstance(license_value["id"], str) or not license_value["id"].strip():
        raise CachePolicyError("license.id must be non-empty")
    if license_value["reviewed"] is not True:
        raise CachePolicyError("license must be explicitly reviewed")

    serialization = value["serialization"]
    if not isinstance(serialization, dict) or set(serialization) != {
        "format",
        "unsafe_deserialization",
        "custom_code",
    }:
        raise CachePolicyError("serialization risk declaration is incomplete")
    if not isinstance(serialization["format"], str) or not serialization["format"]:
        raise CachePolicyError("serialization.format must be non-empty")
    if serialization["unsafe_deserialization"] is not False:
        raise CachePolicyError("unsafe deserialization is denied by cache v1")
    if serialization["custom_code"] is not False:
        raise CachePolicyError("custom/remote executable model code is denied by cache v1")

    recipe = value["recipe"]
    if not isinstance(recipe, dict) or set(recipe) != {"id", "implementation_sha"}:
        raise CachePolicyError("promotion recipe identity is incomplete")
    if recipe["id"] != IMPLEMENTATION_ID:
        raise CachePolicyError("unexpected promotion recipe id")
    if not isinstance(recipe["implementation_sha"], str) or not GIT_SHA_RE.fullmatch(
        recipe["implementation_sha"].lower()
    ):
        raise CachePolicyError("recipe implementation_sha must be exact 40-hex")

    return json.loads(json.dumps(value))


def _validate_relative_path(rel: pathlib.PurePosixPath) -> None:
    if rel.is_absolute() or not rel.parts or any(part in {"", ".", ".."} for part in rel.parts):
        raise CachePolicyError(f"unsafe relative path: {rel}")


def _secret_path_forbidden(rel: pathlib.PurePosixPath) -> bool:
    lower_parts = [part.lower() for part in rel.parts]
    return any(part in SECRET_NAMES for part in lower_parts)


def _validate_file_policy(path: pathlib.Path, rel: pathlib.PurePosixPath) -> None:
    if _secret_path_forbidden(rel):
        raise CachePolicyError(f"secret-bearing filename forbidden: {rel}")
    suffix = path.suffix.lower()
    if suffix in UNSAFE_SUFFIXES:
        raise CachePolicyError(f"unsafe serialization suffix forbidden: {rel}")
    if path.stat().st_size <= 1024 * 1024:
        data = path.read_bytes()
        for marker in SECRET_MARKERS:
            if marker in data:
                raise CachePolicyError(f"secret marker forbidden in cache object: {rel}")


def scan_tree(root: pathlib.Path) -> tuple[list[dict[str, Any]], str, int]:
    root = root.resolve()
    if not root.is_dir():
        raise CachePolicyError(f"payload root is not a directory: {root}")

    manifest: list[dict[str, Any]] = []
    materialized = 0

    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        rel = pathlib.PurePosixPath(path.relative_to(root).as_posix())
        _validate_relative_path(rel)
        st = path.lstat()
        if stat.S_ISLNK(st.st_mode):
            raise CachePolicyError(f"symlinks are forbidden in trusted cache payloads: {rel}")
        if stat.S_ISDIR(st.st_mode):
            continue
        if not stat.S_ISREG(st.st_mode):
            raise CachePolicyError(f"non-regular payload entry forbidden: {rel}")
        _validate_file_policy(path, rel)
        entry = {
            "path": rel.as_posix(),
            "size": st.st_size,
            "sha256": sha256_file(path),
        }
        manifest.append(entry)
        materialized += st.st_size

    if not manifest:
        raise CachePolicyError("empty cache payload is forbidden")

    digest = sha256_bytes(canonical_json(manifest))
    return manifest, digest, materialized


def _copy_regular_tree(source: pathlib.Path, destination: pathlib.Path) -> None:
    source = source.resolve()
    if not source.is_dir():
        raise CachePolicyError(f"source is not a directory: {source}")
    destination.mkdir(parents=True, mode=0o700)

    for path in sorted(source.rglob("*"), key=lambda p: p.as_posix()):
        rel = pathlib.PurePosixPath(path.relative_to(source).as_posix())
        _validate_relative_path(rel)
        st = path.lstat()
        target = destination.joinpath(*rel.parts)
        if stat.S_ISLNK(st.st_mode):
            raise CachePolicyError(f"symlinks are forbidden during acquisition: {rel}")
        if stat.S_ISDIR(st.st_mode):
            target.mkdir(parents=True, exist_ok=True, mode=0o700)
            continue
        if not stat.S_ISREG(st.st_mode):
            raise CachePolicyError(f"non-regular acquisition entry forbidden: {rel}")
        _validate_file_policy(path, rel)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copyfile(path, target)
        os.chmod(target, 0o600)


def _project_state_root(state_root: pathlib.Path, project_id: str) -> pathlib.Path:
    return state_root / project_id


def acquire_local(
    *,
    source: pathlib.Path,
    descriptor: dict[str, Any],
    state_root: pathlib.Path,
) -> dict[str, Any]:
    _require_root()
    descriptor = validate_descriptor(descriptor)
    project_id = descriptor["project_id"]

    project_state = _project_state_root(state_root, project_id)
    quarantine_root = project_state / "quarantine"
    quarantine_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(project_state, 0o700)
    os.chmod(quarantine_root, 0o700)

    quarantine_id = str(uuid.uuid4())
    item = quarantine_root / quarantine_id
    payload = item / "payload"
    item.mkdir(mode=0o700)
    _copy_regular_tree(source, payload)

    manifest, tree_digest, materialized = scan_tree(payload)
    descriptor_sha = sha256_bytes(canonical_json(descriptor))
    record = {
        "schema_version": 1,
        "status": "QUARANTINED",
        "quarantine_id": quarantine_id,
        "project_id": project_id,
        "acquired_at": _now(),
        "descriptor": descriptor,
        "descriptor_sha256": descriptor_sha,
        "tree_digest_sha256": tree_digest,
        "file_count": len(manifest),
        "materialized_bytes": materialized,
        "file_manifest": manifest,
    }
    metadata = item / "quarantine.json"
    metadata.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(metadata, 0o600)
    return record


def _harden_read_only(root: pathlib.Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        st = path.lstat()
        if stat.S_ISLNK(st.st_mode):
            raise CachePolicyError("symlink appeared while hardening promoted object")
        if stat.S_ISDIR(st.st_mode):
            os.chmod(path, 0o555)
        elif stat.S_ISREG(st.st_mode):
            os.chmod(path, 0o444)
        else:
            raise CachePolicyError(f"non-regular promoted entry: {path}")
    os.chmod(root, 0o555)


def _validate_promoted_modes(root: pathlib.Path) -> None:
    for path in [root, *root.rglob("*")]:
        st = path.lstat()
        if st.st_mode & 0o222:
            raise CachePolicyError(f"promoted object remains writable: {path}")
        if stat.S_ISLNK(st.st_mode):
            raise CachePolicyError(f"promoted object contains symlink: {path}")


def verify_object(object_root: pathlib.Path) -> dict[str, Any]:
    object_root = object_root.resolve()
    receipt_path = object_root / "receipt.json"
    payload = object_root / "payload"
    if not receipt_path.is_file() or not payload.is_dir():
        raise CachePolicyError("promoted object missing receipt or payload")

    receipt = _load_json(receipt_path)
    if receipt.get("schema_version") != 1 or receipt.get("decision") != "PASS":
        raise CachePolicyError("promotion receipt is not PASS")
    if receipt.get("object_id") != object_root.name:
        raise CachePolicyError("object_id does not match content-addressed directory")

    manifest, digest, materialized = scan_tree(payload)
    if digest != receipt.get("tree_digest_sha256"):
        raise CachePolicyError("promoted tree digest mismatch")
    if manifest != receipt.get("file_manifest"):
        raise CachePolicyError("promoted file manifest mismatch")
    if len(manifest) != receipt.get("file_count"):
        raise CachePolicyError("promoted file count mismatch")
    if materialized != receipt.get("materialized_bytes"):
        raise CachePolicyError("promoted materialized byte count mismatch")
    if sha256_bytes(canonical_json(receipt["descriptor"])) != receipt.get(
        "descriptor_sha256"
    ):
        raise CachePolicyError("promotion descriptor digest mismatch")
    validate_descriptor(receipt["descriptor"])
    _validate_promoted_modes(object_root)

    return {
        "schema_version": 1,
        "decision": "PASS",
        "object_id": receipt["object_id"],
        "project_id": receipt["project_id"],
        "artifact_kind": receipt["artifact_kind"],
        "tree_digest_sha256": digest,
        "descriptor_sha256": receipt["descriptor_sha256"],
        "file_count": len(manifest),
        "materialized_bytes": materialized,
        "source": receipt["descriptor"]["source"],
        "serialization": receipt["descriptor"]["serialization"],
        "offline_complete": True,
        "read_only": True,
    }


def promote(
    *,
    quarantine_id: str,
    project_id: str,
    state_root: pathlib.Path,
    trusted_root: pathlib.Path,
) -> dict[str, Any]:
    _require_root()
    _safe_component(project_id, "project_id")
    try:
        uuid.UUID(quarantine_id)
    except ValueError as exc:
        raise CachePolicyError("quarantine_id must be UUID") from exc

    project_state = _project_state_root(state_root, project_id)
    item = project_state / "quarantine" / quarantine_id
    metadata = item / "quarantine.json"
    payload = item / "payload"
    record = _load_json(metadata)
    if record.get("status") != "QUARANTINED":
        raise CachePolicyError("quarantine item is not promotable")
    if record.get("project_id") != project_id:
        raise CachePolicyError("quarantine project mismatch")

    descriptor = validate_descriptor(record["descriptor"])
    manifest, tree_digest, materialized = scan_tree(payload)
    if tree_digest != record.get("tree_digest_sha256"):
        raise CachePolicyError("quarantine tree digest changed after acquisition")
    if manifest != record.get("file_manifest"):
        raise CachePolicyError("quarantine file manifest changed after acquisition")
    if materialized != record.get("materialized_bytes"):
        raise CachePolicyError("quarantine materialized bytes changed after acquisition")

    descriptor_sha = sha256_bytes(canonical_json(descriptor))
    if descriptor_sha != record.get("descriptor_sha256"):
        raise CachePolicyError("quarantine descriptor digest changed")

    trusted_root.mkdir(parents=True, exist_ok=True, mode=0o755)
    os.chmod(trusted_root, 0o755)
    objects = trusted_root / "objects" / descriptor["artifact_kind"] / "sha256"
    objects.mkdir(parents=True, exist_ok=True, mode=0o755)
    object_root = objects / tree_digest

    receipt = {
        "schema_version": 1,
        "decision": "PASS",
        "promotion_authority": "root",
        "promotion_recipe": IMPLEMENTATION_ID,
        "promoted_at": _now(),
        "project_id": project_id,
        "object_id": tree_digest,
        "artifact_kind": descriptor["artifact_kind"],
        "descriptor": descriptor,
        "descriptor_sha256": descriptor_sha,
        "tree_digest_sha256": tree_digest,
        "file_count": len(manifest),
        "materialized_bytes": materialized,
        "file_manifest": manifest,
        "quarantine_id": quarantine_id,
        "quarantine_destroyed": True,
        "candidate_promotion_authorized": False,
        "offline_complete": True,
    }

    if object_root.exists():
        existing = _load_json(object_root / "receipt.json")
        if (
            existing.get("tree_digest_sha256") != tree_digest
            or existing.get("descriptor_sha256") != descriptor_sha
        ):
            raise CachePolicyError("content-addressed object collision/metadata mismatch")
        verify_object(object_root)
        shutil.rmtree(item)
        return existing

    tmp = objects / f".incoming-{uuid.uuid4()}"
    try:
        tmp.mkdir(mode=0o700)
        _copy_regular_tree(payload, tmp / "payload")
        (tmp / "receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (tmp / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _harden_read_only(tmp)
        os.replace(tmp, object_root)
    finally:
        if tmp.exists():
            os.chmod(tmp, 0o700)
            shutil.rmtree(tmp, ignore_errors=True)

    receipts = project_state / "receipts"
    receipts.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(receipts, 0o700)
    durable_receipt = receipts / f"{tree_digest}.json"
    fd, tmp_name = tempfile.mkstemp(prefix=".receipt-", dir=receipts)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, durable_receipt)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    verify_object(object_root)
    shutil.rmtree(item)
    return receipt


def create_canary_source(root: pathlib.Path) -> pathlib.Path:
    _require_root()
    source = root / "workspace-ci-trusted-cache-canary-v1"
    source.mkdir(parents=True, exist_ok=False)
    path = source / "canary.txt"
    path.write_text("workspace-ci-trusted-cache-canary-v1\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return source


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    acquire = sub.add_parser("acquire-local")
    acquire.add_argument("--source", type=pathlib.Path, required=True)
    acquire.add_argument("--descriptor", type=pathlib.Path, required=True)
    acquire.add_argument("--state-root", type=pathlib.Path, default=DEFAULT_STATE_ROOT)

    promote_cmd = sub.add_parser("promote")
    promote_cmd.add_argument("--project-id", required=True)
    promote_cmd.add_argument("--quarantine-id", required=True)
    promote_cmd.add_argument("--state-root", type=pathlib.Path, default=DEFAULT_STATE_ROOT)
    promote_cmd.add_argument("--trusted-root", type=pathlib.Path, default=DEFAULT_TRUSTED_ROOT)

    verify = sub.add_parser("verify")
    verify.add_argument("--object", type=pathlib.Path, required=True)

    args = parser.parse_args()

    if args.command == "acquire-local":
        _print(
            acquire_local(
                source=args.source,
                descriptor=_load_json(args.descriptor),
                state_root=args.state_root,
            )
        )
        return 0
    if args.command == "promote":
        _print(
            promote(
                quarantine_id=args.quarantine_id,
                project_id=args.project_id,
                state_root=args.state_root,
                trusted_root=args.trusted_root,
            )
        )
        return 0
    if args.command == "verify":
        _print(verify_object(args.object))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
