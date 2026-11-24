using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Windows.Hotkey;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class HumanSubmitConfirmationGateTests
{
    [TestMethod]
    public void ForegroundPlainEnterUnlocksExactlyOneAdvance()
    {
        var source = new FakeEnterSource();
        var foreground = true;
        using var gate = new HumanSubmitConfirmationGate(
            source,
            () => foreground);

        Assert.IsTrue(gate.Arm());
        Assert.IsTrue(gate.IsAwaitingConfirmation);
        Assert.IsFalse(gate.IsConfirmed);
        Assert.AreEqual(1, source.StartCalls);

        source.RaisePlainEnter();

        Assert.IsTrue(gate.IsConfirmed);
        Assert.IsTrue(gate.TryConsumeConfirmed());
        Assert.IsFalse(gate.IsAwaitingConfirmation);
        Assert.IsFalse(gate.IsConfirmed);
        Assert.AreEqual(1, source.StopCalls);
        Assert.IsFalse(gate.TryConsumeConfirmed());
    }

    [TestMethod]
    public void EnterOutsidePreparedWorkerDoesNotUnlock()
    {
        var source = new FakeEnterSource();
        var foreground = false;
        using var gate = new HumanSubmitConfirmationGate(
            source,
            () => foreground);

        Assert.IsTrue(gate.Arm());
        source.RaisePlainEnter();

        Assert.IsFalse(gate.IsConfirmed);
        Assert.IsFalse(gate.TryConsumeConfirmed());

        foreground = true;
        source.RaisePlainEnter();

        Assert.IsTrue(gate.TryConsumeConfirmed());
    }

    [TestMethod]
    public void ResetStopsObservationAndClearsConfirmation()
    {
        var source = new FakeEnterSource();
        using var gate = new HumanSubmitConfirmationGate(
            source,
            () => true);

        Assert.IsTrue(gate.Arm());
        source.RaisePlainEnter();
        Assert.IsTrue(gate.IsConfirmed);

        gate.Reset();

        Assert.IsFalse(gate.IsAwaitingConfirmation);
        Assert.IsFalse(gate.IsConfirmed);
        Assert.AreEqual(1, source.StopCalls);
    }

    private sealed class FakeEnterSource : IEnterKeyObservationSource
    {
        public event EventHandler? PlainEnterPressed;
        public int StartCalls { get; private set; }
        public int StopCalls { get; private set; }

        public void Start() => StartCalls++;

        public void Stop() => StopCalls++;

        public void RaisePlainEnter() =>
            PlainEnterPressed?.Invoke(this, EventArgs.Empty);

        public void Dispose()
        {
        }
    }
}
