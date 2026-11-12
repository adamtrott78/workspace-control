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
    internal const uint ModNoRepeat = 0x4000;

    private readonly nint _windowHandle;
    private readonly SchedulerHotkeyBinding _binding;
    private readonly IHotkeyNativeApi _nativeApi;

    public WindowsHotkeyRegistrar(nint windowHandle)
        : this(
            windowHandle,
            SchedulerHotkeyBinding.Default,
            new Win32HotkeyNativeApi())
    {
    }

    public WindowsHotkeyRegistrar(
        nint windowHandle,
        SchedulerHotkeyBinding binding)
        : this(windowHandle, binding, new Win32HotkeyNativeApi())
    {
    }

    internal WindowsHotkeyRegistrar(
        nint windowHandle,
        IHotkeyNativeApi nativeApi)
        : this(windowHandle, SchedulerHotkeyBinding.Default, nativeApi)
    {
    }

    internal WindowsHotkeyRegistrar(
        nint windowHandle,
        SchedulerHotkeyBinding binding,
        IHotkeyNativeApi nativeApi)
    {
        _windowHandle = windowHandle;
        _binding = binding;
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
                _binding.Modifiers | ModNoRepeat,
                _binding.VirtualKey))
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
