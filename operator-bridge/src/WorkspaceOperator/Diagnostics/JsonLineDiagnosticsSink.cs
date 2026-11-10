using System.Text.Json;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Diagnostics;

public sealed class JsonLineDiagnosticsSink : IDiagnosticsSink, IDisposable
{
    private readonly TextWriter _writer;
    private readonly object _gate = new();
    private readonly bool _ownsWriter;

    public JsonLineDiagnosticsSink(TextWriter writer, bool ownsWriter = false)
    {
        _writer = writer;
        _ownsWriter = ownsWriter;
    }

    public static JsonLineDiagnosticsSink CreateDefault()
    {
        var root = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "WorkspaceControl",
            "OperatorBridge",
            "logs");
        Directory.CreateDirectory(root);
        var path = Path.Combine(root, "operator-bridge.jsonl");
        var stream = new FileStream(
            path,
            FileMode.Append,
            FileAccess.Write,
            FileShare.ReadWrite);
        return new JsonLineDiagnosticsSink(new StreamWriter(stream) { AutoFlush = true }, true);
    }

    public void Write(DiagnosticEvent diagnosticEvent)
    {
        var json = JsonSerializer.Serialize(diagnosticEvent);
        lock (_gate)
        {
            _writer.WriteLine(json);
            _writer.Flush();
        }
    }

    public void Dispose()
    {
        if (_ownsWriter)
        {
            _writer.Dispose();
        }
    }
}
