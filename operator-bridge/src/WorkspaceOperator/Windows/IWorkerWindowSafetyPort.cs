namespace WorkspaceControl.OperatorBridge.Windows;

public interface IWorkerWindowSafetyPort
{
    bool CaptureForegroundPreparedWorkerWindow();

    bool ForegroundPreparedWorkerWindow();

    bool IsCapturedWorkerWindowForeground();

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

    public bool ForegroundPreparedWorkerWindow() =>
        _port.ForegroundPreparedWorkerWindow();

    public bool IsPreparedWorkerWindowForeground() =>
        _port.IsCapturedWorkerWindowForeground();

    public bool MinimizeAfterNoAction() =>
        _port.MinimizeCapturedWorkerWindow();
}
