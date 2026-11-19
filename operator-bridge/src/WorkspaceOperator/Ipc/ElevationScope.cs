using System.Security.Principal;
using WorkspaceControl.OperatorBridge.Contracts;

namespace WorkspaceControl.OperatorBridge.Ipc;

public enum ProcessElevationScope
{
    Standard,
    Elevated
}

public static class ElevationScope
{
    public static ProcessElevationScope Current()
    {
        using var identity = WindowsIdentity.GetCurrent();
        var principal = new WindowsPrincipal(identity);
        return principal.IsInRole(WindowsBuiltInRole.Administrator)
            ? ProcessElevationScope.Elevated
            : ProcessElevationScope.Standard;
    }

    public static string PipeName(ProcessElevationScope scope) =>
        $"{BrowserAdapterProtocol.PipeBaseName}-" +
        (scope == ProcessElevationScope.Elevated ? "elevated" : "standard");
}
