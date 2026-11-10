namespace WorkspaceControl.OperatorBridge.Ports;

public interface IOperatorSurfacePort
{
    Task OpenJudgmentAsync(CancellationToken cancellationToken);

    Task OpenRecoveryAsync(CancellationToken cancellationToken);
}

public sealed class NullOperatorSurfacePort : IOperatorSurfacePort
{
    public Task OpenJudgmentAsync(CancellationToken cancellationToken) =>
        Task.CompletedTask;

    public Task OpenRecoveryAsync(CancellationToken cancellationToken) =>
        Task.CompletedTask;
}
