using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Windows.Remote;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class RemoteOperatorBridgeConfigurationTests
{
    [TestMethod]
    public void NoRemoteUrlPreservesNoWorkBaseline()
    {
        var result = RemoteOperatorBridgeConfiguration.Parse(
            Array.Empty<string>(),
            "helper-default");

        Assert.IsNull(result);
    }

    [TestMethod]
    public void HttpsOriginParsesWithSafeDefaults()
    {
        var result = RemoteOperatorBridgeConfiguration.Parse(
            new[]
            {
                "--operator-bridge-url=https://workspace-control.tailnet.invalid/",
                "--operator-helper-id=helper-1"
            },
            "fallback");

        Assert.IsNotNull(result);
        Assert.AreEqual(
            "https://workspace-control.tailnet.invalid/",
            result.BaseUri.AbsoluteUri);
        Assert.AreEqual("helper-1", result.HelperInstanceId);
        Assert.AreEqual(TimeSpan.FromSeconds(5), result.RequestTimeout);
        Assert.AreEqual(
            TimeSpan.FromMilliseconds(500),
            result.StatusRefreshInterval);
        Assert.AreEqual(TimeSpan.FromSeconds(30), result.ClaimLease);
    }

    [TestMethod]
    public void ExplicitTimingValuesAreBounded()
    {
        var result = RemoteOperatorBridgeConfiguration.Parse(
            new[]
            {
                "--operator-bridge-url=https://workspace-control.tailnet.invalid/",
                "--operator-bridge-timeout-ms=7000",
                "--operator-status-refresh-ms=750",
                "--operator-claim-lease-ms=45000"
            },
            "helper-default");

        Assert.IsNotNull(result);
        Assert.AreEqual(TimeSpan.FromSeconds(7), result.RequestTimeout);
        Assert.AreEqual(
            TimeSpan.FromMilliseconds(750),
            result.StatusRefreshInterval);
        Assert.AreEqual(TimeSpan.FromSeconds(45), result.ClaimLease);
    }

    [DataTestMethod]
    [DataRow("http://workspace-control.tailnet.invalid/")]
    [DataRow("https://user:pass@workspace-control.tailnet.invalid/")]
    [DataRow("https://workspace-control.tailnet.invalid/path")]
    [DataRow("https://workspace-control.tailnet.invalid/?token=x")]
    [DataRow("https://workspace-control.tailnet.invalid/#fragment")]
    public void UnsafeRemoteOriginsFailClosed(string url)
    {
        Expect<ArgumentException>(() =>
            RemoteOperatorBridgeConfiguration.Parse(
                new[] { $"--operator-bridge-url={url}" },
                "helper-default"));
    }

    [TestMethod]
    public void DuplicateRemoteUrlFailsClosed()
    {
        Expect<ArgumentException>(() =>
            RemoteOperatorBridgeConfiguration.Parse(
                new[]
                {
                    "--operator-bridge-url=https://one.tailnet.invalid/",
                    "--operator-bridge-url=https://two.tailnet.invalid/"
                },
                "helper-default"));
    }

    private static void Expect<TException>(Action action)
        where TException : Exception
    {
        try
        {
            action();
        }
        catch (TException)
        {
            return;
        }

        throw new InvalidOperationException(
            $"Expected exception {typeof(TException).Name}.");
    }

    [DataTestMethod]
    [DataRow("helper with spaces")]
    [DataRow("helper/with/slash")]
    [DataRow("")]
    public void UnsafeHelperIdFailsClosed(string helperId)
    {
        Expect<ArgumentException>(() =>
            RemoteOperatorBridgeConfiguration.Parse(
                new[]
                {
                    "--operator-bridge-url=https://workspace-control.tailnet.invalid/",
                    $"--operator-helper-id={helperId}"
                },
                "fallback"));
    }
}
