using System.Text.Json;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Windows;

public sealed class JsonRecoveryStateStore : IRecoveryStateStore
{
    private readonly string _path;

    public JsonRecoveryStateStore(string path)
    {
        _path = path;
    }

    public static JsonRecoveryStateStore CreateDefault()
    {
        var root = Path.Combine(
            Environment.GetFolderPath(
                Environment.SpecialFolder.LocalApplicationData),
            "WorkspaceControl",
            "OperatorBridge");
        return new JsonRecoveryStateStore(
            Path.Combine(root, "recovery-state.json"));
    }

    public async Task<RecoveryIncident?> LoadAsync(
        CancellationToken cancellationToken)
    {
        if (!File.Exists(_path))
        {
            return null;
        }

        await using var stream = new FileStream(
            _path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read);
        return await JsonSerializer.DeserializeAsync<RecoveryIncident>(
            stream,
            cancellationToken: cancellationToken);
    }

    public async Task SaveAsync(
        RecoveryIncident incident,
        CancellationToken cancellationToken)
    {
        var directory = Path.GetDirectoryName(
            Path.GetFullPath(_path))!;
        Directory.CreateDirectory(directory);
        var temporary = _path + ".tmp";

        await using (var stream = new FileStream(
            temporary,
            FileMode.Create,
            FileAccess.Write,
            FileShare.None))
        {
            await JsonSerializer.SerializeAsync(
                stream,
                incident,
                cancellationToken: cancellationToken);
            await stream.FlushAsync(cancellationToken);
        }

        File.Move(temporary, _path, true);
    }

    public Task ClearAsync(CancellationToken cancellationToken)
    {
        if (File.Exists(_path))
        {
            File.Delete(_path);
        }
        return Task.CompletedTask;
    }
}
