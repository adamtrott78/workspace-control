namespace WorkspaceControl.OperatorBridge.Application;

public enum RecoveryScope
{
    ActionScoped,
    SessionScoped,
    AuthDomainScoped,
    LocalBridgeGlobal
}

public enum RecoveryStatus
{
    Reconciling,
    AwaitingManualAuth,
    Rebuilding,
    ReadyToResume,
    Blocked,
    Healthy
}

public enum RecoverySignal
{
    AuthNavigationDetected,
    AuthReturnOriginObserved,
    OperatorReportedAuthRefresh,
    ManagedTabClosed,
    FirefoxConnectionLost,
    HelperInstanceRestarted,
    OrchestratorUnreachable,
    BindingAmbiguous,
    SystemResumeOrHelperColdStart,
    ExecutorIdentityUnproven
}

public sealed record RecoverySessionRef(
    string WorkerSlotId,
    long SessionGeneration);

public sealed record RecoveryReconciliationResult(
    IReadOnlyList<RecoverySessionRef> SessionsRequiringGenerationAdvance);

public sealed record RecoveryAdvanceResult(
    bool Applied,
    long NewGeneration);

public sealed record BrowserInventoryEntry(
    string WorkerSlotId,
    long SessionGeneration,
    string BindingRef,
    long BindingGeneration,
    string? OriginClassification,
    bool Discarded,
    bool Active);

public sealed class RecoveryIncident
{
    public required string RecoveryId { get; init; }

    public required RecoveryScope Scope { get; init; }

    public RecoveryStatus Status { get; set; } = RecoveryStatus.Reconciling;

    public required string TriggerSignal { get; init; }

    public List<RecoverySessionRef> AffectedSessions { get; init; } = [];

    public List<RecoverySessionRef> PendingGenerationAdvances { get; set; } = [];

    public Dictionary<string, long> ReplacementGenerations { get; init; } =
        new(StringComparer.Ordinal);

    public List<string> CompletedSteps { get; init; } = [];

    public bool ManualAuthReturned { get; set; }
}
