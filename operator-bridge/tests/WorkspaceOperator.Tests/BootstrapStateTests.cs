using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class BootstrapStateTests
{
    [TestMethod]
    public void StageFiveSimulatorFakeWorkerIsActive()
    {
        Assert.IsTrue(
            string.Equals(
                "IMPL_05_SIMULATOR_FAKE_WORKER",
                BootstrapState.Stage,
                StringComparison.Ordinal));
    }
}
