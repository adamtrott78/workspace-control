using System.Text.Json;
using System.Text.Json.Serialization;

namespace WorkspaceControl.OperatorBridge.Contracts.Protocol;

public sealed record ProtocolEnvelope
{
    [JsonPropertyName("protocol_version")]
    public required string ProtocolVersion { get; init; }

    [JsonPropertyName("message_type")]
    public required string MessageType { get; init; }

    [JsonPropertyName("message_id")]
    public required string MessageId { get; init; }

    [JsonPropertyName("request_id")]
    public string? RequestId { get; init; }

    [JsonPropertyName("correlation_id")]
    public string? CorrelationId { get; init; }

    [JsonPropertyName("sent_at_monotonic_ms")]
    public double SentAtMonotonicMs { get; init; }

    [JsonPropertyName("helper_instance_id")]
    public string? HelperInstanceId { get; init; }

    [JsonPropertyName("adapter_instance_id")]
    public string? AdapterInstanceId { get; init; }

    [JsonPropertyName("payload")]
    public JsonElement? Payload { get; init; }
}
