namespace WorkspaceControl.OperatorBridge.Contracts.Protocol;

public sealed class ProtocolException : Exception
{
    public ProtocolException(string code)
        : base(code)
    {
        Code = code;
    }

    public string Code { get; }
}
