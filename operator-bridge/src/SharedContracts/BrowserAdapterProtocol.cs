namespace WorkspaceControl.OperatorBridge.Contracts;

public static class BrowserAdapterProtocol
{
    public const string Version = "1.0";
    public const int MaxFrameBytes = 65_536;
    public const string NativeHostName = "com.workspacecontrol.operator_bridge";
    public const string FirefoxExtensionId = "workspace-control-operator@adamtrott78.local";
    public const string PipeBaseName = "workspace-control-operator-bridge-v1";
}
