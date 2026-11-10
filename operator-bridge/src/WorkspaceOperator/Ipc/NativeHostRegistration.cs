using System.Text.Json;
using Microsoft.Win32;
using WorkspaceControl.OperatorBridge.Contracts;

namespace WorkspaceControl.OperatorBridge.Ipc;

public interface ICurrentUserRegistry
{
    void SetDefaultValue(string subKeyPath, string value);
}

public sealed class WindowsCurrentUserRegistry : ICurrentUserRegistry
{
    public void SetDefaultValue(string subKeyPath, string value)
    {
        using var key = Registry.CurrentUser.CreateSubKey(subKeyPath);
        key.SetValue(null, value, RegistryValueKind.String);
    }
}

public sealed class NativeHostRegistration
{
    public const string RegistrySubKey =
        @"Software\Mozilla\NativeMessagingHosts\" +
        BrowserAdapterProtocol.NativeHostName;

    private readonly ICurrentUserRegistry _registry;

    public NativeHostRegistration(ICurrentUserRegistry registry)
    {
        _registry = registry;
    }

    public string GenerateManifest(
        string executablePath,
        string manifestPath)
    {
        if (!Path.IsPathFullyQualified(executablePath) ||
            !Path.IsPathFullyQualified(manifestPath))
        {
            throw new ArgumentException(
                "Native host executable and manifest paths must be absolute.");
        }

        var document = new
        {
            name = BrowserAdapterProtocol.NativeHostName,
            description = "Workspace Control Operator Browser Adapter",
            path = executablePath,
            type = "stdio",
            allowed_extensions = new[]
            {
                BrowserAdapterProtocol.FirefoxExtensionId
            }
        };

        var json = JsonSerializer.Serialize(
            document,
            new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(manifestPath, json);
        return json;
    }

    public void RegisterManifest(string manifestPath)
    {
        if (!Path.IsPathFullyQualified(manifestPath))
        {
            throw new ArgumentException(
                "Native host manifest path must be absolute.");
        }

        _registry.SetDefaultValue(RegistrySubKey, manifestPath);
    }
}
