using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace WorkspaceControl.OperatorBridge.Simulator.Core;

public sealed record SimTraceEvent(
    long Sequence,
    long MonotonicMilliseconds,
    string Component,
    string EventType,
    string? ActionId = null,
    string? WorkerSlotId = null,
    long? Generation = null,
    string? PayloadSha256 = null,
    string? NormalizedReason = null);

public sealed class TraceRecorder
{
    private readonly VirtualClock _clock;
    private readonly List<SimTraceEvent> _events = [];

    public TraceRecorder(VirtualClock clock)
    {
        _clock = clock;
    }

    public IReadOnlyList<SimTraceEvent> Events => _events;

    public void Record(
        string component,
        string eventType,
        string? actionId = null,
        string? workerSlotId = null,
        long? generation = null,
        string? payloadSha256 = null,
        string? normalizedReason = null)
    {
        _events.Add(new SimTraceEvent(
            _events.Count + 1,
            _clock.MonotonicMilliseconds,
            component,
            eventType,
            actionId,
            workerSlotId,
            generation,
            payloadSha256,
            normalizedReason));
    }

    public string Sha256()
    {
        var json = JsonSerializer.Serialize(_events);
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(json));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }
}
