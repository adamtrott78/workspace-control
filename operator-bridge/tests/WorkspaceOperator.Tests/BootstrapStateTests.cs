using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class BootstrapStateTests
{
    [TestMethod]
    public void StageFourFirefoxMv3AdapterIsActive()
    {
        Assert.IsTrue(
            string.Equals(
                "IMPL_04_FIREFOX_MV3_ADAPTER",
                BootstrapState.Stage,
                StringComparison.Ordinal));
    }
}
