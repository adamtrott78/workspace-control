using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Ipc;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class RuntimeModeDetectorTests
{
    [TestMethod]
    public void ExplicitNativeHostFlagSelectsProxyMode()
    {
        Assert.IsTrue(
            RuntimeModeDetector.IsNativeHostProxy(
                new[] { "--native-host-proxy" }));
    }

    [TestMethod]
    public void IdleProbeNeverSelectsProxyMode()
    {
        Assert.IsFalse(
            RuntimeModeDetector.IsNativeHostProxy(
                new[] { "--idle-probe-ms=7000" }));
    }
}
