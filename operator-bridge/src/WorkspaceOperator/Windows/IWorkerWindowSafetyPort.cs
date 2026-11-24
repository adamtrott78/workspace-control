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

    public bool ForegroundPreparedWorkerWindowWithRetries(
        int attempts = 20,
        int delayMilliseconds = 25)
    {
        if (attempts <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(attempts));
        }

        if (delayMilliseconds < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(delayMilliseconds));
        }

        for (var attempt = 0; attempt < attempts; attempt++)
        {
            if (_port.ForegroundPreparedWorkerWindow())
            {
                return true;
            }

            if (attempt + 1 < attempts && delayMilliseconds > 0)
            {
                Thread.Sleep(delayMilliseconds);
            }
        }

        return false;
    }

    public bool IsPreparedWorkerWindowForeground() =>
        _port.IsCapturedWorkerWindowForeground();

    public bool MinimizeAfterNoAction() =>
        _port.MinimizeCapturedWorkerWindow();
}
