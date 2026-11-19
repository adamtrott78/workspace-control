using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;
using WorkspaceControl.OperatorBridge.Windows;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class RecoveryCoordinatorTests
{
    [TestMethod]
    public async Task AuthRecoveryReconcilesAndAdvancesExactlyOnce()
    {
        var state = new MemoryRecoveryStateStore();
        var authority = new FakeRecoveryAuthority();
        var inventory = new FakeInventory();
        var coordinator = new RecoveryCoordinator(
            state,
            authority,
            inventory,
            new NullDiagnostics());

        await coordinator.BeginAsync(
            "auth-1",
            RecoveryScope.AuthDomainScoped,
            RecoverySignal.AuthNavigationDetected,
            [new RecoverySessionRef("slot-a", 4)]);

        var waiting = await coordinator.ReconcileAsync();
        var repeated = await coordinator.ReconcileAsync();

        Assert.AreEqual(
            RecoveryStatus.AwaitingManualAuth,
            waiting.Status);
        Assert.AreEqual(
            RecoveryStatus.AwaitingManualAuth,
            repeated.Status);
        Assert.AreEqual(1, authority.FreezeCount);
        Assert.AreEqual(1, authority.ReconcileCount);
        Assert.AreEqual(1, authority.AdvanceCount);
        Assert.IsTrue(coordinator.BlocksDispatch);

        var ready = await coordinator.MarkManualAuthReturnedAsync();

        Assert.AreEqual(
            RecoveryStatus.ReadyToResume,
            ready.Status);
        Assert.AreEqual(1, authority.ReconcileCount);
        Assert.AreEqual(1, authority.AdvanceCount);
        Assert.AreEqual(1, inventory.InventoryCount);
        Assert.IsFalse(coordinator.BlocksDispatch);
    }

    [TestMethod]
    public async Task ColdRestartRehydratesWithoutReplayingCompletedSteps()
    {
        var state = new MemoryRecoveryStateStore();
        var authority = new FakeRecoveryAuthority();
        var inventory = new FakeInventory();

        var first = new RecoveryCoordinator(
            state,
            authority,
            inventory,
            new NullDiagnostics());
        await first.BeginAsync(
            "restart-1",
            RecoveryScope.LocalBridgeGlobal,
            RecoverySignal.SystemResumeOrHelperColdStart,
            [new RecoverySessionRef("slot-a", 2)]);
        await first.ReconcileAsync();

        var freezeBefore = authority.FreezeCount;
        var reconcileBefore = authority.ReconcileCount;
        var advanceBefore = authority.AdvanceCount;

        var restarted = new RecoveryCoordinator(
            state,
            authority,
            inventory,
            new NullDiagnostics());
        var loaded = await restarted.InitializeAsync();
        var resumed = await restarted.ReconcileAsync();

        Assert.IsNotNull(loaded);
        Assert.AreEqual(
            RecoveryStatus.ReadyToResume,
            resumed.Status);
        Assert.AreEqual(freezeBefore, authority.FreezeCount);
        Assert.AreEqual(reconcileBefore, authority.ReconcileCount);
        Assert.AreEqual(advanceBefore, authority.AdvanceCount);
    }

    [TestMethod]
    public async Task UnrelatedAmbiguousBindingDoesNotBlockScopedRecovery()
    {
        var state = new MemoryRecoveryStateStore();
        var authority = new FakeRecoveryAuthority();
        var inventory = new FakeInventory
        {
            Entries =
            [
                new BrowserInventoryEntry(
                    "unrelated",
                    0,
                    "a",
                    1,
                    "CHATGPT_ORIGIN",
                    false,
                    false),
                new BrowserInventoryEntry(
                    "unrelated",
                    0,
                    "b",
                    2,
                    "CHATGPT_ORIGIN",
                    false,
                    false)
            ]
        };
        var coordinator = new RecoveryCoordinator(
            state,
            authority,
            inventory,
            new NullDiagnostics());

        await coordinator.BeginAsync(
            "scoped-1",
            RecoveryScope.SessionScoped,
            RecoverySignal.ManagedTabClosed,
            [new RecoverySessionRef("slot-a", 4)]);

        var result = await coordinator.ReconcileAsync();

        Assert.AreEqual(RecoveryStatus.ReadyToResume, result.Status);
    }

    [TestMethod]
    public async Task JsonRecoveryStateContainsOnlyRecoveryMetadata()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            "workspace-operator-recovery-" + Guid.NewGuid().ToString("N"));
        var path = Path.Combine(root, "recovery.json");
        try
        {
            var store = new JsonRecoveryStateStore(path);
            var incident = new RecoveryIncident
            {
                RecoveryId = "r-json",
                Scope = RecoveryScope.SessionScoped,
                Status = RecoveryStatus.Reconciling,
                TriggerSignal = RecoverySignal.ManagedTabClosed.ToString(),
                AffectedSessions =
                [
                    new RecoverySessionRef("slot-a", 3)
                ]
            };

            await store.SaveAsync(incident, CancellationToken.None);
            var raw = await File.ReadAllTextAsync(path);
            var loaded = await store.LoadAsync(CancellationToken.None);

            Assert.IsNotNull(loaded);
            Assert.AreEqual("r-json", loaded.RecoveryId);
            foreach (var forbidden in new[]
                     {
                         "PacketText",
                         "Clipboard",
                         "RawUrl",
                         "PageContent",
                         "Credential",
                         "Token",
                         "Cookie",
                         "Password"
                     })
            {
                Assert.IsFalse(
                    raw.Contains(
                        forbidden,
                        StringComparison.OrdinalIgnoreCase));
            }
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, true);
            }
        }
    }

    private sealed class MemoryRecoveryStateStore : IRecoveryStateStore
    {
        public RecoveryIncident? Incident { get; private set; }

        public Task<RecoveryIncident?> LoadAsync(
            CancellationToken cancellationToken) =>
            Task.FromResult(Incident);

        public Task SaveAsync(
            RecoveryIncident incident,
            CancellationToken cancellationToken)
        {
            Incident = incident;
            return Task.CompletedTask;
        }

        public Task ClearAsync(CancellationToken cancellationToken)
        {
            Incident = null;
            return Task.CompletedTask;
        }
    }

    private sealed class FakeRecoveryAuthority : IRecoveryAuthorityPort
    {
        public int FreezeCount { get; private set; }
        public int ReconcileCount { get; private set; }
        public int AdvanceCount { get; private set; }

        public Task FreezeAsync(
            RecoveryIncident incident,
            CancellationToken cancellationToken)
        {
            FreezeCount++;
            return Task.CompletedTask;
        }

        public Task<RecoveryReconciliationResult> ReconcileAsync(
            RecoveryIncident incident,
            CancellationToken cancellationToken)
        {
            ReconcileCount++;
            return Task.FromResult(
                new RecoveryReconciliationResult(
                    incident.AffectedSessions));
        }

        public Task<RecoveryAdvanceResult>
            SupersedeAndAdvanceGenerationAsync(
                string recoveryId,
                RecoverySessionRef session,
                CancellationToken cancellationToken)
        {
            AdvanceCount++;
            return Task.FromResult(
                new RecoveryAdvanceResult(
                    true,
                    session.SessionGeneration + 1));
        }
    }

    private sealed class FakeInventory : IManagedBrowserInventory
    {
        public int InventoryCount { get; private set; }

        public IReadOnlyList<BrowserInventoryEntry> Entries { get; init; } = [];

        public Task<IReadOnlyList<BrowserInventoryEntry>> InventoryAsync(
            CancellationToken cancellationToken = default)
        {
            InventoryCount++;
            return Task.FromResult(Entries);
        }
    }

    private sealed class NullDiagnostics : IDiagnosticsSink
    {
        public void Write(DiagnosticEvent diagnosticEvent)
        {
        }
    }
}
