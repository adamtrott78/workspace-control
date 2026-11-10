using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Windows.Hotkey;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class WindowsHotkeyRegistrarTests
{
    [TestMethod]
    public void RegisterUsesControlBAndNoRepeatThenUnregisters()
    {
        var native = new FakeNativeApi();
        var registrar = new WindowsHotkeyRegistrar((nint)123, native);

        registrar.Register();

        Assert.IsTrue(registrar.IsRegistered);
        Assert.AreEqual((nint)123, native.RegisterHandle);
        Assert.AreEqual(WindowsHotkeyRegistrar.HotkeyId, native.RegisterId);
        Assert.AreEqual(
            WindowsHotkeyRegistrar.ModControl | WindowsHotkeyRegistrar.ModNoRepeat,
            native.RegisterModifiers);
        Assert.AreEqual(WindowsHotkeyRegistrar.VirtualKeyB, native.RegisterVirtualKey);

        registrar.Unregister();

        Assert.IsFalse(registrar.IsRegistered);
        Assert.AreEqual(1, native.UnregisterCalls);
    }

    [TestMethod]
    public void RegistrationConflictFailsClosedWithNativeError()
    {
        var native = new FakeNativeApi
        {
            RegisterResult = false,
            LastError = 1409
        };
        var registrar = new WindowsHotkeyRegistrar((nint)123, native);

        HotkeyRegistrationException? caught = null;
        try
        {
            registrar.Register();
        }
        catch (HotkeyRegistrationException exception)
        {
            caught = exception;
        }

        Assert.IsNotNull(caught);
        Assert.AreEqual(1409, caught.NativeError);
        Assert.IsFalse(registrar.IsRegistered);
        Assert.AreEqual(0, native.UnregisterCalls);
    }

    private sealed class FakeNativeApi : IHotkeyNativeApi
    {
        public bool RegisterResult { get; init; } = true;
        public int LastError { get; init; }
        public nint RegisterHandle { get; private set; }
        public int RegisterId { get; private set; }
        public uint RegisterModifiers { get; private set; }
        public uint RegisterVirtualKey { get; private set; }
        public int UnregisterCalls { get; private set; }

        public bool RegisterHotKey(
            nint windowHandle,
            int id,
            uint modifiers,
            uint virtualKey)
        {
            RegisterHandle = windowHandle;
            RegisterId = id;
            RegisterModifiers = modifiers;
            RegisterVirtualKey = virtualKey;
            return RegisterResult;
        }

        public bool UnregisterHotKey(nint windowHandle, int id)
        {
            UnregisterCalls++;
            return true;
        }

        public int GetLastError() => LastError;
    }
}
