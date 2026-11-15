"""Production composition for the private Operator Bridge backend.

Run as:
    python -m workspace_semantic_execution.operator_bridge_server

The process binds only 127.0.0.1. A reviewed private reverse proxy such as
Tailscale Serve owns TLS and authenticated tailnet identity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os
import re
from typing import Mapping

from .adapters.operator_bridge_http import (
    OperatorBridgeHttpConfig,
    OperatorBridgeHttpServer,
    build_operator_bridge_http_server,
)
from .adapters.postgres import PostgresEventLedger, PostgresStateStore
from .adapters.system import NoopTelemetry, SystemClock
from .application import (
    DurableOperatorPacketMaterializer,
    ExecutorRegistry,
    OperatorActionService,
    RuntimeCoordinator,
    initial_executor_profiles,
)


_STATE_KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


@dataclass(frozen=True)
class OperatorBridgeServerConfig:
    postgres_dsn: str = field(repr=False)
    expected_tailscale_login: str = field(repr=False)
    state_key: str = "control"
    port: int = 8765
    max_body_bytes: int = 16_384

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "OperatorBridgeServerConfig":
        env = os.environ if environ is None else environ
        dsn = env.get("SEMANTIC_EXECUTION_POSTGRES_DSN", "")
        identity = env.get(
            "WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN",
            "",
        )
        state_key = env.get(
            "SEMANTIC_EXECUTION_STATE_KEY",
            "control",
        )
        raw_port = env.get("WORKSPACE_OPERATOR_BRIDGE_PORT", "8765")
        raw_body = env.get(
            "WORKSPACE_OPERATOR_BRIDGE_MAX_BODY_BYTES",
            "16384",
        )

        try:
            port = int(raw_port)
            max_body_bytes = int(raw_body)
        except ValueError as exc:
            raise ValueError(
                "operator_bridge_numeric_configuration_invalid"
            ) from exc

        config = cls(
            postgres_dsn=dsn,
            expected_tailscale_login=identity,
            state_key=state_key,
            port=port,
            max_body_bytes=max_body_bytes,
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not self.postgres_dsn:
            raise ValueError("semantic_execution_postgres_dsn_required")
        if (
            not self.expected_tailscale_login
            or len(self.expected_tailscale_login) > 256
            or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in self.expected_tailscale_login)
        ):
            raise ValueError("expected_tailscale_login_invalid")
        if not _STATE_KEY_RE.fullmatch(self.state_key):
            raise ValueError("semantic_execution_state_key_invalid")
        if self.port < 1024 or self.port > 65535:
            raise ValueError("operator_bridge_port_out_of_range")
        if self.max_body_bytes < 256 or self.max_body_bytes > 1_048_576:
            raise ValueError("operator_bridge_body_limit_invalid")


def build_operator_bridge_server(
    config: OperatorBridgeServerConfig,
) -> OperatorBridgeHttpServer:
    config.validate()

    state_store = PostgresStateStore(
        config.postgres_dsn,
        state_key=config.state_key,
    )
    event_ledger = PostgresEventLedger(config.postgres_dsn)
    runtime = RuntimeCoordinator(
        state_store=state_store,
        event_ledger=event_ledger,
        telemetry=NoopTelemetry(),
        clock=SystemClock(),
    )
    # Fail closed if the authoritative state key was never initialized.
    runtime.snapshot()

    registry = ExecutorRegistry(initial_executor_profiles())
    materializer = DurableOperatorPacketMaterializer(
        runtime=runtime,
        registry=registry,
    )
    service = OperatorActionService(
        runtime=runtime,
        packet_materializer=materializer,
    )
    return build_operator_bridge_http_server(
        service=service,
        config=OperatorBridgeHttpConfig(
            expected_identity_header="Tailscale-User-Login",
            expected_identity_value=config.expected_tailscale_login,
            bind_host="127.0.0.1",
            port=config.port,
            max_body_bytes=config.max_body_bytes,
        ),
    )


def main() -> int:
    config = OperatorBridgeServerConfig.from_env()
    server = build_operator_bridge_server(config)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
