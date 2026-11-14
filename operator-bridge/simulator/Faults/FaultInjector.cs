using WorkspaceControl.OperatorBridge.Simulator.Core;

namespace WorkspaceControl.OperatorBridge.Simulator.Faults;

public sealed class FaultInjector
{
    private readonly TraceRecorder _trace;
    private readonly HashSet<string> _active = new(StringComparer.Ordinal);

    public FaultInjector(TraceRecorder trace)
    {
        _trace = trace;
    }

    public void Enable(string fault)
    {
        _active.Add(fault);
        _trace.Record("fault_injector", "FAULT_ENABLED", normalizedReason: fault);
    }

    public bool IsEnabled(string fault) => _active.Contains(fault);
}
