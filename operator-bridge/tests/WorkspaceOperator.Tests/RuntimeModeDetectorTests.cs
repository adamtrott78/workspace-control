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

    [TestMethod]
    public void FirefoxOriginArgumentsStillSelectProxyWithRedirectedStdio()
    {
        Assert.IsTrue(
            RuntimeModeDetector.IsNativeHostProxy(
                new[]
                {
                    "moz-extension://workspace-control-operator/",
                    "--parent-window=123"
                },
                inputRedirected: true,
                outputRedirected: true));
    }

    [TestMethod]
    public void BrowserArgumentsWithoutNativeStdioFailClosed()
    {
        Assert.IsFalse(
            RuntimeModeDetector.IsNativeHostProxy(
                new[] { "moz-extension://workspace-control-operator/" },
                inputRedirected: false,
                outputRedirected: false));
    }
}
