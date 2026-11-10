using System.IO.Pipes;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Contracts;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Ipc;

public sealed class LocalIpcServer
{
    private readonly string _pipeName;
    private readonly LocalIpcSessionProcessor? _processor;
    private readonly BrowserCommandHub? _commandHub;
    private readonly IDiagnosticsSink _diagnostics;

    public LocalIpcServer(
        string pipeName,
        BridgeState bridgeState,
        IDiagnosticsSink diagnostics)
    {
        _pipeName = pipeName;
        _diagnostics = diagnostics;
        _processor = new LocalIpcSessionProcessor(
            bridgeState,
            Guid.NewGuid().ToString("N"),
            diagnostics);
    }

    public LocalIpcServer(
        string pipeName,
        BrowserCommandHub commandHub,
        IDiagnosticsSink diagnostics)
    {
        _pipeName = pipeName;
        _diagnostics = diagnostics;
        _commandHub = commandHub;
    }

    public async Task RunAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            await using var server = CreateServer();
            try
            {
                await server.WaitForConnectionAsync(cancellationToken);
                _diagnostics.Write(new DiagnosticEvent(
                    DateTimeOffset.UtcNow,
                    "local_ipc",
                    "proxy_connected",
                    "APPLIED"));

                if (_commandHub is not null)
                {
                    await _commandHub.RunConnectionAsync(
                        server,
                        cancellationToken);
                }
                else
                {
                    await _processor!.ProcessAsync(
                        server,
                        cancellationToken);
                }
            }
            catch (OperationCanceledException)
                when (cancellationToken.IsCancellationRequested)
            {
                return;
            }
            catch (IOException)
            {
                _diagnostics.Write(new DiagnosticEvent(
                    DateTimeOffset.UtcNow,
                    "local_ipc",
                    "proxy_disconnected",
                    "NOT_APPLIED",
                    NormalizedError: "IOException"));
            }
            finally
            {
                if (server.IsConnected)
                {
                    server.Disconnect();
                }
            }
        }
    }

    private NamedPipeServerStream CreateServer() =>
        new(
            _pipeName,
            PipeDirection.InOut,
            1,
            PipeTransmissionMode.Byte,
            PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly,
            BrowserAdapterProtocol.MaxFrameBytes,
            BrowserAdapterProtocol.MaxFrameBytes);
}
