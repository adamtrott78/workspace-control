using System.Collections.Concurrent;
using System.Text.Json;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Ipc;
using WorkspaceControl.OperatorBridge.Simulator.Scenarios;
using WorkspaceControl.OperatorBridge.Simulator.State;
using WorkspaceControl.OperatorBridge.Windows;
using WorkspaceControl.OperatorBridge.Windows.Clipboard;
using WorkspaceControl.OperatorBridge.Windows.Hotkey;

namespace WorkspaceControl.OperatorBridge.IntegrationHarness;

internal static class UsabilityHarness
{
    private const string AdapterVersion = "0.1.10-usability";

    public static int Run(string[] args)
    {
        ApplicationConfiguration.Initialize();
        SynchronizationContext.SetSynchronizationContext(
            new WindowsFormsSynchronizationContext());

        var trialId = GetArgument(args, "--usability-trial")?.ToUpperInvariant()
            ?? throw new ArgumentException("--usability-trial is required.");
        var resultPath = GetArgument(args, "--result")
            ?? Path.Combine(Environment.CurrentDirectory, $"stage10-{trialId.ToLowerInvariant()}-result.json");
        var readyPath = GetArgument(args, "--ready")
            ?? resultPath + ".ready.json";
        var durationSeconds = int.TryParse(GetArgument(args, "--duration-seconds"), out var parsedDuration)
            ? parsedDuration
            : 900;

        if (durationSeconds is < 10 or > 7200)
        {
            throw new ArgumentOutOfRangeException(
                nameof(durationSeconds),
                "Stage 10 duration must be from 10 through 7200 seconds.");
        }

        var world = new SimulatorWorld();
        SeedTrial(world, trialId);

        var diagnostics = new CaptureDiagnostics();
        var bridgeState = new BridgeState();
        var hub = new BrowserCommandHub(
            bridgeState,
            diagnostics,
            requiredAdapterKind: "FIREFOX_EXTENSION",
            requiredAdapterVersion: AdapterVersion);

        using var ipcCancellation = new CancellationTokenSource();
        var pipeName = ElevationScope.PipeName(ElevationScope.Current());
        var ipcTask = new LocalIpcServer(
            pipeName,
            hub,
            diagnostics).RunAsync(ipcCancellation.Token);

        var submissions = new ConcurrentQueue<UsabilitySubmissionRequest>();
        using var fakeWorker = new FakeWorkerLoopbackServer(
            8765,
            submission =>
            {
                var request = new UsabilitySubmissionRequest(submission);
                submissions.Enqueue(request);
                return request.Completion.Task;
            });
        fakeWorker.Start();

        try
        {
            var connected = hub.WaitForConnectionAsync(
                    TimeSpan.FromSeconds(90))
                .GetAwaiter()
                .GetResult();

            if (!connected)
            {
                WriteSetupFailure(
                    resultPath,
                    trialId,
                    "ADAPTER_CONNECTION_NOT_OBSERVED");
                return 1;
            }

            var browser = new IpcBrowserPort(hub);
            SeedBrowser(browser, trialId);

            Directory.CreateDirectory(
                Path.GetDirectoryName(Path.GetFullPath(readyPath))!);
            File.WriteAllText(
                readyPath,
                JsonSerializer.Serialize(
                    new
                    {
                        schema_version = 1,
                        evidence_class = "STAGE10_USABILITY_READY",
                        trial_id = trialId,
                        adapter_version = AdapterVersion,
                        fake_worker_origin = "http://127.0.0.1:8765",
                        configured_hotkey = "Ctrl+B",
                        content_policy = "CONTENT_FREE"
                    },
                    new JsonSerializerOptions { WriteIndented = true }));

            using var context = new UsabilityApplicationContext(
                trialId,
                resultPath,
                durationSeconds,
                world,
                submissions,
                bridgeState,
                browser,
                diagnostics);
            System.Windows.Forms.Application.Run(context);
            return context.ExitCode;
        }
        catch (Exception exception)
        {
            WriteSetupFailure(
                resultPath,
                trialId,
                exception.GetType().Name);
            return 1;
        }
        finally
        {
            ipcCancellation.Cancel();
            try
            {
                ipcTask.GetAwaiter().GetResult();
            }
            catch (OperationCanceledException)
            {
            }
        }
    }

    private static void SeedTrial(
        SimulatorWorld world,
        string trialId)
    {
        switch (trialId)
        {
            case "UT-11":
                return;
            case "UT-01":
                world.Sessions.Add(
                    "slot-1",
                    0,
                    SimContinuity.Trusted,
                    bindingPresent: true);
                world.Sessions.Add(
                    "slot-2",
                    0,
                    SimContinuity.NotEstablished,
                    bindingPresent: false);
                world.Sessions.Add(
                    "slot-3",
                    0,
                    SimContinuity.Trusted,
                    bindingPresent: true);
                world.Queue("ut01-01", "SERVICE_EXISTING", "slot-1", 0);
                world.Queue("ut01-02", "CREATE_AND_SERVICE", "slot-2", 0);
                world.Queue("ut01-03", "SERVICE_EXISTING", "slot-1", 0);
                world.Queue("ut01-04", "RESTORE_AND_SERVICE", "slot-3", 0);
                world.Queue("ut01-05", "SERVICE_EXISTING", "slot-2", 0);
                return;
            case "UT-10":
                world.Sessions.Add(
                    "slot-1",
                    0,
                    SimContinuity.Trusted,
                    bindingPresent: true);
                for (var index = 1; index <= 20; index++)
                {
                    world.Queue(
                        $"ut10-{index:D2}",
                        "SERVICE_EXISTING",
                        "slot-1",
                        0);
                }
                return;
            default:
                throw new ArgumentException(
                    $"Stage 10 usability harness does not yet implement {trialId}.");
        }
    }

    private static void SeedBrowser(
        IpcBrowserPort browser,
        string trialId)
    {
        if (trialId == "UT-11")
        {
            return;
        }

        RequireApplied(
            browser.CreateTargetAsync(
                    new BrowserTarget("slot-1", 0),
                    CancellationToken.None)
                .GetAwaiter()
                .GetResult(),
            "seed slot-1");

        if (trialId == "UT-01")
        {
            RequireApplied(
                browser.CreateTargetAsync(
                        new BrowserTarget("slot-3", 0),
                        CancellationToken.None)
                    .GetAwaiter()
                    .GetResult(),
                "seed slot-3");
            RequireApplied(
                browser.DiscardTargetAsync(
                        new BrowserTarget("slot-3", 0),
                        CancellationToken.None)
                    .GetAwaiter()
                    .GetResult(),
                "discard slot-3");
        }
    }

    private static void RequireApplied(
        BrowserResult result,
        string operation)
    {
        if (!result.IsApplied)
        {
            throw new InvalidOperationException(
                $"Stage 10 browser setup failed at {operation}: " +
                (result.NormalizedError ?? result.Outcome.ToString()));
        }
    }

    private static void WriteSetupFailure(
        string resultPath,
        string trialId,
        string normalizedError)
    {
        Directory.CreateDirectory(
            Path.GetDirectoryName(Path.GetFullPath(resultPath))!);
        File.WriteAllText(
            resultPath,
            JsonSerializer.Serialize(
                new
                {
                    schema_version = 1,
                    stage = "impl_10_usability_trial_execution",
                    evidence_class = "STAGE10_USABILITY_PARTIAL",
                    trial_id = trialId,
                    result = "INVALID",
                    normalized_error = normalizedError,
                    content_policy = "CONTENT_FREE"
                },
                new JsonSerializerOptions { WriteIndented = true }));
    }

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

internal sealed class UsabilityApplicationContext : ApplicationContext
{
    private readonly string _trialId;
    private readonly string _resultPath;
    private readonly DateTimeOffset _started = DateTimeOffset.UtcNow;
    private readonly TimeSpan _duration;
    private readonly SimulatorWorld _world;
    private readonly ConcurrentQueue<UsabilitySubmissionRequest> _submissions;
    private readonly IpcBrowserPort _browser;
    private readonly BridgeController _bridgeController;
    private readonly SingleFlightDispatchCoordinator _dispatch;
    private readonly HotkeyMessageWindow _hotkeyWindow;
    private readonly System.Windows.Forms.Timer _timer;
    private int _dispatching;
    private bool _finishing;

    public UsabilityApplicationContext(
        string trialId,
        string resultPath,
        int durationSeconds,
        SimulatorWorld world,
        ConcurrentQueue<UsabilitySubmissionRequest> submissions,
        BridgeState bridgeState,
        IpcBrowserPort browser,
        CaptureDiagnostics diagnostics)
    {
        _trialId = trialId;
        _resultPath = resultPath;
        _duration = TimeSpan.FromSeconds(durationSeconds);
        _world = world;
        _submissions = submissions;
        _browser = browser;

        _hotkeyWindow = new HotkeyMessageWindow();
        var hotkey = new WindowsHotkeyRegistrar(_hotkeyWindow.Handle);
        _bridgeController = new BridgeController(
            bridgeState,
            hotkey,
            diagnostics);
        _dispatch = new SingleFlightDispatchCoordinator(
            bridgeState,
            new SimulatorOperatorActionPort(world),
            browser,
            new WinFormsClipboardWriter(),
            new SystemMonotonicClock(),
            diagnostics);

        _hotkeyWindow.HotkeyPressed += HotkeyPressed;

        if (_trialId != "UT-11")
        {
            _bridgeController.SetEnabled(true);
        }

        _timer = new System.Windows.Forms.Timer { Interval = 100 };
        _timer.Tick += TimerTick;
        _timer.Start();
    }

    public int ExitCode { get; private set; }
    public int HotkeyPresses { get; private set; }
    public int NoActionPresses { get; private set; }
    public int BusyPresses { get; private set; }
    public int ValidDurableAcks { get; private set; }
    public int WrongWorkerDispatches { get; private set; }
    public int WrongPacketDispatches { get; private set; }
    public int RejectedStateSubmissions { get; private set; }
    public int DispatchFailures { get; private set; }
    public int ClipboardFailedDispatches { get; private set; }
    public string? LastDispatchOutcome { get; private set; }
    public string? LastDispatchError { get; private set; }

    private async void HotkeyPressed(object? sender, EventArgs e)
    {
        HotkeyPresses++;
        if (Interlocked.Exchange(ref _dispatching, 1) != 0)
        {
            BusyPresses++;
            return;
        }

        try
        {
            var result = await _dispatch.DispatchAsync();
            LastDispatchOutcome = result.Outcome.ToString();
            LastDispatchError = result.NormalizedError;

            if (result.Outcome == DispatchOutcome.NoAction)
            {
                NoActionPresses++;
            }
            else if (result.Outcome == DispatchOutcome.Busy)
            {
                BusyPresses++;
            }
            else if (result.Outcome == DispatchOutcome.ClipboardFailed)
            {
                ClipboardFailedDispatches++;
                DispatchFailures++;
                Finish();
            }
            else if (result.Outcome is
                DispatchOutcome.Disabled or
                DispatchOutcome.BrowserPrepareFailed or
                DispatchOutcome.BrowserMaintenanceFailed or
                DispatchOutcome.Stale or
                DispatchOutcome.BrowserFocusFailed or
                DispatchOutcome.Failed)
            {
                DispatchFailures++;
                Finish();
            }
        }
        finally
        {
            Volatile.Write(ref _dispatching, 0);
        }
    }

    private async void TimerTick(object? sender, EventArgs e)
    {
        if (_finishing)
        {
            return;
        }

        _timer.Stop();
        try
        {
            while (_submissions.TryDequeue(out var request))
            {
                var applied = await ApplySubmissionAsync(request.Submission);
                request.Completion.TrySetResult(applied);
            }

            if (ShouldFinish())
            {
                Finish();
                return;
            }
        }
        catch
        {
            ExitCode = 1;
            Finish();
            return;
        }
        finally
        {
            if (!_finishing)
            {
                _timer.Start();
            }
        }
    }

    private async Task<bool> ApplySubmissionAsync(
        FakeWorkerSubmission submission)
    {
        var action = _world.Actions.Actions.FirstOrDefault(
            item => item.ActionId == submission.ActionId);

        if (action is null)
        {
            WrongPacketDispatches++;
            return false;
        }

        var inventory = await _browser.InventoryAsync();
        var active = inventory.FirstOrDefault(item => item.Active);
        if (active is null ||
            active.WorkerSlotId != submission.WorkerSlotId ||
            active.SessionGeneration != submission.SessionGeneration)
        {
            WrongWorkerDispatches++;
            return false;
        }

        if (action.ExpectedPayloadSha256 != submission.PayloadSha256 ||
            action.WorkerSlotId != submission.WorkerSlotId ||
            action.SessionGeneration != submission.SessionGeneration)
        {
            WrongPacketDispatches++;
            return false;
        }

        var applied = _world.HumanSubmit(
            action,
            submission.PayloadSha256);
        if (applied)
        {
            ValidDurableAcks++;
        }
        else
        {
            RejectedStateSubmissions++;
        }
        return applied;
    }

    private bool ShouldFinish()
    {
        if (_trialId == "UT-11")
        {
            return DateTimeOffset.UtcNow - _started >= _duration;
        }

        return _world.Actions.Actions.Count > 0 &&
            _world.Actions.Actions.All(action =>
                action.Status == SimActionStatus.Completed);
    }

    private void Finish()
    {
        if (_finishing)
        {
            return;
        }
        _finishing = true;
        _timer.Stop();

        var intended = _world.Actions.Actions.Count;
        var completed = _world.Actions.Actions.Count(
            action => action.Status == SimActionStatus.Completed);
        var objectivePass = _trialId == "UT-11"
            ? true
            : completed == intended &&
              ValidDurableAcks == intended &&
              WrongWorkerDispatches == 0 &&
              WrongPacketDispatches == 0 &&
              RejectedStateSubmissions == 0 &&
              BusyPresses == 0 &&
              DispatchFailures == 0;

        Directory.CreateDirectory(
            Path.GetDirectoryName(Path.GetFullPath(_resultPath))!);
        File.WriteAllText(
            _resultPath,
            JsonSerializer.Serialize(
                new
                {
                    schema_version = 1,
                    stage = "impl_10_usability_trial_execution",
                    evidence_class = "STAGE10_USABILITY_PARTIAL",
                    trial_id = _trialId,
                    result = objectivePass ? "OBJECTIVE_PASS" : "OBJECTIVE_FAIL",
                    manual_observation_state = "PENDING_OPERATOR_COUNTS_AND_RATINGS",
                    adapter_id = "FIREFOX_EXTENSION",
                    adapter_version = "0.1.10-usability",
                    configured_hotkey = "Ctrl+B",
                    start_timestamp = _started,
                    end_timestamp = DateTimeOffset.UtcNow,
                    actions_intended = intended,
                    actions_completed = completed,
                    valid_durable_acks = ValidDurableAcks,
                    hotkey_presses = HotkeyPresses,
                    no_action_presses = NoActionPresses,
                    busy_presses = BusyPresses,
                    wrong_worker_dispatches = WrongWorkerDispatches,
                    wrong_packet_dispatches = WrongPacketDispatches,
                    rejected_state_submissions = RejectedStateSubmissions,
                    dispatch_failures = DispatchFailures,
                    clipboard_failed_dispatches = ClipboardFailedDispatches,
                    last_dispatch_outcome = LastDispatchOutcome,
                    last_dispatch_error = LastDispatchError,
                    trace_sha256 = _world.Trace.Sha256(),
                    content_policy = "CONTENT_FREE"
                },
                new JsonSerializerOptions { WriteIndented = true }));

        ExitCode = objectivePass ? 0 : 1;
        ExitThread();
    }

    protected override void ExitThreadCore()
    {
        try
        {
            _bridgeController.SetEnabled(false);
        }
        catch
        {
        }

        _hotkeyWindow.HotkeyPressed -= HotkeyPressed;
        _timer.Dispose();
        _hotkeyWindow.Dispose();
        base.ExitThreadCore();
    }
}

internal sealed record UsabilitySubmissionRequest(
    FakeWorkerSubmission Submission)
{
    public TaskCompletionSource<bool> Completion { get; } =
        new(TaskCreationOptions.RunContinuationsAsynchronously);
}
