namespace WorkspaceControl.OperatorBridge.Diagnostics;

public static class ErrorNormalizer
{
    public static string FromException(Exception exception) =>
        exception.GetType().Name;
}
