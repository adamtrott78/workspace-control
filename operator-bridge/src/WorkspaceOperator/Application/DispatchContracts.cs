namespace WorkspaceControl.OperatorBridge.Application;

public sealed record ActionIdentity(
    string ActionId,
    string WorkerSlotId,
    long SessionGeneration);

public enum OperatorActionType
{
    ServiceExisting,
    CreateAndService,
    RestoreAndService,
    DiscardSession,
    RetireSession,
    OpenJudgmentGate,
    OpenRecovery
}

public sealed record OperatorAction(
    ActionIdentity Identity,
    string PacketText,
    string PayloadRef,
    string PayloadSha256,
    OperatorActionType ActionType = OperatorActionType.ServiceExisting);

public sealed record BrowserTarget(
    string WorkerSlotId,
    long SessionGeneration);

public enum BrowserOutcome
{
    Applied,
    NotApplied,
    Unknown,
    Rejected
}

public sealed record BrowserResult(
    BrowserOutcome Outcome,
    string? NormalizedError = null)
{
    public bool IsApplied => Outcome == BrowserOutcome.Applied;

    public static BrowserResult Applied() => new(BrowserOutcome.Applied);
}

public enum DispatchOutcome
{
    Disabled,
    Busy,
    NoAction,
    BrowserPrepareFailed,
    BrowserMaintenanceFailed,
    Stale,
    ClipboardFailed,
    BrowserFocusFailed,
    LocalPrepared,
    LocalCompleted,
    JudgmentGateOpened,
    RecoveryOpened,
    Failed
}

public sealed record DispatchResult(
    DispatchOutcome Outcome,
    string? ActionId = null,
    string? NormalizedError = null);
