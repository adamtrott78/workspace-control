using System.Runtime.ExceptionServices;
using System.Runtime.InteropServices;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Windows.Clipboard;

public sealed class WinFormsClipboardWriter : IClipboardWriter
{
    private const int MaxClipboardAttempts = 5;

    public void WriteText(string text)
    {
        ArgumentNullException.ThrowIfNull(text);

        if (Thread.CurrentThread.GetApartmentState() == ApartmentState.STA)
        {
            WriteClipboardText(text);
            return;
        }

        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                WriteClipboardText(text);
            }
            catch (Exception exception)
            {
                failure = exception;
            }
        })
        {
            IsBackground = true,
            Name = "WorkspaceOperatorClipboardSTA"
        };

        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();

        if (failure is not null)
        {
            ExceptionDispatchInfo.Capture(failure).Throw();
        }
    }

    private static void WriteClipboardText(string text)
    {
        for (var attempt = 1; attempt <= MaxClipboardAttempts; attempt++)
        {
            try
            {
                System.Windows.Forms.Clipboard.SetText(
                    text,
                    TextDataFormat.UnicodeText);
                return;
            }
            catch (ExternalException)
                when (attempt < MaxClipboardAttempts)
            {
                Thread.Sleep(20 * attempt);
            }
        }
    }
}
