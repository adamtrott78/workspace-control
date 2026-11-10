using System.Collections.Concurrent;
using System.IO.Pipes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Contracts.Protocol;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ipc;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class LocalIpcServerTests
{
    [TestMethod]
    public async Task HelloNegotiatesV1AndServerSurvivesClientDisconnect()
    {
        var pipeName = "wc-ob-test-" + Guid.NewGuid().ToString("N");
        var state = new BridgeState();
        var diagnostics = new CaptureDiagnostics();
        using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var serverTask = new LocalIpcServer(
            pipeName,
            state,
            diagnostics).RunAsync(cancellation.Token);

        await using (var first = await ConnectAsync(pipeName, cancellation.Token))
        {
            await SendAsync(first, Hello("hello-1"), cancellation.Token);
            var response = await ReceiveAsync(first, cancellation.Token);
            Assert.AreEqual("HELLO_ACK", response.MessageType);
            Assert.AreEqual(
                "1.0",
                response.Payload!.Value
                    .GetProperty("accepted_protocol_version")
                    .GetString());
            Assert.AreEqual(
                "OFF",
                response.Payload!.Value.GetProperty("bridge_state").GetString());
        }

        await using (var second = await ConnectAsync(pipeName, cancellation.Token))
        {
            await SendAsync(second, Ping("ping-2"), cancellation.Token);
            var response = await ReceiveAsync(second, cancellation.Token);
            Assert.AreEqual("PONG", response.MessageType);
            Assert.AreEqual(
                "nonce-2",
                response.Payload!.Value.GetProperty("nonce").GetString());
        }

        cancellation.Cancel();
        await serverTask;

        Assert.IsTrue(
            diagnostics.Events.Count(e => e.EventName == "proxy_connected") >= 2);
    }

    [TestMethod]
    public void ElevationScopedPipeNamesCannotAlias()
    {
        var standard = ElevationScope.PipeName(ProcessElevationScope.Standard);
        var elevated = ElevationScope.PipeName(ProcessElevationScope.Elevated);

        Assert.IsFalse(string.Equals(standard, elevated, StringComparison.Ordinal));
        Assert.IsTrue(standard.EndsWith("-standard", StringComparison.Ordinal));
        Assert.IsTrue(elevated.EndsWith("-elevated", StringComparison.Ordinal));
    }

    private static async Task<NamedPipeClientStream> ConnectAsync(
        string pipeName,
        CancellationToken cancellationToken)
    {
        var client = new NamedPipeClientStream(
            ".",
            pipeName,
            PipeDirection.InOut,
            PipeOptions.Asynchronous);
        await client.ConnectAsync(3000, cancellationToken);
        return client;
    }

    private static ProtocolEnvelope Hello(string id) =>
        new()
        {
            ProtocolVersion = "1.0",
            MessageType = "HELLO",
            MessageId = id,
            CorrelationId = "corr-" + id,
            SentAtMonotonicMs = 1,
            AdapterInstanceId = "adapter-1",
            Payload = ProtocolJson.Payload(new
            {
                adapter_kind = "FIREFOX_EXTENSION",
                adapter_version = "0.1.0",
                supported_protocol_versions = new[] { "1.0" },
                capabilities = new
                {
                    discard = true,
                    persistent_binding_metadata = true,
                    origin_classification = true,
                    profile_isolation = true
                }
            })
        };

    private static ProtocolEnvelope Ping(string id) =>
        new()
        {
            ProtocolVersion = "1.0",
            MessageType = "PING",
            MessageId = id,
            CorrelationId = "corr-" + id,
            SentAtMonotonicMs = 2,
            AdapterInstanceId = "adapter-1",
            Payload = ProtocolJson.Payload(new { nonce = "nonce-2" })
        };

    private static Task SendAsync(
        Stream stream,
        ProtocolEnvelope envelope,
        CancellationToken cancellationToken) =>
        LengthPrefixedFrameCodec.WriteFrameAsync(
            stream,
            ProtocolJson.Serialize(envelope),
            cancellationToken);

    private static async Task<ProtocolEnvelope> ReceiveAsync(
        Stream stream,
        CancellationToken cancellationToken)
    {
        var frame = await LengthPrefixedFrameCodec.ReadFrameAsync(
            stream,
            cancellationToken);
        Assert.IsNotNull(frame);
        return ProtocolJson.Parse(frame);
    }

    private sealed class CaptureDiagnostics : IDiagnosticsSink
    {
        private readonly ConcurrentQueue<DiagnosticEvent> _events = new();

        public IReadOnlyCollection<DiagnosticEvent> Events => _events.ToArray();

        public void Write(DiagnosticEvent diagnosticEvent) =>
            _events.Enqueue(diagnosticEvent);
    }
}
