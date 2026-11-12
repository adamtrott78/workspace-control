namespace WorkspaceControl.OperatorBridge.Windows;

public interface IWorkerWindowSafetyPort
{
    bool CaptureForegroundPreparedWorkerWindow();

    bool MinimizeCapturedWorkerWindow();
}

public sealed class WorkerWindowSafetyController
{
    private readonly IWorkerWindowSafetyPort _port;

    public WorkerWindowSafetyController(IWorkerWindowSafetyPort port)
    {
        _port = port;
    }

    public bool RecordPreparedWorkerWindow() =>
        _port.CaptureForegroundPreparedWorkerWindow();

    public bool MinimizeAfterNoAction() =>
        _port.MinimizeCapturedWorkerWindow();
}
