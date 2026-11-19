using WorkspaceControl.OperatorBridge.Simulator.Core;
using WorkspaceControl.OperatorBridge.Simulator.FakeWorker;
using WorkspaceControl.OperatorBridge.Simulator.Faults;
using WorkspaceControl.OperatorBridge.Simulator.State;

namespace WorkspaceControl.OperatorBridge.Simulator.Scenarios;

public sealed class SimulatorWorld
{
    public SimulatorWorld()
    {
        Trace = new TraceRecorder(Clock);
        Actions = new FakeActionStore(Trace);
        Sessions = new FakeSessionRegistry(Trace);
        DurableEvents = new FakeDurableEventStore(Actions, Sessions, Trace);
        Worker = new FakeWorkerService(Actions, Sessions, DurableEvents, Trace);
        Faults = new FaultInjector(Trace);
    }

    public VirtualClock Clock { get; } = new();
    public TraceRecorder Trace { get; }
    public FakeActionStore Actions { get; }
    public FakeSessionRegistry Sessions { get; }
    public FakeDurableEventStore DurableEvents { get; }
    public FakeWorkerService Worker { get; }
    public FaultInjector Faults { get; }

    public int ClipboardWriteCount { get; private set; }
    public int BrowserEffectCount { get; private set; }
    public int BrowserStartCount { get; private set; }
    public int FocusChangeCount { get; private set; }
    public int AutoResendCount { get; private set; }
    public int AuthAutomationCount { get; private set; }
    public bool ConsoleOpened { get; private set; }
    public bool RecoveryOpened { get; private set; }
    public bool BrowserAvailable { get; set; } = true;
    public bool AdapterConnected { get; set; } = true;
    public bool OrchestratorAvailable { get; set; } = true;
    public bool DispatchInFlight { get; set; }

    public SimAction Queue(
        string actionId,
        string actionType,
        string slot = "slot-1",
        long generation = 0,
        string? expectedPayloadSha256 = null)
    {
        if (Sessions.Get(slot) is null)
        {
            Sessions.Add(slot, generation, SimContinuity.Trusted, bindingPresent: true);
        }

        var action = new SimAction
        {
            ActionId = actionId,
            ActionType = actionType,
            WorkerSlotId = slot,
            SessionGeneration = generation,
            ExpectedPayloadSha256 =
                expectedPayloadSha256 ?? new string('a', 64)
        };
        Actions.Add(action);
        return action;
    }

    public SimAction? Dispatch()
    {
        if (DispatchInFlight)
        {
            Trace.Record("scenario", "DISPATCH_BUSY");
            return null;
        }

        DispatchInFlight = true;
        try
        {
            var action = Actions.ClaimNext(OrchestratorAvailable);
            if (action is null)
            {
                return null;
            }

            if (action.ActionType == "OPEN_JUDGMENT_GATE")
            {
                ConsoleOpened = true;
                action.Status = SimActionStatus.Completed;
                Trace.Record("scenario", "JUDGMENT_CONSOLE_OPENED", action.ActionId);
                return action;
            }

            if (action.ActionType == "OPEN_RECOVERY")
            {
                RecoveryOpened = true;
                action.Status = SimActionStatus.Blocked;
                Trace.Record("scenario", "RECOVERY_SURFACE_OPENED", action.ActionId);
                return action;
            }

            if (!BrowserAvailable || !AdapterConnected)
            {
                action.Status = SimActionStatus.Blocked;
                Trace.Record(
                    "scenario",
                    "BROWSER_EFFECT_BLOCKED",
                    action.ActionId,
                    action.WorkerSlotId,
                    action.SessionGeneration,
                    normalizedReason: BrowserAvailable
                        ? "ADAPTER_DISCONNECTED"
                        : "BROWSER_UNAVAILABLE");
                return action;
            }

            var session = Sessions.Get(action.WorkerSlotId);
            if (session is null ||
                session.Generation != action.SessionGeneration ||
                session.BindingAmbiguous ||
                !session.ExecutorCompatible)
            {
                action.Status = SimActionStatus.Blocked;
                Trace.Record(
                    "scenario",
                    "IDENTITY_BLOCKED",
                    action.ActionId,
                    action.WorkerSlotId,
                    action.SessionGeneration);
                return action;
            }

            if (action.ActionType is "DISCARD_SESSION" or "RETIRE_SESSION")
            {
                BrowserEffectCount++;
                action.BrowserEffects++;
                session.Status = action.ActionType == "DISCARD_SESSION"
                    ? SimSessionStatus.Discarded
                    : SimSessionStatus.Retired;
                action.Status = SimActionStatus.Completed;
                Trace.Record(
                    "scenario",
                    "LOCAL_MAINTENANCE_COMPLETED",
                    action.ActionId,
                    action.WorkerSlotId,
                    action.SessionGeneration);
                return action;
            }

            if (Faults.IsEnabled("HELPER_CRASH_BEFORE_EFFECT"))
            {
                Trace.Record("scenario", "HELPER_CRASH_BEFORE_EFFECT", action.ActionId);
                return action;
            }

            if (action.ActionType == "CREATE_AND_SERVICE")
            {
                if (session.BindingPresent)
                {
                    action.Status = SimActionStatus.Blocked;
                    Trace.Record("scenario", "CREATE_BLOCKED_EXISTING_BINDING", action.ActionId);
                    return action;
                }

                BrowserStartCount++;
                BrowserEffectCount++;
                action.BrowserEffects++;
                session.BindingPresent = true;
                session.Status = SimSessionStatus.Active;

                if (Faults.IsEnabled("UNKNOWN_CREATE"))
                {
                    session.BindingAmbiguous = true;
                    action.Status = SimActionStatus.Blocked;
                    Trace.Record("scenario", "CREATE_OUTCOME_UNKNOWN", action.ActionId);
                    return action;
                }
            }
            else
            {
                if (!session.BindingPresent)
                {
                    action.Status = SimActionStatus.Blocked;
                    Trace.Record("scenario", "MANAGED_BINDING_MISSING", action.ActionId);
                    return action;
                }

                BrowserEffectCount++;
                action.BrowserEffects++;
                if (action.ActionType == "RESTORE_AND_SERVICE")
                {
                    session.Status = SimSessionStatus.Active;
                }
            }

            if (Faults.IsEnabled("STALE_BEFORE_CLIPBOARD"))
            {
                Actions.MarkStale(action);
                return action;
            }

            if (Faults.IsEnabled("CLIPBOARD_FAIL"))
            {
                Actions.MarkFailedLocal(action, "CLIPBOARD_WRITE_FAILED");
                return action;
            }

            ClipboardWriteCount++;
            action.ClipboardWrites++;
            Trace.Record(
                "scenario",
                "CLIPBOARD_WRITTEN",
                action.ActionId,
                action.WorkerSlotId,
                action.SessionGeneration,
                action.ExpectedPayloadSha256);

            if (Faults.IsEnabled("HELPER_CRASH_AFTER_CLIPBOARD"))
            {
                Trace.Record("scenario", "HELPER_CRASH_AFTER_CLIPBOARD", action.ActionId);
                return action;
            }

            FocusChangeCount++;
            Actions.MarkLocalPrepared(action);
            return action;
        }
        finally
        {
            DispatchInFlight = false;
        }
    }

    public bool HumanSubmit(SimAction action, string? payloadSha256 = null) =>
        Worker.SIM_HUMAN_SUBMIT(
            action.ActionId,
            action.WorkerSlotId,
            action.SessionGeneration,
            payloadSha256 ?? action.ExpectedPayloadSha256);

    public void Advance(long milliseconds)
    {
        Clock.Advance(milliseconds);
        Trace.Record("virtual_clock", "ADVANCED", normalizedReason: milliseconds.ToString());
    }

    public void RecordNoAutoResend() =>
        Trace.Record("scenario", "NO_AUTO_RESEND");

    public void FreezeAuthDomain(string slot)
    {
        Sessions.MarkUnknown(slot, "AUTH_REFRESH_INVALIDATED");
        Trace.Record("scenario", "AUTH_DOMAIN_FROZEN", workerSlotId: slot);
    }

    public void MarkManualAuthBoundary() =>
        Trace.Record("scenario", "MANUAL_AUTH_REQUIRED");

    public void ProveNoAuthAutomation()
    {
        AuthAutomationCount = 0;
        Trace.Record("scenario", "NO_AUTH_AUTOMATION");
    }

    public void ProveNoAutoResend()
    {
        AutoResendCount = 0;
        Trace.Record("scenario", "NO_AUTO_RESEND");
    }
}
