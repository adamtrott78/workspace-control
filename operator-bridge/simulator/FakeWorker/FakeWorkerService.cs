using WorkspaceControl.OperatorBridge.Simulator.Core;
using WorkspaceControl.OperatorBridge.Simulator.State;

namespace WorkspaceControl.OperatorBridge.Simulator.FakeWorker;

public sealed class FakeWorkerService
{
    private readonly FakeActionStore _actions;
    private readonly FakeSessionRegistry _sessions;
    private readonly FakeDurableEventStore _events;
    private readonly TraceRecorder _trace;
    private int _eventSequence;

    public FakeWorkerService(
        FakeActionStore actions,
        FakeSessionRegistry sessions,
        FakeDurableEventStore events,
        TraceRecorder trace)
    {
        _actions = actions;
        _sessions = sessions;
        _events = events;
        _trace = trace;
    }

    public bool SIM_HUMAN_SUBMIT(
        string actionId,
        string workerSlotId,
        long generation,
        string payloadSha256)
    {
        var action = _actions.Actions.FirstOrDefault(item =>
            item.ActionId == actionId);
        if (action is null ||
            action.WorkerSlotId != workerSlotId ||
            action.SessionGeneration != generation ||
            !_sessions.IsCurrent(workerSlotId, generation) ||
            action.Status != SimActionStatus.AwaitingDurableAck)
        {
            _trace.Record(
                "fake_worker",
                "SIM_SUBMIT_REJECTED",
                actionId,
                workerSlotId,
                generation,
                payloadSha256,
                "IDENTITY_OR_STATE_MISMATCH");
            return false;
        }

        if (!string.Equals(
                action.ExpectedPayloadSha256,
                payloadSha256,
                StringComparison.Ordinal))
        {
            _trace.Record(
                "fake_worker",
                "PAYLOAD_HASH_MISMATCH",
                actionId,
                workerSlotId,
                generation,
                payloadSha256);
            return false;
        }

        _trace.Record(
            "fake_worker",
            "SIM_HUMAN_SUBMIT",
            actionId,
            workerSlotId,
            generation,
            payloadSha256);

        var disposition = _events.Append(new SimDurableEvent(
            $"worker-{++_eventSequence:D4}",
            actionId,
            workerSlotId,
            generation,
            "WORKER_TRANSITION"));

        return disposition == DurableEventDisposition.Applied;
    }
}
