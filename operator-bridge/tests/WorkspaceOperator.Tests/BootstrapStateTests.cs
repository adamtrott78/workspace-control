using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class BootstrapStateTests
{
    [TestMethod]
    public void StageThreeNativeMessagingIpcIsActive()
    {
        Assert.IsTrue(
            string.Equals(
                "IMPL_03_NATIVE_MESSAGING_IPC",
                BootstrapState.Stage,
                StringComparison.Ordinal));
    }
}
