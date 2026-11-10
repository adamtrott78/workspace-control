using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Integration.Tests;

[TestClass]
public sealed class StageThreeBoundaryTests
{
    [TestMethod]
    public void NativeMessagingIpcStageIsExplicit()
    {
        Assert.IsTrue(
            string.Equals(
                "IMPL_03_NATIVE_MESSAGING_IPC",
                BootstrapState.Stage,
                StringComparison.Ordinal));
    }
}
