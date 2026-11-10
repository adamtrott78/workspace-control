using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Diagnostics;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class DiagnosticsTests
{
    [TestMethod]
    public void DiagnosticSchemaHasNoPacketClipboardUrlOrContentFields()
    {
        var names = typeof(DiagnosticEvent)
            .GetProperties()
            .Select(property => property.Name)
            .ToArray();

        foreach (var forbidden in new[]
                 {
                     "PacketText",
                     "ClipboardContent",
                     "RawUrl",
                     "PageContent",
                     "OutputText",
                     "Credential",
                     "Token"
                 })
        {
            CollectionAssert.DoesNotContain(names, forbidden);
        }
    }

    [TestMethod]
    public void ErrorNormalizerDropsExceptionMessage()
    {
        var error = new InvalidOperationException("SECRET-MESSAGE");

        var normalized = ErrorNormalizer.FromException(error);

        Assert.AreEqual("InvalidOperationException", normalized);
        StringAssert.DoesNotContain(normalized, "SECRET");
    }
}
