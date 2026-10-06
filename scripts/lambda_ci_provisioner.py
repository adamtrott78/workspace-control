#!/usr/bin/env python3
"""Static policy engine for the Lambda CI root provisioner.

P1 scope: request validation + fixed launch-spec rendering only.
This file does NOT create users, units, runners, sockets, or processes.
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import re
import sys
import uuid
from dataclasses import dataclass
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "architecture" / "lambda-ci-project-research-engine.v1.json"
DEFAULT_PROFILES = ROOT / "architecture" / "lambda-ci-systemd-profiles.v1.json"
DEFAULT_PINS = ROOT / "architecture" / "lambda-ci-upstream-pins.v1.json"

_ALLOWED_REQUEST_KEYS = {
    "schema_version",
    "request_id",
    "project_id",
    "profile",
    "runner_name",
    "jit_config",
}
_RUNNER_NAME = re.compile(r"^lambda-research-engine-[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_MAX_JIT_BYTES = 128 * 1024


class PolicyError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedRequest:
    request_id: str
    project_id: str
    profile: str
    runner_name: str
    jit_config: str


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_request(data: dict[str, Any], manifest: dict[str, Any]) -> ValidatedRequest:
    if set(data) != _ALLOWED_REQUEST_KEYS:
        extra = sorted(set(data) - _ALLOWED_REQUEST_KEYS)
        missing = sorted(_ALLOWED_REQUEST_KEYS - set(data))
        raise PolicyError(f"request keys mismatch extra={extra} missing={missing}")

    if data["schema_version"] != 1:
        raise PolicyError("unsupported schema_version")

    try:
        request_id = str(uuid.UUID(str(data["request_id"])))
    except (ValueError, AttributeError) as exc:
        raise PolicyError("request_id must be UUID") from exc

    project_id = data["project_id"]
    if project_id != manifest["project_id"]:
        raise PolicyError("project_id not authorized by manifest")

    profile = data["profile"]
    if profile not in manifest["profiles"]:
        raise PolicyError("profile not authorized by manifest")

    runner_name = data["runner_name"]
    if not isinstance(runner_name, str) or not _RUNNER_NAME.fullmatch(runner_name):
        raise PolicyError("runner_name rejected")

    jit_config = data["jit_config"]
    if not isinstance(jit_config, str) or not jit_config:
        raise PolicyError("jit_config must be non-empty string")
    if len(jit_config.encode("utf-8")) > _MAX_JIT_BYTES:
        raise PolicyError("jit_config exceeds size limit")
    try:
        decoded = base64.b64decode(jit_config, validate=True)
    except Exception as exc:
        raise PolicyError("jit_config must be strict base64") from exc
    if not decoded:
        raise PolicyError("jit_config decodes empty")

    return ValidatedRequest(
        request_id=request_id,
        project_id=project_id,
        profile=profile,
        runner_name=runner_name,
        jit_config=jit_config,
    )


def build_launch_spec(
    request: ValidatedRequest,
    manifest: dict[str, Any],
    profiles: dict[str, Any],
    pins: dict[str, Any],
) -> dict[str, Any]:
    project_profile = manifest["profiles"][request.profile]
    systemd_profile = profiles["profiles"][request.profile]

    job_root = pathlib.PurePosixPath(manifest["roots"]["jobs"])
    staging = pathlib.PurePosixPath(manifest["roots"]["staging_cache"])
    trusted = pathlib.PurePosixPath(manifest["roots"]["trusted_cache"])
    home = pathlib.PurePosixPath(manifest["roots"]["home"])
    logs = pathlib.PurePosixPath(manifest["roots"]["logs"])

    unit_name = f"workspace-ci-{request.project_id}-{request.request_id}.service"
    runner_release = pins["actions_runner"]

    # This is a declarative spec consumed only by the later privileged launcher.
    # The only secret is jit_config_env_value; callers must not log/serialize it.
    return {
        "schema_version": 1,
        "unit_name": unit_name,
        "project_id": request.project_id,
        "profile": request.profile,
        "runner_name": request.runner_name,
        "run_as": {
            "user": manifest["runner_user"],
            "group": manifest["runner_group"],
        },
        "paths": {
            "job_root": str(job_root),
            "staging_cache": str(staging),
            "trusted_cache": str(trusted),
            "home": str(home),
            "logs": str(logs),
        },
        "runner": {
            "version": runner_release["version"],
            "asset_name": runner_release["asset_name"],
            "sha256": runner_release["linux_x64_sha256"],
            "fixed_command": ["./run.sh"],
            "jit_config_env_name": "ACTIONS_RUNNER_INPUT_JITCONFIG",
            "jit_config_env_value": request.jit_config,
        },
        "resources": {
            "cpu_quota_percent": project_profile["cpu_quota_percent"],
            "memory_max_bytes": project_profile["memory_max_bytes"],
            "tasks_max": project_profile["tasks_max"],
            "runtime_max_seconds": project_profile["runtime_max_seconds"],
            "gpu_indices": project_profile["gpu_indices"],
        },
        "systemd_common": profiles["common"],
        "systemd_profile": systemd_profile,
        "forbidden_paths": manifest["forbidden_paths"],
        "allow_production_services": project_profile["allow_production_services"],
    }


def redacted_spec(spec: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(spec))
    clone["runner"]["jit_config_env_value"] = "<REDACTED>"
    return clone


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("request", type=pathlib.Path)
    p.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    p.add_argument("--profiles", type=pathlib.Path, default=DEFAULT_PROFILES)
    p.add_argument("--pins", type=pathlib.Path, default=DEFAULT_PINS)
    p.add_argument("--emit-redacted-spec", action="store_true")
    args = p.parse_args()

    manifest = _load(args.manifest)
    profiles = _load(args.profiles)
    pins = _load(args.pins)
    request_data = _load(args.request)
    req = validate_request(request_data, manifest)
    spec = build_launch_spec(req, manifest, profiles, pins)

    if args.emit_redacted_spec:
        print(json.dumps(redacted_spec(spec), indent=2, sort_keys=True))
    else:
        print("REQUEST_POLICY=PASS")
        print(f"PROJECT={req.project_id}")
        print(f"PROFILE={req.profile}")
        print(f"RUNNER={req.runner_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
