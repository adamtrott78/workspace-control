using System.Collections.Concurrent;
using System.IO;
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Windows.Remote;

public sealed class HttpOperatorBridgeClient :
    IOperatorActionPort,
    IDisposable
{
    private static readonly JsonSerializerOptions JsonOptions =
        new(JsonSerializerDefaults.Web);

    private readonly HttpClient _httpClient;
    private readonly RemoteOperatorBridgeConfiguration _configuration;
    private readonly bool _ownsHttpClient;
    private readonly ConcurrentDictionary<string, long> _actionGenerations =
        new(StringComparer.Ordinal);
    private readonly CancellationTokenSource _pollCancellation = new();
    private readonly Task? _pollTask;
    private WorkloadStatusSnapshot _currentStatus =
        WorkloadStatusSnapshot.Empty;
    private int _disposed;

    public HttpOperatorBridgeClient(
        HttpClient httpClient,
        RemoteOperatorBridgeConfiguration configuration,
        bool startStatusPolling = true,
        bool ownsHttpClient = false)
    {
        ArgumentNullException.ThrowIfNull(httpClient);
        ArgumentNullException.ThrowIfNull(configuration);

        if (!string.Equals(
                configuration.BaseUri.Scheme,
                Uri.UriSchemeHttps,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException(
                "Operator Bridge remote transport requires HTTPS.",
                nameof(configuration));
        }

        if (httpClient.DefaultRequestHeaders.Authorization is not null)
        {
            throw new ArgumentException(
                "Operator Bridge client must not carry an Authorization header.",
                nameof(httpClient));
        }

        _httpClient = httpClient;
        _configuration = configuration;
        _ownsHttpClient = ownsHttpClient;
        _httpClient.BaseAddress = configuration.BaseUri;
        _httpClient.Timeout = configuration.RequestTimeout;

        if (startStatusPolling)
        {
            _pollTask = Task.Run(PollStatusLoopAsync);
        }
    }

    public WorkloadStatusSnapshot CurrentStatus =>
        Volatile.Read(ref _currentStatus);

    public static HttpOperatorBridgeClient Create(
        RemoteOperatorBridgeConfiguration configuration)
    {
        var httpClient = new HttpClient();
        return new HttpOperatorBridgeClient(
            httpClient,
            configuration,
            startStatusPolling: true,
            ownsHttpClient: true);
    }

    public async Task<OperatorAction?> ClaimNextAsync(
        CancellationToken cancellationToken)
    {
        ThrowIfDisposed();

        var now = DateTimeOffset.UtcNow;
        var request = new ClaimRequest(
            _configuration.HelperInstanceId,
            Guid.NewGuid().ToString("N"),
            now.ToString("O"),
            now.Add(_configuration.ClaimLease).ToString("O"));

        using var response = await _httpClient.PostAsJsonAsync(
            "operator-bridge/v1/actions/claim",
            request,
            JsonOptions,
            cancellationToken);

        if (response.StatusCode == HttpStatusCode.NoContent)
        {
            // A 204 means there is no *new* claimable action. It does not
            // mean the workload is truly idle: a previously prepared action
            // may still be awaiting durable acknowledgement. Refresh the
            // authoritative content-free counters before the caller decides
            // whether the worker window may be minimized.
            await RefreshStatusAsync(cancellationToken);
            return null;
        }

        response.EnsureSuccessStatusCode();
        var envelope = await response.Content.ReadFromJsonAsync<ClaimResponse>(
            JsonOptions,
            cancellationToken);
        if (envelope is null)
        {
            throw new InvalidDataException("REMOTE_ACTION_RESPONSE_EMPTY");
        }

        ValidateClaim(envelope);
        _actionGenerations[envelope.ActionId] = envelope.Generation;

        return new OperatorAction(
            new ActionIdentity(
                envelope.ActionId,
                envelope.WorkerSlotId ?? string.Empty,
                envelope.SessionGeneration ?? 0),
            envelope.PacketText ?? string.Empty,
            envelope.PayloadRef ?? string.Empty,
            envelope.PayloadSha256 ?? string.Empty,
            ParseActionType(envelope.ActionType));
    }

    public async Task<bool> RevalidateAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken)
    {
        ThrowIfDisposed();

        if (!_actionGenerations.TryGetValue(
                identity.ActionId,
                out var generation))
        {
            return false;
        }

        using var response = await _httpClient.PostAsJsonAsync(
            ActionPath(identity.ActionId, "revalidate"),
            BuildIdentityRequest(identity, generation),
            JsonOptions,
            cancellationToken);
        response.EnsureSuccessStatusCode();

        var result = await response.Content.ReadFromJsonAsync<RevalidateResponse>(
            JsonOptions,
            cancellationToken);
        return result?.Valid == true;
    }

    public Task RecordLocalPreparedAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken) =>
        RecordTerminalLocalAsync(
            identity,
            "local-prepared",
            cancellationToken);

    public Task RecordLocalCompletedAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken) =>
        RecordTerminalLocalAsync(
            identity,
            "local-completed",
            cancellationToken);

    public Task RecordLocalFailureAsync(
        ActionIdentity identity,
        string normalizedError,
        CancellationToken cancellationToken) =>
        RecordFailureAsync(
            identity,
            "local-failure",
            "LOCAL_FAILURE",
            normalizedError,
            cancellationToken);

    public Task RecordBlockedAsync(
        ActionIdentity identity,
        string normalizedError,
        CancellationToken cancellationToken) =>
        RecordFailureAsync(
            identity,
            "blocked",
            "LOCAL_BLOCKED",
            normalizedError,
            cancellationToken);

    public async Task RefreshStatusAsync(
        CancellationToken cancellationToken = default)
    {
        ThrowIfDisposed();

        using var response = await _httpClient.GetAsync(
            "operator-bridge/v1/status",
            cancellationToken);
        response.EnsureSuccessStatusCode();

        var status = await response.Content.ReadFromJsonAsync<StatusResponse>(
            JsonOptions,
            cancellationToken);
        if (status is null ||
            status.ReadyManualCycles < 0 ||
            status.SentUnconfirmed < 0)
        {
            throw new InvalidDataException("REMOTE_STATUS_INVALID");
        }

        Volatile.Write(
            ref _currentStatus,
            new WorkloadStatusSnapshot(
                status.ReadyManualCycles,
                status.SentUnconfirmed));
    }

    private async Task RecordTerminalLocalAsync(
        ActionIdentity identity,
        string operation,
        CancellationToken cancellationToken)
    {
        var generation = GetGeneration(identity.ActionId);
        using var response = await _httpClient.PostAsJsonAsync(
            ActionPath(identity.ActionId, operation),
            BuildIdentityRequest(identity, generation),
            JsonOptions,
            cancellationToken);
        response.EnsureSuccessStatusCode();
        _actionGenerations.TryRemove(identity.ActionId, out _);
    }

    private async Task RecordFailureAsync(
        ActionIdentity identity,
        string operation,
        string failureCode,
        string normalizedError,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(normalizedError);
        var generation = GetGeneration(identity.ActionId);
        var request = new FailureRequest(
            generation,
            EmptyToNull(identity.WorkerSlotId),
            EmptyToNull(identity.WorkerSlotId) is null
                ? null
                : identity.SessionGeneration,
            failureCode,
            normalizedError);

        using var response = await _httpClient.PostAsJsonAsync(
            ActionPath(identity.ActionId, operation),
            request,
            JsonOptions,
            cancellationToken);
        response.EnsureSuccessStatusCode();
        _actionGenerations.TryRemove(identity.ActionId, out _);
    }

    private long GetGeneration(string actionId)
    {
        ThrowIfDisposed();
        if (!_actionGenerations.TryGetValue(actionId, out var generation))
        {
            throw new InvalidOperationException(
                "REMOTE_ACTION_GENERATION_UNKNOWN");
        }

        return generation;
    }

    private static IdentityRequest BuildIdentityRequest(
        ActionIdentity identity,
        long generation)
    {
        var slot = EmptyToNull(identity.WorkerSlotId);
        return new IdentityRequest(
            generation,
            slot,
            slot is null ? null : identity.SessionGeneration);
    }

    private static string? EmptyToNull(string value) =>
        string.IsNullOrEmpty(value) ? null : value;

    private static string ActionPath(
        string actionId,
        string operation) =>
        $"operator-bridge/v1/actions/{Uri.EscapeDataString(actionId)}/{operation}";

    private static OperatorActionType ParseActionType(string value) =>
        value switch
        {
            "SERVICE_EXISTING" => OperatorActionType.ServiceExisting,
            "CREATE_AND_SERVICE" => OperatorActionType.CreateAndService,
            "RESTORE_AND_SERVICE" => OperatorActionType.RestoreAndService,
            "DISCARD_SESSION" => OperatorActionType.DiscardSession,
            "RETIRE_SESSION" => OperatorActionType.RetireSession,
            "OPEN_JUDGMENT_GATE" => OperatorActionType.OpenJudgmentGate,
            "OPEN_RECOVERY" => OperatorActionType.OpenRecovery,
            _ => throw new InvalidDataException(
                "REMOTE_ACTION_TYPE_INVALID")
        };

    private static void ValidateClaim(ClaimResponse value)
    {
        if (string.IsNullOrWhiteSpace(value.ActionId) ||
            value.Generation < 0 ||
            string.IsNullOrWhiteSpace(value.ActionType))
        {
            throw new InvalidDataException("REMOTE_ACTION_INVALID");
        }

        var type = ParseActionType(value.ActionType);
        var sessionRequired = type is
            OperatorActionType.ServiceExisting or
            OperatorActionType.CreateAndService or
            OperatorActionType.RestoreAndService or
            OperatorActionType.DiscardSession or
            OperatorActionType.RetireSession;
        if (sessionRequired &&
            (string.IsNullOrWhiteSpace(value.WorkerSlotId) ||
             value.SessionGeneration is null or < 0))
        {
            throw new InvalidDataException(
                "REMOTE_ACTION_SESSION_INVALID");
        }

        var packetRequired = type is
            OperatorActionType.ServiceExisting or
            OperatorActionType.CreateAndService or
            OperatorActionType.RestoreAndService;
        if (packetRequired &&
            (string.IsNullOrEmpty(value.PacketText) ||
             string.IsNullOrWhiteSpace(value.PayloadRef) ||
             !IsSha256(value.PayloadSha256)))
        {
            throw new InvalidDataException(
                "REMOTE_ACTION_PAYLOAD_INVALID");
        }
    }

    private static bool IsSha256(string? value) =>
        value is not null &&
        value.Length == 64 &&
        value.All(ch =>
            (ch >= '0' && ch <= '9') ||
            (ch >= 'a' && ch <= 'f'));

    private async Task PollStatusLoopAsync()
    {
        try
        {
            try
            {
                await RefreshStatusAsync(_pollCancellation.Token);
            }
            catch (Exception) when (!_pollCancellation.IsCancellationRequested)
            {
            }

            using var timer = new PeriodicTimer(
                _configuration.StatusRefreshInterval);
            while (await timer.WaitForNextTickAsync(
                       _pollCancellation.Token))
            {
                try
                {
                    await RefreshStatusAsync(_pollCancellation.Token);
                }
                catch (Exception)
                    when (!_pollCancellation.IsCancellationRequested)
                {
                }
            }
        }
        catch (OperationCanceledException)
            when (_pollCancellation.IsCancellationRequested)
        {
        }
    }

    private void ThrowIfDisposed()
    {
        ObjectDisposedException.ThrowIf(
            Volatile.Read(ref _disposed) != 0,
            this);
    }

    public void Dispose()
    {
        if (Interlocked.Exchange(ref _disposed, 1) != 0)
        {
            return;
        }

        _pollCancellation.Cancel();
        if (_ownsHttpClient)
        {
            _httpClient.Dispose();
        }

        if (_pollTask is null)
        {
            _pollCancellation.Dispose();
        }
        else
        {
            _ = _pollTask.ContinueWith(
                _ => _pollCancellation.Dispose(),
                CancellationToken.None,
                TaskContinuationOptions.ExecuteSynchronously,
                TaskScheduler.Default);
        }

        GC.SuppressFinalize(this);
    }

    private sealed record ClaimRequest(
        string HelperInstanceId,
        string ClaimId,
        string ClaimedAt,
        string ExpiresAt);

    private sealed record ClaimResponse(
        string ActionId,
        long Generation,
        string? WorkerSlotId,
        long? SessionGeneration,
        string ActionType,
        string? PacketText,
        string? PayloadRef,
        string? PayloadSha256);

    private sealed record IdentityRequest(
        long Generation,
        string? WorkerSlotId,
        long? SessionGeneration);

    private sealed record FailureRequest(
        long Generation,
        string? WorkerSlotId,
        long? SessionGeneration,
        string FailureCode,
        string FailureMessage);

    private sealed record RevalidateResponse(bool Valid);

    private sealed record StatusResponse(
        int ReadyManualCycles,
        int SentUnconfirmed);
}
