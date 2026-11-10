using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Application;

public sealed class SingleFlightDispatchCoordinator
{
    private readonly BridgeState _bridgeState;
    private readonly IOperatorActionPort _actions;
    private readonly IBrowserPort _browser;
    private readonly IClipboardWriter _clipboard;
    private readonly IMonotonicClock _clock;
    private readonly IDiagnosticsSink _diagnostics;
    private readonly IOperatorSurfacePort _surface;
    private int _inFlight;

    public SingleFlightDispatchCoordinator(
        BridgeState bridgeState,
        IOperatorActionPort actions,
        IBrowserPort browser,
        IClipboardWriter clipboard,
        IMonotonicClock clock,
        IDiagnosticsSink diagnostics,
        IOperatorSurfacePort? surface = null)
    {
        _bridgeState = bridgeState;
        _actions = actions;
        _browser = browser;
        _clipboard = clipboard;
        _clock = clock;
        _diagnostics = diagnostics;
        _surface = surface ?? new NullOperatorSurfacePort();
    }

    public async Task<DispatchResult> DispatchAsync(
        CancellationToken cancellationToken = default)
    {
        if (!_bridgeState.IsEnabled)
        {
            return new DispatchResult(DispatchOutcome.Disabled);
        }

        if (Interlocked.CompareExchange(ref _inFlight, 1, 0) != 0)
        {
            return new DispatchResult(DispatchOutcome.Busy);
        }

        var started = _clock.GetTimestamp();
        OperatorAction? action = null;

        try
        {
            action = await _actions.ClaimNextAsync(cancellationToken);
            if (action is null)
            {
                Write("dispatch", "NO_ACTION", null, started);
                return new DispatchResult(DispatchOutcome.NoAction);
            }

            if (action.ActionType == OperatorActionType.OpenJudgmentGate)
            {
                await _surface.OpenJudgmentAsync(cancellationToken);
                await _actions.RecordLocalCompletedAsync(
                    action.Identity,
                    cancellationToken);
                Write("dispatch", "JUDGMENT_GATE_OPENED", action, started);
                return new DispatchResult(
                    DispatchOutcome.JudgmentGateOpened,
                    action.Identity.ActionId);
            }

            if (action.ActionType == OperatorActionType.OpenRecovery)
            {
                await _surface.OpenRecoveryAsync(cancellationToken);
                Write("dispatch", "RECOVERY_OPENED", action, started);
                return new DispatchResult(
                    DispatchOutcome.RecoveryOpened,
                    action.Identity.ActionId);
            }

            var target = new BrowserTarget(
                action.Identity.WorkerSlotId,
                action.Identity.SessionGeneration);

            if (action.ActionType is
                OperatorActionType.DiscardSession or
                OperatorActionType.RetireSession)
            {
                var maintenance = action.ActionType == OperatorActionType.DiscardSession
                    ? await _browser.DiscardTargetAsync(target, cancellationToken)
                    : await _browser.CloseTargetAsync(target, cancellationToken);

                if (!maintenance.IsApplied)
                {
                    await RecordFailureAsync(
                        action,
                        maintenance.NormalizedError ?? "BROWSER_MAINTENANCE_FAILED",
                        cancellationToken);
                    Write(
                        "dispatch",
                        "BROWSER_MAINTENANCE_FAILED",
                        action,
                        started,
                        maintenance.NormalizedError);
                    return new DispatchResult(
                        DispatchOutcome.BrowserMaintenanceFailed,
                        action.Identity.ActionId,
                        maintenance.NormalizedError);
                }

                await _actions.RecordLocalCompletedAsync(
                    action.Identity,
                    cancellationToken);
                Write("dispatch", "LOCAL_COMPLETED", action, started);
                return new DispatchResult(
                    DispatchOutcome.LocalCompleted,
                    action.Identity.ActionId);
            }

            var prepared = action.ActionType switch
            {
                OperatorActionType.CreateAndService =>
                    await _browser.CreateTargetAsync(target, cancellationToken),
                OperatorActionType.RestoreAndService =>
                    await _browser.RestoreTargetAsync(target, cancellationToken),
                _ =>
                    await _browser.PrepareTargetAsync(target, cancellationToken)
            };

            if (!prepared.IsApplied)
            {
                await RecordFailureAsync(
                    action,
                    prepared.NormalizedError ?? "BROWSER_PREPARE_FAILED",
                    cancellationToken);
                Write(
                    "dispatch",
                    "BROWSER_PREPARE_FAILED",
                    action,
                    started,
                    prepared.NormalizedError);
                return new DispatchResult(
                    DispatchOutcome.BrowserPrepareFailed,
                    action.Identity.ActionId,
                    prepared.NormalizedError);
            }

            if (!await _actions.RevalidateAsync(
                    action.Identity,
                    cancellationToken))
            {
                await RecordFailureAsync(
                    action,
                    "STALE_ACTION_OR_GENERATION",
                    cancellationToken);
                Write(
                    "dispatch",
                    "STALE",
                    action,
                    started,
                    "STALE_ACTION_OR_GENERATION");
                return new DispatchResult(
                    DispatchOutcome.Stale,
                    action.Identity.ActionId,
                    "STALE_ACTION_OR_GENERATION");
            }

            try
            {
                _clipboard.WriteText(action.PacketText);
            }
            catch (Exception exception)
            {
                var error = ErrorNormalizer.FromException(exception);
                await RecordFailureAsync(action, error, cancellationToken);
                Write("dispatch", "CLIPBOARD_FAILED", action, started, error);
                return new DispatchResult(
                    DispatchOutcome.ClipboardFailed,
                    action.Identity.ActionId,
                    error);
            }

            var focused = await _browser.FocusTargetAsync(
                target,
                cancellationToken);
            if (!focused.IsApplied)
            {
                await RecordFailureAsync(
                    action,
                    focused.NormalizedError ?? "BROWSER_FOCUS_FAILED",
                    cancellationToken);
                Write(
                    "dispatch",
                    "BROWSER_FOCUS_FAILED",
                    action,
                    started,
                    focused.NormalizedError);
                return new DispatchResult(
                    DispatchOutcome.BrowserFocusFailed,
                    action.Identity.ActionId,
                    focused.NormalizedError);
            }

            await _actions.RecordLocalPreparedAsync(
                action.Identity,
                cancellationToken);
            Write("dispatch", "LOCAL_PREPARED", action, started);
            return new DispatchResult(
                DispatchOutcome.LocalPrepared,
                action.Identity.ActionId);
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception exception)
        {
            var error = ErrorNormalizer.FromException(exception);
            if (action is not null)
            {
                await RecordFailureAsync(
                    action,
                    error,
                    CancellationToken.None);
            }

            Write("dispatch", "FAILED", action, started, error);
            return new DispatchResult(
                DispatchOutcome.Failed,
                action?.Identity.ActionId,
                error);
        }
        finally
        {
            Volatile.Write(ref _inFlight, 0);
        }
    }

    private Task RecordFailureAsync(
        OperatorAction action,
        string normalizedError,
        CancellationToken cancellationToken) =>
        _actions.RecordLocalFailureAsync(
            action.Identity,
            normalizedError,
            cancellationToken);

    private void Write(
        string eventName,
        string outcome,
        OperatorAction? action,
        long started,
        string? normalizedError = null)
    {
        var elapsed = _clock.GetElapsedTime(started);
        _diagnostics.Write(new DiagnosticEvent(
            DateTimeOffset.UtcNow,
            "native_helper",
            eventName,
            outcome,
            action?.Identity.ActionId,
            action?.Identity.WorkerSlotId,
            action?.Identity.SessionGeneration,
            action?.PayloadRef,
            action?.PayloadSha256,
            normalizedError,
            elapsed.TotalMilliseconds));
    }
}
