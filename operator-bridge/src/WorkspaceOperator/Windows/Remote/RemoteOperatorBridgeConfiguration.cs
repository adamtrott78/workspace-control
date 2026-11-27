namespace WorkspaceControl.OperatorBridge.Windows.Remote;

public sealed record RemoteOperatorBridgeConfiguration(
    Uri BaseUri,
    string HelperInstanceId,
    TimeSpan RequestTimeout,
    TimeSpan StatusRefreshInterval,
    TimeSpan ClaimLease)
{
    public static RemoteOperatorBridgeConfiguration? Parse(
        string[] args,
        string defaultHelperInstanceId)
    {
        ArgumentNullException.ThrowIfNull(args);
        ValidateHelperInstanceId(defaultHelperInstanceId);

        var rawUrl = ReadSingle(args, "--operator-bridge-url=");
        if (rawUrl is null)
        {
            return null;
        }

        if (!Uri.TryCreate(rawUrl, UriKind.Absolute, out var uri) ||
            !string.Equals(
                uri.Scheme,
                Uri.UriSchemeHttps,
                StringComparison.OrdinalIgnoreCase) ||
            string.IsNullOrWhiteSpace(uri.Host) ||
            !string.IsNullOrEmpty(uri.UserInfo) ||
            !string.IsNullOrEmpty(uri.Query) ||
            !string.IsNullOrEmpty(uri.Fragment) ||
            (uri.AbsolutePath is not "" and not "/"))
        {
            throw new ArgumentException(
                "--operator-bridge-url must be an absolute HTTPS origin with no credentials, path, query, or fragment.");
        }

        var helperInstanceId =
            ReadSingle(args, "--operator-helper-id=") ??
            defaultHelperInstanceId;
        ValidateHelperInstanceId(helperInstanceId);

        var timeoutMs = ReadBoundedMilliseconds(
            args,
            "--operator-bridge-timeout-ms=",
            defaultValue: 5000,
            minimum: 1000,
            maximum: 30000);
        var refreshMs = ReadBoundedMilliseconds(
            args,
            "--operator-status-refresh-ms=",
            defaultValue: 500,
            minimum: 250,
            maximum: 5000);
        var claimLeaseMs = ReadBoundedMilliseconds(
            args,
            "--operator-claim-lease-ms=",
            defaultValue: 30000,
            minimum: 5000,
            maximum: 120000);

        var baseUri = new UriBuilder(uri)
        {
            Path = "/",
            Query = string.Empty,
            Fragment = string.Empty
        }.Uri;

        return new RemoteOperatorBridgeConfiguration(
            baseUri,
            helperInstanceId,
            TimeSpan.FromMilliseconds(timeoutMs),
            TimeSpan.FromMilliseconds(refreshMs),
            TimeSpan.FromMilliseconds(claimLeaseMs));
    }

    private static string? ReadSingle(string[] args, string prefix)
    {
        var values = args
            .Where(arg => arg.StartsWith(
                prefix,
                StringComparison.OrdinalIgnoreCase))
            .Select(arg => arg[prefix.Length..])
            .ToArray();

        if (values.Length > 1)
        {
            throw new ArgumentException(
                $"Duplicate argument: {prefix.TrimEnd('=')}");
        }

        return values.Length == 0 ? null : values[0];
    }

    private static int ReadBoundedMilliseconds(
        string[] args,
        string prefix,
        int defaultValue,
        int minimum,
        int maximum)
    {
        var raw = ReadSingle(args, prefix);
        if (raw is null)
        {
            return defaultValue;
        }

        if (!int.TryParse(raw, out var milliseconds) ||
            milliseconds < minimum ||
            milliseconds > maximum)
        {
            throw new ArgumentException(
                $"{prefix.TrimEnd('=')} must be an integer from {minimum} through {maximum}.");
        }

        return milliseconds;
    }

    private static void ValidateHelperInstanceId(string value)
    {
        if (string.IsNullOrWhiteSpace(value) ||
            value.Length > 128 ||
            value.Any(ch =>
                !(char.IsAsciiLetterOrDigit(ch) ||
                  ch is '-' or '_' or '.' or ':')))
        {
            throw new ArgumentException(
                "Operator helper instance ID must be 1-128 ASCII letters, digits, '.', ':', '_' or '-'.");
        }
    }
}
