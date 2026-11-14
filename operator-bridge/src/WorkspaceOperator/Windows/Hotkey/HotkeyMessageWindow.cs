namespace WorkspaceControl.OperatorBridge.Windows.Hotkey;

public sealed class HotkeyMessageWindow : NativeWindow, IDisposable
{
    public const int WmHotkey = 0x0312;

    public event EventHandler? HotkeyPressed;

    public HotkeyMessageWindow()
    {
        CreateHandle(new CreateParams
        {
            Caption = "WorkspaceControl.OperatorBridge.HotkeyWindow"
        });
    }

    protected override void WndProc(ref Message m)
    {
        if (m.Msg == WmHotkey)
        {
            HotkeyPressed?.Invoke(this, EventArgs.Empty);
        }

        base.WndProc(ref m);
    }

    public void Dispose()
    {
        DestroyHandle();
        GC.SuppressFinalize(this);
    }
}
