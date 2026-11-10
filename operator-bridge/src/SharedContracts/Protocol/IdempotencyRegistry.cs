namespace WorkspaceControl.OperatorBridge.Contracts.Protocol;

public enum IdempotencyDecision
{
    First,
    DuplicateSame,
    Conflict
}

public sealed class IdempotencyRegistry
{
    private readonly object _gate = new();
    private readonly Dictionary<string, string> _requests =
        new(StringComparer.Ordinal);

    public IdempotencyDecision Observe(string requestId, string idempotencyKey)
    {
        if (string.IsNullOrWhiteSpace(requestId) ||
            string.IsNullOrWhiteSpace(idempotencyKey))
        {
            throw new ArgumentException("requestId and idempotencyKey are required.");
        }

        lock (_gate)
        {
            if (!_requests.TryGetValue(requestId, out var existing))
            {
                _requests.Add(requestId, idempotencyKey);
                return IdempotencyDecision.First;
            }

            return string.Equals(existing, idempotencyKey, StringComparison.Ordinal)
                ? IdempotencyDecision.DuplicateSame
                : IdempotencyDecision.Conflict;
        }
    }
}
