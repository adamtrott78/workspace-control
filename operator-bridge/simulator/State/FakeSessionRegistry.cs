using WorkspaceControl.OperatorBridge.Simulator.Core;

namespace WorkspaceControl.OperatorBridge.Simulator.State;

public sealed class FakeSessionRegistry
{
    private readonly TraceRecorder _trace;
    private readonly Dictionary<string, SimSession> _sessions = new(StringComparer.Ordinal);
    private readonly HashSet<string> _appliedRecoveryIds = new(StringComparer.Ordinal);

    public FakeSessionRegistry(TraceRecorder trace)
    {
        _trace = trace;
    }

    public IReadOnlyCollection<SimSession> Sessions => _sessions.Values;

    public SimSession Add(
        string slot,
        long generation = 0,
        SimContinuity continuity = SimContinuity.Trusted,
        bool bindingPresent = true)
    {
        var session = new SimSession
        {
            WorkerSlotId = slot,
            Generation = generation,
            Continuity = continuity,
            Status = bindingPresent ? SimSessionStatus.Active : SimSessionStatus.Lost,
            BindingPresent = bindingPresent
        };
        _sessions[slot] = session;
        return session;
    }

    public SimSession? Get(string slot) =>
        _sessions.TryGetValue(slot, out var session) ? session : null;

    public bool IsCurrent(string slot, long generation) =>
        Get(slot) is { } session && session.Generation == generation;

    public void MarkUnknown(string slot, string reason)
    {
        var session = Get(slot);
        if (session is null)
        {
            return;
        }

        session.Continuity = SimContinuity.Unknown;
        session.Status = SimSessionStatus.ContinuityUnknown;
        _trace.Record(
            "session_registry",
            "CONTINUITY_UNKNOWN",
            workerSlotId: slot,
            generation: session.Generation,
            normalizedReason: reason);
    }

    public bool AdvanceGenerationOnce(string slot, string recoveryId)
    {
        var session = Get(slot);
        if (session is null)
        {
            return false;
        }

        var key = slot + "|" + recoveryId;
        if (!_appliedRecoveryIds.Add(key))
        {
            _trace.Record(
                "session_registry",
                "GENERATION_ADVANCE_DEDUPED",
                workerSlotId: slot,
                generation: session.Generation,
                normalizedReason: recoveryId);
            return false;
        }

        session.Generation++;
        session.Continuity = SimContinuity.Unknown;
        session.Status = SimSessionStatus.ContinuityUnknown;
        session.BindingPresent = false;
        _trace.Record(
            "session_registry",
            "GENERATION_ADVANCED",
            workerSlotId: slot,
            generation: session.Generation,
            normalizedReason: recoveryId);
        return true;
    }
}
