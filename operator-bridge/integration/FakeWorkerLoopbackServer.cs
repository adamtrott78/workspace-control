using System.Net;
using System.Net.Sockets;
using System.Text;

namespace WorkspaceControl.OperatorBridge.IntegrationHarness;

internal sealed record FakeWorkerSubmission(
    string ActionId,
    string WorkerSlotId,
    long SessionGeneration,
    string PayloadSha256);

internal sealed class FakeWorkerLoopbackServer : IDisposable
{
    private readonly TcpListener _listener;
    private readonly Func<FakeWorkerSubmission, Task<bool>> _submit;
    private readonly CancellationTokenSource _cancellation = new();
    private Task? _loop;

    public FakeWorkerLoopbackServer(
        int port,
        Func<FakeWorkerSubmission, Task<bool>> submit)
    {
        _listener = new TcpListener(IPAddress.Loopback, port);
        _submit = submit;
    }

    public void Start()
    {
        _listener.Start();
        _loop = AcceptLoopAsync(_cancellation.Token);
    }

    private async Task AcceptLoopAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            TcpClient client;
            try
            {
                client = await _listener.AcceptTcpClientAsync(
                    cancellationToken);
            }
            catch (OperationCanceledException)
            {
                return;
            }

            _ = HandleClientAsync(client, cancellationToken);
        }
    }

    private async Task HandleClientAsync(
        TcpClient client,
        CancellationToken cancellationToken)
    {
        using (client)
        using (var stream = client.GetStream())
        using (var reader = new StreamReader(
            stream,
            Encoding.UTF8,
            detectEncodingFromByteOrderMarks: false,
            bufferSize: 4096,
            leaveOpen: true))
        {
            var requestLine = await reader.ReadLineAsync(cancellationToken);
            if (string.IsNullOrWhiteSpace(requestLine))
            {
                return;
            }

            var parts = requestLine.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length < 2)
            {
                await SendAsync(stream, 400, "text/plain", "bad request", cancellationToken);
                return;
            }

            var contentLength = 0;
            string? header;
            while (!string.IsNullOrEmpty(
                header = await reader.ReadLineAsync(cancellationToken)))
            {
                if (header.StartsWith(
                    "Content-Length:",
                    StringComparison.OrdinalIgnoreCase))
                {
                    _ = int.TryParse(
                        header["Content-Length:".Length..].Trim(),
                        out contentLength);
                }
            }

            var method = parts[0].ToUpperInvariant();
            var path = parts[1].Split('?', 2)[0];

            if (method == "GET" &&
                (path == "/" || path == "/fake-worker.html"))
            {
                await SendAsync(
                    stream,
                    200,
                    "text/html; charset=utf-8",
                    Html,
                    cancellationToken);
                return;
            }

            if (method == "POST" && path == "/submit")
            {
                var buffer = new char[Math.Max(0, contentLength)];
                var read = 0;
                while (read < buffer.Length)
                {
                    var count = await reader.ReadAsync(
                        buffer.AsMemory(read, buffer.Length - read),
                        cancellationToken);
                    if (count == 0)
                    {
                        break;
                    }
                    read += count;
                }

                var form = ParseForm(new string(buffer, 0, read));
                if (!form.TryGetValue("action_id", out var actionId) ||
                    !form.TryGetValue("worker_slot_id", out var workerSlotId) ||
                    !form.TryGetValue("session_generation", out var generationText) ||
                    !form.TryGetValue("payload_sha256", out var payloadSha256) ||
                    !long.TryParse(generationText, out var generation))
                {
                    await SendAsync(stream, 400, "text/plain", "invalid simulator packet", cancellationToken);
                    return;
                }

                var applied = await _submit(new FakeWorkerSubmission(
                    actionId,
                    workerSlotId,
                    generation,
                    payloadSha256));

                await SendAsync(
                    stream,
                    applied ? 200 : 409,
                    "text/plain",
                    applied ? "ACK_APPLIED" : "ACK_REJECTED",
                    cancellationToken);
                return;
            }

            await SendAsync(stream, 404, "text/plain", "not found", cancellationToken);
        }
    }

    private static Dictionary<string, string> ParseForm(string body)
    {
        var values = new Dictionary<string, string>(
            StringComparer.Ordinal);
        foreach (var part in body.Split(
            '&',
            StringSplitOptions.RemoveEmptyEntries))
        {
            var pair = part.Split('=', 2);
            var key = Uri.UnescapeDataString(
                pair[0].Replace('+', ' '));
            var value = pair.Length > 1
                ? Uri.UnescapeDataString(pair[1].Replace('+', ' '))
                : "";
            values[key] = value;
        }
        return values;
    }

    private static async Task SendAsync(
        NetworkStream stream,
        int status,
        string contentType,
        string body,
        CancellationToken cancellationToken)
    {
        var payload = Encoding.UTF8.GetBytes(body);
        var reason = status switch
        {
            200 => "OK",
            400 => "Bad Request",
            404 => "Not Found",
            409 => "Conflict",
            _ => "Error"
        };
        var header = Encoding.ASCII.GetBytes(
            $"HTTP/1.1 {status} {reason}\r\n" +
            $"Content-Type: {contentType}\r\n" +
            $"Content-Length: {payload.Length}\r\n" +
            "Cache-Control: no-store\r\n" +
            "Connection: close\r\n\r\n");
        await stream.WriteAsync(header, cancellationToken);
        await stream.WriteAsync(payload, cancellationToken);
        await stream.FlushAsync(cancellationToken);
    }

    public void Dispose()
    {
        _cancellation.Cancel();
        _listener.Stop();
        try
        {
            _loop?.GetAwaiter().GetResult();
        }
        catch (OperationCanceledException)
        {
        }
        _cancellation.Dispose();
    }

    private const string Html = """
<!doctype html>
<meta charset="utf-8">
<title>Workspace Operator Usability Fake Worker</title>
<style>
body { font-family: system-ui, sans-serif; margin: 2rem; }
textarea { width: min(900px, 95vw); height: 16rem; font: 15px monospace; }
#status { display: block; margin-top: 1rem; font-weight: 600; }
</style>
<form id="worker">
  <label for="packet">Synthetic simulator packet</label><br>
  <textarea id="packet" autocomplete="off" autofocus></textarea><br>
  <button type="submit">Submit</button>
</form>
<output id="status">Ready for Ctrl+V then Enter.</output>
<script>
"use strict";
const form = document.getElementById("worker");
const packet = document.getElementById("packet");
const status = document.getElementById("status");

function parsePacket(text) {
  const result = {};
  for (const line of text.split(/\r?\n/)) {
    const index = line.indexOf("=");
    if (index > 0) {
      result[line.slice(0, index)] = line.slice(index + 1);
    }
  }
  return result;
}

async function submitPacket() {
  const fields = parsePacket(packet.value);
  const required = [
    "action_id",
    "worker_slot_id",
    "session_generation",
    "payload_sha256"
  ];
  if (required.some(key => !fields[key])) {
    status.textContent = "Synthetic packet rejected: required identity fields missing.";
    return;
  }

  const response = await fetch("/submit", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
    body: new URLSearchParams(fields)
  });
  status.textContent = await response.text();
  if (response.ok) {
    packet.value = "";
  }
  packet.focus();
}

form.addEventListener("submit", event => {
  event.preventDefault();
  void submitPacket();
});

packet.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

window.addEventListener("focus", () => {
  setTimeout(() => packet.focus(), 0);
});
</script>
""";
}
