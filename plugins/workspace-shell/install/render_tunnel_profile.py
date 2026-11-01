#!/usr/bin/env python3
"""Render the exact Workspace Shell tunnel-client v0.0.18 profile."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re


TUNNEL_RE = re.compile(r"^tunnel_(?:[a-z0-9]{4}_)?[a-z0-9]{32}$")


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def q(value: str) -> str:
    # JSON strings are valid YAML scalars and give deterministic escaping.
    return json.dumps(value)


def render(args) -> None:
    if not TUNNEL_RE.fullmatch(args.tunnel_id):
        fail("invalid tunnel ID")
    if args.profile != "workspace-shell-production":
        fail("unexpected profile name")

    out_dir = Path(args.profile_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.profile}.yaml"
    if out.exists() and not args.force:
        fail("profile already exists")

    text = "\n".join([
        "config_version: 1",
        f"ca_bundle: {q(args.ca_bundle)}",
        "control_plane:",
        f"  base_url: {q('https://api.openai.com')}",
        f"  tunnel_id: {q(args.tunnel_id)}",
        f"  api_key: {q(args.api_key_ref)}",
        "health:",
        f"  listen_addr: {q('127.0.0.1:0')}",
        "admin_ui:",
        "  open_browser: false",
        "log:",
        "  level: info",
        "  format: json",
        "mcp:",
        f"  startup_wait_timeout: {q('15s')}",
        "  server_urls:",
        "    - channel: main",
        f"      url: {q('https://127.0.0.1:8797/mcp')}",
        f"      client_cert: {q(args.client_cert)}",
        f"      client_key: {q(args.client_key)}",
        "",
    ])
    out.write_text(text, encoding="utf-8")
    os.chmod(out, 0o600)
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="workspace-shell-production")
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--tunnel-id", required=True)
    parser.add_argument("--api-key-ref", default="file:/etc/workspace-shell/tunnel/runtime-key")
    parser.add_argument("--ca-bundle", default="/etc/workspace-shell/tunnel/ca.crt")
    parser.add_argument("--client-cert", default="/etc/workspace-shell/tunnel/client.crt")
    parser.add_argument("--client-key", default="/etc/workspace-shell/tunnel/client.key")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    render(args)


if __name__ == "__main__":
    main()
