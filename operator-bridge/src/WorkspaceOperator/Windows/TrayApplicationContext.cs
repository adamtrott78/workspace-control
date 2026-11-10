using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Bootstrap;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ipc;
using WorkspaceControl.OperatorBridge.Ports;
using WorkspaceControl.OperatorBridge.Windows.Clipboard;
using WorkspaceControl.OperatorBridge.Windows.Hotkey;

namespace WorkspaceControl.OperatorBridge.Windows;

public sealed class TrayApplicationContext : ApplicationContext
{
    private readonly NotifyIcon _notifyIcon;
    private readonly ToolStripMenuItem _toggleItem;
    private readonly BridgeController _bridgeController;
    private readonly SingleFlightDispatchCoordinator _dispatch;
    private readonly HotkeyMessageWindow _hotkeyWindow;
    private readonly JsonLineDiagnosticsSink _diagnostics;
    private readonly System.Windows.Forms.Timer? _idleProbeTimer;
    private readonly CancellationTokenSource _ipcCancellation = new();
    private readonly Task _ipcTask;
    private int _hotkeyDispatching;

    public TrayApplicationContext(int? idleProbeMilliseconds = null)
    {
        _diagnostics = JsonLineDiagnosticsSink.CreateDefault();
        _hotkeyWindow = new HotkeyMessageWindow();

        var bridgeState = new BridgeState();
        var hotkey = new WindowsHotkeyRegistrar(_hotkeyWindow.Handle);
        _bridgeController = new BridgeController(
            bridgeState,
            hotkey,
            _diagnostics);

        _dispatch = new SingleFlightDispatchCoordinator(
            bridgeState,
            new NoWorkOperatorActionPort(),
            new NoopBrowserPort(),
            new WinFormsClipboardWriter(),
            new SystemMonotonicClock(),
            _diagnostics);

        var pipeName = ElevationScope.PipeName(ElevationScope.Current());
        _ipcTask = new LocalIpcServer(
            pipeName,
            bridgeState,
            _diagnostics).RunAsync(_ipcCancellation.Token);

        _toggleItem = new ToolStripMenuItem("Bridge: OFF");
        _toggleItem.Click += ToggleClicked;

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
        _notifyIcon.ContextMenuStrip.Items.Add(_toggleItem);
        _notifyIcon.ContextMenuStrip.Items.Add(new ToolStripSeparator());
        _notifyIcon.ContextMenuStrip.Items.Add(exitItem);

        _hotkeyWindow.HotkeyPressed += HotkeyPressed;

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
            await _dispatch.DispatchAsync();
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
        _toggleItem.Text = enabled ? "Bridge: ON" : "Bridge: OFF";
        _notifyIcon.Text = enabled
            ? "Workspace Worker Bridge: ON"
            : "Workspace Worker Bridge: OFF";
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
        _notifyIcon.Visible = false;
        _notifyIcon.Dispose();
        _hotkeyWindow.Dispose();
        _diagnostics.Dispose();
        _ipcCancellation.Dispose();
        base.ExitThreadCore();
    }
}
