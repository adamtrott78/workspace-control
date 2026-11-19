"""Localhost-only HTTP adapter for the Operator Bridge backend contract.

The Windows helper is an outbound-only client. Authentication is supplied by
the reviewed reverse proxy (Tailscale Serve in the selected transport) via an
identity header. This adapter never grants execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any
from urllib.parse import unquote, urlparse

from ..application.operator_actions import (
    OperatorActionService,
    OperatorActionServiceError,
)
from ..domain.operator_actions import OperatorActionError


BASE_PATH = "/operator-bridge/v1"


@dataclass(frozen=True)
class OperatorBridgeHttpConfig:
    expected_identity_header: str
    expected_identity_value: str
    bind_host: str = "127.0.0.1"
    port: int = 0
    max_body_bytes: int = 16_384

    def validate(self) -> None:
        if self.bind_host != "127.0.0.1":
            raise ValueError("operator_bridge_http_must_bind_loopback")
        if not self.expected_identity_header.strip():
            raise ValueError("operator_bridge_identity_header_required")
        if not self.expected_identity_value.strip():
            raise ValueError("operator_bridge_identity_value_required")
        if self.port < 0 or self.port > 65535:
            raise ValueError("operator_bridge_port_invalid")
        if self.max_body_bytes < 256 or self.max_body_bytes > 1_048_576:
            raise ValueError("operator_bridge_body_limit_invalid")


class OperatorBridgeHttpServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        config: OperatorBridgeHttpConfig,
        service: OperatorActionService,
    ) -> None:
        config.validate()
        self.operator_bridge_config = config
        self.operator_bridge_service = service
        super().__init__(
            (config.bind_host, config.port),
            OperatorBridgeRequestHandler,
        )


class OperatorBridgeRequestHandler(BaseHTTPRequestHandler):
    server: OperatorBridgeHttpServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _authorized(self) -> bool:
        config = self.server.operator_bridge_config
        observed = self.headers.get(config.expected_identity_header)
        return observed == config.expected_identity_value

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _read_json(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("invalid_content_length") from exc
        if length < 0:
            raise ValueError("invalid_content_length")
        limit = self.server.operator_bridge_config.max_body_bytes
        if length > limit:
            raise OverflowError("request_body_too_large")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid_json") from exc
        if not isinstance(payload, dict):
            raise ValueError("json_object_required")
        return payload

    @staticmethod
    def _required_str(payload: dict[str, Any], name: str) -> str:
        value = payload.get(name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name}_required")
        return value

    @staticmethod
    def _required_int(payload: dict[str, Any], name: str) -> int:
        value = payload.get(name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name}_required")
        return value

    @staticmethod
    def _optional_str(payload: dict[str, Any], name: str) -> str | None:
        value = payload.get(name)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{name}_invalid")
        return value

    @staticmethod
    def _optional_int(payload: dict[str, Any], name: str) -> int | None:
        value = payload.get(name)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name}_invalid")
        return value

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _authenticate_or_reject(self) -> bool:
        if self._authorized():
            return True
        self._send_json(403, {"error": "forbidden"})
        return False

    def do_GET(self) -> None:
        if not self._authenticate_or_reject():
            return
        path = urlparse(self.path).path
        if path != f"{BASE_PATH}/status":
            self._send_json(404, {"error": "not_found"})
            return
        status = self.server.operator_bridge_service.workload_status()
        self._send_json(
            200,
            {
                "readyManualCycles": status.ready_manual_cycles,
                "sentUnconfirmed": status.sent_unconfirmed,
            },
        )

    def do_POST(self) -> None:
        if not self._authenticate_or_reject():
            return
        try:
            payload = self._read_json()
            self._dispatch_post(urlparse(self.path).path, payload)
        except OverflowError:
            self._send_json(413, {"error": "request_too_large"})
        except (ValueError, KeyError, TypeError):
            self._send_json(400, {"error": "invalid_request"})
        except (OperatorActionError, OperatorActionServiceError):
            self._send_json(409, {"error": "action_conflict"})
        except Exception:
            self._send_json(500, {"error": "internal_error"})

    def _dispatch_post(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> None:
        service = self.server.operator_bridge_service
        if path == f"{BASE_PATH}/actions/claim":
            claimed = service.claim_next(
                helper_instance_id=self._required_str(
                    payload, "helperInstanceId"
                ),
                claim_id=self._required_str(payload, "claimId"),
                claimed_at=self._required_str(payload, "claimedAt"),
                expires_at=self._required_str(payload, "expiresAt"),
            )
            if claimed is None:
                self._send_empty(204)
                return
            action = claimed.action
            self._send_json(
                200,
                {
                    "actionId": action.action_id,
                    "generation": action.generation,
                    "workerSlotId": action.worker_slot_id,
                    "sessionGeneration": action.session_generation,
                    "actionType": action.action_type.value,
                    "packetText": claimed.packet_text,
                    "payloadRef": action.payload_ref,
                    "payloadSha256": action.payload_sha256,
                },
            )
            return

        prefix = f"{BASE_PATH}/actions/"
        if not path.startswith(prefix):
            self._send_json(404, {"error": "not_found"})
            return
        remainder = path[len(prefix):]
        if "/" not in remainder:
            self._send_json(404, {"error": "not_found"})
            return
        raw_action_id, operation = remainder.rsplit("/", 1)
        action_id = unquote(raw_action_id)
        if not action_id:
            raise ValueError("action_id_required")

        generation = self._required_int(payload, "generation")
        worker_slot_id = self._optional_str(payload, "workerSlotId")
        session_generation = self._optional_int(
            payload, "sessionGeneration"
        )

        if operation == "revalidate":
            valid = service.revalidate(
                action_id=action_id,
                generation=generation,
                worker_slot_id=worker_slot_id,
                session_generation=session_generation,
            )
            self._send_json(200, {"valid": valid})
            return

        if operation == "local-prepared":
            action = service.record_local_prepared(
                action_id=action_id,
                generation=generation,
                worker_slot_id=worker_slot_id,
                session_generation=session_generation,
                observed_at=self._now(),
            )
            self._send_json(200, {"status": action.status.value})
            return

        if operation == "local-completed":
            action = service.record_local_completed(
                action_id=action_id,
                generation=generation,
                worker_slot_id=worker_slot_id,
                session_generation=session_generation,
                observed_at=self._now(),
            )
            self._send_json(200, {"status": action.status.value})
            return

        if operation in {"local-failure", "blocked"}:
            failure_code = self._required_str(payload, "failureCode")
            failure_message = self._required_str(
                payload, "failureMessage"
            )
            if operation == "local-failure":
                action = service.record_local_failure(
                    action_id=action_id,
                    generation=generation,
                    failure_code=failure_code,
                    failure_message=failure_message,
                )
            else:
                action = service.record_blocked(
                    action_id=action_id,
                    generation=generation,
                    failure_code=failure_code,
                    failure_message=failure_message,
                )
            self._send_json(200, {"status": action.status.value})
            return

        self._send_json(404, {"error": "not_found"})


def build_operator_bridge_http_server(
    *,
    service: OperatorActionService,
    config: OperatorBridgeHttpConfig,
) -> OperatorBridgeHttpServer:
    return OperatorBridgeHttpServer(config, service)
