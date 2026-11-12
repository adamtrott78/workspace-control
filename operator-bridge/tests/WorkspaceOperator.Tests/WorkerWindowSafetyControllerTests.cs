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
            MinimizeResult = true
        };
        var controller = new WorkerWindowSafetyController(port);

        Assert.IsTrue(controller.RecordPreparedWorkerWindow());
        Assert.IsTrue(controller.MinimizeAfterNoAction());
        Assert.AreEqual(1, port.CaptureCalls);
        Assert.AreEqual(1, port.MinimizeCalls);
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
        public bool MinimizeResult { get; set; }
        public int CaptureCalls { get; private set; }
        public int MinimizeCalls { get; private set; }

        public bool CaptureForegroundPreparedWorkerWindow()
        {
            CaptureCalls++;
            return CaptureResult;
        }

        public bool MinimizeCapturedWorkerWindow()
        {
            MinimizeCalls++;
            return MinimizeResult;
        }
    }
}
