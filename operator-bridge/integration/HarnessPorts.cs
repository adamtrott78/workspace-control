using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;
using WorkspaceControl.OperatorBridge.Simulator.Scenarios;
using WorkspaceControl.OperatorBridge.Simulator.State;

namespace WorkspaceControl.OperatorBridge.IntegrationHarness;

public sealed class SimulatorOperatorActionPort : IOperatorActionPort
{
    private readonly SimulatorWorld _world;

    public SimulatorOperatorActionPort(SimulatorWorld world)
    {
        _world = world;
    }

    public TaskCompletionSource? ClaimEntered { get; set; }
    public Task? ClaimGate { get; set; }

    public async Task<OperatorAction?> ClaimNextAsync(
        CancellationToken cancellationToken)
    {
        ClaimEntered?.TrySetResult();
        if (ClaimGate is not null)
        {
            await ClaimGate.WaitAsync(cancellationToken);
        }

        var next = _world.Actions.Actions.FirstOrDefault(item =>
            item.Status == SimActionStatus.Queued);
        if (next is null)
        {
            return null;
        }

        var session = _world.Sessions.Get(next.WorkerSlotId);
        if (session is { ExecutorCompatible: false })
        {
            _world.Trace.Record(
                "integration_action_port",
                "EXECUTOR_COMPATIBILITY_UNPROVEN",
                next.ActionId,
                next.WorkerSlotId,
                next.SessionGeneration);
            return null;
        }

        var claimed = _world.Actions.ClaimNext(_world.OrchestratorAvailable);
        if (claimed is null)
        {
            return null;
        }

        return new OperatorAction(
            new ActionIdentity(
                claimed.ActionId,
                claimed.WorkerSlotId,
                claimed.SessionGeneration),
            $"WORKSPACE_SIM_PACKET_V1\naction_id={claimed.ActionId}\n",
            $"sim://payload/{claimed.ActionId}",
            claimed.ExpectedPayloadSha256,
            ParseType(claimed.ActionType));
    }

    public Task<bool> RevalidateAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken)
    {
        var action = Find(identity);
        var valid =
            action is { Status: SimActionStatus.ClaimedLocal } &&
            _world.Sessions.IsCurrent(
                identity.WorkerSlotId,
                identity.SessionGeneration);
        return Task.FromResult(valid);
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
            "DISCARD_SESSION" => OperatorActionType.DiscardSession,
            "RETIRE_SESSION" => OperatorActionType.RetireSession,
            "OPEN_JUDGMENT_GATE" => OperatorActionType.OpenJudgmentGate,
            "OPEN_RECOVERY" => OperatorActionType.OpenRecovery,
            _ => OperatorActionType.ServiceExisting
        };
}

public sealed class RecordingClipboardWriter : IClipboardWriter
{
    public int WriteCount { get; private set; }
    public string? LastText { get; private set; }

    public void WriteText(string text)
    {
        WriteCount++;
        LastText = text;
    }
}

public sealed class RecordingBrowserPort : IBrowserPort
{
    private readonly IBrowserPort _inner;

    public RecordingBrowserPort(IBrowserPort inner)
    {
        _inner = inner;
    }

    public int EnsureCount { get; private set; }
    public int CreateCount { get; private set; }
    public int RestoreCount { get; private set; }
    public int ActivateCount { get; private set; }
    public int DiscardCount { get; private set; }
    public int CloseCount { get; private set; }

    public async Task<BrowserResult> PrepareTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        EnsureCount++;
        return await _inner.PrepareTargetAsync(target, cancellationToken);
    }

    public async Task<BrowserResult> FocusTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        ActivateCount++;
        return await _inner.FocusTargetAsync(target, cancellationToken);
    }

    public async Task<BrowserResult> CreateTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        CreateCount++;
        return await _inner.CreateTargetAsync(target, cancellationToken);
    }

    public async Task<BrowserResult> RestoreTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        RestoreCount++;
        return await _inner.RestoreTargetAsync(target, cancellationToken);
    }

    public async Task<BrowserResult> DiscardTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        DiscardCount++;
        return await _inner.DiscardTargetAsync(target, cancellationToken);
    }

    public async Task<BrowserResult> CloseTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        CloseCount++;
        return await _inner.CloseTargetAsync(target, cancellationToken);
    }
}

public sealed class InMemoryBrowserPort : IBrowserPort
{
    private readonly Dictionary<string, (long Generation, bool Discarded)> _bindings =
        new(StringComparer.Ordinal);

    public int EffectCount { get; private set; }

    public Task<BrowserResult> PrepareTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        Task.FromResult(Exists(target)
            ? BrowserResult.Applied()
            : new BrowserResult(BrowserOutcome.Rejected, "MANAGED_BINDING_NOT_FOUND"));

    public Task<BrowserResult> FocusTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        if (!Exists(target))
        {
            return Task.FromResult(
                new BrowserResult(BrowserOutcome.Rejected, "MANAGED_BINDING_NOT_FOUND"));
        }

        EffectCount++;
        return Task.FromResult(BrowserResult.Applied());
    }

    public Task<BrowserResult> CreateTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        var key = target.WorkerSlotId;
        if (_bindings.ContainsKey(key))
        {
            return Task.FromResult(
                new BrowserResult(BrowserOutcome.Rejected, "BINDING_ALREADY_EXISTS"));
        }

        _bindings[key] = (target.SessionGeneration, false);
        EffectCount++;
        return Task.FromResult(BrowserResult.Applied());
    }

    public Task<BrowserResult> RestoreTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        if (!Exists(target))
        {
            return Task.FromResult(
                new BrowserResult(BrowserOutcome.Rejected, "MANAGED_BINDING_NOT_FOUND"));
        }

        _bindings[target.WorkerSlotId] = (target.SessionGeneration, false);
        EffectCount++;
        return Task.FromResult(BrowserResult.Applied());
    }

    public Task<BrowserResult> DiscardTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        if (!Exists(target))
        {
            return Task.FromResult(
                new BrowserResult(BrowserOutcome.Rejected, "MANAGED_BINDING_NOT_FOUND"));
        }

        _bindings[target.WorkerSlotId] = (target.SessionGeneration, true);
        EffectCount++;
        return Task.FromResult(BrowserResult.Applied());
    }

    public Task<BrowserResult> CloseTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        if (!Exists(target))
        {
            return Task.FromResult(
                new BrowserResult(BrowserOutcome.Rejected, "MANAGED_BINDING_NOT_FOUND"));
        }

        _bindings.Remove(target.WorkerSlotId);
        EffectCount++;
        return Task.FromResult(BrowserResult.Applied());
    }

    public void Seed(string slot, long generation) =>
        _bindings[slot] = (generation, false);

    private bool Exists(BrowserTarget target) =>
        _bindings.TryGetValue(target.WorkerSlotId, out var binding) &&
        binding.Generation == target.SessionGeneration;
}

public sealed class RecordingOperatorSurface : IOperatorSurfacePort
{
    public int JudgmentCount { get; private set; }
    public int RecoveryCount { get; private set; }

    public Task OpenJudgmentAsync(CancellationToken cancellationToken)
    {
        JudgmentCount++;
        return Task.CompletedTask;
    }

    public Task OpenRecoveryAsync(CancellationToken cancellationToken)
    {
        RecoveryCount++;
        return Task.CompletedTask;
    }
}

public sealed class CaptureDiagnostics : IDiagnosticsSink
{
    private readonly List<DiagnosticEvent> _events = [];
    public IReadOnlyList<DiagnosticEvent> Events => _events;

    public void Write(DiagnosticEvent diagnosticEvent) =>
        _events.Add(diagnosticEvent);
}

public sealed class NoopHotkeyRegistrar : IHotkeyRegistrar
{
    public bool IsRegistered { get; private set; }

    public void Register() => IsRegistered = true;

    public void Unregister() => IsRegistered = false;
}
