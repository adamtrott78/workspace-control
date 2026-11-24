using WorkspaceControl.OperatorBridge.Diagnostics;

namespace WorkspaceControl.OperatorBridge.Ports;

public interface IDiagnosticsSink
{
    void Write(DiagnosticEvent diagnosticEvent);
}
