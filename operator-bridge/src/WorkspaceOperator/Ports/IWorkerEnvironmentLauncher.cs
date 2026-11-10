namespace WorkspaceControl.OperatorBridge.Ports;

public sealed record WorkerEnvironmentLaunchResult(
    bool Started,
    string? NormalizedError = null);

public interface IWorkerEnvironmentLauncher
{
    Task<WorkerEnvironmentLaunchResult> LaunchAsync(
        CancellationToken cancellationToken);
}

public interface IBrowserAdapterConnection
{
    bool IsConnected { get; }

    Task<bool> WaitForConnectionAsync(
        TimeSpan timeout,
        CancellationToken cancellationToken = default);
}
