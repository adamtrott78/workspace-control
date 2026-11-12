using WorkspaceControl.OperatorBridge.Ipc;
using WorkspaceControl.OperatorBridge.Windows;
using WorkspaceControl.OperatorBridge.Windows.Hotkey;

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
        System.Windows.Forms.Application.Run(
            new TrayApplicationContext(
                idleProbeMilliseconds,
                schedulerHotkey));
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
