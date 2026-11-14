using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Bootstrap;

internal sealed class NoWorkOperatorActionPort : IOperatorActionPort
{
    public Task<OperatorAction?> ClaimNextAsync(CancellationToken cancellationToken) =>
        Task.FromResult<OperatorAction?>(null);

    public Task<bool> RevalidateAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken) =>
        Task.FromResult(false);

    public Task RecordLocalPreparedAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken) =>
        Task.CompletedTask;

    public Task RecordLocalFailureAsync(
        ActionIdentity identity,
        string normalizedError,
        CancellationToken cancellationToken) =>
        Task.CompletedTask;
}

internal sealed class NoopBrowserPort : IBrowserPort
{
    public Task<BrowserResult> PrepareTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        Task.FromResult(new BrowserResult(
            BrowserOutcome.Rejected,
            "BROWSER_NOT_IMPLEMENTED_STAGE_02"));

    public Task<BrowserResult> FocusTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        Task.FromResult(new BrowserResult(
            BrowserOutcome.Rejected,
            "BROWSER_NOT_IMPLEMENTED_STAGE_02"));
}
