using System.ComponentModel;
using System.Runtime.InteropServices;

namespace WorkspaceControl.OperatorBridge.Windows.Hotkey;

internal interface IEnterKeyObservationSource : IDisposable
{
    event EventHandler? PlainEnterPressed;

    void Start();

    void Stop();
}

internal sealed class HumanSubmitConfirmationGate : IDisposable
{
    private readonly IEnterKeyObservationSource _source;
    private readonly Func<bool> _isPreparedWorkerForeground;
    private int _awaiting;
    private int _confirmed;
    private int _disposed;

    public HumanSubmitConfirmationGate(
        Func<bool> isPreparedWorkerForeground)
        : this(
            new LowLevelEnterKeyObservationSource(),
            isPreparedWorkerForeground)
    {
    }

    internal HumanSubmitConfirmationGate(
        IEnterKeyObservationSource source,
        Func<bool> isPreparedWorkerForeground)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(isPreparedWorkerForeground);

        _source = source;
        _isPreparedWorkerForeground = isPreparedWorkerForeground;
        _source.PlainEnterPressed += PlainEnterPressed;
    }

    public bool IsAwaitingConfirmation =>
        Volatile.Read(ref _awaiting) != 0;

    public bool IsConfirmed =>
        Volatile.Read(ref _confirmed) != 0;

    public bool Arm()
    {
        ObjectDisposedException.ThrowIf(
            Volatile.Read(ref _disposed) != 0,
            this);

        Volatile.Write(ref _confirmed, 0);
        Volatile.Write(ref _awaiting, 1);

        try
        {
            _source.Start();
            return true;
        }
        catch
        {
            return false;
        }
    }

    public bool TryConsumeConfirmed()
    {
        if (!IsAwaitingConfirmation || !IsConfirmed)
        {
            return false;
        }

        Volatile.Write(ref _confirmed, 0);
        Volatile.Write(ref _awaiting, 0);
        _source.Stop();
        return true;
    }

    public void Reset()
    {
        Volatile.Write(ref _confirmed, 0);
        Volatile.Write(ref _awaiting, 0);
        _source.Stop();
    }

    private void PlainEnterPressed(object? sender, EventArgs e)
    {
        if (!IsAwaitingConfirmation || IsConfirmed)
        {
            return;
        }

        if (_isPreparedWorkerForeground())
        {
            Volatile.Write(ref _confirmed, 1);
        }
    }

    public void Dispose()
    {
        if (Interlocked.Exchange(ref _disposed, 1) != 0)
        {
            return;
        }

        _source.PlainEnterPressed -= PlainEnterPressed;
        Reset();
        _source.Dispose();
        GC.SuppressFinalize(this);
    }
}

internal sealed class LowLevelEnterKeyObservationSource :
    IEnterKeyObservationSource
{
    private const int WhKeyboardLl = 13;
    private const int WmKeyDown = 0x0100;
    private const int WmSysKeyDown = 0x0104;
    private const uint VkReturn = 0x0D;
    private const int VkShift = 0x10;
    private const int VkControl = 0x11;
    private const int VkMenu = 0x12;

    private readonly LowLevelKeyboardProc _callback;
    private nint _hook;

    public LowLevelEnterKeyObservationSource()
    {
        _callback = HookCallback;
    }

    public event EventHandler? PlainEnterPressed;

    public void Start()
    {
        if (_hook != 0)
        {
            return;
        }

        _hook = SetWindowsHookEx(
            WhKeyboardLl,
            _callback,
            GetModuleHandle(null),
            0);

        if (_hook == 0)
        {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }

    public void Stop()
    {
        var hook = Interlocked.Exchange(ref _hook, 0);
        if (hook != 0)
        {
            _ = UnhookWindowsHookEx(hook);
        }
    }

    private nint HookCallback(
        int nCode,
        nint wParam,
        nint lParam)
    {
        if (nCode >= 0 &&
            (wParam == WmKeyDown || wParam == WmSysKeyDown))
        {
            var data = Marshal.PtrToStructure<KbdLlHookStruct>(lParam);
            if (data.VirtualKey == VkReturn &&
                !IsDown(VkShift) &&
                !IsDown(VkControl) &&
                !IsDown(VkMenu))
            {
                PlainEnterPressed?.Invoke(this, EventArgs.Empty);
            }
        }

        return CallNextHookEx(_hook, nCode, wParam, lParam);
    }

    private static bool IsDown(int virtualKey) =>
        (GetAsyncKeyState(virtualKey) & 0x8000) != 0;

    public void Dispose()
    {
        Stop();
        GC.SuppressFinalize(this);
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct KbdLlHookStruct
    {
        public uint VirtualKey;
        public uint ScanCode;
        public uint Flags;
        public uint Time;
        public nuint ExtraInfo;
    }

    private delegate nint LowLevelKeyboardProc(
        int nCode,
        nint wParam,
        nint lParam);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern nint SetWindowsHookEx(
        int idHook,
        LowLevelKeyboardProc callback,
        nint moduleHandle,
        uint threadId);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool UnhookWindowsHookEx(nint hook);

    [DllImport("user32.dll")]
    private static extern nint CallNextHookEx(
        nint hook,
        int nCode,
        nint wParam,
        nint lParam);

    [DllImport("user32.dll")]
    private static extern short GetAsyncKeyState(int virtualKey);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    private static extern nint GetModuleHandle(string? moduleName);
}
