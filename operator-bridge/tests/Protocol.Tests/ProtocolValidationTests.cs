using System.Buffers.Binary;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Contracts.Protocol;

namespace WorkspaceControl.OperatorBridge.Protocol.Tests;

[TestClass]
public sealed class ProtocolValidationTests
{
    [TestMethod]
    public void WrongVersionFailsClosed()
    {
        var json = """
        {"protocol_version":"2.0","message_type":"PING","message_id":"m1","sent_at_monotonic_ms":1,"payload":{"nonce":"n"}}
        """;

        var error = Capture(() => ProtocolJson.Parse(Encoding.UTF8.GetBytes(json)));

        Assert.AreEqual("UNSUPPORTED_PROTOCOL_VERSION", error.Code);
    }

    [TestMethod]
    public void MalformedJsonFailsClosed()
    {
        var error = Capture(() => ProtocolJson.Parse(Encoding.UTF8.GetBytes("{")));

        Assert.AreEqual("MALFORMED_OR_UNKNOWN_JSON", error.Code);
    }

    [TestMethod]
    public void UnknownTopLevelFieldFailsClosed()
    {
        var json = """
        {"protocol_version":"1.0","message_type":"PING","message_id":"m1","sent_at_monotonic_ms":1,"packet_text":"secret","payload":{"nonce":"n"}}
        """;

        var error = Capture(() => ProtocolJson.Parse(Encoding.UTF8.GetBytes(json)));

        Assert.AreEqual("MALFORMED_OR_UNKNOWN_JSON", error.Code);
    }

    [TestMethod]
    public void ForbiddenPayloadContentFieldFailsClosed()
    {
        var json = """
        {"protocol_version":"1.0","message_type":"PING","message_id":"m1","sent_at_monotonic_ms":1,"payload":{"url":"https://example.invalid"}}
        """;

        var error = Capture(() => ProtocolJson.Parse(Encoding.UTF8.GetBytes(json)));

        Assert.AreEqual("FORBIDDEN_CONTENT_FIELD", error.Code);
    }

    [TestMethod]
    public async Task OversizeFrameHeaderFailsBeforeAllocation()
    {
        var header = new byte[4];
        BinaryPrimitives.WriteUInt32LittleEndian(header, 65_537);
        using var stream = new MemoryStream(header);

        ProtocolException? caught = null;
        try
        {
            await LengthPrefixedFrameCodec.ReadFrameAsync(stream);
        }
        catch (ProtocolException exception)
        {
            caught = exception;
        }

        Assert.IsNotNull(caught);
        Assert.AreEqual("INVALID_FRAME_SIZE", caught.Code);
    }

    [TestMethod]
    public async Task TruncatedFrameBodyFailsClosed()
    {
        var header = new byte[4];
        BinaryPrimitives.WriteUInt32LittleEndian(header, 10);
        using var stream = new MemoryStream();
        await stream.WriteAsync(header);
        await stream.WriteAsync(new byte[3]);
        stream.Position = 0;

        ProtocolException? caught = null;
        try
        {
            await LengthPrefixedFrameCodec.ReadFrameAsync(stream);
        }
        catch (ProtocolException exception)
        {
            caught = exception;
        }

        Assert.IsNotNull(caught);
        Assert.AreEqual("TRUNCATED_FRAME_BODY", caught.Code);
    }

    private static ProtocolException Capture(Action action)
    {
        try
        {
            action();
        }
        catch (ProtocolException exception)
        {
            return exception;
        }

        Assert.Fail("Expected ProtocolException.");
        throw new InvalidOperationException();
    }
}
