using System.Text.Json;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Ipc;
using WorkspaceControl.OperatorBridge.Simulator.Scenarios;
using WorkspaceControl.OperatorBridge.Simulator.State;
using WorkspaceControl.OperatorBridge.Windows;

namespace WorkspaceControl.OperatorBridge.IntegrationHarness;

internal static class Program
{
    private static async Task<int> Main(string[] args)
    {
        var resultPath = GetArgument(args, "--result") ??
            Path.Combine(Environment.CurrentDirectory, "stage06-firefox-result.json");
        var timeoutSeconds = int.TryParse(
            GetArgument(args, "--timeout-seconds"),
            out var parsed)
            ? parsed
            : 60;

        var diagnostics = new CaptureDiagnostics();
        var bridgeState = new BridgeState();
        var bridgeController = new BridgeController(
            bridgeState,
            new NoopHotkeyRegistrar(),
            diagnostics);
        bridgeController.SetEnabled(true);

        var hub = new BrowserCommandHub(bridgeState, diagnostics);
        var pipeName = ElevationScope.PipeName(ElevationScope.Current());
        using var cancellation = new CancellationTokenSource();
        var serverTask = new LocalIpcServer(
            pipeName,
            hub,
            diagnostics).RunAsync(cancellation.Token);

        var predicates = new Dictionary<string, bool>(StringComparer.Ordinal);
        var details = new Dictionary<string, object?>(StringComparer.Ordinal);

        try
        {
            var connected = await hub.WaitForConnectionAsync(
                TimeSpan.FromSeconds(timeoutSeconds));
            predicates["native_messaging_connected"] = connected;
            if (!connected)
            {
                return await FinishAsync(
                    resultPath,
                    predicates,
                    details,
                    null,
                    cancellation,
                    serverTask);
            }

            var ipc = new IpcBrowserPort(hub);
            var browser = new RecordingBrowserPort(ipc);
            var clipboard = new RecordingClipboardWriter();

            var initialInventory = await ipc.InventoryAsync();
            predicates["SIM-025_unmanaged_lookalike_not_adopted"] =
                initialInventory.All(item =>
                    item.WorkerSlotId != "lookalike-slot");

            var lookalikeEnsure = await ipc.PrepareTargetAsync(
                new BrowserTarget("lookalike-slot", 0),
                CancellationToken.None);
            var afterLookalike = await ipc.InventoryAsync();
            predicates["SIM-025_managed_surface_created_instead"] =
                lookalikeEnsure.IsApplied &&
                afterLookalike.Count(item =>
                    item.WorkerSlotId == "lookalike-slot" &&
                    item.SessionGeneration == 0) == 1;

            var ambiguous = await ipc.PrepareTargetAsync(
                new BrowserTarget("ambiguous-slot", 0),
                CancellationToken.None);
            predicates["SIM-026_binding_ambiguity_fails_closed"] =
                ambiguous.Outcome == BrowserOutcome.Rejected &&
                ambiguous.NormalizedError == "BINDING_AMBIGUOUS";

            var world = new SimulatorWorld();
            world.Sessions.Add(
                "slot-existing",
                0,
                SimContinuity.Trusted,
                bindingPresent: true);
            var seeded = await ipc.CreateTargetAsync(
                new BrowserTarget("slot-existing", 0),
                CancellationToken.None);
            predicates["seed_existing_binding"] = seeded.IsApplied;

            var actionPort = new SimulatorOperatorActionPort(world);
            var coordinator = new SingleFlightDispatchCoordinator(
                bridgeState,
                actionPort,
                browser,
                clipboard,
                new SystemMonotonicClock(),
                diagnostics);

            var existing = world.Queue(
                "l3-existing",
                "SERVICE_EXISTING",
                "slot-existing",
                0);
            var activateBefore = browser.ActivateCount;
            var clipboardBefore = clipboard.WriteCount;
            var existingDispatch = await coordinator.DispatchAsync();
            var existingSubmit = world.HumanSubmit(existing);
            predicates["SIM-001_service_existing"] =
                existingDispatch.Outcome == DispatchOutcome.LocalPrepared &&
                existingSubmit &&
                existing.Status == SimActionStatus.Completed &&
                browser.ActivateCount - activateBefore == 1 &&
                clipboard.WriteCount - clipboardBefore == 1;

            world.Sessions.Add(
                "slot-create",
                0,
                SimContinuity.NotEstablished,
                bindingPresent: false);
            var create = world.Queue(
                "l3-create",
                "CREATE_AND_SERVICE",
                "slot-create",
                0);
            var createBefore = browser.CreateCount;
            var createDispatch = await coordinator.DispatchAsync();
            var createSubmit = world.HumanSubmit(create);
            predicates["SIM-002_create_worker"] =
                createDispatch.Outcome == DispatchOutcome.LocalPrepared &&
                createSubmit &&
                browser.CreateCount - createBefore == 1 &&
                world.Sessions.Get("slot-create")!.Continuity ==
                    SimContinuity.Trusted;

            world.Sessions.Add(
                "slot-restore",
                0,
                SimContinuity.Trusted,
                bindingPresent: true);
            var restoreSeed = await ipc.CreateTargetAsync(
                new BrowserTarget("slot-restore", 0),
                CancellationToken.None);
            var discard = await ipc.DiscardTargetAsync(
                new BrowserTarget("slot-restore", 0),
                CancellationToken.None);
            var restore = world.Queue(
                "l3-restore",
                "RESTORE_AND_SERVICE",
                "slot-restore",
                0);
            var restoreBefore = browser.RestoreCount;
            var generationBefore =
                world.Sessions.Get("slot-restore")!.Generation;
            var restoreDispatch = await coordinator.DispatchAsync();
            var restoreSubmit = world.HumanSubmit(restore);
            predicates["SIM-003_restore_discarded"] =
                restoreSeed.IsApplied &&
                discard.IsApplied &&
                restoreDispatch.Outcome == DispatchOutcome.LocalPrepared &&
                restoreSubmit &&
                browser.RestoreCount - restoreBefore == 1 &&
                world.Sessions.Get("slot-restore")!.Generation ==
                    generationBefore;
            details["SIM-003_restore_discarded"] = new
            {
                seed = restoreSeed.Outcome.ToString(),
                discard = discard.Outcome.ToString(),
                discard_error = discard.NormalizedError,
                dispatch = restoreDispatch.Outcome.ToString(),
                submit = restoreSubmit,
                restore_delta = browser.RestoreCount - restoreBefore,
                generation_before = generationBefore,
                generation_after = world.Sessions.Get("slot-restore")!.Generation
            };

            var incompatibleWorld = new SimulatorWorld();
            var incompatibleSession = incompatibleWorld.Sessions.Add(
                "slot-existing",
                0,
                SimContinuity.Trusted,
                bindingPresent: true);
            incompatibleSession.ExecutorCompatible = false;
            incompatibleWorld.Queue(
                "l3-incompatible",
                "SERVICE_EXISTING",
                "slot-existing",
                0);
            var incompatiblePort =
                new SimulatorOperatorActionPort(incompatibleWorld);
            var browserEffectsBefore = BrowserEffectTotal(browser);
            var incompatibleCoordinator =
                new SingleFlightDispatchCoordinator(
                    bridgeState,
                    incompatiblePort,
                    browser,
                    clipboard,
                    new SystemMonotonicClock(),
                    diagnostics);
            var incompatibleDispatch =
                await incompatibleCoordinator.DispatchAsync();
            var browserEffectsAfter = BrowserEffectTotal(browser);
            predicates["SIM-027_executor_identity_unproven"] =
                incompatibleDispatch.Outcome == DispatchOutcome.NoAction &&
                browserEffectsAfter == browserEffectsBefore;

            var inMemoryParity =
                new ScenarioController().Run("SIM-001");
            predicates["adapter_parity_terminal_predicate"] =
                inMemoryParity.Passed &&
                existing.Status == SimActionStatus.Completed &&
                world.Sessions.Get("slot-existing")!.Continuity ==
                    SimContinuity.Trusted;

            await RunStageSevenRecoveryAsync(
                predicates,
                details,
                bridgeState,
                ipc,
                browser,
                clipboard,
                diagnostics);

            var quietClipboard = clipboard.WriteCount;
            var quietBrowser = BrowserEffectTotal(browser);
            await Task.Delay(500);
            predicates["no_background_clipboard_mutation"] =
                clipboard.WriteCount == quietClipboard;
            predicates["no_background_helper_browser_effect"] =
                BrowserEffectTotal(browser) == quietBrowser;

            details["firefox_inventory_count"] =
                (await ipc.InventoryAsync()).Count;
            details["browser_command_counts"] = new
            {
                ensure = browser.EnsureCount,
                create = browser.CreateCount,
                restore = browser.RestoreCount,
                activate = browser.ActivateCount,
                discard = browser.DiscardCount,
                close = browser.CloseCount
            };
            details["clipboard_write_count"] = clipboard.WriteCount;
            details["browser_event_count"] = hub.BrowserEvents.Count;
            details["trace_sha256"] = world.Trace.Sha256();
            details["adapter_parity"] = new
            {
                schema_version = 1,
                fixture = "SIM-001",
                authoritative_terminal_state_in_memory =
                    "COMPLETED/TRUSTED",
                authoritative_terminal_state_firefox =
                    $"{existing.Status.ToString().ToUpperInvariant()}/" +
                    $"{world.Sessions.Get("slot-existing")!.Continuity.ToString().ToUpperInvariant()}",
                local_binding_ids_in_authoritative_state = false
            };

            return await FinishAsync(
                resultPath,
                predicates,
                details,
                world.Trace.Sha256(),
                cancellation,
                serverTask);
        }
        catch (Exception exception)
        {
            predicates["runner_exception"] = false;
            details["normalized_exception"] =
                exception.GetType().Name;
            return await FinishAsync(
                resultPath,
                predicates,
                details,
                null,
                cancellation,
                serverTask);
        }
    }

    private static async Task<int> FinishAsync(
        string resultPath,
        Dictionary<string, bool> predicates,
        Dictionary<string, object?> details,
        string? traceSha256,
        CancellationTokenSource cancellation,
        Task serverTask)
    {
        var passed = predicates.Count > 0 &&
            predicates.Values.All(value => value);

        var report = new
        {
            schema_version = 1,
            stage = "impl_07_recovery_and_fault_closure",
            layer = "L3_FIREFOX_EXTENSION_RECOVERY_FAKE_WORKER",
            result = passed ? "PASS" : "FAIL",
            predicates,
            details,
            trace_sha256 = traceSha256,
            content_policy = "CONTENT_FREE"
        };

        Directory.CreateDirectory(
            Path.GetDirectoryName(Path.GetFullPath(resultPath))!);
        await File.WriteAllTextAsync(
            resultPath,
            JsonSerializer.Serialize(
                report,
                new JsonSerializerOptions { WriteIndented = true }));

        cancellation.Cancel();
        try
        {
            await serverTask;
        }
        catch (OperationCanceledException)
        {
        }

        return passed ? 0 : 1;
    }


    private static async Task RunStageSevenRecoveryAsync(
        Dictionary<string, bool> predicates,
        Dictionary<string, object?> details,
        BridgeState bridgeState,
        IpcBrowserPort ipc,
        RecordingBrowserPort browser,
        RecordingClipboardWriter clipboard,
        CaptureDiagnostics diagnostics)
    {
        var recoveryDetails =
            new Dictionary<string, object?>(StringComparer.Ordinal);

        // SIM-018: real managed binding is lost before submit.
        var world18 = new SimulatorWorld();
        world18.Sessions.Add(
            "slot-r18",
            0,
            SimContinuity.Trusted,
            bindingPresent: true);
        var action18 = world18.Queue(
            "r18-old",
            "SERVICE_EXISTING",
            "slot-r18",
            0);
        action18.Status = SimActionStatus.AwaitingDurableAck;
        action18.ClaimCount = 1;
        var seed18 = await ipc.CreateTargetAsync(
            new BrowserTarget("slot-r18", 0),
            CancellationToken.None);
        var close18 = await ipc.CloseTargetAsync(
            new BrowserTarget("slot-r18", 0),
            CancellationToken.None);
        var authority18 = new SimulatorRecoveryAuthorityPort(world18);
        var inventory18 = new RecordingManagedBrowserInventory(ipc);
        var recovery18 = new RecoveryCoordinator(
            new InMemoryRecoveryStateStore(),
            authority18,
            inventory18,
            diagnostics);
        await recovery18.BeginAsync(
            "l3-r18",
            RecoveryScope.SessionScoped,
            RecoverySignal.ManagedTabClosed,
            [new RecoverySessionRef("slot-r18", 0)]);
        var result18 = await recovery18.ReconcileAsync();
        predicates["SIM-018_tab_closed_before_submit"] =
            seed18.IsApplied &&
            close18.IsApplied &&
            authority18.ReconcileCount == 1 &&
            authority18.AdvanceCount == 1 &&
            inventory18.InventoryCount == 1 &&
            action18.Status == SimActionStatus.Superseded &&
            world18.Sessions.Get("slot-r18")!.Generation == 1 &&
            result18.Status == RecoveryStatus.ReadyToResume;

        // SIM-019: global browser-loss signal freezes all browser-dependent dispatch.
        var world19 = new SimulatorWorld();
        world19.Sessions.Add("slot-r19", 0, SimContinuity.Trusted, true);
        var action19 = world19.Queue("r19", "SERVICE_EXISTING", "slot-r19", 0);
        var authority19 = new SimulatorRecoveryAuthorityPort(world19);
        var inventory19 = new RecordingManagedBrowserInventory(ipc);
        var recovery19 = new RecoveryCoordinator(
            new InMemoryRecoveryStateStore(),
            authority19,
            inventory19,
            diagnostics);
        await recovery19.BeginAsync(
            "l3-r19",
            RecoveryScope.LocalBridgeGlobal,
            RecoverySignal.FirefoxConnectionLost,
            [new RecoverySessionRef("slot-r19", 0)]);
        var surface19 = new RecordingOperatorSurface();
        var coordinator19 = new SingleFlightDispatchCoordinator(
            bridgeState,
            new SimulatorOperatorActionPort(world19),
            browser,
            clipboard,
            new SystemMonotonicClock(),
            diagnostics,
            surface19,
            recovery19);
        var clipboard19 = clipboard.WriteCount;
        var effects19 = BrowserEffectTotal(browser);
        var blocked19 = await coordinator19.DispatchAsync();
        var ready19 = await recovery19.ReconcileAsync();
        predicates["SIM-019_browser_crash"] =
            blocked19.Outcome == DispatchOutcome.RecoveryOpened &&
            action19.ClaimCount == 0 &&
            clipboard.WriteCount == clipboard19 &&
            BrowserEffectTotal(browser) == effects19 &&
            world19.Sessions.Get("slot-r19")!.Continuity ==
                SimContinuity.Unknown &&
            inventory19.InventoryCount == 1 &&
            ready19.Status == RecoveryStatus.ReadyToResume;

        // SIM-020: adapter disconnect is a blocking signal until reinventory.
        var world20 = new SimulatorWorld();
        world20.Sessions.Add("slot-r20", 0, SimContinuity.Trusted, true);
        var seed20 = await ipc.CreateTargetAsync(
            new BrowserTarget("slot-r20", 0),
            CancellationToken.None);
        var action20 = world20.Queue("r20", "SERVICE_EXISTING", "slot-r20", 0);
        var authority20 = new SimulatorRecoveryAuthorityPort(world20);
        var inventory20 = new RecordingManagedBrowserInventory(ipc);
        var recovery20 = new RecoveryCoordinator(
            new InMemoryRecoveryStateStore(),
            authority20,
            inventory20,
            diagnostics);
        await recovery20.BeginAsync(
            "l3-r20",
            RecoveryScope.LocalBridgeGlobal,
            RecoverySignal.FirefoxConnectionLost,
            [new RecoverySessionRef("slot-r20", 0)]);
        var coordinator20 = new SingleFlightDispatchCoordinator(
            bridgeState,
            new SimulatorOperatorActionPort(world20),
            browser,
            clipboard,
            new SystemMonotonicClock(),
            diagnostics,
            new RecordingOperatorSurface(),
            recovery20);
        var blocked20 = await coordinator20.DispatchAsync();
        var ready20 = await recovery20.ReconcileAsync();
        var dispatch20 = await coordinator20.DispatchAsync();
        predicates["SIM-020_adapter_disconnect_reinventory"] =
            seed20.IsApplied &&
            blocked20.Outcome == DispatchOutcome.RecoveryOpened &&
            ready20.Status == RecoveryStatus.ReadyToResume &&
            inventory20.InventoryCount == 1 &&
            dispatch20.Outcome == DispatchOutcome.LocalPrepared &&
            action20.ClaimCount == 1;

        // SIM-022: create effect is real but its receipt is treated as unknown.
        var world22 = new SimulatorWorld();
        world22.Sessions.Add(
            "slot-r22",
            0,
            SimContinuity.NotEstablished,
            bindingPresent: true);
        var action22 = world22.Queue(
            "r22-unknown-create",
            "CREATE_AND_SERVICE",
            "slot-r22",
            0);
        action22.Status = SimActionStatus.Blocked;
        var create22Before = browser.CreateCount;
        var create22 = await browser.CreateTargetAsync(
            new BrowserTarget("slot-r22", 0),
            CancellationToken.None);
        var create22AfterEffect = browser.CreateCount;
        var authority22 = new SimulatorRecoveryAuthorityPort(world22);
        var inventory22 = new RecordingManagedBrowserInventory(ipc);
        var recovery22 = new RecoveryCoordinator(
            new InMemoryRecoveryStateStore(),
            authority22,
            inventory22,
            diagnostics);
        await recovery22.BeginAsync(
            "l3-r22",
            RecoveryScope.SessionScoped,
            RecoverySignal.BindingAmbiguous,
            [new RecoverySessionRef("slot-r22", 0)]);
        var result22 = await recovery22.ReconcileAsync();
        predicates["SIM-022_unknown_create_no_duplicate"] =
            create22.IsApplied &&
            create22AfterEffect - create22Before == 1 &&
            browser.CreateCount == create22AfterEffect &&
            inventory22.InventoryCount == 1 &&
            result22.Status == RecoveryStatus.ReadyToResume;

        // SIM-028: real browser inventory supplies only origin classification.
        var world28 = new SimulatorWorld();
        world28.Sessions.Add("slot-r28", 0, SimContinuity.Trusted, true);
        var seed28 = await ipc.CreateTargetAsync(
            new BrowserTarget("slot-r28", 0),
            CancellationToken.None);
        await Task.Delay(250);
        var inventoryBefore28 = await ipc.InventoryAsync();
        var offOrigin28 = inventoryBefore28.Any(item =>
            item.WorkerSlotId == "slot-r28" &&
            item.OriginClassification == "OFF_CHATGPT_ORIGIN");
        var authority28 = new SimulatorRecoveryAuthorityPort(world28);
        var recovery28 = new RecoveryCoordinator(
            new InMemoryRecoveryStateStore(),
            authority28,
            new RecordingManagedBrowserInventory(ipc),
            diagnostics);
        await recovery28.BeginAsync(
            "l3-r28",
            RecoveryScope.AuthDomainScoped,
            RecoverySignal.AuthNavigationDetected,
            [new RecoverySessionRef("slot-r28", 0)]);
        var waiting28 = await recovery28.ReconcileAsync();
        predicates["SIM-028_metadata_only_auth_entry"] =
            seed28.IsApplied &&
            offOrigin28 &&
            waiting28.Status == RecoveryStatus.AwaitingManualAuth &&
            world28.Sessions.Get("slot-r28")!.Continuity ==
                SimContinuity.Unknown &&
            world28.AuthAutomationCount == 0;

        // SIM-029: all-tab auth recovery reconciles once and advances once.
        var world29 = new SimulatorWorld();
        foreach (var slot in new[] { "slot-r29a", "slot-r29b" })
        {
            world29.Sessions.Add(slot, 0, SimContinuity.Trusted, true);
            var action = world29.Queue(
                "action-" + slot,
                "SERVICE_EXISTING",
                slot,
                0);
            action.Status = SimActionStatus.AwaitingDurableAck;
            action.ClaimCount = 1;
            await ipc.CreateTargetAsync(
                new BrowserTarget(slot, 0),
                CancellationToken.None);
        }
        var authority29 = new SimulatorRecoveryAuthorityPort(world29);
        var inventory29 = new RecordingManagedBrowserInventory(ipc);
        var recovery29 = new RecoveryCoordinator(
            new InMemoryRecoveryStateStore(),
            authority29,
            inventory29,
            diagnostics);
        await recovery29.BeginAsync(
            "l3-r29",
            RecoveryScope.AuthDomainScoped,
            RecoverySignal.OperatorReportedAuthRefresh,
            [
                new RecoverySessionRef("slot-r29a", 0),
                new RecoverySessionRef("slot-r29b", 0)
            ]);
        var waiting29 = await recovery29.ReconcileAsync();
        var ready29 = await recovery29.MarkManualAuthReturnedAsync();
        await recovery29.ReconcileAsync();
        predicates["SIM-029_auth_refresh_all_tabs"] =
            waiting29.Status == RecoveryStatus.AwaitingManualAuth &&
            ready29.Status == RecoveryStatus.ReadyToResume &&
            authority29.FreezeCount == 1 &&
            authority29.ReconcileCount == 1 &&
            authority29.AdvanceCount == 2 &&
            world29.Sessions.Get("slot-r29a")!.Generation == 1 &&
            world29.Sessions.Get("slot-r29b")!.Generation == 1 &&
            world29.Sessions.Get("slot-r29a")!.Continuity ==
                SimContinuity.Unknown &&
            world29.Sessions.Get("slot-r29b")!.Continuity ==
                SimContinuity.Unknown;

        // SIM-033: helper cold-start rehydrates the same incident and blocks replay.
        var world33 = new SimulatorWorld();
        world33.Sessions.Add("slot-r33", 2, SimContinuity.Trusted, true);
        var action33 = world33.Queue(
            "r33-pending",
            "SERVICE_EXISTING",
            "slot-r33",
            2);
        action33.Status = SimActionStatus.AwaitingDurableAck;
        action33.ClaimCount = 1;
        await ipc.CreateTargetAsync(
            new BrowserTarget("slot-r33", 2),
            CancellationToken.None);
        var state33 = new InMemoryRecoveryStateStore();
        var authority33 = new SimulatorRecoveryAuthorityPort(world33);
        var inventory33 = new RecordingManagedBrowserInventory(ipc);
        var first33 = new RecoveryCoordinator(
            state33,
            authority33,
            inventory33,
            diagnostics);
        await first33.BeginAsync(
            "l3-r33",
            RecoveryScope.LocalBridgeGlobal,
            RecoverySignal.SystemResumeOrHelperColdStart,
            [new RecoverySessionRef("slot-r33", 2)]);
        var restarted33 = new RecoveryCoordinator(
            state33,
            authority33,
            inventory33,
            diagnostics);
        var loaded33 = await restarted33.InitializeAsync();
        var coordinator33 = new SingleFlightDispatchCoordinator(
            bridgeState,
            new SimulatorOperatorActionPort(world33),
            browser,
            clipboard,
            new SystemMonotonicClock(),
            diagnostics,
            new RecordingOperatorSurface(),
            restarted33);
        var blocked33 = await coordinator33.DispatchAsync();
        var ready33 = await restarted33.ReconcileAsync();
        predicates["SIM-033_cold_restart_no_stale_replay"] =
            loaded33 is not null &&
            blocked33.Outcome == DispatchOutcome.RecoveryOpened &&
            action33.ClaimCount == 1 &&
            ready33.Status == RecoveryStatus.ReadyToResume &&
            authority33.AdvanceCount == 1 &&
            inventory33.InventoryCount == 1;

        recoveryDetails["authority_reconcile_counts"] = new
        {
            sim018 = authority18.ReconcileCount,
            sim019 = authority19.ReconcileCount,
            sim020 = authority20.ReconcileCount,
            sim022 = authority22.ReconcileCount,
            sim028 = authority28.ReconcileCount,
            sim029 = authority29.ReconcileCount,
            sim033 = authority33.ReconcileCount
        };
        recoveryDetails["auth_generation_advances"] =
            authority29.AdvanceCount;
        recoveryDetails["cold_restart_claim_count"] =
            action33.ClaimCount;
        details["stage07_recovery"] = recoveryDetails;
    }

    private static int BrowserEffectTotal(
        RecordingBrowserPort browser) =>
        browser.EnsureCount +
        browser.CreateCount +
        browser.RestoreCount +
        browser.ActivateCount +
        browser.DiscardCount +
        browser.CloseCount;

    private static string? GetArgument(
        string[] args,
        string name)
    {
        var prefix = name + "=";
        return args.FirstOrDefault(arg =>
                arg.StartsWith(
                    prefix,
                    StringComparison.OrdinalIgnoreCase))
            ?[prefix.Length..];
    }
}
