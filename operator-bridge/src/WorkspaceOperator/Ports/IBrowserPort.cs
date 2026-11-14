using WorkspaceControl.OperatorBridge.Application;

namespace WorkspaceControl.OperatorBridge.Ports;

public interface IBrowserPort
{
    Task<BrowserResult> PrepareTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken);

    Task<BrowserResult> FocusTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken);

    Task<BrowserResult> CreateTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        PrepareTargetAsync(target, cancellationToken);

    Task<BrowserResult> RestoreTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        PrepareTargetAsync(target, cancellationToken);

    Task<BrowserResult> DiscardTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        Task.FromResult(new BrowserResult(
            BrowserOutcome.Rejected,
            "DISCARD_NOT_IMPLEMENTED"));

    Task<BrowserResult> CloseTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        Task.FromResult(new BrowserResult(
            BrowserOutcome.Rejected,
            "CLOSE_NOT_IMPLEMENTED"));
}
