using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Contracts.Protocol;

namespace WorkspaceControl.OperatorBridge.Protocol.Tests;

[TestClass]
public sealed class IdempotencyRegistryTests
{
    [TestMethod]
    public void DuplicateSameKeyDoesNotBecomeNewWork()
    {
        var registry = new IdempotencyRegistry();

        Assert.AreEqual(
            IdempotencyDecision.First,
            registry.Observe("request-1", "idem-1"));
        Assert.AreEqual(
            IdempotencyDecision.DuplicateSame,
            registry.Observe("request-1", "idem-1"));
        Assert.AreEqual(
            IdempotencyDecision.Conflict,
            registry.Observe("request-1", "idem-2"));
    }
}
