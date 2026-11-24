using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Windows;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class WorkloadStatusPresentationTests
{
    [TestMethod]
    public void ReadyStateShowsReadyCountAndConfiguredHotkey()
    {
        var presentation = WorkloadStatusPresentation.Project(
            bridgeEnabled: true,
            new WorkloadStatusSnapshot(7, 2),
            "Ctrl+Space");

        Assert.AreEqual(WorkloadDominantState.Ready, presentation.State);
        Assert.AreEqual("7", presentation.IconText);
        Assert.AreEqual("Ready now: 7; Ctrl+Space to service next", presentation.Tooltip);
        Assert.AreEqual("Ready now: 7", presentation.ReadyLabel);
        Assert.AreEqual("Sent / unconfirmed: 2", presentation.SentUnconfirmedLabel);
    }

    [TestMethod]
    public void IdleStateMakesNoWorkExplicit()
    {
        var presentation = WorkloadStatusPresentation.Project(
            bridgeEnabled: true,
            WorkloadStatusSnapshot.Empty,
            "Ctrl+Space");

        Assert.AreEqual(WorkloadDominantState.Idle, presentation.State);
        Assert.AreEqual("0", presentation.IconText);
        Assert.AreEqual("Nothing needs service", presentation.Tooltip);
    }

    [TestMethod]
    public void WaitingStateDoesNotPretendUnconfirmedWorkIsReady()
    {
        var presentation = WorkloadStatusPresentation.Project(
            bridgeEnabled: true,
            new WorkloadStatusSnapshot(0, 3),
            "Ctrl+Space");

        Assert.AreEqual(
            WorkloadDominantState.WaitingUnconfirmed,
            presentation.State);
        Assert.AreEqual("W", presentation.IconText);
        Assert.AreEqual(
            "Waiting for durable acknowledgments",
            presentation.Tooltip);
        Assert.AreEqual("Ready now: 0", presentation.ReadyLabel);
        Assert.AreEqual("Sent / unconfirmed: 3", presentation.SentUnconfirmedLabel);
    }

    [TestMethod]
    public void ReadyCountBadgeCapsAtNinetyNinePlus()
    {
        var presentation = WorkloadStatusPresentation.Project(
            bridgeEnabled: true,
            new WorkloadStatusSnapshot(120, 0),
            "Ctrl+Space");

        Assert.AreEqual("99+", presentation.IconText);
    }
}
