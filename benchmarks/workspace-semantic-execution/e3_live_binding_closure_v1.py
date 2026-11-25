"""Cross-artifact binding closure for E3 live attempts.

This module is inert on import. It validates one canonical binding manifest
against the authority artifact, repository blobs, and observed candidate branch
head before a live authority can be consumed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MANIFEST_ID = "workspace-semantic-execution-e3-live-binding-manifest-v1"


class BindingClosureError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BindingClosureError(f"json_not_object:{path}")
    return data


def _sha(name: str, value: object) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise BindingClosureError(f"{name}_invalid")
    return value


def _sha256(name: str, value: object) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise BindingClosureError(f"{name}_invalid")
    return value


def _relpath(name: str, value: object) -> str:
    if not isinstance(value, str) or not value or value.startswith("/"):
        raise BindingClosureError(f"{name}_invalid")
    p = Path(value)
    if ".." in p.parts:
        raise BindingClosureError(f"{name}_invalid")
    return value


def _git(repo_root: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if cp.returncode != 0:
        raise BindingClosureError(
            f"git_failed:{' '.join(args)}:{cp.stderr.strip()}"
        )
    return cp.stdout.strip()


def git_blob(repo_root: Path, relpath: str, ref: str = "HEAD") -> str:
    return _sha(
        f"git_blob:{relpath}",
        _git(repo_root, "rev-parse", f"{ref}:{relpath}"),
    )


def load_manifest(path: Path) -> dict[str, Any]:
    m = _load_json(path)
    if m.get("schema_version") != 1:
        raise BindingClosureError("manifest_schema_mismatch")
    if m.get("artifact_id") != MANIFEST_ID:
        raise BindingClosureError("manifest_artifact_id_mismatch")
    _sha("candidate_baseline", m.get("candidate_baseline"))
    branch = m.get("candidate_branch")
    if branch != "worker-result-candidates-v1":
        raise BindingClosureError("candidate_branch_mismatch")
    _sha256("root_packet_sha256", m.get("root_packet_sha256"))

    paths = m.get("paths")
    blobs = m.get("blobs")
    provenance = m.get("provenance")
    if not isinstance(paths, dict) or not isinstance(blobs, dict) or not isinstance(provenance, dict):
        raise BindingClosureError("manifest_shape_invalid")

    for key in ("wrapper", "e2_harness", "observer", "closure_helper"):
        _relpath(f"path:{key}", paths.get(key))
        _sha(f"blob:{key}", blobs.get(key))

    for key in (
        "worker_result_schema_review_head",
        "worker_result_schema_blob",
        "a8_frontend_review_head",
        "a8_frontend_source_head",
        "a8_frontend_src_tree",
        "accepted_a7_dev_harness_blob",
        "operator_transport_head",
        "source_head",
    ):
        _sha(f"provenance:{key}", provenance.get(key))
    return m


def validate_repo_manifest(repo_root: Path, manifest: dict[str, Any]) -> None:
    paths = manifest["paths"]
    blobs = manifest["blobs"]
    for key in ("wrapper", "e2_harness", "observer", "closure_helper"):
        actual = git_blob(repo_root, paths[key])
        if actual != blobs[key]:
            raise BindingClosureError(
                f"manifest_blob_mismatch:{key}:{actual}:{blobs[key]}"
            )


def validate_authority(
    repo_root: Path,
    authority_path: Path,
    manifest_path: Path,
    *,
    expected_artifact_id: str,
) -> dict[str, Any]:
    a = _load_json(authority_path)
    if a.get("schema_version") != 1:
        raise BindingClosureError("authority_schema_mismatch")
    if a.get("artifact_id") != expected_artifact_id:
        raise BindingClosureError("authority_artifact_id_mismatch")
    if a.get("status") != "PENDING_OPERATOR_WOP_EXECUTION":
        raise BindingClosureError("authority_status_mismatch")

    attempt = a.get("attempt_contract")
    if not isinstance(attempt, dict):
        raise BindingClosureError("authority_attempt_contract_missing")
    if attempt.get("attempts_authorized") != 1:
        raise BindingClosureError("authority_attempt_count_mismatch")
    if attempt.get("consumed") is not False:
        raise BindingClosureError("authority_already_consumed")
    if attempt.get("reusable") is not False or attempt.get("no_silent_retry") is not True:
        raise BindingClosureError("authority_reuse_policy_mismatch")

    bindings = a.get("execution_bindings")
    if not isinstance(bindings, dict):
        raise BindingClosureError("authority_bindings_missing")
    manifest_blob = git_blob(
        repo_root,
        str(manifest_path.relative_to(repo_root)),
    )
    if bindings.get("binding_manifest_blob") != manifest_blob:
        raise BindingClosureError(
            f"authority_manifest_blob_mismatch:{manifest_blob}:"
            f"{bindings.get('binding_manifest_blob')}"
        )
    review = _sha(
        "authority_review_head",
        (a.get("reviewed_source") or {}).get("review_head"),
    )
    return {"authority": a, "review_head": review, "manifest_blob": manifest_blob}


def validate_closure(
    *,
    repo_root: Path,
    authority_rel: str,
    manifest_rel: str,
    expected_authority_id: str,
    candidate_head: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    authority_rel = _relpath("authority_rel", authority_rel)
    manifest_rel = _relpath("manifest_rel", manifest_rel)
    manifest_path = repo_root / manifest_rel
    authority_path = repo_root / authority_rel

    manifest = load_manifest(manifest_path)
    validate_repo_manifest(repo_root, manifest)
    authority = validate_authority(
        repo_root,
        authority_path,
        manifest_path,
        expected_artifact_id=expected_authority_id,
    )

    if candidate_head is not None:
        candidate_head = _sha("candidate_head", candidate_head)
        if candidate_head != manifest["candidate_baseline"]:
            raise BindingClosureError(
                f"candidate_head_mismatch:{candidate_head}:"
                f"{manifest['candidate_baseline']}"
            )

    return {
        "manifest": manifest,
        "review_head": authority["review_head"],
        "manifest_blob": authority["manifest_blob"],
    }


def _emit_lines(result: dict[str, Any]) -> None:
    m = result["manifest"]
    p = m["paths"]
    b = m["blobs"]
    pr = m["provenance"]
    values = [
        m["candidate_branch"],
        m["candidate_baseline"],
        m["root_packet_sha256"],
        p["wrapper"],
        b["wrapper"],
        p["e2_harness"],
        b["e2_harness"],
        p["observer"],
        b["observer"],
        p["closure_helper"],
        b["closure_helper"],
        pr["worker_result_schema_review_head"],
        pr["worker_result_schema_blob"],
        pr["a8_frontend_review_head"],
        pr["a8_frontend_source_head"],
        pr["a8_frontend_src_tree"],
        pr["accepted_a7_dev_harness_blob"],
        pr["operator_transport_head"],
        pr["source_head"],
        result["review_head"],
        result["manifest_blob"],
    ]
    print("\n".join(values))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--authority", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-authority-id", required=True)
    parser.add_argument("--candidate-head")
    parser.add_argument("--emit-lines", action="store_true")
    args = parser.parse_args()

    try:
        result = validate_closure(
            repo_root=Path(args.repo_root),
            authority_rel=args.authority,
            manifest_rel=args.manifest,
            expected_authority_id=args.expected_authority_id,
            candidate_head=args.candidate_head,
        )
    except Exception as exc:
        print(f"E3_BINDING_CLOSURE_ERROR={type(exc).__name__}:{exc}", flush=True)
        return 2

    if args.emit_lines:
        _emit_lines(result)
    else:
        print("E3_BINDING_CLOSURE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
