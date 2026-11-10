using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Integration.Tests;

[TestClass]
public sealed class StageFiveBoundaryTests
{
    [TestMethod]
    public void SimulatorFakeWorkerStageIsExplicit()
    {
        Assert.IsTrue(
            string.Equals(
                "IMPL_05_SIMULATOR_FAKE_WORKER",
                BootstrapState.Stage,
                StringComparison.Ordinal));
    }
}
