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
}
