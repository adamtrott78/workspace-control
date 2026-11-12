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
    private Icon? _statusIcon;
    private readonly CancellationTokenSource _ipcCancellation = new();
    private readonly Task _ipcTask;
    private readonly BrowserCommandHub _browserCommandHub;
    private int _hotkeyDispatching;

    public TrayApplicationContext(
        int? idleProbeMilliseconds = null,
        SchedulerHotkeyBinding? schedulerHotkey = null,
        Func<WorkloadStatusSnapshot>? workloadStatusProvider = null)
    {
        _diagnostics = JsonLineDiagnosticsSink.CreateDefault();
        _hotkeyWindow = new HotkeyMessageWindow();

        var bridgeState = new BridgeState();
        var binding = schedulerHotkey ?? SchedulerHotkeyBinding.Default;
        _configuredHotkey = binding.DisplayName;
        _workloadStatusProvider =
            workloadStatusProvider ?? (() => WorkloadStatusSnapshot.Empty);
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
            new NoWorkOperatorActionPort(),
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

        _statusTimer = new System.Windows.Forms.Timer
        {
            Interval = 500
        };
        _statusTimer.Tick += (_, _) => RefreshPresentation();
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
            var result = await _dispatch.DispatchAsync();
            if (result.Outcome == DispatchOutcome.NoAction)
            {
                _notifyIcon.ShowBalloonTip(
                    1500,
                    "Workspace Worker Bridge",
                    "Nothing needs service",
                    ToolTipIcon.None);
            }

            RefreshPresentation();
        }
        finally
        {
            Volatile.Write(ref _hotkeyDispatching, 0);
        }
    }

    private void ExitClicked(object? sender, EventArgs e) => ExitThread();

    private void RefreshPresentation()
    {
        var enabled = _bridgeController.IsEnabled;
        var presentation = WorkloadStatusPresentation.Project(
            enabled,
            _workloadStatusProvider(),
            _configuredHotkey);

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
        _idleProbeTimer?.Dispose();
        _statusTimer.Stop();
        _statusTimer.Dispose();
        _notifyIcon.Visible = false;
        _notifyIcon.Dispose();
        _statusIcon?.Dispose();
        _hotkeyWindow.Dispose();
        _diagnostics.Dispose();
        _ipcCancellation.Dispose();
        base.ExitThreadCore();
    }
}
