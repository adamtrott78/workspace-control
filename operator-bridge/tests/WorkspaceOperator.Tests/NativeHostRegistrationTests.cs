using System.Text.Json;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Contracts;
using WorkspaceControl.OperatorBridge.Ipc;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class NativeHostRegistrationTests
{
    [TestMethod]
    public void ManifestAndRegistrationArePerUserAndExtensionBound()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            "wc-ob-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var executable = Path.Combine(root, "WorkspaceOperator.exe");
            var manifest = Path.Combine(root, "native-host.json");
            File.WriteAllBytes(executable, Array.Empty<byte>());
            var registry = new FakeRegistry();
            var registration = new NativeHostRegistration(registry);

            var json = registration.GenerateManifest(executable, manifest);
            registration.RegisterManifest(manifest);

            using var document = JsonDocument.Parse(json);
            var rootElement = document.RootElement;
            Assert.AreEqual(
                BrowserAdapterProtocol.NativeHostName,
                rootElement.GetProperty("name").GetString());
            Assert.AreEqual(executable, rootElement.GetProperty("path").GetString());
            Assert.AreEqual("stdio", rootElement.GetProperty("type").GetString());
            Assert.AreEqual(
                BrowserAdapterProtocol.FirefoxExtensionId,
                rootElement.GetProperty("allowed_extensions")[0].GetString());
            Assert.AreEqual(NativeHostRegistration.RegistrySubKey, registry.SubKey);
            Assert.AreEqual(manifest, registry.Value);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private sealed class FakeRegistry : ICurrentUserRegistry
    {
        public string? SubKey { get; private set; }
        public string? Value { get; private set; }

        public void SetDefaultValue(string subKeyPath, string value)
        {
            SubKey = subKeyPath;
            Value = value;
        }
    }
}
