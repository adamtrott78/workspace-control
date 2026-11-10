using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class BridgeControllerTests
{
    [TestMethod]
    public void EnableRegistersHotkeyAndDisableUnregistersIt()
    {
        var state = new BridgeState();
        var hotkey = new FakeHotkeyRegistrar();
        var diagnostics = new CaptureDiagnostics();
        var controller = new BridgeController(state, hotkey, diagnostics);

        controller.SetEnabled(true);

        Assert.IsTrue(controller.IsEnabled);
        Assert.AreEqual(1, hotkey.RegisterCalls);
        Assert.AreEqual(0, hotkey.UnregisterCalls);

        controller.SetEnabled(false);

        Assert.IsFalse(controller.IsEnabled);
        Assert.AreEqual(1, hotkey.RegisterCalls);
        Assert.AreEqual(1, hotkey.UnregisterCalls);
    }

    [TestMethod]
    public void RegistrationFailureLeavesBridgeOff()
    {
        var state = new BridgeState();
        var hotkey = new FakeHotkeyRegistrar { ThrowOnRegister = true };
        var diagnostics = new CaptureDiagnostics();
        var controller = new BridgeController(state, hotkey, diagnostics);

        Assert.ThrowsException<InvalidOperationException>(() =>
            controller.SetEnabled(true));

        Assert.IsFalse(controller.IsEnabled);
        Assert.IsFalse(hotkey.IsRegistered);
        Assert.AreEqual("REJECTED", diagnostics.Events[^1].Outcome);
    }

    private sealed class FakeHotkeyRegistrar : IHotkeyRegistrar
    {
        public bool IsRegistered { get; private set; }
        public int RegisterCalls { get; private set; }
        public int UnregisterCalls { get; private set; }
        public bool ThrowOnRegister { get; init; }

        public void Register()
        {
            RegisterCalls++;
            if (ThrowOnRegister)
            {
                throw new InvalidOperationException("conflict");
            }

            IsRegistered = true;
        }

        public void Unregister()
        {
            UnregisterCalls++;
            IsRegistered = false;
        }
    }

    private sealed class CaptureDiagnostics : IDiagnosticsSink
    {
        public List<DiagnosticEvent> Events { get; } = [];

        public void Write(DiagnosticEvent diagnosticEvent) =>
            Events.Add(diagnosticEvent);
    }
}
