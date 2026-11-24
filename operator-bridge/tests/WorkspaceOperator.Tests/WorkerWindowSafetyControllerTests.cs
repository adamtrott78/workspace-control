using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Windows;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class WorkerWindowSafetyControllerTests
{
    [TestMethod]
    public void NoActionMinimizeUsesOnlyPreviouslyCapturedPreparedWindow()
    {
        var port = new FakePort
        {
            CaptureResult = true,
            ForegroundResult = true,
            MinimizeResult = true
        };
        var controller = new WorkerWindowSafetyController(port);

        Assert.IsTrue(controller.RecordPreparedWorkerWindow());
        Assert.IsTrue(controller.ForegroundPreparedWorkerWindow());
        Assert.IsTrue(controller.IsPreparedWorkerWindowForeground());
        Assert.IsTrue(controller.MinimizeAfterNoAction());
        Assert.AreEqual(1, port.CaptureCalls);
        Assert.AreEqual(1, port.ForegroundCalls);
        Assert.AreEqual(1, port.MinimizeCalls);
    }

    [TestMethod]
    public void ForegroundRetriesUntilPreparedWorkerWinsTransientFocusRace()
    {
        var port = new FakePort
        {
            ForegroundSucceedsOnCall = 3
        };
        var controller = new WorkerWindowSafetyController(port);

        Assert.IsTrue(
            controller.ForegroundPreparedWorkerWindowWithRetries(
                attempts: 4,
                delayMilliseconds: 0));
        Assert.AreEqual(3, port.ForegroundCalls);
    }

    [TestMethod]
    public void ForegroundRetriesFailClosedWhenWorkerNeverWinsFocus()
    {
        var port = new FakePort();
        var controller = new WorkerWindowSafetyController(port);

        Assert.IsFalse(
            controller.ForegroundPreparedWorkerWindowWithRetries(
                attempts: 3,
                delayMilliseconds: 0));
        Assert.AreEqual(3, port.ForegroundCalls);
    }

    [TestMethod]
    public void CaptureFailureDoesNotPretendNoActionMinimizeSucceeded()
    {
        var port = new FakePort
        {
            CaptureResult = false,
            MinimizeResult = false
        };
        var controller = new WorkerWindowSafetyController(port);

        Assert.IsFalse(controller.RecordPreparedWorkerWindow());
        Assert.IsFalse(controller.MinimizeAfterNoAction());
    }

    private sealed class FakePort : IWorkerWindowSafetyPort
    {
        public bool CaptureResult { get; set; }
        public bool ForegroundResult { get; set; }
        public int ForegroundSucceedsOnCall { get; set; }
        public bool MinimizeResult { get; set; }
        public bool IsForegroundResult { get; set; } = true;
        public int CaptureCalls { get; private set; }
        public int ForegroundCalls { get; private set; }
        public int MinimizeCalls { get; private set; }

        public bool CaptureForegroundPreparedWorkerWindow()
        {
            CaptureCalls++;
            return CaptureResult;
        }

        public bool ForegroundPreparedWorkerWindow()
        {
            ForegroundCalls++;
            return ForegroundResult ||
                (ForegroundSucceedsOnCall > 0 &&
                 ForegroundCalls >= ForegroundSucceedsOnCall);
        }

        public bool IsCapturedWorkerWindowForeground() =>
            IsForegroundResult;

        public bool MinimizeCapturedWorkerWindow()
        {
            MinimizeCalls++;
            return MinimizeResult;
        }
    }
}
