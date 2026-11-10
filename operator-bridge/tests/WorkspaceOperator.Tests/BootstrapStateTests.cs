using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class BootstrapStateTests
{
    [TestMethod]
    public void StageTwoHelperKernelIsActive()
    {
        Assert.AreEqual("IMPL_02_HELPER_KERNEL", BootstrapState.Stage);
    }
}
