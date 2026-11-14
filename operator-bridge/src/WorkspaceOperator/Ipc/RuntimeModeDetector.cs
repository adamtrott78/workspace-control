namespace WorkspaceControl.OperatorBridge.Ipc;

public static class RuntimeModeDetector
{
    public static bool IsNativeHostProxy(string[] args) =>
        IsNativeHostProxy(
            args,
            Console.IsInputRedirected,
            Console.IsOutputRedirected);

    internal static bool IsNativeHostProxy(
        string[] args,
        bool inputRedirected,
        bool outputRedirected)
    {
        if (args.Any(arg =>
                string.Equals(
                    arg,
                    "--native-host-proxy",
                    StringComparison.OrdinalIgnoreCase)))
        {
            return true;
        }

        if (args.Any(arg =>
                arg.StartsWith(
                    "--idle-probe-ms=",
                    StringComparison.OrdinalIgnoreCase)))
        {
            return false;
        }

        return inputRedirected && outputRedirected;
    }
}
