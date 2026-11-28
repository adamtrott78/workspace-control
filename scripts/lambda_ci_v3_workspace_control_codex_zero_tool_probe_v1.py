#!/usr/bin/env python3
"""No-inference zero-tool request probe for pinned Workspace Control Codex.

This helper is stdlib-only. It launches the exact checksum-pinned Codex app-server
against a loopback fake Responses endpoint, starts one ephemeral turn, captures the
outbound request before any model can answer, and requires an empty model-visible
tool list. It does not copy or use ChatGPT credentials.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
from types import ModuleType
from typing import Any, Mapping


class ProbeError(RuntimeError):
    pass


def _child_environment(
    environment: Mapping[str, str],
    *,
    probe_home: Path,
) -> dict[str, str]:
    child = dict(environment)
    for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "PYTHONPATH", "PYTHONHOME"):
        child.pop(key, None)
    child["CODEX_HOME"] = str(probe_home)
    return child


def _load_trusted_helper(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "workspace_control_trusted_calibration_helper",
        path,
    )
    if spec is None or spec.loader is None:
        raise ProbeError("trusted_helper_import_spec_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not isinstance(getattr(module, "CALIBRATION_MODEL", None), str):
        raise ProbeError("trusted_helper_model_missing")
    if not callable(getattr(module, "_tool_free_model_catalog", None)):
        raise ProbeError("trusted_helper_model_catalog_missing")
    return module


def _prepare_probe_home(*, trusted_codex_home: Path, temp_root: Path) -> Path:
    trusted_config = trusted_codex_home / "config.toml"
    if not trusted_config.is_file() or trusted_config.is_symlink():
        raise ProbeError("trusted_codex_config_invalid")
    probe_home = Path(
        tempfile.mkdtemp(prefix="codex-zero-tool-home.", dir=temp_root)
    )
    config_lines = [
        line
        for line in trusted_config.read_text(encoding="utf-8").splitlines()
        if not line.startswith("forced_login_method")
        and not line.startswith("cli_auth_credentials_store")
    ]
    (probe_home / "config.toml").write_text(
        "\n".join(config_lines) + "\n",
        encoding="utf-8",
    )
    os.chmod(probe_home, 0o700)
    os.chmod(probe_home / "config.toml", 0o600)
    if (probe_home / "auth.json").exists():
        raise ProbeError("probe_home_must_not_contain_auth")
    return probe_home


def _write_model_catalog(
    *,
    helper: ModuleType,
    temp_root: Path,
) -> Path:
    path = temp_root / "codex-zero-tool.models.json"
    catalog = helper._tool_free_model_catalog()
    path.write_text(json.dumps(catalog, sort_keys=True), encoding="utf-8")
    return path


def _output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["result_kind", "summary", "evidence_refs"],
        "properties": {
            "result_kind": {"type": "string", "enum": ["RESULT"]},
            "summary": {"type": "string", "enum": ["CALIBRATION_OK"]},
            "evidence_refs": {
                "type": "array",
                "maxItems": 0,
                "items": {"type": "string"},
            },
        },
    }


def _build_app_server_command(
    *,
    codex_bin: str,
    model: str,
    model_catalog: Path,
    port: int,
) -> list[str]:
    provider = (
        'model_providers.zero_tool_probe={ name = "zero-tool-probe", '
        f'base_url = "http://127.0.0.1:{port}/v1", '
        'wire_api = "responses", requires_openai_auth = false, '
        'request_max_retries = 0, stream_max_retries = 0, '
        'supports_websockets = false }'
    )
    return [
        codex_bin,
        "--config",
        'model_provider="zero_tool_probe"',
        "--config",
        f"model={json.dumps(model)}",
        "--config",
        f"model_catalog_json={json.dumps(str(model_catalog))}",
        "--config",
        provider,
        "app-server",
        "--listen",
        "stdio://",
    ]


def _validate_observed_request(
    observed: Mapping[str, Any],
    *,
    model: str,
) -> None:
    if "capture_error" in observed:
        raise ProbeError("request_capture_failed")
    if observed.get("path") != "/v1/responses":
        raise ProbeError("unexpected_request_path")
    if observed.get("authorization_header_present") is not False:
        raise ProbeError("authorization_header_present")
    body = observed.get("body")
    if not isinstance(body, Mapping):
        raise ProbeError("request_body_missing")
    if body.get("model") != model:
        raise ProbeError("request_model_mismatch")
    if body.get("tools") != []:
        raise ProbeError("model_visible_tools_present")


def _rpc_reader(
    proc: subprocess.Popen[str],
    lines: queue.Queue[object],
) -> None:
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            lines.put(line)
    finally:
        lines.put(None)


def _rpc_write(
    proc: subprocess.Popen[str],
    payload: Mapping[str, Any],
) -> None:
    if proc.stdin is None:
        raise ProbeError("app_server_stdin_unavailable")
    proc.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
    proc.stdin.flush()


def _rpc_request(
    proc: subprocess.Popen[str],
    lines: queue.Queue[object],
    *,
    request_id: int,
    method: str,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"method": method, "id": request_id}
    if params is not None:
        payload["params"] = dict(params)
    _rpc_write(proc, payload)
    while True:
        try:
            item = lines.get(timeout=8.0)
        except queue.Empty as exc:
            raise ProbeError(f"rpc_timeout:{method}") from exc
        if item is None:
            raise ProbeError(f"app_server_closed:{method}")
        try:
            response = json.loads(str(item))
        except json.JSONDecodeError:
            continue
        if not isinstance(response, dict) or response.get("id") != request_id:
            continue
        if response.get("error") is not None:
            error = response.get("error")
            code = error.get("code") if isinstance(error, Mapping) else "unknown"
            raise ProbeError(f"rpc_error:{method}:code={code}")
        result = response.get("result")
        if not isinstance(result, dict):
            raise ProbeError(f"rpc_result_missing:{method}")
        return result


def run_probe(
    *,
    helper_path: Path,
    codex_bin: str,
    trusted_codex_home: Path,
    temp_root: Path,
    environment: Mapping[str, str],
) -> None:
    helper = _load_trusted_helper(helper_path)
    model = helper.CALIBRATION_MODEL
    model_catalog = _write_model_catalog(helper=helper, temp_root=temp_root)
    probe_home = _prepare_probe_home(
        trusted_codex_home=trusted_codex_home,
        temp_root=temp_root,
    )
    work = Path(tempfile.mkdtemp(prefix="codex-zero-tool-work.", dir=temp_root))
    subprocess.run(
        ["git", "init", "-q", str(work)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    captured: queue.Queue[dict[str, Any]] = queue.Queue()

    class CaptureHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                body = json.loads(raw)
                if not isinstance(body, dict):
                    raise ValueError("request body must be object")
                captured.put(
                    {
                        "path": self.path,
                        "authorization_header_present": (
                            self.headers.get("Authorization") is not None
                        ),
                        "body": body,
                    }
                )
            except Exception as exc:
                captured.put({"capture_error": type(exc).__name__})
            response = b'{"error":{"message":"zero-tool-probe-stop"}}'
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    server = ThreadingHTTPServer(("127.0.0.1", 0), CaptureHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    port = int(server.server_address[1])

    command = _build_app_server_command(
        codex_bin=codex_bin,
        model=model,
        model_catalog=model_catalog,
        port=port,
    )
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        bufsize=1,
        env=_child_environment(environment, probe_home=probe_home),
        cwd=work,
        shell=False,
    )
    if proc.stdin is None or proc.stdout is None:
        raise ProbeError("app_server_stdio_unavailable")

    lines: queue.Queue[object] = queue.Queue()
    threading.Thread(
        target=_rpc_reader,
        args=(proc, lines),
        daemon=True,
    ).start()

    try:
        _rpc_request(
            proc,
            lines,
            request_id=1,
            method="initialize",
            params={
                "clientInfo": {
                    "name": "workspace-control-zero-tool-probe",
                    "version": "1.0",
                }
            },
        )
        _rpc_write(proc, {"method": "initialized", "params": {}})
        thread_result = _rpc_request(
            proc,
            lines,
            request_id=2,
            method="thread/start",
            params={
                "cwd": str(work),
                "ephemeral": True,
                "model": model,
            },
        )
        thread = thread_result.get("thread")
        if not isinstance(thread, Mapping) or not isinstance(thread.get("id"), str):
            raise ProbeError("thread_id_missing")
        _rpc_request(
            proc,
            lines,
            request_id=3,
            method="turn/start",
            params={
                "threadId": thread["id"],
                "input": [{"type": "text", "text": "ZERO_TOOL_PROBE"}],
                "outputSchema": _output_schema(),
            },
        )
        try:
            observed = captured.get(timeout=8.0)
        except queue.Empty as exc:
            raise ProbeError("no_model_request_captured") from exc
        _validate_observed_request(observed, model=model)
        time.sleep(0.2)
        if not captured.empty():
            raise ProbeError("multiple_model_requests_observed")
    finally:
        try:
            if proc.stdin is not None:
                proc.stdin.close()
        except OSError:
            pass
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=1.0)
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1.0)


def _self_test() -> int:
    print("WORKSPACE_CONTROL_CODEX_ZERO_TOOL_PROBE_SELF_TEST=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--helper")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    if not args.helper:
        raise ProbeError("trusted_helper_argument_required")
    if "OPENAI_API_KEY" in os.environ or "CODEX_API_KEY" in os.environ:
        raise ProbeError("api_key_environment_must_be_absent")
    run_probe(
        helper_path=Path(args.helper),
        codex_bin=os.environ["CODEX_BIN"],
        trusted_codex_home=Path(os.environ["CODEX_HOME"]),
        temp_root=Path(os.environ["RUNNER_TEMP"]),
        environment=os.environ,
    )
    print("WORKSPACE_CONTROL_CODEX_ZERO_TOOL_PROBE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
