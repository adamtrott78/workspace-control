"""HTTP transport acceptance tests for the Operator Bridge backend."""
from __future__ import annotations

from contextlib import contextmanager
import http.client
import json
from pathlib import Path
import sys
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters.in_memory import (  # noqa: E402
    FakeClock,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
)
from workspace_semantic_execution.adapters.operator_bridge_http import (  # noqa: E402
    OperatorBridgeHttpConfig,
    build_operator_bridge_http_server,
)
from workspace_semantic_execution.application import (  # noqa: E402
    OperatorActionService,
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    SemanticPacketCompiler,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    OperatorAckMode,
    OperatorAction,
    OperatorActionState,
    OperatorActionType,
    OperatorHumanRequirement,
    OperatorPostLocalSuccess,
)

IDENTITY_HEADER = "Tailscale-User-Login"
IDENTITY = "operator@example.invalid"
PROCESS_ID = "http-leaf"
SLOT_ID = "instant-slot-http"
EXECUTOR = openai_chat_instant_current_profile()


def compiled_packet():
    return SemanticPacketCompiler().compile(
        PacketCompilationInput(
            process_id=PROCESS_ID,
            source_checkpoint="task@sha",
            objective="Execute one HTTP-transported bounded leaf.",
            constraints=("manual paste and submit only",),
            evidence_refs=("evidence:durable",),
            authority_refs=("scope:proposal-only",),
            allowed_actions=("report-result",),
            validator_contract="validator:typed-result-v1",
            next_safe_boundary="return typed result",
        ),
        executor=EXECUTOR,
    )


class StaticMaterializer:
    def __init__(self, packet):
        self.packet = packet

    def materialize(self, action):
        return self.packet


def service_and_runtime():
    runtime = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    runtime.initialize(
        DomainKernel.create_graph(
            [DomainKernel.create_process(PROCESS_ID)]
        )
    )
    packet = compiled_packet()
    broker = PersistentExecutorSessionBroker(runtime)
    broker.ensure_session(
        profile=EXECUTOR,
        slot_id=SLOT_ID,
        session_id="chat-session-http",
    )
    broker.bind(
        profile=EXECUTOR,
        slot_id=SLOT_ID,
        expected_session_generation=0,
        process_id=PROCESS_ID,
        process_generation=0,
        packet_sha256=packet.packet_sha256,
    )
    service = OperatorActionService(
        runtime=runtime,
        packet_materializer=StaticMaterializer(packet),
    )
    service.enqueue(
        OperatorAction(
            action_id="action:http/leaf",
            generation=0,
            action_type=OperatorActionType.SERVICE_EXISTING,
            status=OperatorActionState.QUEUED,
            priority_rank=10,
            queue_sequence=1,
            created_at="T0",
            task_id="task",
            reasoning_process_id=PROCESS_ID,
            process_generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            executor_id=EXECUTOR.executor_id,
            payload_ref=f"semantic-packet://{PROCESS_ID}/0",
            payload_sha256=packet.packet_sha256,
            human_requirement=(
                OperatorHumanRequirement.PASTE_AND_SUBMIT
            ),
            ack_mode=OperatorAckMode.DURABLE_EVENT,
            post_local_success=(
                OperatorPostLocalSuccess.AWAIT_DURABLE_ACK
            ),
        )
    )
    return service, runtime, broker, packet


@contextmanager
def running_server(service):
    server = build_operator_bridge_http_server(
        service=service,
        config=OperatorBridgeHttpConfig(
            expected_identity_header=IDENTITY_HEADER,
            expected_identity_value=IDENTITY,
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request_json(
    base_url,
    method,
    path,
    payload=None,
    *,
    identity=IDENTITY,
):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if identity is not None:
        headers[IDENTITY_HEADER] = identity
    request = Request(
        base_url + path,
        data=data,
        headers=headers,
        method=method,
    )
    with urlopen(request, timeout=2) as response:
        raw = response.read()
        return response.status, (
            None if not raw else json.loads(raw.decode("utf-8"))
        )


def request_chunked_json(
    base_url,
    path,
    payload,
):
    body = json.dumps(payload).encode("utf-8")
    parsed = urlparse(base_url)
    connection = http.client.HTTPConnection(
        parsed.hostname,
        parsed.port,
        timeout=2,
    )
    try:
        connection.request(
            "POST",
            path,
            body=(part for part in (body[:7], body[7:])),
            headers={
                IDENTITY_HEADER: IDENTITY,
                "Content-Type": "application/json",
            },
            encode_chunked=True,
        )
        response = connection.getresponse()
        raw = response.read()
        return response.status, (
            None if not raw else json.loads(raw.decode("utf-8"))
        )
    finally:
        connection.close()


class OperatorBridgeHttpTests(unittest.TestCase):
    def test_server_rejects_non_loopback_binding(self):
        service, *_ = service_and_runtime()
        with self.assertRaisesRegex(
            ValueError,
            "operator_bridge_http_must_bind_loopback",
        ):
            build_operator_bridge_http_server(
                service=service,
                config=OperatorBridgeHttpConfig(
                    expected_identity_header=IDENTITY_HEADER,
                    expected_identity_value=IDENTITY,
                    bind_host="0.0.0.0",
                ),
            )

    def test_missing_or_wrong_proxy_identity_fails_closed(self):
        service, *_ = service_and_runtime()
        with running_server(service) as base:
            for identity in (None, "wrong@example.invalid"):
                with self.assertRaises(HTTPError) as ctx:
                    request_json(
                        base,
                        "GET",
                        "/operator-bridge/v1/status",
                        identity=identity,
                    )
                self.assertEqual(ctx.exception.code, 403)

    def test_status_claim_revalidate_and_prepare_round_trip(self):
        service, _runtime, _broker, packet = service_and_runtime()
        with running_server(service) as base:
            status, body = request_json(
                base, "GET", "/operator-bridge/v1/status"
            )
            self.assertEqual(status, 200)
            self.assertEqual(
                body,
                {"readyManualCycles": 1, "sentUnconfirmed": 0},
            )
            status, claimed = request_json(
                base,
                "POST",
                "/operator-bridge/v1/actions/claim",
                {
                    "helperInstanceId": "windows-helper",
                    "claimId": "claim-http-1",
                    "claimedAt": "T1",
                    "expiresAt": "T2",
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(claimed["actionId"], "action:http/leaf")
            self.assertEqual(claimed["generation"], 0)
            self.assertEqual(claimed["workerSlotId"], SLOT_ID)
            self.assertEqual(claimed["sessionGeneration"], 0)
            self.assertEqual(
                claimed["actionType"], "SERVICE_EXISTING"
            )
            self.assertEqual(claimed["packetText"], packet.text)
            self.assertEqual(
                claimed["payloadSha256"], packet.packet_sha256
            )
            action_id = quote(claimed["actionId"], safe="")
            identity = {
                "generation": 0,
                "workerSlotId": SLOT_ID,
                "sessionGeneration": 0,
            }
            _, revalidated = request_json(
                base,
                "POST",
                f"/operator-bridge/v1/actions/{action_id}/revalidate",
                identity,
            )
            self.assertEqual(revalidated, {"valid": True})
            _, prepared = request_json(
                base,
                "POST",
                f"/operator-bridge/v1/actions/{action_id}/local-prepared",
                identity,
            )
            self.assertEqual(
                prepared["status"], "AWAITING_DURABLE_ACK"
            )
            _, status_body = request_json(
                base, "GET", "/operator-bridge/v1/status"
            )
            self.assertEqual(
                status_body,
                {"readyManualCycles": 0, "sentUnconfirmed": 1},
            )

    def test_chunked_json_claim_round_trip(self):
        service, _runtime, _broker, packet = service_and_runtime()
        with running_server(service) as base:
            status, claimed = request_chunked_json(
                base,
                "/operator-bridge/v1/actions/claim",
                {
                    "helperInstanceId": "windows-helper",
                    "claimId": "claim-chunked-1",
                    "claimedAt": "T1",
                    "expiresAt": "T2",
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(claimed["actionId"], "action:http/leaf")
            self.assertEqual(claimed["packetText"], packet.text)

    def test_chunked_json_body_limit_is_enforced(self):
        service, *_ = service_and_runtime()
        with running_server(service) as base:
            status, body = request_chunked_json(
                base,
                "/operator-bridge/v1/actions/claim",
                {
                    "helperInstanceId": "x" * 20_000,
                    "claimId": "claim-chunked-too-large",
                    "claimedAt": "T1",
                    "expiresAt": "T2",
                },
            )
            self.assertEqual(status, 413)
            self.assertEqual(body, {"error": "request_too_large"})

    def test_claim_no_work_returns_204(self):
        service, *_ = service_and_runtime()
        with running_server(service) as base:
            request_json(
                base,
                "POST",
                "/operator-bridge/v1/actions/claim",
                {
                    "helperInstanceId": "windows-helper",
                    "claimId": "claim-1",
                    "claimedAt": "T1",
                    "expiresAt": "T2",
                },
            )
            status, body = request_json(
                base,
                "POST",
                "/operator-bridge/v1/actions/claim",
                {
                    "helperInstanceId": "windows-helper",
                    "claimId": "claim-2",
                    "claimedAt": "T3",
                    "expiresAt": "T4",
                },
            )
            self.assertEqual(status, 204)
            self.assertIsNone(body)

    def test_unlisted_routes_and_oversized_body_fail_closed(self):
        service, *_ = service_and_runtime()
        with running_server(service) as base:
            with self.assertRaises(HTTPError) as ctx:
                request_json(
                    base,
                    "POST",
                    "/operator-bridge/v1/authority/grant",
                    {},
                )
            self.assertEqual(ctx.exception.code, 404)
            request = Request(
                base + "/operator-bridge/v1/actions/claim",
                data=b"x" * 20_000,
                headers={
                    IDENTITY_HEADER: IDENTITY,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with self.assertRaises(HTTPError) as ctx:
                urlopen(request, timeout=2)
            self.assertEqual(ctx.exception.code, 413)

    def test_local_failure_is_bounded(self):
        service, *_ = service_and_runtime()
        with running_server(service) as base:
            _, claimed = request_json(
                base,
                "POST",
                "/operator-bridge/v1/actions/claim",
                {
                    "helperInstanceId": "windows-helper",
                    "claimId": "claim-failure",
                    "claimedAt": "T1",
                    "expiresAt": "T2",
                },
            )
            action_id = quote(claimed["actionId"], safe="")
            _, failed = request_json(
                base,
                "POST",
                f"/operator-bridge/v1/actions/{action_id}/local-failure",
                {
                    "generation": 0,
                    "workerSlotId": SLOT_ID,
                    "sessionGeneration": 0,
                    "failureCode": "CLIPBOARD_FAILED",
                    "failureMessage": "bounded-local-failure",
                },
            )
            self.assertEqual(failed["status"], "FAILED_LOCAL")


if __name__ == "__main__":
    unittest.main()
