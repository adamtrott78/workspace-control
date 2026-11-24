namespace WorkspaceControl.OperatorBridge.Ports;

public interface IMonotonicClock
{
    long GetTimestamp();

    TimeSpan GetElapsedTime(long startingTimestamp);
}
