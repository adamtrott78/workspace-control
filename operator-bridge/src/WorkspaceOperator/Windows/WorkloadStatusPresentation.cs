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
    public static WorkloadStatusPresentation Project(
        bool bridgeEnabled,
        WorkloadStatusSnapshot snapshot,
        string schedulerHotkey)
    {
        ArgumentNullException.ThrowIfNull(snapshot);
        ArgumentException.ThrowIfNullOrWhiteSpace(schedulerHotkey);

        if (snapshot.ReadyManualCycles < 0 || snapshot.SentUnconfirmed < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(snapshot),
                "Workload counters must be non-negative.");
        }

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
}
