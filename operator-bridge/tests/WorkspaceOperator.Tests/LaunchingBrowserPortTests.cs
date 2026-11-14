using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class LaunchingBrowserPortTests
{
    [TestMethod]
    public async Task ConnectedAdapterDelegatesWithoutLaunching()
    {
        var inner = new FakeBrowserPort();
        var connection = new FakeConnection
        {
            IsConnected = true
        };
        var launcher = new FakeLauncher();
        var port = Create(inner, connection, launcher);

        var result = await port.PrepareTargetAsync(
            new BrowserTarget("worker-a", 0),
            CancellationToken.None);

        Assert.IsTrue(result.IsApplied);
        Assert.AreEqual(0, launcher.LaunchCount);
        Assert.AreEqual(1, inner.PrepareCount);
    }

    [TestMethod]
    public async Task DisconnectedAdapterLaunchesAndWaitsBeforeDelegating()
    {
        var inner = new FakeBrowserPort();
        var connection = new FakeConnection
        {
            ConnectOnWait = true
        };
        var launcher = new FakeLauncher();
        var port = Create(inner, connection, launcher);

        var result = await port.CreateTargetAsync(
            new BrowserTarget("worker-a", 0),
            CancellationToken.None);

        Assert.IsTrue(result.IsApplied);
        Assert.AreEqual(1, launcher.LaunchCount);
        Assert.AreEqual(1, connection.WaitCount);
        Assert.AreEqual(1, inner.CreateCount);
    }

    [TestMethod]
    public async Task LaunchFailureRejectsWithoutBrowserMutation()
    {
        var inner = new FakeBrowserPort();
        var connection = new FakeConnection();
        var launcher = new FakeLauncher
        {
            Result = new WorkerEnvironmentLaunchResult(
                false,
                "FIREFOX_EXECUTABLE_NOT_FOUND")
        };
        var port = Create(inner, connection, launcher);

        var result = await port.FocusTargetAsync(
            new BrowserTarget("worker-a", 0),
            CancellationToken.None);

        Assert.AreEqual(BrowserOutcome.Rejected, result.Outcome);
        Assert.AreEqual(
            "BROWSER_ADAPTER_UNAVAILABLE_AFTER_LAUNCH",
            result.NormalizedError);
        Assert.AreEqual(1, launcher.LaunchCount);
        Assert.AreEqual(0, connection.WaitCount);
        Assert.AreEqual(0, inner.FocusCount);
    }

    [TestMethod]
    public async Task ConnectionTimeoutRejectsWithoutBrowserMutation()
    {
        var inner = new FakeBrowserPort();
        var connection = new FakeConnection();
        var launcher = new FakeLauncher();
        var port = Create(inner, connection, launcher);

        var result = await port.RestoreTargetAsync(
            new BrowserTarget("worker-a", 0),
            CancellationToken.None);

        Assert.AreEqual(BrowserOutcome.Rejected, result.Outcome);
        Assert.AreEqual(1, launcher.LaunchCount);
        Assert.AreEqual(1, connection.WaitCount);
        Assert.AreEqual(0, inner.RestoreCount);
    }

    [TestMethod]
    public async Task DiscardAndCloseNeverLaunchStoppedEnvironment()
    {
        var inner = new FakeBrowserPort();
        var connection = new FakeConnection();
        var launcher = new FakeLauncher();
        var port = Create(inner, connection, launcher);
        var target = new BrowserTarget("worker-a", 0);

        var discard = await port.DiscardTargetAsync(
            target,
            CancellationToken.None);
        var close = await port.CloseTargetAsync(
            target,
            CancellationToken.None);

        Assert.IsTrue(discard.IsApplied);
        Assert.IsTrue(close.IsApplied);
        Assert.AreEqual(0, launcher.LaunchCount);
        Assert.AreEqual(1, inner.DiscardCount);
        Assert.AreEqual(1, inner.CloseCount);
    }

    private static LaunchingBrowserPort Create(
        FakeBrowserPort inner,
        FakeConnection connection,
        FakeLauncher launcher) =>
        new(
            inner,
            connection,
            launcher,
            TimeSpan.FromMilliseconds(50));

    private sealed class FakeConnection : IBrowserAdapterConnection
    {
        public bool IsConnected { get; set; }
        public bool ConnectOnWait { get; set; }
        public int WaitCount { get; private set; }

        public Task<bool> WaitForConnectionAsync(
            TimeSpan timeout,
            CancellationToken cancellationToken = default)
        {
            WaitCount++;
            if (ConnectOnWait)
            {
                IsConnected = true;
            }
            return Task.FromResult(IsConnected);
        }
    }

    private sealed class FakeLauncher : IWorkerEnvironmentLauncher
    {
        public int LaunchCount { get; private set; }
        public WorkerEnvironmentLaunchResult Result { get; set; } =
            new(true);

        public Task<WorkerEnvironmentLaunchResult> LaunchAsync(
            CancellationToken cancellationToken)
        {
            LaunchCount++;
            return Task.FromResult(Result);
        }
    }

    private sealed class FakeBrowserPort : IBrowserPort
    {
        public int PrepareCount { get; private set; }
        public int FocusCount { get; private set; }
        public int CreateCount { get; private set; }
        public int RestoreCount { get; private set; }
        public int DiscardCount { get; private set; }
        public int CloseCount { get; private set; }

        public Task<BrowserResult> PrepareTargetAsync(
            BrowserTarget target,
            CancellationToken cancellationToken)
        {
            PrepareCount++;
            return Task.FromResult(BrowserResult.Applied());
        }

        public Task<BrowserResult> FocusTargetAsync(
            BrowserTarget target,
            CancellationToken cancellationToken)
        {
            FocusCount++;
            return Task.FromResult(BrowserResult.Applied());
        }

        public Task<BrowserResult> CreateTargetAsync(
            BrowserTarget target,
            CancellationToken cancellationToken)
        {
            CreateCount++;
            return Task.FromResult(BrowserResult.Applied());
        }

        public Task<BrowserResult> RestoreTargetAsync(
            BrowserTarget target,
            CancellationToken cancellationToken)
        {
            RestoreCount++;
            return Task.FromResult(BrowserResult.Applied());
        }

        public Task<BrowserResult> DiscardTargetAsync(
            BrowserTarget target,
            CancellationToken cancellationToken)
        {
            DiscardCount++;
            return Task.FromResult(BrowserResult.Applied());
        }

        public Task<BrowserResult> CloseTargetAsync(
            BrowserTarget target,
            CancellationToken cancellationToken)
        {
            CloseCount++;
            return Task.FromResult(BrowserResult.Applied());
        }
    }
}
