namespace WorkspaceControl.OperatorBridge.Windows;

public enum WorkloadDominantState
{
    BridgeOff,
    Ready,
    WaitingUnconfirmed,
    Idle
}

public sealed record WorkloadStatusSnapshot(
    int ReadyManualCycles,
    int SentUnconfirmed)
{
    public static WorkloadStatusSnapshot Empty { get; } = new(0, 0);
}

public sealed record WorkloadStatusPresentation(
    WorkloadDominantState State,
    string IconText,
    string Tooltip,
    string ReadyLabel,
    string SentUnconfirmedLabel)
{
    public static bool BecameReady(
        bool bridgeEnabled,
        WorkloadStatusSnapshot previous,
        WorkloadStatusSnapshot current)
    {
        ArgumentNullException.ThrowIfNull(previous);
        ArgumentNullException.ThrowIfNull(current);
        ValidateCounters(previous);
        ValidateCounters(current);

        return bridgeEnabled &&
            previous.ReadyManualCycles == 0 &&
            current.ReadyManualCycles > 0;
    }

    public static bool NoActionMayMinimize(WorkloadStatusSnapshot snapshot)
    {
        ArgumentNullException.ThrowIfNull(snapshot);
        ValidateCounters(snapshot);
        return snapshot.ReadyManualCycles == 0 && snapshot.SentUnconfirmed == 0;
    }

    public static WorkloadStatusPresentation Project(
        bool bridgeEnabled,
        WorkloadStatusSnapshot snapshot,
        string schedulerHotkey)
    {
        ArgumentNullException.ThrowIfNull(snapshot);
        ArgumentException.ThrowIfNullOrWhiteSpace(schedulerHotkey);

        ValidateCounters(snapshot);

        var readyLabel = $"Ready now: {snapshot.ReadyManualCycles}";
        var sentLabel = $"Sent / unconfirmed: {snapshot.SentUnconfirmed}";

        if (!bridgeEnabled)
        {
            return new(
                WorkloadDominantState.BridgeOff,
                "OFF",
                snapshot.ReadyManualCycles > 0
                    ? $"Bridge OFF; ready waiting: {snapshot.ReadyManualCycles}"
                    : "Bridge OFF",
                readyLabel,
                sentLabel);
        }

        if (snapshot.ReadyManualCycles > 0)
        {
            return new(
                WorkloadDominantState.Ready,
                snapshot.ReadyManualCycles > 99
                    ? "99+"
                    : snapshot.ReadyManualCycles.ToString(),
                $"Ready now: {snapshot.ReadyManualCycles}; {schedulerHotkey} to service next",
                readyLabel,
                sentLabel);
        }

        if (snapshot.SentUnconfirmed > 0)
        {
            return new(
                WorkloadDominantState.WaitingUnconfirmed,
                "W",
                "Waiting for durable acknowledgments",
                readyLabel,
                sentLabel);
        }

        return new(
            WorkloadDominantState.Idle,
            "0",
            "Nothing needs service",
            readyLabel,
            sentLabel);
    }

    private static void ValidateCounters(WorkloadStatusSnapshot snapshot)
    {
        if (snapshot.ReadyManualCycles < 0 || snapshot.SentUnconfirmed < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(snapshot),
                "Workload counters must be non-negative.");
        }
    }
}
