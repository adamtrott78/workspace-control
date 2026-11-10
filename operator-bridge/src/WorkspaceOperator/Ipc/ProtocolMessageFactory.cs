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
