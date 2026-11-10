using System.Diagnostics;
using WorkspaceControl.OperatorBridge.Ports;

namespace WorkspaceControl.OperatorBridge.Windows.Firefox;

public sealed class FirefoxWorkerEnvironmentLauncher
    : IWorkerEnvironmentLauncher
{
    public const string ProfileName = "WorkspaceWorkers";

    public Task<WorkerEnvironmentLaunchResult> LaunchAsync(
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var executable = FindFirefoxExecutable();
        if (executable is null)
        {
            return Task.FromResult(new WorkerEnvironmentLaunchResult(
                false,
                "FIREFOX_EXECUTABLE_NOT_FOUND"));
        }

        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = executable,
                UseShellExecute = false
            };
            startInfo.ArgumentList.Add("-P");
            startInfo.ArgumentList.Add(ProfileName);
            startInfo.ArgumentList.Add("-no-remote");

            var process = Process.Start(startInfo);
            if (process is null)
            {
                return Task.FromResult(new WorkerEnvironmentLaunchResult(
                    false,
                    "FIREFOX_START_FAILED"));
            }

            process.Dispose();
            return Task.FromResult(new WorkerEnvironmentLaunchResult(true));
        }
        catch (Exception exception)
            when (exception is System.ComponentModel.Win32Exception
                  or InvalidOperationException)
        {
            return Task.FromResult(new WorkerEnvironmentLaunchResult(
                false,
                "FIREFOX_START_FAILED"));
        }
    }

    private static string? FindFirefoxExecutable()
    {
        var candidates = new[]
        {
            Path.Combine(
                Environment.GetFolderPath(
                    Environment.SpecialFolder.ProgramFiles),
                "Mozilla Firefox",
                "firefox.exe"),
            Path.Combine(
                Environment.GetFolderPath(
                    Environment.SpecialFolder.ProgramFilesX86),
                "Mozilla Firefox",
                "firefox.exe")
        };

        return candidates.FirstOrDefault(File.Exists);
    }
}
