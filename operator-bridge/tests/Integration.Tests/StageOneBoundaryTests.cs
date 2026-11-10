using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Contracts;

namespace WorkspaceControl.OperatorBridge.Integration.Tests;

[TestClass]
public sealed class StageOneBoundaryTests
{
    [TestMethod]
    public void SkeletonExposesOnlyFrozenProtocolIdentity()
    {
        Assert.AreEqual("IMPL_01_SKELETON_ONLY", BootstrapState.Stage);
        Assert.AreEqual("1.0", BrowserAdapterProtocol.Version);
    }
}
