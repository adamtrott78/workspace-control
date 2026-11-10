using System.Text.Json;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Ipc;

public sealed class IpcBrowserPort : IBrowserPort, IManagedBrowserInventory
{
    private readonly BrowserCommandHub _hub;

    public IpcBrowserPort(BrowserCommandHub hub)
    {
        _hub = hub;
    }

    public Task<BrowserResult> PrepareTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        SendAsync("ENSURE_WORKER_SURFACE", target, cancellationToken);

    public Task<BrowserResult> FocusTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        SendAsync("ACTIVATE_WORKER_BINDING", target, cancellationToken);

    public Task<BrowserResult> CreateTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        SendAsync("CREATE_WORKER_BINDING", target, cancellationToken);

    public Task<BrowserResult> RestoreTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        SendAsync("RELOAD_OR_RESTORE_WORKER_BINDING", target, cancellationToken);

    public Task<BrowserResult> DiscardTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        SendAsync("DISCARD_WORKER_BINDING", target, cancellationToken);

    public Task<BrowserResult> CloseTargetAsync(
        BrowserTarget target,
        CancellationToken cancellationToken) =>
        SendAsync("CLOSE_WORKER_BINDING", target, cancellationToken);

    public async Task<IReadOnlyList<BrowserInventoryEntry>> InventoryAsync(
        CancellationToken cancellationToken = default)
    {
        var response = await _hub.SendBrowserCommandAsync(
            "INVENTORY_MANAGED_BINDINGS",
            new BrowserTarget("__inventory__", 0),
            cancellationToken: cancellationToken);

        var payload = response.Payload!.Value;
        var outcome = payload.GetProperty("outcome").GetString();
        if (!string.Equals(outcome, "APPLIED", StringComparison.Ordinal))
        {
            return [];
        }

        if (!payload.TryGetProperty("inventory", out var inventory) ||
            inventory.ValueKind != JsonValueKind.Array)
        {
            return [];
        }

        var entries = new List<BrowserInventoryEntry>();
        foreach (var item in inventory.EnumerateArray())
        {
            entries.Add(new BrowserInventoryEntry(
                item.GetProperty("worker_slot_id").GetString() ?? "",
                item.GetProperty("session_generation").GetInt64(),
                item.GetProperty("binding_ref").GetString() ?? "",
                item.GetProperty("binding_generation").GetInt64(),
                item.TryGetProperty(
                    "origin_classification",
                    out var origin)
                    ? origin.GetString()
                    : null,
                item.TryGetProperty("discarded", out var discarded) &&
                    discarded.ValueKind == JsonValueKind.True,
                item.TryGetProperty("active", out var active) &&
                    active.ValueKind == JsonValueKind.True));
        }

        return entries;
    }

    private async Task<BrowserResult> SendAsync(
        string operation,
        BrowserTarget target,
        CancellationToken cancellationToken)
    {
        var response = await _hub.SendBrowserCommandAsync(
            operation,
            target,
            cancellationToken: cancellationToken);
        var payload = response.Payload!.Value;

        var outcome = payload.GetProperty("outcome").GetString();
        var normalizedError =
            payload.TryGetProperty("normalized_error", out var error) &&
            error.ValueKind == JsonValueKind.String
                ? error.GetString()
                : null;

        return new BrowserResult(
            outcome switch
            {
                "APPLIED" => BrowserOutcome.Applied,
                "NOT_APPLIED" => BrowserOutcome.NotApplied,
                "UNKNOWN" => BrowserOutcome.Unknown,
                _ => BrowserOutcome.Rejected
            },
            normalizedError);
    }
}
