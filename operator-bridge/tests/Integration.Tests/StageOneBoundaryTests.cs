using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Integration.Tests;

[TestClass]
public sealed class StageSixBoundaryTests
{
    [TestMethod]
    public void IntegratedLocalBridgeE2EStageIsExplicit()
    {
        Assert.IsTrue(
            string.Equals(
                "IMPL_06_INTEGRATED_LOCAL_BRIDGE_E2E",
                BootstrapState.Stage,
                StringComparison.Ordinal));
    }
}
