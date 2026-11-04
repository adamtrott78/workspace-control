#!/usr/bin/env python3
"""Validate tunnel-client doctor output for Workspace Shell commissioning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED_MCP_URL = "https://127.0.0.1:8797/mcp"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def by_id(report: dict) -> dict[str, dict]:
    checks = report.get("checks")
    if not isinstance(checks, list):
        fail("doctor report checks must be a list")
    result = {}
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("id"), str):
            fail("doctor report contains malformed check")
        result[check["id"]] = check
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--exit-code", required=True, type=int)
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    checks = by_id(report)
    failed = report.get("failed_checks") or []
    if not isinstance(failed, list) or not all(isinstance(x, str) for x in failed):
        fail("doctor failed_checks must be a string list")

    required_pass = {
        "config_source",
        "profile_load",
        "tunnel_id",
        "control_plane_api_key",
        "mcp_target",
        "mcp_server_reachable",
        "health_listener",
        "ui",
    }
    for check_id in required_pass:
        check = checks.get(check_id)
        if not check or check.get("status") != "PASS":
            fail(f"doctor check {check_id} did not PASS")

    if checks["mcp_target"].get("summary") != EXPECTED_MCP_URL:
        fail("doctor MCP target does not match Workspace Shell loopback endpoint")

    if args.exit_code == 0:
        if report.get("result") != "ok" or failed:
            fail("doctor exit 0 did not produce an all-clear report")
        print("TUNNEL_DOCTOR_GATE=PASS")
        return

    if args.exit_code != 2:
        fail(f"unexpected tunnel-client doctor exit code {args.exit_code}")

    # tunnel-client v0.0.18 doctor builds its diagnostic HTTP client from the
    # global CA bundle only. It does not apply the binding's client certificate.
    # The real runtime does apply binding.ClientCertificate to the MCP origin.
    # Accept only the exact mTLS-auth diagnostic false-negative, and only after
    # the activation operator has independently proven the same endpoint with
    # curl --cert/--key.
    if report.get("result") != "fail" or failed != ["oauth_metadata"]:
        fail("doctor failure is not the single known oauth_metadata mTLS diagnostic limitation")

    oauth = checks.get("oauth_metadata") or {}
    if oauth.get("status") != "FAIL":
        fail("oauth_metadata is not FAIL in the known limitation case")
    oauth_summary = str(oauth.get("summary") or "")
    if "certificate required" not in oauth_summary:
        fail("oauth_metadata failure is not the expected missing-client-certificate diagnostic")

    reachability = checks["mcp_server_reachable"]
    reachability_summary = str(reachability.get("summary") or "")
    if "TCP connect succeeded" not in reachability_summary or "certificate required" not in reachability_summary:
        fail("reachability evidence does not match the known mTLS doctor limitation")

    for check in checks.values():
        if check.get("id") != "oauth_metadata" and check.get("status") == "FAIL":
            fail(f"unexpected additional doctor failure: {check.get('id')}")

    print("TUNNEL_DOCTOR_GATE=KNOWN_V0_0_18_MTLS_DIAGNOSTIC_LIMITATION")


if __name__ == "__main__":
    main()
