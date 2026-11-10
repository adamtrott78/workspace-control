using WorkspaceControl.OperatorBridge.Ports;
using WorkspaceControl.OperatorBridge.Windows.Clipboard;

namespace WorkspaceControl.OperatorBridge.IntegrationHarness;

public sealed class StaClipboard : IClipboardWriter
{
    private readonly WinFormsClipboardWriter _inner = new();

    public int WriteCount { get; private set; }

    public void WriteText(string text)
    {
        RunSta(() => _inner.WriteText(text));
        WriteCount++;
    }

    public string ReadTextForTestOnly() =>
        RunSta(() => System.Windows.Forms.Clipboard.GetText());

    private static void RunSta(Action action)
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                action();
            }
            catch (Exception exception)
            {
                failure = exception;
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();
        if (failure is not null)
        {
            throw failure;
        }
    }

    private static T RunSta<T>(Func<T> action)
    {
        Exception? failure = null;
        T? value = default;
        var thread = new Thread(() =>
        {
            try
            {
                value = action();
            }
            catch (Exception exception)
            {
                failure = exception;
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();
        if (failure is not null)
        {
            throw failure;
        }
        return value!;
    }
}
