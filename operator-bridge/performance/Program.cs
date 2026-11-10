using System.Collections.Concurrent;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ipc;
using WorkspaceControl.OperatorBridge.Ports;
using WorkspaceControl.OperatorBridge.Simulator.Scenarios;
using WorkspaceControl.OperatorBridge.Simulator.State;
using WorkspaceControl.OperatorBridge.Windows;
using WorkspaceControl.OperatorBridge.Windows.Clipboard;
using WorkspaceControl.OperatorBridge.Windows.Hotkey;
using WorkspaceControl.OperatorBridge.Windows.Firefox;

namespace WorkspaceControl.OperatorBridge.PerformanceHarness;

internal static class Program
{
    private const string FirefoxProcessName = "firefox";
    private const string PerformanceAdapterKind = "FIREFOX_EXTENSION";
    private const string PerformanceAdapterVersion = "0.1.9-perf";

    [STAThread]
    private static async Task<int> Main(string[] args)
    {
        var resultPath = RequiredArgument(args, "--result");
        var helperPath = RequiredArgument(args, "--helper");
        var readyFile = GetArgument(args, "--ready-file");
        var mode = (GetArgument(args, "--mode") ?? "ci").ToLowerInvariant();
        if (mode is not ("ci" or "target" or "cold-target" or "adapter-preflight"))
        {
            throw new ArgumentException(
                "--mode must be ci, target, cold-target, or adapter-preflight.");
        }

        var warmupMs = IntArgument(args, "--warmup-ms", mode == "target" ? 60000 : 250);
        var sampleMs = IntArgument(args, "--sample-ms", mode == "target" ? 120000 : 1200);
        var sampleIntervalMs = IntArgument(args, "--sample-interval-ms", mode == "target" ? 1000 : 200);
        var latencyScale = IntArgument(args, "--latency-scale", mode == "target" ? 1 : 10);
        var timeoutSeconds = IntArgument(args, "--timeout-seconds", 90);
        var skipLatency = HasFlag(args, "--skip-latency");

        var counts = new TrialCounts(
            Reuse: Math.Max(1, 50 / latencyScale),
            Restore: Math.Max(1, 30 / latencyScale),
            Create: Math.Max(1, 30 / latencyScale),
            Primitive: Math.Max(1, 100 / latencyScale));

        var diagnostics = new CaptureDiagnostics();
        if (mode == "adapter-preflight")
        {
            return await RunAdapterPreflightAsync(
                resultPath,
                readyFile,
                timeoutSeconds,
                diagnostics);
        }
        if (mode == "cold-target")
        {
            var coldCount = IntArgument(args, "--cold-count", 10);
            return await RunColdStartTargetAsync(
                resultPath,
                coldCount,
                diagnostics);
        }

        var helperIdle = await MeasureHelperIdleAsync(
            helperPath,
            warmupMs,
            sampleMs,
            sampleIntervalMs);

        var bridgeState = new BridgeState();
        var bridgeController = new BridgeController(
            bridgeState,
            new NoopHotkeyRegistrar(),
            diagnostics);
        bridgeController.SetEnabled(true);

        var hub = new BrowserCommandHub(
            bridgeState,
            diagnostics,
            PerformanceAdapterKind,
            PerformanceAdapterVersion);
        var pipeName = ElevationScope.PipeName(ElevationScope.Current());
        using var cancellation = new CancellationTokenSource();
        var serverTask = new LocalIpcServer(
            pipeName,
            hub,
            diagnostics).RunAsync(cancellation.Token);

        if (!string.IsNullOrWhiteSpace(readyFile))
        {
            Directory.CreateDirectory(
                Path.GetDirectoryName(Path.GetFullPath(readyFile))!);
            await File.WriteAllTextAsync(readyFile, "SERVER_READY");
        }

        try
        {
            var connected = await hub.WaitForConnectionAsync(
                TimeSpan.FromSeconds(timeoutSeconds));
            if (!connected)
            {
                throw new InvalidOperationException(
                    "Firefox performance adapter did not connect.");
            }

            var ipc = new IpcBrowserPort(hub);
            using var clipboard = new StaBenchmarkClipboard();
            var resourceRuns = new List<ResourceRun>();

            await CloseAllManagedAsync(ipc);
            resourceRuns.Add(await SampleProcessGroupAsync(
                FirefoxProcessName,
                "FIREFOX_0_WORKERS",
                1,
                0,
                0,
                warmupMs,
                sampleMs,
                sampleIntervalMs));

            var liveTargets = new List<BrowserTarget>();
            for (var index = 1; index <= 4; index++)
            {
                var target = new BrowserTarget($"perf-live-{index}", 0);
                var created = await ipc.CreateTargetAsync(
                    target,
                    CancellationToken.None);
                if (!created.IsApplied)
                {
                    throw new InvalidOperationException(
                        $"Unable to create performance target {index}: " +
                        created.NormalizedError);
                }
                liveTargets.Add(target);

                if (index is 1 or 2 or 4)
                {
                    resourceRuns.Add(await SampleProcessGroupAsync(
                        FirefoxProcessName,
                        $"FIREFOX_{index}_WORKERS",
                        1,
                        index,
                        0,
                        warmupMs,
                        sampleMs,
                        sampleIntervalMs));
                }
            }

            var focused = await ipc.FocusTargetAsync(
                liveTargets[0],
                CancellationToken.None);
            if (!focused.IsApplied)
            {
                throw new InvalidOperationException(
                    "Unable to focus the retained active performance target.");
            }

            foreach (var target in liveTargets.Skip(1))
            {
                var discarded = await ipc.DiscardTargetAsync(
                    target,
                    CancellationToken.None);
                if (!discarded.IsApplied)
                {
                    throw new InvalidOperationException(
                        "Unable to discard performance target: " +
                        discarded.NormalizedError);
                }
            }

            resourceRuns.Add(await SampleProcessGroupAsync(
                FirefoxProcessName,
                "FIREFOX_4_WITH_3_DISCARDED",
                1,
                4,
                3,
                warmupMs,
                sampleMs,
                sampleIntervalMs));

            var restoredOne = await ipc.RestoreTargetAsync(
                liveTargets[1],
                CancellationToken.None);
            if (!restoredOne.IsApplied)
            {
                throw new InvalidOperationException(
                    "Unable to restore one performance target.");
            }
            resourceRuns.Add(await SampleProcessGroupAsync(
                FirefoxProcessName,
                "FIREFOX_RESTORE_ONE",
                1,
                4,
                2,
                warmupMs,
                sampleMs,
                sampleIntervalMs));

            foreach (var target in liveTargets.Skip(2))
            {
                var restored = await ipc.RestoreTargetAsync(
                    target,
                    CancellationToken.None);
                if (!restored.IsApplied)
                {
                    throw new InvalidOperationException(
                        "Unable to restore performance target.");
                }
            }
            resourceRuns.Add(await SampleProcessGroupAsync(
                FirefoxProcessName,
                "FIREFOX_RESTORE_ALL",
                1,
                4,
                0,
                warmupMs,
                sampleMs,
                sampleIntervalMs));

            LatencyReport? latency = null;
            HotkeyMeasurement? hotkey = null;
            if (!skipLatency)
            {
                latency = await MeasureLatenciesAsync(
                    ipc,
                    bridgeState,
                    clipboard,
                    diagnostics,
                    liveTargets[0],
                    liveTargets[1],
                    counts);

                hotkey = MeasureHotkeyQueueToCallback(counts.Primitive);
            }

            var fourLive = resourceRuns.Single(x =>
                x.ScenarioId == "FIREFOX_4_WORKERS");
            var discardedThree = resourceRuns.Single(x =>
                x.ScenarioId == "FIREFOX_4_WITH_3_DISCARDED");
            var discardReduction = fourLive.WorkingSet.P95 <= 0
                ? 0
                : Math.Max(
                    0,
                    (fourLive.WorkingSet.P95 - discardedThree.WorkingSet.P95) /
                    fourLive.WorkingSet.P95 * 100.0);

            var report = new
            {
                schema_version = 1,
                stage = "impl_09_performance_benchmark_execution",
                evidence_class = mode == "target"
                    ? "TARGET_MODE_PARTIAL"
                    : "GITHUB_HOSTED_WINDOWS_CI",
                target_contract_complete = false,
                target_contract_incomplete_reasons = new[]
                {
                    "Firefox/Chrome three-complete-replicate order alternation is not performed by this CI harness.",
                    "Chrome Memory Saver parity control is not performed by this CI harness.",
                    "Cold-Firefox-start is collected only by the dedicated cold-target mode and is not part of this steady-state run.",
                    "GitHub-hosted Windows is not the target operator workstation."
                },
                content_policy = "CONTENT_FREE",
                trial_counts = counts,
                measurement = new
                {
                    warmup_ms = warmupMs,
                    sample_ms = sampleMs,
                    sample_interval_ms = sampleIntervalMs
                },
                helper_idle = helperIdle,
                firefox_resource_runs = resourceRuns,
                discard_three_of_four_p95_reduction_percent = discardReduction,
                latency = latency,
                hotkey_queue_to_callback_proxy = hotkey,
                cold_firefox_start = new
                {
                    status = "NOT_MEASURED_IN_THIS_RUN",
                    pass_fail = "INVALID",
                    reason = "Use dedicated cold-target mode on the target workstation."
                },
                security = new
                {
                    dom_or_page_content_collected = false,
                    raw_urls_collected = false,
                    screenshots_collected = false,
                    credentials_or_tokens_collected = false,
                    synthetic_paste_enter_send_or_mouse = false,
                    simulator_only = true
                }
            };

            Directory.CreateDirectory(
                Path.GetDirectoryName(Path.GetFullPath(resultPath))!);
            await File.WriteAllTextAsync(
                resultPath,
                JsonSerializer.Serialize(
                    report,
                    new JsonSerializerOptions { WriteIndented = true }));

            return 0;
        }
        catch (Exception exception)
        {
            Directory.CreateDirectory(
                Path.GetDirectoryName(Path.GetFullPath(resultPath))!);
            var failure = new
            {
                schema_version = 1,
                stage = "impl_09_performance_benchmark_execution",
                evidence_class = mode == "target"
                    ? "TARGET_MODE_PARTIAL"
                    : "GITHUB_HOSTED_WINDOWS_CI",
                target_contract_complete = false,
                result = "HARNESS_FAILURE",
                normalized_exception = exception.GetType().Name,
                content_policy = "CONTENT_FREE"
            };
            await File.WriteAllTextAsync(
                resultPath,
                JsonSerializer.Serialize(
                    failure,
                    new JsonSerializerOptions { WriteIndented = true }));
            return 1;
        }
        finally
        {
            cancellation.Cancel();
            try
            {
                await serverTask;
            }
            catch (OperationCanceledException)
            {
            }
        }
    }

    private static async Task<int> RunAdapterPreflightAsync(
        string resultPath,
        string? readyFile,
        int timeoutSeconds,
        IDiagnosticsSink diagnostics)
    {
        var bridgeState = new BridgeState();
        var bridgeController = new BridgeController(
            bridgeState,
            new NoopHotkeyRegistrar(),
            diagnostics);
        bridgeController.SetEnabled(true);

        var hub = new BrowserCommandHub(
            bridgeState,
            diagnostics,
            PerformanceAdapterKind,
            PerformanceAdapterVersion);
        var pipeName = ElevationScope.PipeName(ElevationScope.Current());
        using var cancellation = new CancellationTokenSource();
        var serverTask = new LocalIpcServer(
            pipeName,
            hub,
            diagnostics).RunAsync(cancellation.Token);

        if (!string.IsNullOrWhiteSpace(readyFile))
        {
            Directory.CreateDirectory(
                Path.GetDirectoryName(Path.GetFullPath(readyFile))!);
            await File.WriteAllTextAsync(readyFile, "SERVER_READY");
        }

        try
        {
            var connected = await hub.WaitForConnectionAsync(
                TimeSpan.FromSeconds(timeoutSeconds));
            if (!connected)
            {
                throw new InvalidOperationException(
                    "Stage 09 performance adapter did not connect with the required identity.");
            }

            var evidence = new
            {
                schema_version = 1,
                evidence_class = "TARGET_ADAPTER_PREFLIGHT",
                target_contract_complete = false,
                adapter_kind = PerformanceAdapterKind,
                adapter_version = PerformanceAdapterVersion,
                status = "PASS"
            };
            await File.WriteAllTextAsync(
                resultPath,
                JsonSerializer.Serialize(
                    evidence,
                    new JsonSerializerOptions { WriteIndented = true }));
            Console.WriteLine("STAGE09_TARGET_ADAPTER_PREFLIGHT=PASS");
            return 0;
        }
        catch (Exception exception)
        {
            var captured = diagnostics is CaptureDiagnostics capture
                ? capture.Snapshot
                : Array.Empty<DiagnosticEvent>();
            var normalizedFailure = captured.Any(item =>
                    string.Equals(
                        item.NormalizedError,
                        "ADAPTER_IDENTITY_REJECTED",
                        StringComparison.Ordinal))
                ? "ADAPTER_IDENTITY_REJECTED"
                : captured.Any(item =>
                    string.Equals(
                        item.Component,
                        "local_ipc",
                        StringComparison.Ordinal) &&
                    string.Equals(
                        item.EventName,
                        "proxy_connected",
                        StringComparison.Ordinal))
                    ? "ADAPTER_HANDSHAKE_INCOMPLETE"
                    : "ADAPTER_CONNECTION_NOT_OBSERVED";
            var failure = new
            {
                schema_version = 1,
                evidence_class = "TARGET_ADAPTER_PREFLIGHT",
                target_contract_complete = false,
                adapter_kind = PerformanceAdapterKind,
                adapter_version = PerformanceAdapterVersion,
                status = "FAIL",
                error_type = exception.GetType().Name,
                normalized_failure = normalizedFailure,
                diagnostics = captured
            };
            await File.WriteAllTextAsync(
                resultPath,
                JsonSerializer.Serialize(
                    failure,
                    new JsonSerializerOptions { WriteIndented = true }));
            return 1;
        }
        finally
        {
            cancellation.Cancel();
            try
            {
                await serverTask;
            }
            catch (OperationCanceledException)
            {
            }
        }
    }

    private static async Task<int> RunColdStartTargetAsync(
        string resultPath,
        int coldCount,
        IDiagnosticsSink diagnostics)
    {
        var bridgeState = new BridgeState();
        var bridgeController = new BridgeController(
            bridgeState,
            new NoopHotkeyRegistrar(),
            diagnostics);
        bridgeController.SetEnabled(true);

        var hub = new BrowserCommandHub(
            bridgeState,
            diagnostics,
            PerformanceAdapterKind,
            PerformanceAdapterVersion);
        var pipeName = ElevationScope.PipeName(ElevationScope.Current());
        using var cancellation = new CancellationTokenSource();
        var serverTask = new LocalIpcServer(
            pipeName,
            hub,
            diagnostics).RunAsync(cancellation.Token);

        try
        {
            if (HasFirefoxProcess())
            {
                throw new InvalidOperationException(
                    "Cold target run requires zero pre-existing Firefox processes.");
            }

            using var clipboard = new StaBenchmarkClipboard();
            var recordingLauncher = new RecordingWorkerEnvironmentLauncher(
                new FirefoxWorkerEnvironmentLauncher());
            var browser = new LaunchingBrowserPort(
                new IpcBrowserPort(hub),
                hub,
                recordingLauncher,
                TimeSpan.FromSeconds(8));
            var samples = new List<double>();

            for (var index = 0; index < coldCount; index++)
            {
                if (HasFirefoxProcess())
                {
                    throw new InvalidOperationException(
                        "Unowned Firefox process appeared during cold-start measurement.");
                }

                recordingLauncher.Reset();

                var world = new SimulatorWorld();
                var slot = $"perf-cold-{index}";
                world.Sessions.Add(
                    slot,
                    0,
                    SimContinuity.NotEstablished,
                    bindingPresent: false);
                var action = world.Queue(
                    $"perf-cold-action-{index}",
                    "CREATE_AND_SERVICE",
                    slot,
                    0);
                var coordinator = new SingleFlightDispatchCoordinator(
                    bridgeState,
                    new SimulatorActionPort(world),
                    browser,
                    clipboard,
                    new SystemMonotonicClock(),
                    diagnostics);

                var started = Stopwatch.GetTimestamp();
                var result = await coordinator.DispatchAsync();
                samples.Add(
                    Stopwatch.GetElapsedTime(started).TotalMilliseconds);

                if (result.Outcome != DispatchOutcome.LocalPrepared ||
                    !world.HumanSubmit(action))
                {
                    throw new InvalidOperationException(
                        "Cold-start performance dispatch failed.");
                }

                if (recordingLauncher.LastProcessId is not int processId)
                {
                    throw new InvalidOperationException(
                        "Cold-start launcher did not return an owned process ID.");
                }

                await TerminateOwnedFirefoxAsync(processId);

                var disconnectDeadline = Stopwatch.StartNew();
                while (hub.IsConnected &&
                       disconnectDeadline.Elapsed < TimeSpan.FromSeconds(10))
                {
                    await Task.Delay(100);
                }

                if (hub.IsConnected)
                {
                    throw new InvalidOperationException(
                        "Firefox adapter did not disconnect after owned process exit.");
                }
                if (HasFirefoxProcess())
                {
                    throw new InvalidOperationException(
                        "Firefox process attribution was lost after cold-start trial.");
                }
            }

            var report = new
            {
                schema_version = 1,
                stage = "impl_09_performance_benchmark_execution",
                evidence_class = "TARGET_COLD_FIREFOX_PARTIAL",
                target_contract_complete = false,
                content_policy = "CONTENT_FREE",
                cold_firefox_start = new
                {
                    count = coldCount,
                    latency_ms = SummarizeLatency(samples)
                },
                security = new
                {
                    dom_or_page_content_collected = false,
                    raw_urls_collected = false,
                    screenshots_collected = false,
                    credentials_or_tokens_collected = false,
                    synthetic_paste_enter_send_or_mouse = false,
                    only_launcher_returned_process_tree_terminated = true
                }
            };

            Directory.CreateDirectory(
                Path.GetDirectoryName(Path.GetFullPath(resultPath))!);
            await File.WriteAllTextAsync(
                resultPath,
                JsonSerializer.Serialize(
                    report,
                    new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
        catch (Exception exception)
        {
            Directory.CreateDirectory(
                Path.GetDirectoryName(Path.GetFullPath(resultPath))!);
            var failure = new
            {
                schema_version = 1,
                stage = "impl_09_performance_benchmark_execution",
                evidence_class = "TARGET_COLD_FIREFOX_PARTIAL",
                target_contract_complete = false,
                result = "HARNESS_FAILURE",
                normalized_exception = exception.GetType().Name,
                content_policy = "CONTENT_FREE"
            };
            await File.WriteAllTextAsync(
                resultPath,
                JsonSerializer.Serialize(
                    failure,
                    new JsonSerializerOptions { WriteIndented = true }));
            return 1;
        }
        finally
        {
            cancellation.Cancel();
            try
            {
                await serverTask;
            }
            catch (OperationCanceledException)
            {
            }
        }
    }

    private static bool HasFirefoxProcess()
    {
        var processes = Process.GetProcessesByName(FirefoxProcessName);
        try
        {
            return processes.Length > 0;
        }
        finally
        {
            foreach (var process in processes)
            {
                process.Dispose();
            }
        }
    }

    private static async Task TerminateOwnedFirefoxAsync(int processId)
    {
        try
        {
            using var process = Process.GetProcessById(processId);
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync();
            }
        }
        catch (ArgumentException)
        {
        }

        await Task.Delay(500);
    }

    private static async Task<ResourceRun> MeasureHelperIdleAsync(
        string helperPath,
        int warmupMs,
        int sampleMs,
        int intervalMs)
    {
        if (!File.Exists(helperPath))
        {
            throw new FileNotFoundException(
                "WorkspaceOperator helper missing.",
                helperPath);
        }

        using var process = Process.Start(new ProcessStartInfo
        {
            FileName = helperPath,
            UseShellExecute = false
        }) ?? throw new InvalidOperationException(
            "Unable to start WorkspaceOperator helper.");

        try
        {
            return await SampleSpecificProcessAsync(
                process,
                "HELPER_IDLE",
                1,
                warmupMs,
                sampleMs,
                intervalMs);
        }
        finally
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync();
            }
            await Task.Delay(300);
        }
    }

    private static async Task<LatencyReport> MeasureLatenciesAsync(
        IpcBrowserPort ipc,
        BridgeState bridgeState,
        StaBenchmarkClipboard clipboard,
        IDiagnosticsSink diagnostics,
        BrowserTarget reuseTarget,
        BrowserTarget restoreTarget,
        TrialCounts counts)
    {
        var reuseWorld = new SimulatorWorld();
        reuseWorld.Sessions.Add(
            reuseTarget.WorkerSlotId,
            reuseTarget.SessionGeneration,
            SimContinuity.Trusted,
            bindingPresent: true);
        var reuseCoordinator = new SingleFlightDispatchCoordinator(
            bridgeState,
            new SimulatorActionPort(reuseWorld),
            ipc,
            clipboard,
            new SystemMonotonicClock(),
            diagnostics);

        var reuse = new List<double>();
        for (var index = 0; index < counts.Reuse; index++)
        {
            var action = reuseWorld.Queue(
                $"perf-reuse-{index}",
                "SERVICE_EXISTING",
                reuseTarget.WorkerSlotId,
                reuseTarget.SessionGeneration);
            var started = Stopwatch.GetTimestamp();
            var result = await reuseCoordinator.DispatchAsync();
            reuse.Add(Stopwatch.GetElapsedTime(started).TotalMilliseconds);
            if (result.Outcome != DispatchOutcome.LocalPrepared ||
                !reuseWorld.HumanSubmit(action))
            {
                throw new InvalidOperationException(
                    "Reuse performance dispatch failed.");
            }
        }

        var restoreWorld = new SimulatorWorld();
        restoreWorld.Sessions.Add(
            restoreTarget.WorkerSlotId,
            restoreTarget.SessionGeneration,
            SimContinuity.Trusted,
            bindingPresent: true);
        var restoreCoordinator = new SingleFlightDispatchCoordinator(
            bridgeState,
            new SimulatorActionPort(restoreWorld),
            ipc,
            clipboard,
            new SystemMonotonicClock(),
            diagnostics);

        var restore = new List<double>();
        for (var index = 0; index < counts.Restore; index++)
        {
            var focusParking = await ipc.FocusTargetAsync(
                reuseTarget,
                CancellationToken.None);
            var discarded = await ipc.DiscardTargetAsync(
                restoreTarget,
                CancellationToken.None);
            if (!focusParking.IsApplied || !discarded.IsApplied)
            {
                throw new InvalidOperationException(
                    "Restore benchmark precondition failed.");
            }

            var action = restoreWorld.Queue(
                $"perf-restore-{index}",
                "RESTORE_AND_SERVICE",
                restoreTarget.WorkerSlotId,
                restoreTarget.SessionGeneration);
            var started = Stopwatch.GetTimestamp();
            var result = await restoreCoordinator.DispatchAsync();
            restore.Add(Stopwatch.GetElapsedTime(started).TotalMilliseconds);
            if (result.Outcome != DispatchOutcome.LocalPrepared ||
                !restoreWorld.HumanSubmit(action))
            {
                throw new InvalidOperationException(
                    "Restore performance dispatch failed.");
            }
        }

        var create = new List<double>();
        for (var index = 0; index < counts.Create; index++)
        {
            var world = new SimulatorWorld();
            var slot = $"perf-create-{index}";
            world.Sessions.Add(
                slot,
                0,
                SimContinuity.NotEstablished,
                bindingPresent: false);
            var action = world.Queue(
                $"perf-create-action-{index}",
                "CREATE_AND_SERVICE",
                slot,
                0);
            var coordinator = new SingleFlightDispatchCoordinator(
                bridgeState,
                new SimulatorActionPort(world),
                ipc,
                clipboard,
                new SystemMonotonicClock(),
                diagnostics);

            var started = Stopwatch.GetTimestamp();
            var result = await coordinator.DispatchAsync();
            create.Add(Stopwatch.GetElapsedTime(started).TotalMilliseconds);
            if (result.Outcome != DispatchOutcome.LocalPrepared ||
                !world.HumanSubmit(action))
            {
                throw new InvalidOperationException(
                    "Create performance dispatch failed.");
            }

            var closed = await ipc.CloseTargetAsync(
                new BrowserTarget(slot, 0),
                CancellationToken.None);
            if (!closed.IsApplied)
            {
                throw new InvalidOperationException(
                    "Create performance cleanup failed.");
            }
        }

        var activate = new List<double>();
        for (var index = 0; index < counts.Primitive; index++)
        {
            await ipc.FocusTargetAsync(
                restoreTarget,
                CancellationToken.None);
            var started = Stopwatch.GetTimestamp();
            var result = await ipc.FocusTargetAsync(
                reuseTarget,
                CancellationToken.None);
            activate.Add(
                Stopwatch.GetElapsedTime(started).TotalMilliseconds);
            if (!result.IsApplied)
            {
                throw new InvalidOperationException(
                    "Activation performance operation failed.");
            }
        }

        var clipboardBefore = clipboard.Durations.Count;
        for (var index = 0; index < counts.Primitive; index++)
        {
            clipboard.WriteText(
                $"WORKSPACE_STAGE09_SYNTHETIC_PACKET_{index}");
        }
        var clipboardDurations = clipboard.Durations
            .Skip(clipboardBefore)
            .ToArray();

        var noWorkCoordinator = new SingleFlightDispatchCoordinator(
            bridgeState,
            new NoWorkActionPort(),
            ipc,
            clipboard,
            new SystemMonotonicClock(),
            diagnostics);
        var noWork = new List<double>();
        for (var index = 0; index < counts.Primitive; index++)
        {
            var started = Stopwatch.GetTimestamp();
            var result = await noWorkCoordinator.DispatchAsync();
            noWork.Add(
                Stopwatch.GetElapsedTime(started).TotalMilliseconds);
            if (result.Outcome != DispatchOutcome.NoAction)
            {
                throw new InvalidOperationException(
                    "No-work performance dispatch failed.");
            }
        }

        return new LatencyReport(
            SummarizeLatency(reuse),
            SummarizeLatency(restore),
            SummarizeLatency(create),
            SummarizeLatency(activate),
            SummarizeLatency(clipboardDurations),
            SummarizeLatency(noWork));
    }

    private static HotkeyMeasurement MeasureHotkeyQueueToCallback(
        int repetitions)
    {
        var samples = new List<double>();
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                using var window = new HotkeyMessageWindow();
                var registrar = new WindowsHotkeyRegistrar(window.Handle);
                registrar.Register();
                try
                {
                    for (var index = 0; index < repetitions; index++)
                    {
                        var completed = false;
                        var elapsed = 0.0;
                        var started = 0L;

                        EventHandler handler = (_, _) =>
                        {
                            elapsed = Stopwatch.GetElapsedTime(started)
                                .TotalMilliseconds;
                            completed = true;
                        };
                        window.HotkeyPressed += handler;
                        try
                        {
                            started = Stopwatch.GetTimestamp();
                            if (!PostMessage(
                                window.Handle,
                                HotkeyMessageWindow.WmHotkey,
                                new IntPtr(0x5743),
                                IntPtr.Zero))
                            {
                                throw new InvalidOperationException(
                                    "PostMessage WM_HOTKEY failed.");
                            }

                            var deadline = Stopwatch.StartNew();
                            while (!completed &&
                                   deadline.Elapsed < TimeSpan.FromSeconds(2))
                            {
                                System.Windows.Forms.Application.DoEvents();
                                Thread.Sleep(1);
                            }

                            if (!completed)
                            {
                                throw new TimeoutException(
                                    "WM_HOTKEY callback timed out.");
                            }
                            samples.Add(elapsed);
                        }
                        finally
                        {
                            window.HotkeyPressed -= handler;
                        }
                    }
                }
                finally
                {
                    registrar.Unregister();
                }
            }
            catch (Exception exception)
            {
                failure = exception;
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();

        return failure is null
            ? new HotkeyMeasurement(
                "WM_HOTKEY_QUEUE_TO_CALLBACK",
                "PASS",
                SummarizeLatency(samples),
                null)
            : new HotkeyMeasurement(
                "WM_HOTKEY_QUEUE_TO_CALLBACK",
                "INVALID",
                null,
                failure.GetType().Name);
    }

    private static async Task CloseAllManagedAsync(IpcBrowserPort ipc)
    {
        var inventory = await ipc.InventoryAsync();
        foreach (var entry in inventory)
        {
            await ipc.CloseTargetAsync(
                new BrowserTarget(
                    entry.WorkerSlotId,
                    entry.SessionGeneration),
                CancellationToken.None);
        }
    }

    private static async Task<ResourceRun> SampleSpecificProcessAsync(
        Process process,
        string scenarioId,
        int repetition,
        int warmupMs,
        int sampleMs,
        int intervalMs)
    {
        await Task.Delay(warmupMs);
        process.Refresh();
        var previousCpu = process.TotalProcessorTime;
        var previousTime = Stopwatch.GetTimestamp();
        var working = new List<double>();
        var privateMemory = new List<double>();
        var cpu = new List<double>();
        var deadline = Stopwatch.StartNew();

        while (deadline.ElapsedMilliseconds < sampleMs)
        {
            await Task.Delay(intervalMs);
            process.Refresh();
            if (process.HasExited)
            {
                throw new InvalidOperationException(
                    "Measured helper process exited early.");
            }

            var now = Stopwatch.GetTimestamp();
            var currentCpu = process.TotalProcessorTime;
            var wallMs = Stopwatch.GetElapsedTime(previousTime, now)
                .TotalMilliseconds;
            var cpuMs = (currentCpu - previousCpu).TotalMilliseconds;

            working.Add(process.WorkingSet64 / 1048576.0);
            privateMemory.Add(process.PrivateMemorySize64 / 1048576.0);
            cpu.Add(wallMs <= 0 ? 0 : Math.Max(0, cpuMs / wallMs * 100.0));

            previousCpu = currentCpu;
            previousTime = now;
        }

        return new ResourceRun(
            scenarioId,
            repetition,
            null,
            null,
            working,
            privateMemory,
            cpu,
            Summarize(working),
            Summarize(privateMemory),
            Summarize(cpu));
    }

    private static async Task<ResourceRun> SampleProcessGroupAsync(
        string processName,
        string scenarioId,
        int repetition,
        int? liveTabs,
        int? discardedTabs,
        int warmupMs,
        int sampleMs,
        int intervalMs)
    {
        await Task.Delay(warmupMs);

        var currentSession = Process.GetCurrentProcess().SessionId;
        var previousCpu = SnapshotCpu(processName, currentSession);
        var previousTime = Stopwatch.GetTimestamp();
        var working = new List<double>();
        var privateMemory = new List<double>();
        var cpu = new List<double>();
        var deadline = Stopwatch.StartNew();

        while (deadline.ElapsedMilliseconds < sampleMs)
        {
            await Task.Delay(intervalMs);
            var processes = Process.GetProcessesByName(processName)
                .Where(p =>
                {
                    try { return p.SessionId == currentSession; }
                    catch { return false; }
                })
                .ToArray();

            if (processes.Length == 0)
            {
                throw new InvalidOperationException(
                    $"No {processName} processes available for sampling.");
            }

            double workingMiB = 0;
            double privateMiB = 0;
            var currentCpu = new Dictionary<int, TimeSpan>();
            foreach (var process in processes)
            {
                try
                {
                    process.Refresh();
                    workingMiB += process.WorkingSet64 / 1048576.0;
                    privateMiB += process.PrivateMemorySize64 / 1048576.0;
                    currentCpu[process.Id] = process.TotalProcessorTime;
                }
                catch
                {
                }
                finally
                {
                    process.Dispose();
                }
            }

            var now = Stopwatch.GetTimestamp();
            var wallMs = Stopwatch.GetElapsedTime(previousTime, now)
                .TotalMilliseconds;
            var cpuMs = 0.0;
            foreach (var pair in currentCpu)
            {
                if (previousCpu.TryGetValue(pair.Key, out var before))
                {
                    cpuMs += Math.Max(
                        0,
                        (pair.Value - before).TotalMilliseconds);
                }
            }

            working.Add(workingMiB);
            privateMemory.Add(privateMiB);
            cpu.Add(wallMs <= 0 ? 0 : cpuMs / wallMs * 100.0);

            previousCpu = currentCpu;
            previousTime = now;
        }

        return new ResourceRun(
            scenarioId,
            repetition,
            liveTabs,
            discardedTabs,
            working,
            privateMemory,
            cpu,
            Summarize(working),
            Summarize(privateMemory),
            Summarize(cpu));
    }

    private static Dictionary<int, TimeSpan> SnapshotCpu(
        string processName,
        int sessionId)
    {
        var result = new Dictionary<int, TimeSpan>();
        foreach (var process in Process.GetProcessesByName(processName))
        {
            try
            {
                if (process.SessionId == sessionId)
                {
                    result[process.Id] = process.TotalProcessorTime;
                }
            }
            catch
            {
            }
            finally
            {
                process.Dispose();
            }
        }
        return result;
    }

    private static Summary Summarize(IEnumerable<double> values)
    {
        var ordered = values.Order().ToArray();
        if (ordered.Length == 0)
        {
            return new Summary(0, 0, 0, 0);
        }
        return new Summary(
            Percentile(ordered, 0.50),
            Percentile(ordered, 0.95),
            ordered[^1],
            ordered.Average());
    }

    private static LatencySummary SummarizeLatency(
        IEnumerable<double> values)
    {
        var array = values.ToArray();
        var summary = Summarize(array);
        return new LatencySummary(
            array.Length,
            summary.P50,
            summary.P95,
            summary.Max,
            summary.Mean);
    }

    private static double Percentile(double[] sorted, double percentile)
    {
        var index = Math.Clamp(
            (int)Math.Ceiling(percentile * sorted.Length) - 1,
            0,
            sorted.Length - 1);
        return sorted[index];
    }

    private static string RequiredArgument(string[] args, string name) =>
        GetArgument(args, name) ??
        throw new ArgumentException($"{name} is required.");

    private static int IntArgument(
        string[] args,
        string name,
        int defaultValue) =>
        int.TryParse(GetArgument(args, name), out var value) && value > 0
            ? value
            : defaultValue;

    private static string? GetArgument(string[] args, string name)
    {
        var prefix = name + "=";
        return args.FirstOrDefault(x =>
                x.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            ?[prefix.Length..];
    }

    private static bool HasFlag(string[] args, string name) =>
        args.Any(x => x.Equals(name, StringComparison.OrdinalIgnoreCase));

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool PostMessage(
        IntPtr hWnd,
        int msg,
        IntPtr wParam,
        IntPtr lParam);
}

internal sealed record TrialCounts(
    int Reuse,
    int Restore,
    int Create,
    int Primitive);

internal sealed record Summary(
    double P50,
    double P95,
    double Max,
    double Mean);

internal sealed record ResourceRun(
    string ScenarioId,
    int Repetition,
    int? LiveTabs,
    int? DiscardedTabs,
    IReadOnlyList<double> WorkingSetMiBSamples,
    IReadOnlyList<double> PrivateMemoryMiBSamples,
    IReadOnlyList<double> CpuOneLogicalCpuPercentSamples,
    Summary WorkingSet,
    Summary PrivateMemory,
    Summary CpuOneLogicalCpuPercent);

internal sealed record LatencySummary(
    int Count,
    double P50,
    double P95,
    double Max,
    double Mean);

internal sealed record LatencyReport(
    LatencySummary ReuseReady,
    LatencySummary RestoreReady,
    LatencySummary CreateReady,
    LatencySummary ExistingTabActivate,
    LatencySummary ClipboardWrite,
    LatencySummary NoWork);

internal sealed record HotkeyMeasurement(
    string Metric,
    string Status,
    LatencySummary? Latency,
    string? InvalidReason);

internal sealed class CaptureDiagnostics : IDiagnosticsSink
{
    private const int MaxEvents = 64;
    private readonly object _gate = new();
    private readonly List<DiagnosticEvent> _events = [];

    public IReadOnlyList<DiagnosticEvent> Snapshot
    {
        get
        {
            lock (_gate)
            {
                return _events.ToArray();
            }
        }
    }

    public void Write(DiagnosticEvent diagnosticEvent)
    {
        lock (_gate)
        {
            if (_events.Count < MaxEvents)
            {
                _events.Add(diagnosticEvent);
            }
        }
    }
}

internal sealed class RecordingWorkerEnvironmentLauncher
    : IWorkerEnvironmentLauncher
{
    private readonly IWorkerEnvironmentLauncher _inner;

    public RecordingWorkerEnvironmentLauncher(
        IWorkerEnvironmentLauncher inner)
    {
        _inner = inner;
    }

    public int? LastProcessId { get; private set; }

    public void Reset() => LastProcessId = null;

    public async Task<WorkerEnvironmentLaunchResult> LaunchAsync(
        CancellationToken cancellationToken)
    {
        var result = await _inner.LaunchAsync(cancellationToken);
        LastProcessId = result.ProcessId;
        return result;
    }
}

internal sealed class NoopHotkeyRegistrar : IHotkeyRegistrar
{
    public bool IsRegistered { get; private set; }
    public void Register() => IsRegistered = true;
    public void Unregister() => IsRegistered = false;
}

internal sealed class NoWorkActionPort : IOperatorActionPort
{
    public Task<OperatorAction?> ClaimNextAsync(
        CancellationToken cancellationToken) =>
        Task.FromResult<OperatorAction?>(null);

    public Task<bool> RevalidateAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken) =>
        Task.FromResult(false);

    public Task RecordLocalPreparedAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken) =>
        Task.CompletedTask;

    public Task RecordLocalFailureAsync(
        ActionIdentity identity,
        string normalizedError,
        CancellationToken cancellationToken) =>
        Task.CompletedTask;
}

internal sealed class SimulatorActionPort : IOperatorActionPort
{
    private readonly SimulatorWorld _world;

    public SimulatorActionPort(SimulatorWorld world)
    {
        _world = world;
    }

    public Task<OperatorAction?> ClaimNextAsync(
        CancellationToken cancellationToken)
    {
        var next = _world.Actions.Actions.FirstOrDefault(item =>
            item.Status == SimActionStatus.Queued);
        if (next is null)
        {
            return Task.FromResult<OperatorAction?>(null);
        }

        var claimed = _world.Actions.ClaimNext(_world.OrchestratorAvailable);
        if (claimed is null)
        {
            return Task.FromResult<OperatorAction?>(null);
        }

        return Task.FromResult<OperatorAction?>(new OperatorAction(
            new ActionIdentity(
                claimed.ActionId,
                claimed.WorkerSlotId,
                claimed.SessionGeneration),
            $"WORKSPACE_STAGE09_PACKET_V1\naction_id={claimed.ActionId}\n",
            $"sim://payload/{claimed.ActionId}",
            claimed.ExpectedPayloadSha256,
            ParseType(claimed.ActionType)));
    }

    public Task<bool> RevalidateAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken)
    {
        var action = Find(identity);
        return Task.FromResult(
            action is { Status: SimActionStatus.ClaimedLocal } &&
            _world.Sessions.IsCurrent(
                identity.WorkerSlotId,
                identity.SessionGeneration));
    }

    public Task RecordLocalPreparedAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken)
    {
        var action = Find(identity) ??
            throw new InvalidOperationException("Synthetic action missing.");
        _world.Actions.MarkLocalPrepared(action);
        return Task.CompletedTask;
    }

    public Task RecordLocalFailureAsync(
        ActionIdentity identity,
        string normalizedError,
        CancellationToken cancellationToken)
    {
        var action = Find(identity);
        if (action is not null)
        {
            _world.Actions.MarkFailedLocal(action, normalizedError);
        }
        return Task.CompletedTask;
    }

    public Task RecordBlockedAsync(
        ActionIdentity identity,
        string normalizedError,
        CancellationToken cancellationToken)
    {
        var action = Find(identity) ??
            throw new InvalidOperationException("Synthetic action missing.");
        action.Status = SimActionStatus.Blocked;
        return Task.CompletedTask;
    }

    public Task RecordLocalCompletedAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken)
    {
        var action = Find(identity) ??
            throw new InvalidOperationException("Synthetic action missing.");
        _world.Actions.MarkLocalCompleted(action);
        return Task.CompletedTask;
    }

    private SimAction? Find(ActionIdentity identity) =>
        _world.Actions.Actions.FirstOrDefault(item =>
            item.ActionId == identity.ActionId &&
            item.WorkerSlotId == identity.WorkerSlotId &&
            item.SessionGeneration == identity.SessionGeneration);

    private static OperatorActionType ParseType(string actionType) =>
        actionType switch
        {
            "CREATE_AND_SERVICE" => OperatorActionType.CreateAndService,
            "RESTORE_AND_SERVICE" => OperatorActionType.RestoreAndService,
            _ => OperatorActionType.ServiceExisting
        };
}

internal sealed class StaBenchmarkClipboard : IClipboardWriter, IDisposable
{
    private sealed record WorkItem(
        string Text,
        TaskCompletionSource<double> Completion);

    private readonly BlockingCollection<WorkItem> _queue = new();
    private readonly Thread _thread;
    private readonly List<double> _durations = [];
    private readonly object _gate = new();

    public StaBenchmarkClipboard()
    {
        _thread = new Thread(Run);
        _thread.SetApartmentState(ApartmentState.STA);
        _thread.Start();
    }

    public IReadOnlyList<double> Durations
    {
        get
        {
            lock (_gate)
            {
                return _durations.ToArray();
            }
        }
    }

    public void WriteText(string text)
    {
        var completion = new TaskCompletionSource<double>(
            TaskCreationOptions.RunContinuationsAsynchronously);
        _queue.Add(new WorkItem(text, completion));
        completion.Task.GetAwaiter().GetResult();
    }

    private void Run()
    {
        var writer = new WinFormsClipboardWriter();
        foreach (var item in _queue.GetConsumingEnumerable())
        {
            try
            {
                var started = Stopwatch.GetTimestamp();
                writer.WriteText(item.Text);
                var elapsed = Stopwatch.GetElapsedTime(started)
                    .TotalMilliseconds;
                lock (_gate)
                {
                    _durations.Add(elapsed);
                }
                item.Completion.SetResult(elapsed);
            }
            catch (Exception exception)
            {
                item.Completion.SetException(exception);
            }
        }
    }

    public void Dispose()
    {
        _queue.CompleteAdding();
        _thread.Join();
        _queue.Dispose();
    }
}
