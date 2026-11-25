using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Bootstrap;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class LocalSmokeOperatorActionPortTests
{
    [TestMethod]
    public async Task SmokeActionIsSingleShotAndRevalidatesOnlyWhileClaimed()
    {
        var port = new LocalSmokeOperatorActionPort();

        Assert.IsTrue(port.HasReadyAction);
        Assert.IsFalse(port.HasSentUnconfirmed);
        var action = await port.ClaimNextAsync(CancellationToken.None);

        Assert.IsNotNull(action);
        Assert.AreEqual(
            OperatorActionType.CreateAndService,
            action.ActionType);
        Assert.AreEqual(
            LocalSmokeOperatorActionPort.SmokePacketText,
            action.PacketText);
        Assert.AreEqual(64, action.PayloadSha256.Length);
        Assert.IsFalse(port.HasReadyAction);
        Assert.IsFalse(port.HasSentUnconfirmed);
        Assert.IsTrue(await port.RevalidateAsync(
            action.Identity,
            CancellationToken.None));

        await port.RecordLocalPreparedAsync(
            action.Identity,
            CancellationToken.None);

        Assert.IsFalse(await port.RevalidateAsync(
            action.Identity,
            CancellationToken.None));
        Assert.IsTrue(port.HasSentUnconfirmed);
        Assert.IsNull(await port.ClaimNextAsync(CancellationToken.None));
    }
}
