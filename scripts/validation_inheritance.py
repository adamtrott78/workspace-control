#!/usr/bin/env python3
"""Fail-closed inheritance of prior full validation for unchanged implementation bytes."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _write_output(name: str, value: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def _match(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _load_receipt(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("receipt schema_version must be 1")
    if not isinstance(data.get("validated_head"), str) or len(data["validated_head"]) != 40:
        raise ValueError("validated_head must be a full SHA")
    if not isinstance(data.get("domains"), dict):
        raise ValueError("domains must be an object")
    if not isinstance(data.get("validation_runs"), dict):
        raise ValueError("validation_runs must be an object")
    return data


def _verify_run(repository: str, token: str, run: dict, validated_head: str) -> tuple[bool, str]:
    run_id = run.get("run_id")
    expected_name = run.get("workflow_name")
    if not isinstance(run_id, int) or not expected_name:
        return False, "receipt_run_binding_invalid"
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/actions/runs/{run_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "workspace-validation-inheritance-v1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, f"run_lookup_unavailable:{type(exc).__name__}"
    if payload.get("head_sha") != validated_head:
        return False, "validated_run_head_mismatch"
    if payload.get("conclusion") != "success":
        return False, "validated_run_not_success"
    if payload.get("name") != expected_name:
        return False, "validated_run_workflow_name_mismatch"
    return True, "validated_run_exact_success"


def decide(*, receipt_path: str, domain: str, current_sha: str, repository: str, token: str) -> dict:
    try:
        receipt = _load_receipt(receipt_path)
        domain_cfg = receipt["domains"][domain]
        run_key = domain_cfg["validation_run"]
        run = receipt["validation_runs"][run_key]
        patterns = list(domain_cfg["implementation_patterns"])
        validated_head = receipt["validated_head"]

        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", validated_head, current_sha],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        changed = [
            line
            for line in _git("diff", "--name-only", validated_head, current_sha).splitlines()
            if line
        ]
        relevant = sorted(path for path in changed if _match(path, patterns))
        if relevant:
            return {
                "inherited": False,
                "reason": "implementation_bytes_changed",
                "validated_head": validated_head,
                "relevant_changes": relevant,
            }

        ok, reason = _verify_run(repository, token, run, validated_head)
        return {
            "inherited": bool(ok),
            "reason": reason,
            "validated_head": validated_head,
            "relevant_changes": [],
            "validated_run_id": run.get("run_id"),
        }
    except (KeyError, ValueError, subprocess.CalledProcessError, OSError) as exc:
        return {
            "inherited": False,
            "reason": f"fail_closed:{type(exc).__name__}",
            "relevant_changes": [],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()

    result = decide(
        receipt_path=args.receipt,
        domain=args.domain,
        current_sha=args.current_sha,
        repository=args.repository,
        token=os.environ.get("GITHUB_TOKEN", ""),
    )
    _write_output("inherited", "true" if result["inherited"] else "false")
    _write_output("reason", str(result["reason"]).replace("\n", " "))
    _write_output("validated_head", str(result.get("validated_head", "")))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
