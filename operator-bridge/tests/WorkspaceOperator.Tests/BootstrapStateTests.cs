using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class BootstrapStateTests
{
    [TestMethod]
    public void StageOneRemainsSkeletonOnly()
    {
        Assert.AreEqual("IMPL_01_SKELETON_ONLY", BootstrapState.Stage);
    }
}
