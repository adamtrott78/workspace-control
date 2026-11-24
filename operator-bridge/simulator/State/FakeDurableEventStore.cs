using WorkspaceControl.OperatorBridge.Simulator.Core;

namespace WorkspaceControl.OperatorBridge.Simulator.State;

public sealed record SimDurableEvent(
    string EventId,
    string ActionId,
    string WorkerSlotId,
    long Generation,
    string EventType);

public enum DurableEventDisposition
{
    Applied,
    Duplicate,
    StaleGeneration,
    UnknownAction,
    NotAwaitingAck
}

public sealed class FakeDurableEventStore
{
    private readonly FakeActionStore _actions;
    private readonly FakeSessionRegistry _sessions;
    private readonly TraceRecorder _trace;
    private readonly HashSet<string> _eventIds = new(StringComparer.Ordinal);
    private readonly List<SimDurableEvent> _events = [];

    public FakeDurableEventStore(
        FakeActionStore actions,
        FakeSessionRegistry sessions,
        TraceRecorder trace)
    {
        _actions = actions;
        _sessions = sessions;
        _trace = trace;
    }

    public IReadOnlyList<SimDurableEvent> Events => _events;

    public DurableEventDisposition Append(SimDurableEvent durableEvent)
    {
        _events.Add(durableEvent);

        if (!_eventIds.Add(durableEvent.EventId))
        {
            _trace.Record(
                "durable_event_store",
                "DUPLICATE_EVENT",
                durableEvent.ActionId,
                durableEvent.WorkerSlotId,
                durableEvent.Generation);
            return DurableEventDisposition.Duplicate;
        }

        var action = _actions.Actions.FirstOrDefault(item =>
            item.ActionId == durableEvent.ActionId);
        if (action is null)
        {
            return DurableEventDisposition.UnknownAction;
        }

        if (!_sessions.IsCurrent(
                durableEvent.WorkerSlotId,
                durableEvent.Generation) ||
            action.SessionGeneration != durableEvent.Generation)
        {
            _trace.Record(
                "durable_event_store",
                "STALE_OLD_GENERATION_EVIDENCE",
                durableEvent.ActionId,
                durableEvent.WorkerSlotId,
                durableEvent.Generation);
            return DurableEventDisposition.StaleGeneration;
        }

        if (!_actions.ApplyAck(action))
        {
            return DurableEventDisposition.NotAwaitingAck;
        }

        var session = _sessions.Get(durableEvent.WorkerSlotId);
        if (session is not null)
        {
            session.Continuity = SimContinuity.Trusted;
            session.Status = SimSessionStatus.Active;
            session.LastAcknowledgedActionId = action.ActionId;
        }

        return DurableEventDisposition.Applied;
    }
}
