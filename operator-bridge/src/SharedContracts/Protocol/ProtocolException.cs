namespace WorkspaceControl.OperatorBridge.Contracts.Protocol;

public sealed class ProtocolException : InvalidDataException
{
    public ProtocolException(string code)
        : base(code)
    {
        Code = code;
    }

    public string Code { get; }
}
