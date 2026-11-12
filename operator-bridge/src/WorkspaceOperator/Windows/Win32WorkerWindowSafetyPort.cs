using System.Diagnostics;
using System.Runtime.InteropServices;

namespace WorkspaceControl.OperatorBridge.Windows;

public sealed class Win32WorkerWindowSafetyPort : IWorkerWindowSafetyPort
{
    private const int SwMinimize = 6;
    private nint _capturedWindow;

    public bool CaptureForegroundPreparedWorkerWindow()
    {
        var window = GetForegroundWindow();
        if (!IsFirefoxWindow(window))
        {
            return false;
        }

        _capturedWindow = window;
        return true;
    }

    public bool MinimizeCapturedWorkerWindow()
    {
        var window = _capturedWindow;
        if (window == 0 ||
            !IsWindow(window) ||
            GetForegroundWindow() != window ||
            !IsFirefoxWindow(window))
        {
            return false;
        }

        _ = ShowWindow(window, SwMinimize);
        return IsIconic(window);
    }

    private static bool IsFirefoxWindow(nint window)
    {
        if (window == 0 || !IsWindow(window))
        {
            return false;
        }

        _ = GetWindowThreadProcessId(window, out var processId);
        if (processId == 0)
        {
            return false;
        }

        try
        {
            using var process = Process.GetProcessById((int)processId);
            return string.Equals(
                process.ProcessName,
                "firefox",
                StringComparison.OrdinalIgnoreCase);
        }
        catch (ArgumentException)
        {
            return false;
        }
        catch (InvalidOperationException)
        {
            return false;
        }
    }

    [DllImport("user32.dll")]
    private static extern nint GetForegroundWindow();

    [DllImport("user32.dll")]
    private static extern bool IsWindow(nint hWnd);

    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(
        nint hWnd,
        out uint processId);

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(nint hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    private static extern bool IsIconic(nint hWnd);
}
