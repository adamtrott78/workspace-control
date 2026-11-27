using System.Diagnostics;
using System.Runtime.InteropServices;

namespace WorkspaceControl.OperatorBridge.Windows;

public sealed class Win32WorkerWindowSafetyPort : IWorkerWindowSafetyPort
{
    private const int SwRestore = 9;
    private const int SwShowMinNoActive = 7;
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

    public bool ForegroundPreparedWorkerWindow()
    {
        var window = _capturedWindow;
        if (window == 0 || !IsWindow(window) || !IsFirefoxWindow(window))
        {
            window = FindSoleVisibleFirefoxWindow();
            if (window == 0)
            {
                return false;
            }

            _capturedWindow = window;
        }

        if (IsIconic(window))
        {
            _ = ShowWindow(window, SwRestore);
        }

        _ = SetForegroundWindow(window);

        for (var attempt = 0; attempt < 10; attempt++)
        {
            if (GetForegroundWindow() == window)
            {
                return true;
            }

            Thread.Sleep(25);
        }

        return false;
    }

    public bool IsCapturedWorkerWindowForeground()
    {
        var window = _capturedWindow;
        return window != 0 &&
            IsWindow(window) &&
            IsFirefoxWindow(window) &&
            GetForegroundWindow() == window;
    }

    public bool MinimizeCapturedWorkerWindow()
    {
        var window = _capturedWindow;
        if (window == 0 ||
            !IsWindow(window) ||
            !IsFirefoxWindow(window))
        {
            return false;
        }

        _ = ShowWindow(window, SwShowMinNoActive);
        return IsIconic(window);
    }

    private static nint FindSoleVisibleFirefoxWindow()
    {
        var matches = new List<nint>();
        _ = EnumWindows(
            (window, _) =>
            {
                if (IsWindowVisible(window) && IsFirefoxWindow(window))
                {
                    matches.Add(window);
                }

                return true;
            },
            0);

        return matches.Count == 1 ? matches[0] : 0;
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

    private delegate bool EnumWindowsProc(nint hWnd, nint lParam);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumWindows(
        EnumWindowsProc lpEnumFunc,
        nint lParam);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsWindowVisible(nint hWnd);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetForegroundWindow(nint hWnd);

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(nint hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    private static extern bool IsIconic(nint hWnd);
}
