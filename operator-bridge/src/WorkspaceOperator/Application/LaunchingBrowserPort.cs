using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Application;

public sealed class LaunchingBrowserPort : IBrowserPort
{
    private readonly IBrowserPort _inner;
    private readonly IBrowserAdapterConnection _connection;
    private readonly IWorkerEnvironmentLauncher _launcher;
    private readonly TimeSpan _connectionTimeout;
    private readonly SemaphoreSlim _launchGate = new(1, 1);

    public LaunchingBrowserPort(
        IBrowserPort inner,
        IBrowserAdapterConnection connection,
        IWorkerEnvironmentLauncher launcher,
        TimeSpan connectionTimeout)
    {
        ArgumentNullException.ThrowIfNull(inner);
        ArgumentNullException.ThrowIfNull(connection);
        ArgumentNullException.ThrowIfNull(launcher);
        if (connectionTimeout <= TimeSpan.Zero)
        {
            throw new ArgumentOutOfRangeException(
                nameof(connectionTimeout));
        }

        _inner = inner;
        _connection = connection;
        _launcher = launcher;
        _connectionTimeout = connectionTimeout;
    }

    public Task<BrowserResult> PrepareTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        ExecuteConnectedAsync(
            ct => _inner.PrepareTargetAsync(target, ct),
            cancellationToken);

    public Task<BrowserResult> FocusTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        ExecuteConnectedAsync(
            ct => _inner.FocusTargetAsync(target, ct),
            cancellationToken);

    public Task<BrowserResult> CreateTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        ExecuteConnectedAsync(
            ct => _inner.CreateTargetAsync(target, ct),
            cancellationToken);

    public Task<BrowserResult> RestoreTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        ExecuteConnectedAsync(
            ct => _inner.RestoreTargetAsync(target, ct),
            cancellationToken);

    public Task<BrowserResult> DiscardTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        _inner.DiscardTargetAsync(target, cancellationToken);

    public Task<BrowserResult> CloseTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        _inner.CloseTargetAsync(target, cancellationToken);

    private async Task<BrowserResult> ExecuteConnectedAsync(
        Func<CancellationToken, Task<BrowserResult>> operation,
        CancellationToken cancellationToken)
    {
        if (!await EnsureConnectedAsync(cancellationToken))
        {
            return new BrowserResult(
                BrowserOutcome.Rejected,
                "BROWSER_ADAPTER_UNAVAILABLE_AFTER_LAUNCH");
        }

        return await operation(cancellationToken);
    }

    private async Task<bool> EnsureConnectedAsync(
        CancellationToken cancellationToken)
    {
        if (_connection.IsConnected)
        {
            return true;
        }

        await _launchGate.WaitAsync(cancellationToken);
        try
        {
            if (_connection.IsConnected)
            {
                return true;
            }

            var launch = await _launcher.LaunchAsync(cancellationToken);
            if (!launch.Started)
            {
                return false;
            }

            return await _connection.WaitForConnectionAsync(
                _connectionTimeout,
                cancellationToken);
        }
        finally
        {
            _launchGate.Release();
        }
    }
}
