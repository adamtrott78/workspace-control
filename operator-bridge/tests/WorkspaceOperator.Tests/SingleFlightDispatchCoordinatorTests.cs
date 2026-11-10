using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class SingleFlightDispatchCoordinatorTests
{
    [TestMethod]
    public async Task BridgeOffHasNoClaimBrowserOrClipboardSideEffects()
    {
        var fixture = new Fixture(enabled: false);

        var result = await fixture.Coordinator.DispatchAsync();

        Assert.AreEqual(DispatchOutcome.Disabled, result.Outcome);
        Assert.AreEqual(0, fixture.Actions.ClaimCalls);
        Assert.AreEqual(0, fixture.Browser.PrepareCalls);
        Assert.AreEqual(0, fixture.Clipboard.WriteCalls);
    }

    [TestMethod]
    public async Task NoActionLeavesBrowserAndClipboardUntouched()
    {
        var fixture = new Fixture(enabled: true);
        fixture.Actions.NextAction = null;

        var result = await fixture.Coordinator.DispatchAsync();

        Assert.AreEqual(DispatchOutcome.NoAction, result.Outcome);
        Assert.AreEqual(1, fixture.Actions.ClaimCalls);
        Assert.AreEqual(0, fixture.Browser.PrepareCalls);
        Assert.AreEqual(0, fixture.Clipboard.WriteCalls);
    }

    [TestMethod]
    public async Task ClipboardOccursOnlyAfterPrepareAndRevalidateBeforeFinalFocus()
    {
        var fixture = new Fixture(enabled: true);

        var result = await fixture.Coordinator.DispatchAsync();

        Assert.AreEqual(DispatchOutcome.LocalPrepared, result.Outcome);
        CollectionAssert.AreEqual(
            new[] { "claim", "prepare", "revalidate", "clipboard", "focus", "local_prepared" },
            fixture.Order);
        Assert.AreEqual("PACKET-SECRET-CONTENT", fixture.Clipboard.LastText);
        Assert.AreEqual(1, fixture.Actions.LocalPreparedCalls);
    }

    [TestMethod]
    public async Task StaleRevalidationPreventsClipboardAndFinalFocus()
    {
        var fixture = new Fixture(enabled: true);
        fixture.Actions.RevalidateResult = false;

        var result = await fixture.Coordinator.DispatchAsync();

        Assert.AreEqual(DispatchOutcome.Stale, result.Outcome);
        CollectionAssert.AreEqual(
            new[] { "claim", "prepare", "revalidate", "local_failure" },
            fixture.Order);
        Assert.AreEqual(0, fixture.Clipboard.WriteCalls);
        Assert.AreEqual(0, fixture.Browser.FocusCalls);
    }

    [TestMethod]
    public async Task SecondDispatchWhileFirstIsPreparingReturnsBusyWithoutSecondClaim()
    {
        var fixture = new Fixture(enabled: true);
        var releaseClaim = new TaskCompletionSource<OperatorAction?>(
            TaskCreationOptions.RunContinuationsAsynchronously);
        fixture.Actions.ClaimGate = releaseClaim.Task;

        var first = fixture.Coordinator.DispatchAsync();
        await fixture.Actions.FirstClaimEntered.Task;

        var second = await fixture.Coordinator.DispatchAsync();

        Assert.AreEqual(DispatchOutcome.Busy, second.Outcome);
        Assert.AreEqual(1, fixture.Actions.ClaimCalls);

        releaseClaim.SetResult(null);
        var firstResult = await first;
        Assert.AreEqual(DispatchOutcome.NoAction, firstResult.Outcome);
    }

    [TestMethod]
    public async Task DiagnosticEventsNeverContainPacketText()
    {
        var fixture = new Fixture(enabled: true);

        var result = await fixture.Coordinator.DispatchAsync();

        Assert.AreEqual(DispatchOutcome.LocalPrepared, result.Outcome);
        var joined = string.Join(
            Environment.NewLine,
            fixture.Diagnostics.Events.Select(e =>
                System.Text.Json.JsonSerializer.Serialize(e)));
        StringAssert.DoesNotContain(joined, "PACKET-SECRET-CONTENT");
    }

    private sealed class Fixture
    {
        public Fixture(bool enabled)
        {
            State.SetEnabled(enabled);
            Actions.Order = Order;
            Browser.Order = Order;
            Clipboard.Order = Order;
            Coordinator = new SingleFlightDispatchCoordinator(
                State,
                Actions,
                Browser,
                Clipboard,
                new FakeClock(),
                Diagnostics);
        }

        public List<string> Order { get; } = [];
        public BridgeState State { get; } = new();
        public FakeActionPort Actions { get; } = new();
        public FakeBrowserPort Browser { get; } = new();
        public FakeClipboard Clipboard { get; } = new();
        public CaptureDiagnostics Diagnostics { get; } = new();
        public SingleFlightDispatchCoordinator Coordinator { get; }
    }

    private sealed class FakeActionPort : IOperatorActionPort
    {
        public List<string> Order { get; set; } = [];
        public int ClaimCalls { get; private set; }
        public int LocalPreparedCalls { get; private set; }
        public bool RevalidateResult { get; set; } = true;
        public Task<OperatorAction?>? ClaimGate { get; set; }
        public TaskCompletionSource FirstClaimEntered { get; } =
            new(TaskCreationOptions.RunContinuationsAsynchronously);
        public OperatorAction? NextAction { get; set; } = new(
            new ActionIdentity("action-1", "slot-1", 7),
            "PACKET-SECRET-CONTENT",
            "payload-ref-1",
            new string('a', 64));

        public async Task<OperatorAction?> ClaimNextAsync(
            CancellationToken cancellationToken)
        {
            ClaimCalls++;
            Order.Add("claim");
            FirstClaimEntered.TrySetResult();
            if (ClaimGate is not null)
            {
                return await ClaimGate;
            }

            return NextAction;
        }

        public Task<bool> RevalidateAsync(
            ActionIdentity identity,
            CancellationToken cancellationToken)
        {
            Order.Add("revalidate");
            return Task.FromResult(RevalidateResult);
        }

        public Task RecordLocalPreparedAsync(
            ActionIdentity identity,
            CancellationToken cancellationToken)
        {
            LocalPreparedCalls++;
            Order.Add("local_prepared");
            return Task.CompletedTask;
        }

        public Task RecordLocalFailureAsync(
            ActionIdentity identity,
            string normalizedError,
            CancellationToken cancellationToken)
        {
            Order.Add("local_failure");
            return Task.CompletedTask;
        }
    }

    private sealed class FakeBrowserPort : IBrowserPort
    {
        public List<string> Order { get; set; } = [];
        public int PrepareCalls { get; private set; }
        public int FocusCalls { get; private set; }

        public Task<BrowserResult> PrepareTargetAsync(
            BrowserTarget target,
            CancellationToken cancellationToken)
        {
            PrepareCalls++;
            Order.Add("prepare");
            return Task.FromResult(BrowserResult.Applied());
        }

        public Task<BrowserResult> FocusTargetAsync(
            BrowserTarget target,
            CancellationToken cancellationToken)
        {
            FocusCalls++;
            Order.Add("focus");
            return Task.FromResult(BrowserResult.Applied());
        }
    }

    private sealed class FakeClipboard : IClipboardWriter
    {
        public List<string> Order { get; set; } = [];
        public int WriteCalls { get; private set; }
        public string? LastText { get; private set; }

        public void WriteText(string text)
        {
            WriteCalls++;
            LastText = text;
            Order.Add("clipboard");
        }
    }

    private sealed class FakeClock : IMonotonicClock
    {
        public long GetTimestamp() => 100;

        public TimeSpan GetElapsedTime(long startingTimestamp) =>
            TimeSpan.FromMilliseconds(5);
    }

    private sealed class CaptureDiagnostics : IDiagnosticsSink
    {
        public List<DiagnosticEvent> Events { get; } = [];

        public void Write(DiagnosticEvent diagnosticEvent) =>
            Events.Add(diagnosticEvent);
    }
}
