using System.Text.Json;
using WorkspaceControl.OperatorBridge.Contracts;

namespace WorkspaceControl.OperatorBridge.Contracts.Protocol;

public static class ProtocolValidator
{
    private static readonly HashSet<string> MessageTypes = new(StringComparer.Ordinal)
    {
        "HELLO", "HELLO_ACK", "BROWSER_COMMAND", "BROWSER_RESULT",
        "BROWSER_EVENT", "PING", "PONG", "PROTOCOL_ERROR"
    };
    private static readonly HashSet<string> BrowserOperations = new(StringComparer.Ordinal)
    {
        "ENSURE_WORKER_SURFACE", "CREATE_WORKER_BINDING", "ACTIVATE_WORKER_BINDING",
        "RELOAD_OR_RESTORE_WORKER_BINDING", "DISCARD_WORKER_BINDING",
        "CLOSE_WORKER_BINDING", "INVENTORY_MANAGED_BINDINGS"
    };
    private static readonly HashSet<string> BrowserEventTypes = new(StringComparer.Ordinal)
    {
        "ADAPTER_READY", "BINDING_CLOSED", "BINDING_DISCARDED",
        "BINDING_ACTIVATED", "ORIGIN_CLASS_CHANGED"
    };
    private static readonly HashSet<string> ForbiddenPropertyNames = new(StringComparer.OrdinalIgnoreCase)
    {
        "packet", "packet_text", "clipboard", "clipboard_content", "url", "raw_url",
        "path", "query", "fragment", "title", "favicon", "page_content", "output_text",
        "credential", "credentials", "token", "tokens", "cookie", "cookies", "password"
    };

    public static void Validate(ProtocolEnvelope envelope)
    {
        if (!string.Equals(envelope.ProtocolVersion, BrowserAdapterProtocol.Version, StringComparison.Ordinal))
            throw new ProtocolException("UNSUPPORTED_PROTOCOL_VERSION");
        if (!MessageTypes.Contains(envelope.MessageType))
            throw new ProtocolException("UNKNOWN_MESSAGE_TYPE");
        ValidateBoundedString(envelope.MessageId, "INVALID_MESSAGE_ID", true);
        ValidateBoundedString(envelope.RequestId, "INVALID_REQUEST_ID");
        ValidateBoundedString(envelope.CorrelationId, "INVALID_CORRELATION_ID");
        ValidateBoundedString(envelope.HelperInstanceId, "INVALID_HELPER_INSTANCE_ID");
        ValidateBoundedString(envelope.AdapterInstanceId, "INVALID_ADAPTER_INSTANCE_ID");
        if (envelope.SentAtMonotonicMs < 0 || double.IsNaN(envelope.SentAtMonotonicMs) || double.IsInfinity(envelope.SentAtMonotonicMs))
            throw new ProtocolException("INVALID_MONOTONIC_TIMESTAMP");
        if (envelope.Payload is { } payload) RejectForbiddenProperties(payload);

        switch (envelope.MessageType)
        {
            case "HELLO": ValidateHello(envelope); break;
            case "HELLO_ACK": ValidateHelloAck(envelope); break;
            case "BROWSER_COMMAND": ValidateBrowserCommand(envelope); break;
            case "BROWSER_RESULT": ValidateBrowserResult(envelope); break;
            case "BROWSER_EVENT": ValidateBrowserEvent(envelope); break;
            case "PING":
            case "PONG": ValidatePingPong(envelope); break;
            case "PROTOCOL_ERROR": ValidateProtocolError(envelope); break;
        }
    }

    private static void ValidateHello(ProtocolEnvelope envelope)
    {
        var payload = RequireObjectPayload(envelope);
        EnsureOnly(payload, "adapter_kind", "adapter_version", "supported_protocol_versions", "capabilities");
        var kind = RequireString(payload, "adapter_kind", 64);
        if (kind is not ("FIREFOX_EXTENSION" or "CUSTOM_SHELL" or "IN_MEMORY_SIMULATOR"))
            throw new ProtocolException("INVALID_ADAPTER_KIND");
        RequireString(payload, "adapter_version", 64);
        var supported = RequireArray(payload, "supported_protocol_versions");
        if (supported.GetArrayLength() is < 1 or > 8) throw new ProtocolException("INVALID_SUPPORTED_PROTOCOL_VERSIONS");
        foreach (var item in supported.EnumerateArray())
            if (item.ValueKind != JsonValueKind.String || string.IsNullOrWhiteSpace(item.GetString()))
                throw new ProtocolException("INVALID_SUPPORTED_PROTOCOL_VERSIONS");
        var capabilities = RequireProperty(payload, "capabilities");
        if (capabilities.ValueKind != JsonValueKind.Object) throw new ProtocolException("INVALID_CAPABILITIES");
        EnsureOnly(capabilities, "discard", "persistent_binding_metadata", "origin_classification", "profile_isolation");
        foreach (var name in new[] { "discard", "persistent_binding_metadata", "origin_classification", "profile_isolation" })
        {
            var value = RequireProperty(capabilities, name);
            if (value.ValueKind is not (JsonValueKind.True or JsonValueKind.False))
                throw new ProtocolException("INVALID_CAPABILITIES");
        }
    }

    private static void ValidateHelloAck(ProtocolEnvelope envelope)
    {
        var payload = RequireObjectPayload(envelope);
        EnsureOnly(payload, "accepted_protocol_version", "bridge_state");
        var accepted = RequireString(payload, "accepted_protocol_version", 16);
        if (!string.Equals(accepted, BrowserAdapterProtocol.Version, StringComparison.Ordinal))
            throw new ProtocolException("INVALID_HELLO_ACK_VERSION");
        var state = RequireString(payload, "bridge_state", 32);
        if (state is not ("ON" or "OFF" or "RECOVERING" or "BLOCKED"))
            throw new ProtocolException("INVALID_BRIDGE_STATE");
    }

    private static void ValidateBrowserCommand(ProtocolEnvelope envelope)
    {
        ValidateBoundedString(envelope.RequestId, "MISSING_REQUEST_ID", true);
        var payload = RequireObjectPayload(envelope);
        EnsureOnly(payload, "operation", "idempotency_key", "worker_slot_id", "session_generation", "expected_binding_generation");
        if (!BrowserOperations.Contains(RequireString(payload, "operation", 64)))
            throw new ProtocolException("UNKNOWN_BROWSER_OPERATION");
        RequireString(payload, "idempotency_key", 256);
    }

    private static void ValidateBrowserResult(ProtocolEnvelope envelope)
    {
        ValidateBoundedString(envelope.RequestId, "MISSING_REQUEST_ID", true);
        var payload = RequireObjectPayload(envelope);
        EnsureOnly(payload, "operation", "outcome", "normalized_error", "worker_slot_id", "session_generation", "binding_ref", "binding_generation", "origin_classification", "discarded", "active", "inventory");
        if (!BrowserOperations.Contains(RequireString(payload, "operation", 64)))
            throw new ProtocolException("UNKNOWN_BROWSER_OPERATION");
        var outcome = RequireString(payload, "outcome", 32);
        if (outcome is not ("APPLIED" or "NOT_APPLIED" or "UNKNOWN" or "REJECTED"))
            throw new ProtocolException("INVALID_BROWSER_OUTCOME");
    }

    private static void ValidateBrowserEvent(ProtocolEnvelope envelope)
    {
        var payload = RequireObjectPayload(envelope);
        EnsureOnly(payload, "event_type", "worker_slot_id", "session_generation", "binding_ref", "binding_generation", "origin_classification", "normalized_reason");
        if (!BrowserEventTypes.Contains(RequireString(payload, "event_type", 64)))
            throw new ProtocolException("UNKNOWN_BROWSER_EVENT");
    }

    private static void ValidatePingPong(ProtocolEnvelope envelope)
    {
        if (envelope.Payload is not { } payload) return;
        if (payload.ValueKind != JsonValueKind.Object) throw new ProtocolException("INVALID_PING_PAYLOAD");
        EnsureOnly(payload, "nonce");
        if (payload.TryGetProperty("nonce", out var nonce) &&
            (nonce.ValueKind != JsonValueKind.String || (nonce.GetString()?.Length ?? 0) > 128))
            throw new ProtocolException("INVALID_PING_NONCE");
    }

    private static void ValidateProtocolError(ProtocolEnvelope envelope)
    {
        var payload = RequireObjectPayload(envelope);
        EnsureOnly(payload, "code", "related_message_id");
        RequireString(payload, "code", 128);
    }

    private static JsonElement RequireObjectPayload(ProtocolEnvelope envelope)
    {
        if (envelope.Payload is not { } payload || payload.ValueKind != JsonValueKind.Object)
            throw new ProtocolException("MISSING_OR_INVALID_PAYLOAD");
        return payload;
    }
    private static JsonElement RequireProperty(JsonElement obj, string name)
    {
        if (!obj.TryGetProperty(name, out var value)) throw new ProtocolException($"MISSING_{name.ToUpperInvariant()}");
        return value;
    }
    private static JsonElement RequireArray(JsonElement obj, string name)
    {
        var value = RequireProperty(obj, name);
        if (value.ValueKind != JsonValueKind.Array) throw new ProtocolException($"INVALID_{name.ToUpperInvariant()}");
        return value;
    }
    private static string RequireString(JsonElement obj, string name, int maxLength)
    {
        var value = RequireProperty(obj, name);
        if (value.ValueKind != JsonValueKind.String) throw new ProtocolException($"INVALID_{name.ToUpperInvariant()}");
        var s = value.GetString();
        if (string.IsNullOrWhiteSpace(s) || s.Length > maxLength) throw new ProtocolException($"INVALID_{name.ToUpperInvariant()}");
        return s;
    }
    private static void ValidateBoundedString(string? value, string code, bool required = false)
    {
        if (value is null)
        {
            if (required) throw new ProtocolException(code);
            return;
        }
        if ((required && string.IsNullOrWhiteSpace(value)) || value.Length > 128) throw new ProtocolException(code);
    }
    private static void EnsureOnly(JsonElement obj, params string[] names)
    {
        var allowed = new HashSet<string>(names, StringComparer.Ordinal);
        foreach (var property in obj.EnumerateObject())
            if (!allowed.Contains(property.Name)) throw new ProtocolException("UNKNOWN_PAYLOAD_FIELD");
    }
    private static void RejectForbiddenProperties(JsonElement element)
    {
        if (element.ValueKind == JsonValueKind.Object)
        {
            foreach (var property in element.EnumerateObject())
            {
                if (ForbiddenPropertyNames.Contains(property.Name)) throw new ProtocolException("FORBIDDEN_CONTENT_FIELD");
                RejectForbiddenProperties(property.Value);
            }
        }
        else if (element.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in element.EnumerateArray()) RejectForbiddenProperties(item);
        }
    }
}
