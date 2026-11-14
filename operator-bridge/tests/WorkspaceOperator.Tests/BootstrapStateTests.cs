using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class BootstrapStateTests
{
    [TestMethod]
    public void StageSixIntegratedLocalBridgeE2EIsActive()
    {
        Assert.IsTrue(
            string.Equals(
                "IMPL_06_INTEGRATED_LOCAL_BRIDGE_E2E",
                BootstrapState.Stage,
                StringComparison.Ordinal));
    }
}
