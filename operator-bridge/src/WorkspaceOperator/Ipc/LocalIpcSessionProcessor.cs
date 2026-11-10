using System.Text.Json;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Contracts;
using WorkspaceControl.OperatorBridge.Contracts.Protocol;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Ipc;

public sealed class LocalIpcSessionProcessor
{
    private readonly BridgeState _bridgeState;
    private readonly string _helperInstanceId;
    private readonly IDiagnosticsSink _diagnostics;

    public LocalIpcSessionProcessor(
        BridgeState bridgeState,
        string helperInstanceId,
        IDiagnosticsSink diagnostics)
    {
        _bridgeState = bridgeState;
        _helperInstanceId = helperInstanceId;
        _diagnostics = diagnostics;
    }

    public async Task ProcessAsync(
        Stream stream,
        CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            byte[]? frame;
            try
            {
                frame = await LengthPrefixedFrameCodec.ReadFrameAsync(
                    stream,
                    cancellationToken);
            }
            catch (ProtocolException exception)
            {
                await WriteErrorAsync(
                    stream,
                    exception.Code,
                    null,
                    null,
                    cancellationToken);
                return;
            }

            if (frame is null)
            {
                return;
            }

            ProtocolEnvelope message;
            try
            {
                message = ProtocolJson.Parse(frame);
            }
            catch (ProtocolException exception)
            {
                await WriteErrorAsync(
                    stream,
                    exception.Code,
                    null,
                    null,
                    cancellationToken);
                return;
            }

            ProtocolEnvelope response;
            if (message.MessageType == "HELLO")
            {
                response = HandleHello(message);
            }
            else if (message.MessageType == "PING")
            {
                response = ProtocolMessageFactory.Pong(
                    _helperInstanceId,
                    message.CorrelationId,
                    message.Payload);
            }
            else
            {
                response = ProtocolMessageFactory.Error(
                    _helperInstanceId,
                    "MESSAGE_NOT_HANDLED_STAGE_03",
                    message.MessageId,
                    message.CorrelationId);
            }

            var responseBytes = ProtocolJson.Serialize(response);
            await LengthPrefixedFrameCodec.WriteFrameAsync(
                stream,
                responseBytes,
                cancellationToken);
        }
    }

    private ProtocolEnvelope HandleHello(ProtocolEnvelope message)
    {
        var payload = message.Payload!.Value;
        var versions = payload
            .GetProperty("supported_protocol_versions")
            .EnumerateArray()
            .Select(item => item.GetString())
            .Where(item => item is not null);

        if (!versions.Contains(
                BrowserAdapterProtocol.Version,
                StringComparer.Ordinal))
        {
            return ProtocolMessageFactory.Error(
                _helperInstanceId,
                "NO_COMMON_PROTOCOL_VERSION",
                message.MessageId,
                message.CorrelationId);
        }

        return ProtocolMessageFactory.HelloAck(
            _helperInstanceId,
            message.CorrelationId,
            _bridgeState);
    }

    private async Task WriteErrorAsync(
        Stream stream,
        string code,
        string? relatedMessageId,
        string? correlationId,
        CancellationToken cancellationToken)
    {
        try
        {
            var response = ProtocolMessageFactory.Error(
                _helperInstanceId,
                code,
                relatedMessageId,
                correlationId);
            await LengthPrefixedFrameCodec.WriteFrameAsync(
                stream,
                ProtocolJson.Serialize(response),
                cancellationToken);
        }
        catch
        {
            // Framing/transport failure is terminal for this proxy connection.
        }

        _diagnostics.Write(new DiagnosticEvent(
            DateTimeOffset.UtcNow,
            "local_ipc",
            "protocol_error",
            "REJECTED",
            NormalizedError: code));
    }
}
