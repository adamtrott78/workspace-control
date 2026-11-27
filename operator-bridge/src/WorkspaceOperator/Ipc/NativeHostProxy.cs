using System.IO.Pipes;
using WorkspaceControl.OperatorBridge.Contracts.Protocol;

namespace WorkspaceControl.OperatorBridge.Ipc;

public static class NativeHostProxy
{
    public static async Task RunAsync(
        Stream nativeInput,
        Stream nativeOutput,
        string pipeName,
        CancellationToken cancellationToken = default)
    {
        await using var pipe = new NamedPipeClientStream(
            ".",
            pipeName,
            PipeDirection.InOut,
            PipeOptions.Asynchronous);

        await pipe.ConnectAsync(5000, cancellationToken);

        using var linked = CancellationTokenSource.CreateLinkedTokenSource(
            cancellationToken);

        var browserToHelper = PumpAsync(
            nativeInput,
            pipe,
            linked.Token);
        var helperToBrowser = PumpAsync(
            pipe,
            nativeOutput,
            linked.Token);

        await Task.WhenAny(browserToHelper, helperToBrowser);
        linked.Cancel();

        try
        {
            await Task.WhenAll(browserToHelper, helperToBrowser);
        }
        catch (OperationCanceledException)
            when (linked.IsCancellationRequested)
        {
        }
    }

    private static async Task PumpAsync(
        Stream source,
        Stream destination,
        CancellationToken cancellationToken)
    {
        while (await LengthPrefixedFrameCodec.CopyValidatedFrameAsync(
                   source,
                   destination,
                   cancellationToken))
        {
        }
    }
}
