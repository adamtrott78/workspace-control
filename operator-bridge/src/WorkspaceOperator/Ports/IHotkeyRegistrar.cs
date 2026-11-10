namespace WorkspaceControl.OperatorBridge.Ports;

public interface IHotkeyRegistrar
{
    bool IsRegistered { get; }

    void Register();

    void Unregister();
}
