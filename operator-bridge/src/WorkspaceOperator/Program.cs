using WorkspaceControl.OperatorBridge.Windows;

namespace WorkspaceControl.OperatorBridge;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        ApplicationConfiguration.Initialize();
        var idleProbeMilliseconds = ParseIdleProbe(args);
        System.Windows.Forms.Application.Run(
            new TrayApplicationContext(idleProbeMilliseconds));
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
