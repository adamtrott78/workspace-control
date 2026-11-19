using System.Security.Cryptography;
using System.Text;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Bootstrap;

public sealed class LocalSmokeOperatorActionPort : IOperatorActionPort
{
    public const string SmokePacketText = "WORKSPACE_OPERATOR_SMOKE_PACKET_V1";
    public const string SmokeActionId = "local-smoke-action-v1";
    public const string SmokeWorkerSlotId = "local-smoke-worker-v1";
    public const string SmokePayloadRef = "local-smoke://packet/v1";

    private static readonly ActionIdentity SmokeIdentity =
        new(SmokeActionId, SmokeWorkerSlotId, 0);

    private static readonly string SmokePayloadSha256 =
        Convert.ToHexString(
            SHA256.HashData(Encoding.UTF8.GetBytes(SmokePacketText)))
        .ToLowerInvariant();

    private int _state;

    public bool HasReadyAction => Volatile.Read(ref _state) == 0;

    public Task<OperatorAction?> ClaimNextAsync(
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (Interlocked.CompareExchange(ref _state, 1, 0) != 0)
        {
            return Task.FromResult<OperatorAction?>(null);
        }

        return Task.FromResult<OperatorAction?>(new OperatorAction(
            SmokeIdentity,
            SmokePacketText,
            SmokePayloadRef,
            SmokePayloadSha256,
            OperatorActionType.CreateAndService));
    }

    public Task<bool> RevalidateAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(
            Volatile.Read(ref _state) == 1 &&
            identity == SmokeIdentity);
    }

    public Task RecordLocalPreparedAsync(
        ActionIdentity identity,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        Complete(identity);
        return Task.CompletedTask;
    }

    public Task RecordLocalFailureAsync(
        ActionIdentity identity,
        string normalizedError,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        Complete(identity);
        return Task.CompletedTask;
    }

    private void Complete(ActionIdentity identity)
    {
        if (identity != SmokeIdentity)
        {
            throw new InvalidOperationException(
                "LOCAL_SMOKE_ACTION_IDENTITY_MISMATCH");
        }

        Interlocked.Exchange(ref _state, 2);
    }
}
