using WorkspaceControl.OperatorBridge.Simulator.Core;

namespace WorkspaceControl.OperatorBridge.Simulator.State;

public sealed class FakeActionStore
{
    private readonly TraceRecorder _trace;
    private readonly List<SimAction> _actions = [];

    public FakeActionStore(TraceRecorder trace)
    {
        _trace = trace;
    }

    public IReadOnlyList<SimAction> Actions => _actions;

    public void Add(SimAction action) => _actions.Add(action);

    public SimAction? ClaimNext(bool orchestratorAvailable = true)
    {
        if (!orchestratorAvailable)
        {
            _trace.Record("action_store", "CLAIM_BLOCKED", normalizedReason: "ORCHESTRATOR_UNAVAILABLE");
            return null;
        }

        var action = _actions.FirstOrDefault(item => item.Status == SimActionStatus.Queued);
        if (action is null)
        {
            _trace.Record("action_store", "NO_READY_ACTION");
            return null;
        }

        action.Status = SimActionStatus.ClaimedLocal;
        action.ClaimCount++;
        _trace.Record(
            "action_store",
            "CLAIMED_LOCAL",
            action.ActionId,
            action.WorkerSlotId,
            action.SessionGeneration,
            action.ExpectedPayloadSha256);
        return action;
    }

    public bool MarkLocalPrepared(SimAction action)
    {
        if (action.Status != SimActionStatus.ClaimedLocal)
        {
            return false;
        }

        action.Status = SimActionStatus.AwaitingDurableAck;
        _trace.Record(
            "action_store",
            "AWAITING_DURABLE_ACK",
            action.ActionId,
            action.WorkerSlotId,
            action.SessionGeneration,
            action.ExpectedPayloadSha256);
        return true;
    }

    public bool MarkLocalCompleted(SimAction action)
    {
        if (action.Status != SimActionStatus.ClaimedLocal)
        {
            return false;
        }

        action.Status = SimActionStatus.Completed;
        _trace.Record(
            "action_store",
            "COMPLETED_LOCAL",
            action.ActionId,
            action.WorkerSlotId,
            action.SessionGeneration);
        return true;
    }

    public void MarkFailedLocal(SimAction action, string reason)
    {
        action.Status = SimActionStatus.FailedLocal;
        _trace.Record(
            "action_store",
            "FAILED_LOCAL",
            action.ActionId,
            action.WorkerSlotId,
            action.SessionGeneration,
            normalizedReason: reason);
    }

    public void MarkStale(SimAction action)
    {
        action.Status = SimActionStatus.Stale;
        _trace.Record(
            "action_store",
            "STALE",
            action.ActionId,
            action.WorkerSlotId,
            action.SessionGeneration);
    }

    public void Supersede(SimAction action)
    {
        if (action.Status is SimActionStatus.Completed or SimActionStatus.Superseded)
        {
            return;
        }

        action.Status = SimActionStatus.Superseded;
        _trace.Record(
            "action_store",
            "SUPERSEDED",
            action.ActionId,
            action.WorkerSlotId,
            action.SessionGeneration);
    }

    public bool ApplyAck(SimAction action)
    {
        if (action.Status == SimActionStatus.Completed)
        {
            return false;
        }

        if (action.Status != SimActionStatus.AwaitingDurableAck)
        {
            return false;
        }

        action.Status = SimActionStatus.Acknowledged;
        _trace.Record(
            "action_store",
            "ACKNOWLEDGED",
            action.ActionId,
            action.WorkerSlotId,
            action.SessionGeneration);
        action.Status = SimActionStatus.Completed;
        _trace.Record(
            "action_store",
            "COMPLETED",
            action.ActionId,
            action.WorkerSlotId,
            action.SessionGeneration);
        return true;
    }
}
