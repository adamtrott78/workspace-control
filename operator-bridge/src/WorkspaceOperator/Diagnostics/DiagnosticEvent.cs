namespace WorkspaceControl.OperatorBridge.Diagnostics;

public sealed record DiagnosticEvent(
    DateTimeOffset Timestamp,
    string Component,
    string EventName,
    string Outcome,
    string? ActionId = null,
    string? WorkerSlotId = null,
    long? SessionGeneration = null,
    string? PayloadRef = null,
    string? PayloadSha256 = null,
    string? NormalizedError = null,
    double? DurationMs = null);
