#!/usr/bin/env python3
"""Exact-host fake-worker transport acceptance for November Integrated v0.

This harness performs no model inference and no browser automation. It creates
one unique Postgres-backed semantic process, serves the production Operator
Bridge backend on loopback, drives status/claim/revalidate/local-prepared
through either loopback or a pre-reviewed private reverse-proxy URL, injects
one immutable fake worker-result candidate, independently validates it, and
requires the final durable process/action/session state to be complete/ready.

When --base-url is supplied, the client deliberately does NOT inject
Tailscale-User-Login; the reviewed proxy must provide that identity header.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import sys
from threading import Thread
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    ImmutableWorkerResultCandidate,
    PostgresEventLedger,
    PostgresStateStore,
    RecordingTelemetry,
    WorkerResultCandidateAdapter,
)
from workspace_semantic_execution.application import (  # noqa: E402
    ExecutorRegistry,
    OperatorDispatchPlanner,
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    WorkerResultIntakeService,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    ExecutorSessionState,
    OperatorActionState,
    ProcessState,
    ValidationResult,
)
from workspace_semantic_execution.operator_bridge_server import (  # noqa: E402
    OperatorBridgeServerConfig,
    build_operator_bridge_server,
)


IDENTITY_HEADER = "Tailscale-User-Login"
PROFILE = openai_chat_instant_current_profile()
VALIDATOR_ID = "validator:live-fake-worker-v1"
CONTRACT = {
    "schema": "workspace-semantic-live-fake-worker-transport.v1",
    "model_inference": False,
    "browser_automation": False,
    "gpu_required": False,
    "backend_bind": "127.0.0.1",
    "remote_identity_rule": (
        "client omits Tailscale-User-Login; reviewed private proxy must inject it"
    ),
    "required_flow": [
        "status_ready_1",
        "claim_exact_packet",
        "revalidate_true",
        "local_prepared_awaiting_ack",
        "immutable_fake_candidate_intake",
        "independent_validator_pass",
        "process_completed",
        "operator_action_completed",
        "session_ready",
        "status_ready_0_sent_0",
    ],
}


class AcceptanceValidator:
    def __init__(self) -> None:
        self.packet_sha256: str | None = None

    def validate(self, publication, packet_source):
        self.packet_sha256 = packet_source.packet_sha256
        return ValidationResult(
            validator_id=VALIDATOR_ID,
            passed=True,
            evidence_ref="acceptance:live-fake-worker-validator-pass",
            observed_at="T5",
        )


def _json_request(
    base_url: str,
    method: str,
    path: str,
    *,
    payload: dict | None = None,
    identity: str | None = None,
) -> tuple[int, dict | None]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if identity is not None:
        headers[IDENTITY_HEADER] = identity
    request = Request(
        base_url.rstrip("/") + path,
        data=data,
        headers=headers,
        method=method,
    )
    with urlopen(request, timeout=5) as response:
        raw = response.read()
        return response.status, (
            None if not raw else json.loads(raw.decode("utf-8"))
        )


def _free_loopback_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = int(probe.getsockname()[1])
    if port < 1024:
        raise RuntimeError("unexpected_privileged_ephemeral_port")
    return port


def _required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"{name}:required")
    return value


def run_acceptance(
    *,
    postgres_dsn: str,
    expected_tailscale_login: str,
    base_url: str | None,
    serve_port: int | None,
) -> dict[str, object]:
    token = uuid.uuid4().hex
    state_key = f"live-fake-worker:{token}"
    process_id = f"live-fake-worker-process:{token}"
    slot_id = f"live-fake-worker-slot:{token}"
    action_id = f"action:live-fake-worker:{token}"
    target_ref = (
        "github-candidate://adamtrott78/workspace-control/"
        f"worker-results/candidates/live-fake-worker-{token}.json"
    )

    runtime1 = RuntimeCoordinator(
        state_store=PostgresStateStore(
            postgres_dsn,
            state_key=state_key,
        ),
        event_ledger=PostgresEventLedger(postgres_dsn),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    runtime1.initialize(
        DomainKernel.create_graph(
            [DomainKernel.create_process(process_id)]
        )
    )
    registry = ExecutorRegistry((PROFILE,))
    PersistentExecutorSessionBroker(runtime1).ensure_session(
        profile=PROFILE,
        slot_id=slot_id,
        session_id=f"live-fake-worker-session:{token}",
    )
    planned = OperatorDispatchPlanner(
        runtime=runtime1,
        registry=registry,
    ).plan_service_existing(
        task_id="workspace-semantic-execution-migration-v1",
        action_id=action_id,
        action_generation=0,
        process_id=process_id,
        process_generation=0,
        worker_slot_id=slot_id,
        session_generation=0,
        executor_id=PROFILE.executor_id,
        packet_input=PacketCompilationInput(
            process_id=process_id,
            source_checkpoint="live-fake-worker@exact-host",
            objective=(
                "Complete one account-free exact-host fake-worker "
                "transport acceptance."
            ),
            constraints=(
                "no model inference",
                "no browser automation",
                "candidate-only result publication",
            ),
            evidence_refs=("acceptance:exact-host",),
            authority_refs=("scope:proposal-only",),
            allowed_actions=("publish-candidate-result",),
            validator_contract=VALIDATOR_ID,
            output_schema="WORKER_RESULT_V1",
            next_safe_boundary="publish immutable fake candidate",
        ),
        priority_rank=1,
        queue_sequence=1,
        created_at="T0",
        result_publication_target_ref=target_ref,
    )

    port = serve_port if serve_port is not None else _free_loopback_port()
    server = build_operator_bridge_server(
        OperatorBridgeServerConfig(
            postgres_dsn=postgres_dsn,
            expected_tailscale_login=expected_tailscale_login,
            state_key=state_key,
            port=port,
        )
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    route = (
        base_url.rstrip("/")
        if base_url
        else f"http://127.0.0.1:{port}"
    )
    request_identity = None if base_url else expected_tailscale_login
    try:
        _, initial = _json_request(
            route,
            "GET",
            "/operator-bridge/v1/status",
            identity=request_identity,
        )
        if initial != {
            "readyManualCycles": 1,
            "sentUnconfirmed": 0,
        }:
            raise RuntimeError(
                f"initial_status_mismatch:{initial!r}"
            )

        _, claimed = _json_request(
            route,
            "POST",
            "/operator-bridge/v1/actions/claim",
            identity=request_identity,
            payload={
                "helperInstanceId": "live-fake-worker",
                "claimId": f"claim:{token}",
                "claimedAt": "T1",
                "expiresAt": "T2",
            },
        )
        if not isinstance(claimed, dict):
            raise RuntimeError("claim_response_missing")
        if claimed.get("actionId") != action_id:
            raise RuntimeError("claim_action_id_mismatch")
        if claimed.get("payloadSha256") != planned.packet.packet_sha256:
            raise RuntimeError("claim_packet_sha_mismatch")
        if claimed.get("packetText") != planned.packet.text:
            raise RuntimeError("claim_packet_text_mismatch")

        action_path = quote(action_id, safe="")
        binding = {
            "generation": 0,
            "workerSlotId": slot_id,
            "sessionGeneration": 0,
        }
        _, revalidated = _json_request(
            route,
            "POST",
            f"/operator-bridge/v1/actions/{action_path}/revalidate",
            identity=request_identity,
            payload=binding,
        )
        if revalidated != {"valid": True}:
            raise RuntimeError(
                f"revalidate_failed:{revalidated!r}"
            )

        _, prepared = _json_request(
            route,
            "POST",
            f"/operator-bridge/v1/actions/{action_path}/local-prepared",
            identity=request_identity,
            payload=binding,
        )
        if not isinstance(prepared, dict) or (
            prepared.get("status") != "AWAITING_DURABLE_ACK"
        ):
            raise RuntimeError(
                f"local_prepared_failed:{prepared!r}"
            )

        contract = planned.packet_source.result_publication
        if contract is None:
            raise RuntimeError("result_publication_contract_missing")
        candidate_bytes = json.dumps(
            {
                "publication_id": contract.publication_id,
                "action_id": action_id,
                "action_generation": 0,
                "process_id": process_id,
                "process_generation": 0,
                "executor_id": PROFILE.executor_id,
                "worker_slot_id": slot_id,
                "session_generation": 0,
                "packet_sha256": planned.packet.packet_sha256,
                "kind": "RESULT",
                "observed_at": "T4",
                "result_payload_ref": (
                    "acceptance://live-fake-worker/result"
                ),
                "result_payload_sha256": "e" * 64,
                "evidence_refs": [
                    "acceptance://live-fake-worker/evidence"
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        runtime2 = RuntimeCoordinator(
            state_store=PostgresStateStore(
                postgres_dsn,
                state_key=state_key,
            ),
            event_ledger=PostgresEventLedger(postgres_dsn),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(seconds=10),
        )
        validator = AcceptanceValidator()
        outcome = WorkerResultCandidateAdapter(
            intake=WorkerResultIntakeService(
                runtime=runtime2,
                validators={VALIDATOR_ID: validator},
            )
        ).ingest(
            ImmutableWorkerResultCandidate(
                target_ref=target_ref,
                immutable_revision="f" * 40,
                raw_bytes=candidate_bytes,
            )
        )
        if outcome.process_state != ProcessState.COMPLETED:
            raise RuntimeError("candidate_intake_not_completed")
        if validator.packet_sha256 != planned.packet.packet_sha256:
            raise RuntimeError("validator_packet_sha_mismatch")

        graph = PostgresStateStore(
            postgres_dsn,
            state_key=state_key,
        ).load().graph
        if graph.processes[process_id].state != ProcessState.COMPLETED:
            raise RuntimeError("durable_process_not_completed")
        if (
            graph.operator_actions[action_id].status
            != OperatorActionState.COMPLETED
        ):
            raise RuntimeError("durable_action_not_completed")
        if (
            graph.executor_sessions[slot_id].state
            != ExecutorSessionState.READY
        ):
            raise RuntimeError("durable_session_not_ready")

        _, final = _json_request(
            route,
            "GET",
            "/operator-bridge/v1/status",
            identity=request_identity,
        )
        if final != {
            "readyManualCycles": 0,
            "sentUnconfirmed": 0,
        }:
            raise RuntimeError(
                f"final_status_mismatch:{final!r}"
            )

        return {
            **CONTRACT,
            "result": "PASS",
            "route_mode": (
                "reviewed_private_proxy"
                if base_url
                else "loopback_control"
            ),
            "state_key": state_key,
            "process_id": process_id,
            "action_id": action_id,
            "packet_sha256": planned.packet.packet_sha256,
            "publication_id": contract.publication_id,
            "immutable_revision": "f" * 40,
            "final_process_state": "COMPLETED",
            "final_action_state": "COMPLETED",
            "final_session_state": "READY",
            "final_status": final,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument(
        "--describe",
        action="store_true",
        help="print the content-free acceptance contract only",
    )
    result.add_argument(
        "--base-url",
        help=(
            "reviewed private proxy URL; when set, the client omits "
            "the Tailscale identity header and requires proxy injection"
        ),
    )
    result.add_argument(
        "--serve-port",
        type=int,
        help=(
            "loopback backend port. Required to match the reviewed "
            "private route when --base-url is used."
        ),
    )
    return result


def main() -> int:
    args = parser().parse_args()
    if args.describe:
        print(json.dumps(CONTRACT, sort_keys=True))
        return 0
    if args.base_url and args.serve_port is None:
        raise SystemExit("--serve-port is required with --base-url")
    if args.serve_port is not None and not (
        1024 <= args.serve_port <= 65535
    ):
        raise SystemExit("--serve-port must be 1024..65535")

    report = run_acceptance(
        postgres_dsn=_required_env(
            "SEMANTIC_EXECUTION_POSTGRES_DSN"
        ),
        expected_tailscale_login=_required_env(
            "WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN"
        ),
        base_url=args.base_url,
        serve_port=args.serve_port,
    )
    print(
        "LIVE_FAKE_WORKER_TRANSPORT="
        + json.dumps(
            report,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
