namespace WorkspaceControl.OperatorBridge.Simulator.Core;

public sealed class VirtualClock
{
    public long MonotonicMilliseconds { get; private set; }

    public void Advance(long milliseconds)
    {
        if (milliseconds < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(milliseconds));
        }

        MonotonicMilliseconds += milliseconds;
    }
}
