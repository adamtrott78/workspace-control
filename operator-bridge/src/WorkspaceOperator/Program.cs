using WorkspaceControl.OperatorBridge.Ipc;
using WorkspaceControl.OperatorBridge.Windows;
using WorkspaceControl.OperatorBridge.Windows.Hotkey;
using WorkspaceControl.OperatorBridge.Windows.Remote;

namespace WorkspaceControl.OperatorBridge;

internal static class Program
{
    [STAThread]
    private static async Task Main(string[] args)
    {
        if (RuntimeModeDetector.IsNativeHostProxy(args))
        {
            var pipeName = ElevationScope.PipeName(ElevationScope.Current());
            await NativeHostProxy.RunAsync(
                Console.OpenStandardInput(),
                Console.OpenStandardOutput(),
                pipeName);
            return;
        }

        ApplicationConfiguration.Initialize();
        var idleProbeMilliseconds = ParseIdleProbe(args);
        var schedulerHotkey = ParseSchedulerHotkey(args);
        var remoteConfiguration =
            RemoteOperatorBridgeConfiguration.Parse(
                args,
                $"workspaceoperator-{Guid.NewGuid():N}");
        HttpOperatorBridgeClient? remoteClient = null;

        try
        {
            remoteClient = remoteConfiguration is null
                ? null
                : HttpOperatorBridgeClient.Create(remoteConfiguration);

            System.Windows.Forms.Application.Run(
                new TrayApplicationContext(
                    idleProbeMilliseconds,
                    schedulerHotkey,
                    workloadStatusProvider: remoteClient is null
                        ? null
                        : () => remoteClient.CurrentStatus,
                    operatorActionPort: remoteClient,
                    operatorActionLifetime: remoteClient));
        }
        catch
        {
            remoteClient?.Dispose();
            throw;
        }
    }

    private static SchedulerHotkeyBinding ParseSchedulerHotkey(string[] args)
    {
        const string prefix = "--scheduler-hotkey=";
        var value = args.FirstOrDefault(arg =>
            arg.StartsWith(prefix, StringComparison.OrdinalIgnoreCase));

        return SchedulerHotkeyBinding.Parse(
            value is null ? null : value[prefix.Length..]);
    }

    private static int? ParseIdleProbe(string[] args)
    {
        const string prefix = "--idle-probe-ms=";
        var value = args.FirstOrDefault(arg =>
            arg.StartsWith(prefix, StringComparison.OrdinalIgnoreCase));

        if (value is null)
        {
            return null;
        }

        if (int.TryParse(value[prefix.Length..], out var milliseconds) &&
            milliseconds is >= 1000 and <= 60000)
        {
            return milliseconds;
        }

        throw new ArgumentException(
            "--idle-probe-ms must be an integer from 1000 through 60000.");
    }
}
