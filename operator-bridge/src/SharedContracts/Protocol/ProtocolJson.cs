using System.Text.Json;
using System.Text.Json.Serialization;
using WorkspaceControl.OperatorBridge.Contracts;

namespace WorkspaceControl.OperatorBridge.Contracts.Protocol;

public static class ProtocolJson
{
    private static readonly JsonSerializerOptions Options = new()
    {
        PropertyNameCaseInsensitive = false,
        UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
        WriteIndented = false
    };

    public static ProtocolEnvelope Parse(ReadOnlySpan<byte> utf8Json)
    {
        if (utf8Json.Length is <= 0 or > BrowserAdapterProtocol.MaxFrameBytes)
            throw new ProtocolException("INVALID_FRAME_SIZE");

        ProtocolEnvelope? envelope;
        try
        {
            envelope = JsonSerializer.Deserialize<ProtocolEnvelope>(utf8Json, Options);
        }
        catch (JsonException)
        {
            throw new ProtocolException("MALFORMED_OR_UNKNOWN_JSON");
        }

        if (envelope is null)
            throw new ProtocolException("MALFORMED_OR_UNKNOWN_JSON");

        ProtocolValidator.Validate(envelope);
        return envelope;
    }

    public static byte[] Serialize(ProtocolEnvelope envelope)
    {
        ProtocolValidator.Validate(envelope);
        var bytes = JsonSerializer.SerializeToUtf8Bytes(envelope, Options);
        if (bytes.Length > BrowserAdapterProtocol.MaxFrameBytes)
            throw new ProtocolException("FRAME_TOO_LARGE");
        return bytes;
    }

    public static JsonElement Payload(object value) =>
        JsonSerializer.SerializeToElement(value, Options);
}
