using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Integration.Tests;

[TestClass]
public sealed class StageTwoBoundaryTests
{
    [TestMethod]
    public void HelperKernelStageIsExplicit()
    {
        Assert.IsTrue(
            string.Equals(
                "IMPL_02_HELPER_KERNEL",
                BootstrapState.Stage,
                StringComparison.Ordinal));
    }
}
