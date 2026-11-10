using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Simulator.Core;
using WorkspaceControl.OperatorBridge.Simulator.Scenarios;

namespace WorkspaceControl.OperatorBridge.Simulator.Tests;

[TestClass]
public sealed class StageFiveScenarioTests
{
    public static IEnumerable<object[]> FixtureIds =>
        ScenarioController.StageFiveFixtureIds.Select(id => new object[] { id });

    [DataTestMethod]
    [DynamicData(nameof(FixtureIds))]
    public void RequiredL0L1ScenarioPassesDeterministically(string fixtureId)
    {
        var controller = new ScenarioController();

        var first = controller.Run(fixtureId);
        var second = controller.Run(fixtureId);

        var failed = first.Predicates
            .Where(pair => !pair.Value)
            .Select(pair => pair.Key)
            .ToArray();

        Assert.IsTrue(
            first.Passed,
            $"Fixture {fixtureId} failed predicates: {string.Join(", ", failed)}");
        Assert.AreEqual(first.TraceSha256, second.TraceSha256);
        Assert.AreEqual(64, first.TraceSha256.Length);
    }

    [TestMethod]
    public void VirtualClockAdvancesOnlyWhenExplicitlyRequested()
    {
        var clock = new VirtualClock();

        Assert.AreEqual(0L, clock.MonotonicMilliseconds);
        clock.Advance(1234);
        Assert.AreEqual(1234L, clock.MonotonicMilliseconds);
        clock.Advance(66);
        Assert.AreEqual(1300L, clock.MonotonicMilliseconds);
    }

    [TestMethod]
    public void StageFiveCatalogHasExactlyRequiredFixtureCount()
    {
        Assert.AreEqual(36, ScenarioController.StageFiveFixtureIds.Length);
        Assert.AreEqual(
            ScenarioController.StageFiveFixtureIds.Length,
            ScenarioController.StageFiveFixtureIds.Distinct(StringComparer.Ordinal).Count());
    }
}
