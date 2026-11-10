namespace WorkspaceControl.OperatorBridge.Application;

public sealed class BridgeState
{
    private int _enabled;

    public bool IsEnabled => Volatile.Read(ref _enabled) == 1;

    internal void SetEnabled(bool enabled) =>
        Interlocked.Exchange(ref _enabled, enabled ? 1 : 0);
}
