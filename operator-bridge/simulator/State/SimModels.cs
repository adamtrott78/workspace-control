namespace WorkspaceControl.OperatorBridge.Simulator.State;

public enum SimActionStatus
{
    Queued,
    ClaimedLocal,
    LocalPrepared,
    AwaitingDurableAck,
    Acknowledged,
    Completed,
    FailedLocal,
    Blocked,
    Stale,
    Superseded
}

public enum SimContinuity
{
    NotEstablished,
    Trusted,
    Unknown,
    Lost
}

public enum SimSessionStatus
{
    Active,
    Idle,
    Discarded,
    ContinuityUnknown,
    RotateRequired,
    Lost,
    Retired
}

public sealed class SimAction
{
    public required string ActionId { get; init; }
    public required string ActionType { get; init; }
    public required string WorkerSlotId { get; init; }
    public required long SessionGeneration { get; init; }
    public required string ExpectedPayloadSha256 { get; init; }
    public SimActionStatus Status { get; set; } = SimActionStatus.Queued;
    public int ClaimCount { get; set; }
    public int ClipboardWrites { get; set; }
    public int BrowserEffects { get; set; }
}

public sealed class SimSession
{
    public required string WorkerSlotId { get; init; }
    public long Generation { get; set; }
    public SimContinuity Continuity { get; set; } = SimContinuity.NotEstablished;
    public SimSessionStatus Status { get; set; } = SimSessionStatus.Active;
    public bool BindingPresent { get; set; }
    public bool BindingAmbiguous { get; set; }
    public bool ExecutorCompatible { get; set; } = true;
    public string OriginClassification { get; set; } = "CHATGPT_ORIGIN";
    public string? LastAcknowledgedActionId { get; set; }
}
