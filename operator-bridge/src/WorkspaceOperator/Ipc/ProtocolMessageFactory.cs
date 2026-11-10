using System.Diagnostics;
using System.Text.Json;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Contracts;
using WorkspaceControl.OperatorBridge.Contracts.Protocol;

namespace WorkspaceControl.OperatorBridge.Ipc;

public static class ProtocolMessageFactory
{
    public static ProtocolEnvelope HelloAck(
        string helperInstanceId,
        string? correlationId,
        BridgeState bridgeState) =>
        Create(
            "HELLO_ACK",
            correlationId: correlationId,
            helperInstanceId: helperInstanceId,
            payload: new
            {
                accepted_protocol_version = BrowserAdapterProtocol.Version,
                bridge_state = bridgeState.IsEnabled ? "ON" : "OFF"
            });

    public static ProtocolEnvelope Pong(
        string helperInstanceId,
        string? correlationId,
        JsonElement? sourcePayload) =>
        Create(
            "PONG",
            correlationId: correlationId,
            helperInstanceId: helperInstanceId,
            payload: sourcePayload is { } payload &&
                     payload.ValueKind == JsonValueKind.Object &&
                     payload.TryGetProperty("nonce", out var nonce) &&
                     nonce.ValueKind == JsonValueKind.String
                ? new { nonce = nonce.GetString() }
                : new { });

    public static ProtocolEnvelope Error(
        string helperInstanceId,
        string code,
        string? relatedMessageId = null,
        string? correlationId = null) =>
        Create(
            "PROTOCOL_ERROR",
            correlationId: correlationId,
            helperInstanceId: helperInstanceId,
            payload: new
            {
                code,
                related_message_id = relatedMessageId
            });

    public static ProtocolEnvelope BrowserCommand(
        string helperInstanceId,
        string requestId,
        string correlationId,
        string operation,
        string idempotencyKey,
        BrowserTarget target,
        long? expectedBindingGeneration) =>
        new()
        {
            ProtocolVersion = BrowserAdapterProtocol.Version,
            MessageType = "BROWSER_COMMAND",
            MessageId = Guid.NewGuid().ToString("N"),
            RequestId = requestId,
            CorrelationId = correlationId,
            SentAtMonotonicMs =
                Stopwatch.GetTimestamp() * 1000.0 / Stopwatch.Frequency,
            HelperInstanceId = helperInstanceId,
            Payload = ProtocolJson.Payload(new
            {
                operation,
                idempotency_key = idempotencyKey,
                worker_slot_id = target.WorkerSlotId,
                session_generation = target.SessionGeneration,
                expected_binding_generation = expectedBindingGeneration
            })
        };

    private static ProtocolEnvelope Create(
        string messageType,
        string? correlationId,
        string helperInstanceId,
        object payload) =>
        new()
        {
            ProtocolVersion = BrowserAdapterProtocol.Version,
            MessageType = messageType,
            MessageId = Guid.NewGuid().ToString("N"),
            CorrelationId = correlationId,
            SentAtMonotonicMs =
                Stopwatch.GetTimestamp() * 1000.0 / Stopwatch.Frequency,
            HelperInstanceId = helperInstanceId,
            Payload = ProtocolJson.Payload(payload)
        };
}
