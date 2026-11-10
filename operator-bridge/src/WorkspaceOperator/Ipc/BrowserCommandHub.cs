using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.Json;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Contracts;
using WorkspaceControl.OperatorBridge.Contracts.Protocol;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Ipc;

public sealed class BrowserCommandHub
{
    private readonly BridgeState _bridgeState;
    private readonly string _helperInstanceId;
    private readonly IDiagnosticsSink _diagnostics;
    private readonly object _connectionGate = new();
    private readonly SemaphoreSlim _writeGate = new(1, 1);
    private readonly ConcurrentDictionary<string, TaskCompletionSource<ProtocolEnvelope>> _pending =
        new(StringComparer.Ordinal);
    private readonly List<ProtocolEnvelope> _events = [];
    private Stream? _stream;
    private TaskCompletionSource<bool> _connected = NewConnectionSource();

    public BrowserCommandHub(
        BridgeState bridgeState,
        IDiagnosticsSink diagnostics)
    {
        _bridgeState = bridgeState;
        _diagnostics = diagnostics;
        _helperInstanceId = Guid.NewGuid().ToString("N");
    }

    public bool IsConnected
    {
        get
        {
            lock (_connectionGate)
            {
                return _stream is not null;
            }
        }
    }

    public IReadOnlyList<ProtocolEnvelope> BrowserEvents
    {
        get
        {
            lock (_events)
            {
                return _events.ToArray();
            }
        }
    }

    public async Task<bool> WaitForConnectionAsync(
        TimeSpan timeout,
        CancellationToken cancellationToken = default)
    {
        Task connectedTask;
        lock (_connectionGate)
        {
            if (_stream is not null)
            {
                return true;
            }
            connectedTask = _connected.Task;
        }

        using var timeoutCancellation =
            CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeoutCancellation.CancelAfter(timeout);

        try
        {
            await connectedTask.WaitAsync(timeoutCancellation.Token);
            return true;
        }
        catch (OperationCanceledException)
            when (!cancellationToken.IsCancellationRequested)
        {
            return false;
        }
    }

    public async Task RunConnectionAsync(
        Stream stream,
        CancellationToken cancellationToken)
    {
        ProtocolEnvelope? hello = null;

        try
        {
            var firstFrame = await LengthPrefixedFrameCodec.ReadFrameAsync(
                stream,
                cancellationToken);
            if (firstFrame is null)
            {
                return;
            }

            hello = ProtocolJson.Parse(firstFrame);
            if (hello.MessageType != "HELLO")
            {
                await WriteAsync(
                    stream,
                    ProtocolMessageFactory.Error(
                        _helperInstanceId,
                        "HELLO_REQUIRED",
                        hello.MessageId,
                        hello.CorrelationId),
                    cancellationToken);
                return;
            }

            var versions = hello.Payload!.Value
                .GetProperty("supported_protocol_versions")
                .EnumerateArray()
                .Select(item => item.GetString())
                .Where(item => item is not null);

            if (!versions.Contains(
                    BrowserAdapterProtocol.Version,
                    StringComparer.Ordinal))
            {
                await WriteAsync(
                    stream,
                    ProtocolMessageFactory.Error(
                        _helperInstanceId,
                        "NO_COMMON_PROTOCOL_VERSION",
                        hello.MessageId,
                        hello.CorrelationId),
                    cancellationToken);
                return;
            }

            await WriteAsync(
                stream,
                ProtocolMessageFactory.HelloAck(
                    _helperInstanceId,
                    hello.CorrelationId,
                    _bridgeState),
                cancellationToken);

            lock (_connectionGate)
            {
                if (_stream is not null)
                {
                    throw new InvalidOperationException(
                        "A browser adapter connection is already active.");
                }

                _stream = stream;
                _connected.TrySetResult(true);
            }

            _diagnostics.Write(new DiagnosticEvent(
                DateTimeOffset.UtcNow,
                "browser_command_hub",
                "adapter_connected",
                "APPLIED"));

            while (!cancellationToken.IsCancellationRequested)
            {
                var frame = await LengthPrefixedFrameCodec.ReadFrameAsync(
                    stream,
                    cancellationToken);
                if (frame is null)
                {
                    return;
                }

                var message = ProtocolJson.Parse(frame);
                switch (message.MessageType)
                {
                    case "BROWSER_RESULT":
                        CompletePending(message);
                        break;
                    case "BROWSER_EVENT":
                        lock (_events)
                        {
                            _events.Add(message);
                        }
                        break;
                    case "PING":
                        await WriteAsync(
                            stream,
                            ProtocolMessageFactory.Pong(
                                _helperInstanceId,
                                message.CorrelationId,
                                message.Payload),
                            cancellationToken);
                        break;
                    case "PROTOCOL_ERROR":
                        FailPendingFromProtocolError(message);
                        break;
                    default:
                        await WriteAsync(
                            stream,
                            ProtocolMessageFactory.Error(
                                _helperInstanceId,
                                "UNEXPECTED_ADAPTER_MESSAGE",
                                message.MessageId,
                                message.CorrelationId),
                            cancellationToken);
                        break;
                }
            }
        }
        catch (OperationCanceledException)
            when (cancellationToken.IsCancellationRequested)
        {
        }
        catch (ProtocolException exception)
        {
            _diagnostics.Write(new DiagnosticEvent(
                DateTimeOffset.UtcNow,
                "browser_command_hub",
                "protocol_error",
                "REJECTED",
                NormalizedError: exception.Code));
        }
        finally
        {
            lock (_connectionGate)
            {
                if (ReferenceEquals(_stream, stream))
                {
                    _stream = null;
                    _connected = NewConnectionSource();
                }
            }

            foreach (var pair in _pending.ToArray())
            {
                if (_pending.TryRemove(pair.Key, out var completion))
                {
                    completion.TrySetException(
                        new IOException("Browser adapter disconnected."));
                }
            }

            if (hello is not null)
            {
                _diagnostics.Write(new DiagnosticEvent(
                    DateTimeOffset.UtcNow,
                    "browser_command_hub",
                    "adapter_disconnected",
                    "NOT_APPLIED"));
            }
        }
    }

    public async Task<ProtocolEnvelope> SendBrowserCommandAsync(
        string operation,
        BrowserTarget target,
        long? expectedBindingGeneration = null,
        string? requestId = null,
        string? idempotencyKey = null,
        CancellationToken cancellationToken = default)
    {
        Stream stream;
        lock (_connectionGate)
        {
            stream = _stream ??
                throw new IOException("Browser adapter is not connected.");
        }

        requestId ??= Guid.NewGuid().ToString("N");
        idempotencyKey ??= requestId;

        var completion = new TaskCompletionSource<ProtocolEnvelope>(
            TaskCreationOptions.RunContinuationsAsynchronously);
        if (!_pending.TryAdd(requestId, completion))
        {
            throw new InvalidOperationException("Duplicate pending request ID.");
        }

        var message = ProtocolMessageFactory.BrowserCommand(
            _helperInstanceId,
            requestId,
            requestId,
            operation,
            idempotencyKey,
            target,
            expectedBindingGeneration);

        try
        {
            await WriteAsync(stream, message, cancellationToken);
            return await completion.Task.WaitAsync(
                TimeSpan.FromSeconds(10),
                cancellationToken);
        }
        finally
        {
            _pending.TryRemove(requestId, out _);
        }
    }

    private async Task WriteAsync(
        Stream stream,
        ProtocolEnvelope message,
        CancellationToken cancellationToken)
    {
        await _writeGate.WaitAsync(cancellationToken);
        try
        {
            await LengthPrefixedFrameCodec.WriteFrameAsync(
                stream,
                ProtocolJson.Serialize(message),
                cancellationToken);
        }
        finally
        {
            _writeGate.Release();
        }
    }

    private void CompletePending(ProtocolEnvelope message)
    {
        if (message.RequestId is null)
        {
            return;
        }

        if (_pending.TryRemove(message.RequestId, out var completion))
        {
            completion.TrySetResult(message);
        }
    }

    private void FailPendingFromProtocolError(ProtocolEnvelope message)
    {
        if (message.RequestId is null)
        {
            return;
        }

        if (_pending.TryRemove(message.RequestId, out var completion))
        {
            completion.TrySetException(
                new ProtocolException("ADAPTER_PROTOCOL_ERROR"));
        }
    }

    private static TaskCompletionSource<bool> NewConnectionSource() =>
        new(TaskCreationOptions.RunContinuationsAsynchronously);
}
