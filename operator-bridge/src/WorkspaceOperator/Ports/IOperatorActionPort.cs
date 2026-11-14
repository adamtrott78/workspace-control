using WorkspaceControl.OperatorBridge.Application;

namespace WorkspaceControl.OperatorBridge.Ports;

public interface IOperatorActionPort
{
    Task<OperatorAction?> ClaimNextAsync(CancellationToken cancellationToken);

    Task<bool> RevalidateAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken);

    Task RecordLocalPreparedAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken);

    Task RecordLocalFailureAsync(
        ActionIdentity identity,
        string normalizedError,
        CancellationToken cancellationToken);

    Task RecordBlockedAsync(
        ActionIdentity identity,
        string normalizedError,
        CancellationToken cancellationToken) =>
        RecordLocalFailureAsync(
            identity,
            normalizedError,
            cancellationToken);

    Task RecordLocalCompletedAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken) =>
        Task.CompletedTask;
}
