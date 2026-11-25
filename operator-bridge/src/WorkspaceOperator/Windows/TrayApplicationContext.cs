using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Bootstrap;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ipc;
using WorkspaceControl.OperatorBridge.Ports;
using WorkspaceControl.OperatorBridge.Windows.Clipboard;
using WorkspaceControl.OperatorBridge.Windows.Hotkey;
using WorkspaceControl.OperatorBridge.Windows.Firefox;

namespace WorkspaceControl.OperatorBridge.Windows;

public sealed class TrayApplicationContext : ApplicationContext
{
    private readonly NotifyIcon _notifyIcon;
    private readonly ToolStripMenuItem _toggleItem;
    private readonly ToolStripMenuItem _readyItem;
    private readonly ToolStripMenuItem _sentItem;
    private readonly BridgeController _bridgeController;
    private readonly SingleFlightDispatchCoordinator _dispatch;
    private readonly HotkeyMessageWindow _hotkeyWindow;
    private readonly JsonLineDiagnosticsSink _diagnostics;
    private readonly System.Windows.Forms.Timer? _idleProbeTimer;
    private readonly System.Windows.Forms.Timer _statusTimer;
    private readonly Func<WorkloadStatusSnapshot> _workloadStatusProvider;
    private readonly string _configuredHotkey;
    private readonly WorkerWindowSafetyController _workerWindowSafety;
    private readonly HumanSubmitConfirmationGate _humanSubmitConfirmation;
    private readonly IDisposable? _operatorActionLifetime;
    private Icon? _statusIcon;
    private readonly CancellationTokenSource _ipcCancellation = new();
    private readonly Task _ipcTask;
    private readonly BrowserCommandHub _browserCommandHub;
    private WorkloadStatusSnapshot _lastWorkloadStatus =
        WorkloadStatusSnapshot.Empty;
    private bool _lastBridgeEnabled;
    private bool _hasObservedWorkloadStatus;
    private int _humanSubmitMinimizePending;
    private int _hotkeyDispatching;

    public TrayApplicationContext(
        int? idleProbeMilliseconds = null,
        SchedulerHotkeyBinding? schedulerHotkey = null,
        Func<WorkloadStatusSnapshot>? workloadStatusProvider = null,
        IOperatorActionPort? operatorActionPort = null,
        IDisposable? operatorActionLifetime = null,
        bool startEnabled = false)
    {
        _diagnostics = JsonLineDiagnosticsSink.CreateDefault();
        _hotkeyWindow = new HotkeyMessageWindow();

        var bridgeState = new BridgeState();
        var binding = schedulerHotkey ?? SchedulerHotkeyBinding.Default;
        _configuredHotkey = binding.DisplayName;
        _workloadStatusProvider =
            workloadStatusProvider ?? (() => WorkloadStatusSnapshot.Empty);
        _operatorActionLifetime = operatorActionLifetime;
        _workerWindowSafety = new WorkerWindowSafetyController(
            new Win32WorkerWindowSafetyPort());
        _humanSubmitConfirmation = new HumanSubmitConfirmationGate(
            _workerWindowSafety.IsPreparedWorkerWindowForeground);
        var hotkey = new WindowsHotkeyRegistrar(
            _hotkeyWindow.Handle,
            binding);
        _bridgeController = new BridgeController(
            bridgeState,
            hotkey,
            _diagnostics);

        _browserCommandHub = new BrowserCommandHub(
            bridgeState,
            _diagnostics);

        var browserPort = new LaunchingBrowserPort(
            new IpcBrowserPort(_browserCommandHub),
            _browserCommandHub,
            new FirefoxWorkerEnvironmentLauncher(),
            TimeSpan.FromSeconds(8));

        _dispatch = new SingleFlightDispatchCoordinator(
            bridgeState,
            operatorActionPort ?? new NoWorkOperatorActionPort(),
            browserPort,
            new WinFormsClipboardWriter(),
            new SystemMonotonicClock(),
            _diagnostics);

        var pipeName = ElevationScope.PipeName(ElevationScope.Current());
        _ipcTask = new LocalIpcServer(
            pipeName,
            _browserCommandHub,
            _diagnostics).RunAsync(_ipcCancellation.Token);

        _toggleItem = new ToolStripMenuItem("Bridge: OFF");
        _toggleItem.Click += ToggleClicked;

        _readyItem = new ToolStripMenuItem("Ready now: 0")
        {
            Enabled = false
        };
        _sentItem = new ToolStripMenuItem("Sent / unconfirmed: 0")
        {
            Enabled = false
        };

        var statusItem = new ToolStripMenuItem("Stage 03 local IPC")
        {
            Enabled = false
        };

        var exitItem = new ToolStripMenuItem("Exit");
        exitItem.Click += ExitClicked;

        _notifyIcon = new NotifyIcon
        {
            Icon = SystemIcons.Application,
            Text = "Workspace Worker Bridge: OFF",
            Visible = true,
            ContextMenuStrip = new ContextMenuStrip()
        };
        _notifyIcon.ContextMenuStrip.Items.Add(statusItem);
        _notifyIcon.ContextMenuStrip.Items.Add(_readyItem);
        _notifyIcon.ContextMenuStrip.Items.Add(_sentItem);
        _notifyIcon.ContextMenuStrip.Items.Add(new ToolStripSeparator());
        _notifyIcon.ContextMenuStrip.Items.Add(_toggleItem);
        _notifyIcon.ContextMenuStrip.Items.Add(new ToolStripSeparator());
        _notifyIcon.ContextMenuStrip.Items.Add(exitItem);

        _hotkeyWindow.HotkeyPressed += HotkeyPressed;
        _humanSubmitConfirmation.Confirmed += HumanSubmitConfirmed;

        if (startEnabled)
        {
            _bridgeController.SetEnabled(true);
        }

        _statusTimer = new System.Windows.Forms.Timer
        {
            Interval = 250
        };
        _statusTimer.Tick += (_, _) =>
        {
            ProcessHumanSubmitUiEffects();
            RefreshPresentation();
        };
        _statusTimer.Start();
        RefreshPresentation();

        if (idleProbeMilliseconds is > 0)
        {
            _idleProbeTimer = new System.Windows.Forms.Timer
            {
                Interval = idleProbeMilliseconds.Value
            };
            _idleProbeTimer.Tick += (_, _) =>
            {
                _idleProbeTimer.Stop();
                ExitThread();
            };
            _idleProbeTimer.Start();
        }
    }

    private void ToggleClicked(object? sender, EventArgs e)
    {
        try
        {
            _bridgeController.SetEnabled(!_bridgeController.IsEnabled);
        }
        catch (HotkeyRegistrationException)
        {
        }

        RefreshPresentation();
    }

    private async void HotkeyPressed(object? sender, EventArgs e)
    {
        if (Interlocked.Exchange(ref _hotkeyDispatching, 1) != 0)
        {
            return;
        }

        try
        {
            if (_humanSubmitConfirmation.IsAwaitingConfirmation &&
                !_humanSubmitConfirmation.TryConsumeConfirmed())
            {
                _workerWindowSafety.ForegroundPreparedWorkerWindow();
                _notifyIcon.ShowBalloonTip(
                    2500,
                    "Workspace Worker Bridge",
                    "No Enter confirmation recorded. Press Enter in the prepared worker Firefox tab after pasting the prompt, then press Ctrl+Space again.",
                    ToolTipIcon.None);
                return;
            }

            var result = await _dispatch.DispatchAsync();
            if (result.Outcome == DispatchOutcome.LocalPrepared)
            {
                _workerWindowSafety.ForegroundPreparedWorkerWindow();
                var captured =
                    _workerWindowSafety.RecordPreparedWorkerWindow();
                var armed =
                    captured && _humanSubmitConfirmation.Arm();
                if (!armed)
                {
                    _notifyIcon.ShowBalloonTip(
                        3000,
                        "Workspace Worker Bridge",
                        "Enter confirmation monitor unavailable; this worker will remain blocked rather than advance.",
                        ToolTipIcon.Warning);
                }
            }
            else if (result.Outcome == DispatchOutcome.NoAction)
            {
                var workload = _workloadStatusProvider();
                if (workload.SentUnconfirmed > 0)
                {
                    _notifyIcon.ShowBalloonTip(
                        2500,
                        "Workspace Worker Bridge",
                        "Still awaiting durable acknowledgment; no new action is ready. Worker Firefox remains minimized.",
                        ToolTipIcon.None);
                }
                else if (workload.ReadyManualCycles > 0)
                {
                    _notifyIcon.ShowBalloonTip(
                        3000,
                        "Workspace Worker Bridge",
                        "Backend reports ready work, but no action was claimed. Worker Firefox was not changed.",
                        ToolTipIcon.Warning);
                }
                else
                {
                    var minimized = _workerWindowSafety.MinimizeAfterNoAction();
                    _notifyIcon.ShowBalloonTip(
                        1500,
                        "Workspace Worker Bridge",
                        minimized
                            ? "Nothing needs service; worker Firefox minimized"
                            : "Nothing needs service",
                        ToolTipIcon.None);
                }
            }

            RefreshPresentation();
        }
        finally
        {
            Volatile.Write(ref _hotkeyDispatching, 0);
        }
    }

    private void HumanSubmitConfirmed(object? sender, EventArgs e)
    {
        // Do not minimize from inside the low-level keyboard hook callback.
        // Deferring to the UI timer lets Firefox receive the Enter key first.
        Volatile.Write(ref _humanSubmitMinimizePending, 1);
    }

    private void ProcessHumanSubmitUiEffects()
    {
        if (Interlocked.Exchange(ref _humanSubmitMinimizePending, 0) == 0)
        {
            return;
        }

        if (!_workerWindowSafety.MinimizeAfterHumanSubmit())
        {
            _notifyIcon.ShowBalloonTip(
                3000,
                "Workspace Worker Bridge",
                "Enter was observed, but the prepared worker Firefox window could not be safely minimized. Durable acknowledgment still controls progress.",
                ToolTipIcon.Warning);
        }
    }

    private void ExitClicked(object? sender, EventArgs e) => ExitThread();

    private void RefreshPresentation()
    {
        var enabled = _bridgeController.IsEnabled;
        var workload = _workloadStatusProvider();
        var presentation = WorkloadStatusPresentation.Project(
            enabled,
            workload,
            _configuredHotkey);

        var readyBecameServiceable =
            enabled &&
            workload.ReadyManualCycles > 0 &&
            (!_hasObservedWorkloadStatus ||
             !_lastBridgeEnabled ||
             WorkloadStatusPresentation.BecameReady(
                 _lastWorkloadStatus,
                 workload));

        if (readyBecameServiceable)
        {
            _notifyIcon.ShowBalloonTip(
                2500,
                "Workspace Worker Bridge",
                "New worker action ready — press Ctrl+Space to service.",
                ToolTipIcon.Info);
        }

        _lastWorkloadStatus = workload;
        _lastBridgeEnabled = enabled;
        _hasObservedWorkloadStatus = true;

        _toggleItem.Text = enabled ? "Bridge: ON" : "Bridge: OFF";
        _readyItem.Text = presentation.ReadyLabel;
        _sentItem.Text = presentation.SentUnconfirmedLabel;
        _notifyIcon.Text = presentation.Tooltip;

        var nextIcon = WorkloadTrayIconFactory.Create(presentation);
        var previous = _statusIcon;
        _statusIcon = nextIcon;
        _notifyIcon.Icon = nextIcon;
        previous?.Dispose();
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

        _ipcCancellation.Cancel();
        try
        {
            _ipcTask.GetAwaiter().GetResult();
        }
        catch (OperationCanceledException)
        {
        }

        _hotkeyWindow.HotkeyPressed -= HotkeyPressed;
        _humanSubmitConfirmation.Confirmed -= HumanSubmitConfirmed;
        _humanSubmitConfirmation.Dispose();
        _idleProbeTimer?.Dispose();
        _statusTimer.Stop();
        _statusTimer.Dispose();
        _notifyIcon.Visible = false;
        _notifyIcon.Dispose();
        _statusIcon?.Dispose();
        _hotkeyWindow.Dispose();
        _operatorActionLifetime?.Dispose();
        _diagnostics.Dispose();
        _ipcCancellation.Dispose();
        base.ExitThreadCore();
    }
}
