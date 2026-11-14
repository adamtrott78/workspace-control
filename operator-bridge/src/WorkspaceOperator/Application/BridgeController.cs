using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Application;

public sealed class BridgeController
{
    private readonly BridgeState _state;
    private readonly IHotkeyRegistrar _hotkey;
    private readonly IDiagnosticsSink _diagnostics;

    public BridgeController(
        BridgeState state,
        IHotkeyRegistrar hotkey,
        IDiagnosticsSink diagnostics)
    {
        _state = state;
        _hotkey = hotkey;
        _diagnostics = diagnostics;
    }

    public bool IsEnabled => _state.IsEnabled;

    public void SetEnabled(bool enabled)
    {
        if (enabled == _state.IsEnabled)
        {
            return;
        }

        if (enabled)
        {
            try
            {
                _hotkey.Register();
                _state.SetEnabled(true);
                Write("bridge_toggle", "ENABLED");
            }
            catch (Exception exception)
            {
                _state.SetEnabled(false);
                Write(
                    "bridge_toggle",
                    "REJECTED",
                    ErrorNormalizer.FromException(exception));
                throw;
            }

            return;
        }

        _state.SetEnabled(false);
        _hotkey.Unregister();
        Write("bridge_toggle", "DISABLED");
    }

    private void Write(string eventName, string outcome, string? error = null) =>
        _diagnostics.Write(new DiagnosticEvent(
            DateTimeOffset.UtcNow,
            "native_helper",
            eventName,
            outcome,
            NormalizedError: error));
}
