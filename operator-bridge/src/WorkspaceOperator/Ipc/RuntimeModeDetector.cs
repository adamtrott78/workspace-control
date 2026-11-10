namespace WorkspaceControl.OperatorBridge.Ipc;

public static class RuntimeModeDetector
{
    public static bool IsNativeHostProxy(string[] args)
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

        return args.Length == 0 &&
               Console.IsInputRedirected &&
               Console.IsOutputRedirected;
    }
}
