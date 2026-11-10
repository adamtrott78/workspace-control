using WorkspaceControl.OperatorBridge.Application;

namespace WorkspaceControl.OperatorBridge.Ports;

public interface IRecoveryAuthorityPort
{
    Task FreezeAsync(
        RecoveryIncident incident,
        CancellationToken cancellationToken);

    Task<RecoveryReconciliationResult> ReconcileAsync(
        RecoveryIncident incident,
        CancellationToken cancellationToken);

    Task<RecoveryAdvanceResult> SupersedeAndAdvanceGenerationAsync(
        string recoveryId,
        RecoverySessionRef session,
        CancellationToken cancellationToken);
}

public interface IRecoveryStateStore
{
    Task<RecoveryIncident?> LoadAsync(CancellationToken cancellationToken);

    Task SaveAsync(
        RecoveryIncident incident,
        CancellationToken cancellationToken);

    Task ClearAsync(CancellationToken cancellationToken);
}

public interface IManagedBrowserInventory
{
    Task<IReadOnlyList<BrowserInventoryEntry>> InventoryAsync(
        CancellationToken cancellationToken = default);
}

public interface IRecoveryGate
{
    bool BlocksDispatch { get; }

    Task OnBlockingOperatorPressAsync(CancellationToken cancellationToken);
}

public sealed class NullRecoveryGate : IRecoveryGate
{
    public static NullRecoveryGate Instance { get; } = new();

    public bool BlocksDispatch => false;

    public Task OnBlockingOperatorPressAsync(
        CancellationToken cancellationToken) =>
        Task.CompletedTask;
}
