using System.Runtime.InteropServices;

namespace WorkspaceControl.OperatorBridge.Windows.Hotkey;

internal interface IHotkeyNativeApi
{
    bool RegisterHotKey(nint windowHandle, int id, uint modifiers, uint virtualKey);

    bool UnregisterHotKey(nint windowHandle, int id);

    int GetLastError();
}

internal sealed class Win32HotkeyNativeApi : IHotkeyNativeApi
{
    public bool RegisterHotKey(nint windowHandle, int id, uint modifiers, uint virtualKey) =>
        NativeMethods.RegisterHotKey(windowHandle, id, modifiers, virtualKey);

    public bool UnregisterHotKey(nint windowHandle, int id) =>
        NativeMethods.UnregisterHotKey(windowHandle, id);

    public int GetLastError() => Marshal.GetLastWin32Error();

    private static class NativeMethods
    {
        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool RegisterHotKey(
            nint hWnd,
            int id,
            uint fsModifiers,
            uint vk);

        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool UnregisterHotKey(nint hWnd, int id);
    }
}
