using System.Buffers.Binary;
using WorkspaceControl.OperatorBridge.Contracts;

namespace WorkspaceControl.OperatorBridge.Contracts.Protocol;

public static class LengthPrefixedFrameCodec
{
    public static async Task<byte[]?> ReadFrameAsync(Stream stream, CancellationToken cancellationToken = default)
    {
        var header = new byte[4];
        var headerBytes = await ReadAtMostAsync(stream, header, cancellationToken);
        if (headerBytes == 0) return null;
        if (headerBytes != header.Length) throw new ProtocolException("TRUNCATED_FRAME_HEADER");

        var length = BinaryPrimitives.ReadUInt32LittleEndian(header);
        if (length is 0 or > BrowserAdapterProtocol.MaxFrameBytes)
            throw new ProtocolException("INVALID_FRAME_SIZE");

        var body = new byte[(int)length];
        var bodyBytes = await ReadAtMostAsync(stream, body, cancellationToken);
        if (bodyBytes != body.Length) throw new ProtocolException("TRUNCATED_FRAME_BODY");
        return body;
    }

    public static async Task WriteFrameAsync(Stream stream, ReadOnlyMemory<byte> body, CancellationToken cancellationToken = default)
    {
        if (body.Length is <= 0 or > BrowserAdapterProtocol.MaxFrameBytes)
            throw new ProtocolException("INVALID_FRAME_SIZE");
        var header = new byte[4];
        BinaryPrimitives.WriteUInt32LittleEndian(header, (uint)body.Length);
        await stream.WriteAsync(header, cancellationToken);
        await stream.WriteAsync(body, cancellationToken);
        await stream.FlushAsync(cancellationToken);
    }

    public static async Task<bool> CopyValidatedFrameAsync(Stream source, Stream destination, CancellationToken cancellationToken = default)
    {
        var body = await ReadFrameAsync(source, cancellationToken);
        if (body is null) return false;
        ProtocolJson.Parse(body);
        await WriteFrameAsync(destination, body, cancellationToken);
        return true;
    }

    private static async Task<int> ReadAtMostAsync(Stream stream, byte[] buffer, CancellationToken cancellationToken)
    {
        var total = 0;
        while (total < buffer.Length)
        {
            var read = await stream.ReadAsync(buffer.AsMemory(total, buffer.Length - total), cancellationToken);
            if (read == 0) break;
            total += read;
        }
        return total;
    }
}
