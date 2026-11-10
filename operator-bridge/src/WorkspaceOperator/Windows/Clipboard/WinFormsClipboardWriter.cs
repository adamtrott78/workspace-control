using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Windows.Clipboard;

public sealed class WinFormsClipboardWriter : IClipboardWriter
{
    public void WriteText(string text)
    {
        if (Thread.CurrentThread.GetApartmentState() != ApartmentState.STA)
        {
            throw new InvalidOperationException("Clipboard writes require the STA UI thread.");
        }

        System.Windows.Forms.Clipboard.SetText(text, TextDataFormat.UnicodeText);
    }
}
