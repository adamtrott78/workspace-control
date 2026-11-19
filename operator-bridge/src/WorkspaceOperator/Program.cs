using WorkspaceControl.OperatorBridge.Bootstrap;
using WorkspaceControl.OperatorBridge.Ipc;
using WorkspaceControl.OperatorBridge.Ports;
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
        var startEnabled = HasFlag(args, "--bridge-start-enabled");
        var localSmoke = HasFlag(args, "--local-smoke");
        var remoteConfiguration =
            RemoteOperatorBridgeConfiguration.Parse(
                args,
                $"workspaceoperator-{Guid.NewGuid():N}");

        if (localSmoke && remoteConfiguration is not null)
        {
            throw new ArgumentException(
                "--local-smoke cannot be combined with --operator-bridge-url.");
        }

        HttpOperatorBridgeClient? remoteClient = null;

        try
        {
            remoteClient = remoteConfiguration is null
                ? null
                : HttpOperatorBridgeClient.Create(remoteConfiguration);
            var localSmokePort = localSmoke
                ? new LocalSmokeOperatorActionPort()
                : null;
            IOperatorActionPort? actionPort = remoteClient ?? localSmokePort;
            Func<WorkloadStatusSnapshot>? statusProvider =
                remoteClient is not null
                    ? () => remoteClient.CurrentStatus
                    : localSmokePort is not null
                        ? () => new WorkloadStatusSnapshot(
                            localSmokePort.HasReadyAction ? 1 : 0,
                            0)
                        : null;

            var context = new TrayApplicationContext(
                idleProbeMilliseconds,
                schedulerHotkey,
                workloadStatusProvider: statusProvider,
                operatorActionPort: actionPort,
                operatorActionLifetime: remoteClient,
                startEnabled: startEnabled);

            if (startEnabled)
            {
                Console.WriteLine("WORKSPACE_OPERATOR_BRIDGE_ENABLED=PASS");
            }

            if (localSmoke)
            {
                Console.WriteLine("WORKSPACE_OPERATOR_LOCAL_SMOKE_READY=PASS");
            }

            System.Windows.Forms.Application.Run(context);
        }
        catch
        {
            remoteClient?.Dispose();
            throw;
        }
    }

    private static bool HasFlag(string[] args, string flag) =>
        args.Any(arg => string.Equals(
            arg,
            flag,
            StringComparison.OrdinalIgnoreCase));

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
