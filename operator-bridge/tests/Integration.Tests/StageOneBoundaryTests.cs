using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Integration.Tests;

[TestClass]
public sealed class StageFourBoundaryTests
{
    [TestMethod]
    public void FirefoxMv3AdapterStageIsExplicit()
    {
        Assert.IsTrue(
            string.Equals(
                "IMPL_04_FIREFOX_MV3_ADAPTER",
                BootstrapState.Stage,
                StringComparison.Ordinal));
    }
}
