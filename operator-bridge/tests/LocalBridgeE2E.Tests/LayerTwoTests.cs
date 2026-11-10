using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.IntegrationHarness;
using WorkspaceControl.OperatorBridge.Simulator.Scenarios;
using WorkspaceControl.OperatorBridge.Simulator.State;
using WorkspaceControl.OperatorBridge.Windows;
using WorkspaceControl.OperatorBridge.Windows.Hotkey;

namespace WorkspaceControl.OperatorBridge.LocalBridgeE2E.Tests;

[TestClass]
public sealed class LayerTwoTests
{
    [TestMethod]
    public async Task SIM004_LocalMaintenanceDrainsBeforeService()
    {
        var world = new SimulatorWorld();
        world.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        var discard = world.Queue("discard", "DISCARD_SESSION");
        var service = world.Queue("service", "RESTORE_AND_SERVICE");
        var browser = new InMemoryBrowserPort();
        browser.Seed("slot-1", 0);
        var clipboard = new StaClipboard();
        var coordinator = CreateCoordinator(
            world,
            browser,
            clipboard,
            new RecordingOperatorSurface());

        var maintenance = await coordinator.DispatchAsync();
        var serviceDispatch = await coordinator.DispatchAsync();
        var submitted = world.HumanSubmit(service);

        Assert.AreEqual(
            DispatchOutcome.LocalCompleted,
            maintenance.Outcome);
        Assert.AreEqual(
            SimActionStatus.Completed,
            discard.Status);
        Assert.AreEqual(
            DispatchOutcome.LocalPrepared,
            serviceDispatch.Outcome);
        Assert.IsTrue(submitted);
        Assert.AreEqual(1, clipboard.WriteCount);
    }

    [TestMethod]
    public async Task SIM006_NoWorkLeavesOsClipboardAndBrowserUntouched()
    {
        var world = new SimulatorWorld();
        var browser = new InMemoryBrowserPort();
        var clipboard = new StaClipboard();
        const string sentinel = "WORKSPACE_SIM_CLIPBOARD_SENTINEL";
        clipboard.WriteText(sentinel);
        var baselineWrites = clipboard.WriteCount;
        var coordinator = CreateCoordinator(
            world,
            browser,
            clipboard,
            new RecordingOperatorSurface());

        var result = await coordinator.DispatchAsync();

        Assert.AreEqual(DispatchOutcome.NoAction, result.Outcome);
        Assert.AreEqual(sentinel, clipboard.ReadTextForTestOnly());
        Assert.AreEqual(baselineWrites, clipboard.WriteCount);
        Assert.AreEqual(0, browser.EffectCount);
    }

    [TestMethod]
    public async Task SIM007_JudgmentGateOpensSurfaceOnly()
    {
        var world = new SimulatorWorld();
        world.Queue("judgment", "OPEN_JUDGMENT_GATE");
        var browser = new InMemoryBrowserPort();
        var clipboard = new StaClipboard();
        const string sentinel = "WORKSPACE_SIM_JUDGMENT_SENTINEL";
        clipboard.WriteText(sentinel);
        var baselineWrites = clipboard.WriteCount;
        var surface = new RecordingOperatorSurface();
        var coordinator = CreateCoordinator(
            world,
            browser,
            clipboard,
            surface);

        var result = await coordinator.DispatchAsync();

        Assert.AreEqual(
            DispatchOutcome.JudgmentGateOpened,
            result.Outcome);
        Assert.AreEqual(1, surface.JudgmentCount);
        Assert.AreEqual(0, browser.EffectCount);
        Assert.AreEqual(baselineWrites, clipboard.WriteCount);
        Assert.AreEqual(sentinel, clipboard.ReadTextForTestOnly());
    }

    [TestMethod]
    public async Task SIM015_HeldRepeatCannotDuplicateDispatch()
    {
        AssertActualCtrlBRegistration();

        var world = new SimulatorWorld();
        world.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        var action = world.Queue("held-repeat", "SERVICE_EXISTING");
        var browser = new InMemoryBrowserPort();
        browser.Seed("slot-1", 0);
        var clipboard = new StaClipboard();
        var actionPort = new SimulatorOperatorActionPort(world)
        {
            ClaimEntered = new TaskCompletionSource(
                TaskCreationOptions.RunContinuationsAsynchronously)
        };
        var gate = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        actionPort.ClaimGate = gate.Task;
        var coordinator = CreateCoordinator(
            world,
            browser,
            clipboard,
            new RecordingOperatorSurface(),
            actionPort);

        var first = coordinator.DispatchAsync();
        await actionPort.ClaimEntered.Task;
        var repeat = await coordinator.DispatchAsync();
        gate.SetResult();
        var firstResult = await first;

        Assert.AreEqual(DispatchOutcome.Busy, repeat.Outcome);
        Assert.AreEqual(
            DispatchOutcome.LocalPrepared,
            firstResult.Outcome);
        Assert.AreEqual(1, action.ClaimCount);
        Assert.AreEqual(1, clipboard.WriteCount);
    }

    [TestMethod]
    public async Task SIM016_SecondPressWhilePreparingCannotClaimSecond()
    {
        var world = new SimulatorWorld();
        world.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        var firstAction = world.Queue("first", "SERVICE_EXISTING");
        var secondAction = world.Queue("second", "SERVICE_EXISTING");
        var browser = new InMemoryBrowserPort();
        browser.Seed("slot-1", 0);
        var clipboard = new StaClipboard();
        var actionPort = new SimulatorOperatorActionPort(world)
        {
            ClaimEntered = new TaskCompletionSource(
                TaskCreationOptions.RunContinuationsAsynchronously)
        };
        var gate = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        actionPort.ClaimGate = gate.Task;
        var coordinator = CreateCoordinator(
            world,
            browser,
            clipboard,
            new RecordingOperatorSurface(),
            actionPort);

        var first = coordinator.DispatchAsync();
        await actionPort.ClaimEntered.Task;
        var secondPress = await coordinator.DispatchAsync();
        gate.SetResult();
        await first;

        Assert.AreEqual(DispatchOutcome.Busy, secondPress.Outcome);
        Assert.AreEqual(1, firstAction.ClaimCount);
        Assert.AreEqual(0, secondAction.ClaimCount);
        Assert.AreEqual(1, clipboard.WriteCount);
    }

    private static SingleFlightDispatchCoordinator CreateCoordinator(
        SimulatorWorld world,
        WorkspaceControl.OperatorBridge.Ports.IBrowserPort browser,
        WorkspaceControl.OperatorBridge.Ports.IClipboardWriter clipboard,
        RecordingOperatorSurface surface,
        SimulatorOperatorActionPort? actionPort = null)
    {
        var state = new BridgeState();
        var diagnostics = new CaptureDiagnostics();
        new BridgeController(
            state,
            new NoopHotkeyRegistrar(),
            diagnostics).SetEnabled(true);

        return new SingleFlightDispatchCoordinator(
            state,
            actionPort ?? new SimulatorOperatorActionPort(world),
            browser,
            clipboard,
            new SystemMonotonicClock(),
            diagnostics,
            surface);
    }

    private static void AssertActualCtrlBRegistration()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                using var window = new HotkeyMessageWindow();
                var registrar =
                    new WindowsHotkeyRegistrar(window.Handle);
                registrar.Register();
                Assert.IsTrue(registrar.IsRegistered);
                registrar.Unregister();
                Assert.IsFalse(registrar.IsRegistered);
            }
            catch (Exception exception)
            {
                failure = exception;
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();

        if (failure is not null)
        {
            throw failure;
        }
    }
}
