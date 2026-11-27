using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Contracts;

namespace WorkspaceControl.OperatorBridge.Protocol.Tests;

[TestClass]
public sealed class ProtocolIdentityTests
{
    [TestMethod]
    public void FrozenProtocolIdentityMatchesUx12Contract()
    {
        Assert.AreEqual("1.0", BrowserAdapterProtocol.Version);
        Assert.AreEqual(65_536, BrowserAdapterProtocol.MaxFrameBytes);
        Assert.AreEqual("com.workspacecontrol.operator_bridge", BrowserAdapterProtocol.NativeHostName);
        Assert.AreEqual("workspace-control-operator@adamtrott78.local", BrowserAdapterProtocol.FirefoxExtensionId);
    }
}
