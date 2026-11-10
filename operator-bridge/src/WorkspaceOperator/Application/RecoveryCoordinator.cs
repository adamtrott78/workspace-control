using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Application;

public sealed class RecoveryCoordinator : IRecoveryGate
{
    private readonly IRecoveryStateStore _stateStore;
    private readonly IRecoveryAuthorityPort _authority;
    private readonly IManagedBrowserInventory _inventory;
    private readonly IDiagnosticsSink _diagnostics;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private RecoveryIncident? _current;

    public RecoveryCoordinator(
        IRecoveryStateStore stateStore,
        IRecoveryAuthorityPort authority,
        IManagedBrowserInventory inventory,
        IDiagnosticsSink diagnostics)
    {
        _stateStore = stateStore;
        _authority = authority;
        _inventory = inventory;
        _diagnostics = diagnostics;
    }

    public RecoveryIncident? Current => Volatile.Read(ref _current);

    public bool BlocksDispatch
    {
        get
        {
            var current = Current;
            return current is not null &&
                current.Status is not
                    (RecoveryStatus.ReadyToResume or RecoveryStatus.Healthy);
        }
    }

    public async Task<RecoveryIncident?> InitializeAsync(
        CancellationToken cancellationToken = default)
    {
        await _gate.WaitAsync(cancellationToken);
        try
        {
            _current = await _stateStore.LoadAsync(cancellationToken);
            if (_current is not null &&
                _current.Status != RecoveryStatus.Healthy)
            {
                Write("recovery_rehydrated", "BLOCKING");
            }
            return _current;
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<RecoveryIncident> BeginAsync(
        string recoveryId,
        RecoveryScope scope,
        RecoverySignal signal,
        IReadOnlyList<RecoverySessionRef> affectedSessions,
        CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(recoveryId);

        await _gate.WaitAsync(cancellationToken);
        try
        {
            if (_current is not null &&
                _current.Status != RecoveryStatus.Healthy)
            {
                if (string.Equals(
                    _current.RecoveryId,
                    recoveryId,
                    StringComparison.Ordinal))
                {
                    await EnsureFrozenAsync(_current, cancellationToken);
                    return _current;
                }

                throw new InvalidOperationException(
                    "RECOVERY_ALREADY_ACTIVE");
            }

            var incident = new RecoveryIncident
            {
                RecoveryId = recoveryId,
                Scope = scope,
                Status = RecoveryStatus.Reconciling,
                TriggerSignal = signal.ToString(),
                AffectedSessions = affectedSessions
                    .Distinct()
                    .ToList()
            };

            _current = incident;
            await _stateStore.SaveAsync(incident, cancellationToken);
            await EnsureFrozenAsync(incident, cancellationToken);
            Write("recovery_started", "BLOCKING");
            return incident;
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<RecoveryIncident> ReconcileAsync(
        CancellationToken cancellationToken = default)
    {
        await _gate.WaitAsync(cancellationToken);
        try
        {
            var incident = _current ??
                throw new InvalidOperationException(
                    "NO_ACTIVE_RECOVERY");

            await EnsureFrozenAsync(incident, cancellationToken);

            if (!HasStep(incident, "DURABLE_RECONCILED"))
            {
                var reconciliation =
                    await _authority.ReconcileAsync(
                        incident,
                        cancellationToken);
                incident.PendingGenerationAdvances =
                    reconciliation.SessionsRequiringGenerationAdvance
                        .Distinct()
                        .ToList();
                AddStep(incident, "DURABLE_RECONCILED");
                await _stateStore.SaveAsync(incident, cancellationToken);
            }

            foreach (var session in
                     incident.PendingGenerationAdvances.ToArray())
            {
                var step = AdvanceStep(session);
                if (HasStep(incident, step))
                {
                    continue;
                }

                var advanced =
                    await _authority.SupersedeAndAdvanceGenerationAsync(
                        incident.RecoveryId,
                        session,
                        cancellationToken);

                incident.ReplacementGenerations[session.WorkerSlotId] =
                    advanced.NewGeneration;
                AddStep(incident, step);
                await _stateStore.SaveAsync(incident, cancellationToken);
            }

            if (incident.Scope == RecoveryScope.AuthDomainScoped &&
                !incident.ManualAuthReturned)
            {
                incident.Status = RecoveryStatus.AwaitingManualAuth;
                await _stateStore.SaveAsync(incident, cancellationToken);
                Write("recovery_waiting_manual_auth", "BLOCKING");
                return incident;
            }

            incident.Status = RecoveryStatus.Rebuilding;
            await _stateStore.SaveAsync(incident, cancellationToken);

            if (!HasStep(incident, "BROWSER_REINVENTORIED"))
            {
                IReadOnlyList<BrowserInventoryEntry> browserInventory;
                try
                {
                    browserInventory =
                        await _inventory.InventoryAsync(cancellationToken);
                }
                catch
                {
                    incident.Status = RecoveryStatus.Blocked;
                    await _stateStore.SaveAsync(
                        incident,
                        cancellationToken);
                    Write(
                        "recovery_inventory",
                        "BLOCKED",
                        "BROWSER_INVENTORY_UNAVAILABLE");
                    return incident;
                }

                var ambiguous = browserInventory
                    .GroupBy(item => new
                    {
                        item.WorkerSlotId,
                        item.SessionGeneration
                    })
                    .Any(group => group.Count() > 1);

                if (ambiguous)
                {
                    incident.Status = RecoveryStatus.Blocked;
                    await _stateStore.SaveAsync(
                        incident,
                        cancellationToken);
                    Write(
                        "recovery_inventory",
                        "BLOCKED",
                        "BINDING_AMBIGUOUS");
                    return incident;
                }

                AddStep(incident, "BROWSER_REINVENTORIED");
            }

            incident.Status = RecoveryStatus.ReadyToResume;
            await _stateStore.SaveAsync(incident, cancellationToken);
            Write("recovery_ready", "READY_TO_RESUME");
            return incident;
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<RecoveryIncident> MarkManualAuthReturnedAsync(
        CancellationToken cancellationToken = default)
    {
        await _gate.WaitAsync(cancellationToken);
        try
        {
            var incident = _current ??
                throw new InvalidOperationException(
                    "NO_ACTIVE_RECOVERY");

            incident.ManualAuthReturned = true;
            incident.Status = RecoveryStatus.Reconciling;
            await _stateStore.SaveAsync(incident, cancellationToken);
            Write("manual_auth_return_observed", "RECONCILE");
        }
        finally
        {
            _gate.Release();
        }

        return await ReconcileAsync(cancellationToken);
    }

    public async Task MarkHealthyAsync(
        CancellationToken cancellationToken = default)
    {
        await _gate.WaitAsync(cancellationToken);
        try
        {
            if (_current is null)
            {
                return;
            }

            if (_current.Status != RecoveryStatus.ReadyToResume)
            {
                throw new InvalidOperationException(
                    "RECOVERY_NOT_READY");
            }

            _current.Status = RecoveryStatus.Healthy;
            await _stateStore.ClearAsync(cancellationToken);
            _current = null;
            Write("recovery_completed", "HEALTHY");
        }
        finally
        {
            _gate.Release();
        }
    }

    public Task OnBlockingOperatorPressAsync(
        CancellationToken cancellationToken)
    {
        Write("blocking_recovery_operator_press", "RECOVERY_ONLY");
        return Task.CompletedTask;
    }

    private async Task EnsureFrozenAsync(
        RecoveryIncident incident,
        CancellationToken cancellationToken)
    {
        if (HasStep(incident, "SESSIONS_FROZEN"))
        {
            return;
        }

        await _authority.FreezeAsync(incident, cancellationToken);
        AddStep(incident, "SESSIONS_FROZEN");
        await _stateStore.SaveAsync(incident, cancellationToken);
    }

    private static string AdvanceStep(RecoverySessionRef session) =>
        $"GENERATION_ADVANCED:{session.WorkerSlotId}:{session.SessionGeneration}";

    private static bool HasStep(
        RecoveryIncident incident,
        string step) =>
        incident.CompletedSteps.Contains(
            step,
            StringComparer.Ordinal);

    private static void AddStep(
        RecoveryIncident incident,
        string step)
    {
        if (!HasStep(incident, step))
        {
            incident.CompletedSteps.Add(step);
        }
    }

    private void Write(
        string eventName,
        string outcome,
        string? normalizedError = null) =>
        _diagnostics.Write(new DiagnosticEvent(
            DateTimeOffset.UtcNow,
            "recovery_coordinator",
            eventName,
            outcome,
            NormalizedError: normalizedError));
}
