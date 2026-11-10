using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Windows.Hotkey;

public sealed class HotkeyRegistrationException : InvalidOperationException
{
    public HotkeyRegistrationException(int nativeError)
        : base($"Global scheduler hotkey registration failed with Win32 error {nativeError}.")
    {
        NativeError = nativeError;
    }

    public int NativeError { get; }
}

public sealed class WindowsHotkeyRegistrar : IHotkeyRegistrar
{
    internal const int HotkeyId = 0x5743;
    internal const uint ModControl = 0x0002;
    internal const uint ModNoRepeat = 0x4000;
    internal const uint VirtualKeyB = 0x42;

    private readonly nint _windowHandle;
    private readonly IHotkeyNativeApi _nativeApi;

    public WindowsHotkeyRegistrar(nint windowHandle)
        : this(windowHandle, new Win32HotkeyNativeApi())
    {
    }

    internal WindowsHotkeyRegistrar(nint windowHandle, IHotkeyNativeApi nativeApi)
    {
        _windowHandle = windowHandle;
        _nativeApi = nativeApi;
    }

    public bool IsRegistered { get; private set; }

    public void Register()
    {
        if (IsRegistered)
        {
            return;
        }

        if (!_nativeApi.RegisterHotKey(
                _windowHandle,
                HotkeyId,
                ModControl | ModNoRepeat,
                VirtualKeyB))
        {
            throw new HotkeyRegistrationException(_nativeApi.GetLastError());
        }

        IsRegistered = true;
    }

    public void Unregister()
    {
        if (!IsRegistered)
        {
            return;
        }

        _nativeApi.UnregisterHotKey(_windowHandle, HotkeyId);
        IsRegistered = false;
    }
}
