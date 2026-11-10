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
            stage = "impl_06_integrated_local_bridge_e2e",
            layer = "L3_FIREFOX_EXTENSION_FAKE_WORKER",
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
