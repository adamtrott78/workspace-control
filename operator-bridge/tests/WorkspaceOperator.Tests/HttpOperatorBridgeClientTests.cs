using System.Net;
using System.Text;
using System.Text.Json;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using WorkspaceControl.OperatorBridge.Application;
using WorkspaceControl.OperatorBridge.Windows.Remote;

namespace WorkspaceControl.OperatorBridge.Tests;

[TestClass]
public sealed class HttpOperatorBridgeClientTests
{
    private static readonly RemoteOperatorBridgeConfiguration Configuration =
        new(
            new Uri("https://workspace-control.tailnet.invalid/"),
            "helper-test",
            TimeSpan.FromSeconds(5),
            TimeSpan.FromSeconds(1),
            TimeSpan.FromSeconds(30));

    [TestMethod]
    public async Task ClaimMapsFrozenActionContractWithoutSendingCredentials()
    {
        HttpRequestMessage? captured = null;
        var handler = new StubHandler(async request =>
        {
            captured = request;
            var body = await request.Content!.ReadAsStringAsync();
            using var json = JsonDocument.Parse(body);
            Assert.AreEqual(
                "helper-test",
                json.RootElement.GetProperty("helperInstanceId").GetString());
            Assert.IsFalse(string.IsNullOrWhiteSpace(
                json.RootElement.GetProperty("claimId").GetString()));

            return Json(
                HttpStatusCode.OK,
                """
                {
                  "actionId":"action:http/leaf",
                  "generation":7,
                  "workerSlotId":"instant-slot-1",
                  "sessionGeneration":3,
                  "actionType":"SERVICE_EXISTING",
                  "packetText":"WORKSPACE_REASONING_PACKET_V1\nhello",
                  "payloadRef":"semantic-packet://leaf/7",
                  "payloadSha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                }
                """);
        });

        using var http = new HttpClient(handler);
        using var client = new HttpOperatorBridgeClient(
            http,
            Configuration,
            startStatusPolling: false);

        var action = await client.ClaimNextAsync(CancellationToken.None);

        Assert.IsNotNull(action);
        Assert.AreEqual("action:http/leaf", action.Identity.ActionId);
        Assert.AreEqual("instant-slot-1", action.Identity.WorkerSlotId);
        Assert.AreEqual(3L, action.Identity.SessionGeneration);
        Assert.AreEqual(
            OperatorActionType.ServiceExisting,
            action.ActionType);
        Assert.AreEqual(
            "WORKSPACE_REASONING_PACKET_V1\nhello",
            action.PacketText);

        Assert.IsNotNull(captured);
        Assert.IsNull(captured.Headers.Authorization);
        Assert.IsFalse(captured.Headers.Contains("Tailscale-User-Login"));
        Assert.AreEqual(
            "/operator-bridge/v1/actions/claim",
            captured.RequestUri!.AbsolutePath);
    }

    [TestMethod]
    public async Task ExactClaimGenerationIsReturnedOnRevalidateAndPrepare()
    {
        var requests = new List<(string Path, string Body)>();
        var handler = new StubHandler(async request =>
        {
            var body = request.Content is null
                ? string.Empty
                : await request.Content.ReadAsStringAsync();
            requests.Add((request.RequestUri!.AbsolutePath, body));

            if (request.RequestUri.AbsolutePath.EndsWith(
                    "/actions/claim",
                    StringComparison.Ordinal))
            {
                return Json(
                    HttpStatusCode.OK,
                    """
                    {
                      "actionId":"action:http/leaf",
                      "generation":11,
                      "workerSlotId":"slot",
                      "sessionGeneration":5,
                      "actionType":"SERVICE_EXISTING",
                      "packetText":"packet",
                      "payloadRef":"semantic-packet://leaf/11",
                      "payloadSha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
                    }
                    """);
            }

            if (request.RequestUri.AbsolutePath.EndsWith(
                    "/revalidate",
                    StringComparison.Ordinal))
            {
                return Json(HttpStatusCode.OK, """{"valid":true}""");
            }

            return Json(
                HttpStatusCode.OK,
                """{"status":"AWAITING_DURABLE_ACK"}""");
        });

        using var http = new HttpClient(handler);
        using var client = new HttpOperatorBridgeClient(
            http,
            Configuration,
            startStatusPolling: false);

        var action = await client.ClaimNextAsync(CancellationToken.None);
        Assert.IsNotNull(action);

        Assert.IsTrue(await client.RevalidateAsync(
            action.Identity,
            CancellationToken.None));
        await client.RecordLocalPreparedAsync(
            action.Identity,
            CancellationToken.None);

        Assert.AreEqual(3, requests.Count);
        using var revalidate = JsonDocument.Parse(requests[1].Body);
        using var prepared = JsonDocument.Parse(requests[2].Body);
        foreach (var document in new[] { revalidate, prepared })
        {
            Assert.AreEqual(
                11L,
                document.RootElement.GetProperty("generation").GetInt64());
            Assert.AreEqual(
                "slot",
                document.RootElement.GetProperty("workerSlotId").GetString());
            Assert.AreEqual(
                5L,
                document.RootElement.GetProperty("sessionGeneration").GetInt64());
        }

        Assert.IsFalse(await client.RevalidateAsync(
            action.Identity,
            CancellationToken.None));
        Assert.AreEqual(3, requests.Count);
    }

    [TestMethod]
    public async Task NoWorkClaimRefreshesStatusBeforeReturningNull()
    {
        var requests = new List<string>();
        var handler = new StubHandler(request =>
        {
            requests.Add(request.RequestUri!.AbsolutePath);
            if (request.RequestUri.AbsolutePath.EndsWith(
                    "/actions/claim",
                    StringComparison.Ordinal))
            {
                return Task.FromResult(new HttpResponseMessage(
                    HttpStatusCode.NoContent));
            }

            Assert.AreEqual(
                "/operator-bridge/v1/status",
                request.RequestUri.AbsolutePath);
            return Task.FromResult(Json(
                HttpStatusCode.OK,
                """{"readyManualCycles":0,"sentUnconfirmed":1}"""));
        });

        using var http = new HttpClient(handler);
        using var client = new HttpOperatorBridgeClient(
            http,
            Configuration,
            startStatusPolling: false);

        var action = await client.ClaimNextAsync(CancellationToken.None);

        Assert.IsNull(action);
        CollectionAssert.AreEqual(
            new[]
            {
                "/operator-bridge/v1/actions/claim",
                "/operator-bridge/v1/status"
            },
            requests);
        Assert.AreEqual(0, client.CurrentStatus.ReadyManualCycles);
        Assert.AreEqual(1, client.CurrentStatus.SentUnconfirmed);
    }

    [TestMethod]
    public async Task StatusRefreshUpdatesCachedPresentationState()
    {
        var handler = new StubHandler(_ =>
            Task.FromResult(Json(
                HttpStatusCode.OK,
                """{"readyManualCycles":4,"sentUnconfirmed":2}""")));

        using var http = new HttpClient(handler);
        using var client = new HttpOperatorBridgeClient(
            http,
            Configuration,
            startStatusPolling: false);

        await client.RefreshStatusAsync();

        Assert.AreEqual(4, client.CurrentStatus.ReadyManualCycles);
        Assert.AreEqual(2, client.CurrentStatus.SentUnconfirmed);
    }

    [TestMethod]
    public async Task MalformedPayloadHashFailsClosed()
    {
        var handler = new StubHandler(_ =>
            Task.FromResult(Json(
                HttpStatusCode.OK,
                """
                {
                  "actionId":"bad",
                  "generation":0,
                  "workerSlotId":"slot",
                  "sessionGeneration":0,
                  "actionType":"SERVICE_EXISTING",
                  "packetText":"packet",
                  "payloadRef":"semantic-packet://bad/0",
                  "payloadSha256":"not-a-sha"
                }
                """)));

        using var http = new HttpClient(handler);
        using var client = new HttpOperatorBridgeClient(
            http,
            Configuration,
            startStatusPolling: false);

        await ExpectAsync<InvalidDataException>(
            () => client.ClaimNextAsync(CancellationToken.None));
    }

    [TestMethod]
    public async Task FailureAndBlockedUseBoundedWireCodes()
    {
        var requests = new List<(string Path, string Body)>();
        var handler = new StubHandler(async request =>
        {
            var body = request.Content is null
                ? string.Empty
                : await request.Content.ReadAsStringAsync();
            requests.Add((request.RequestUri!.AbsolutePath, body));
            if (request.RequestUri.AbsolutePath.EndsWith(
                    "/actions/claim",
                    StringComparison.Ordinal))
            {
                return Json(
                    HttpStatusCode.OK,
                    """
                    {
                      "actionId":"action-1",
                      "generation":9,
                      "workerSlotId":"slot",
                      "sessionGeneration":2,
                      "actionType":"SERVICE_EXISTING",
                      "packetText":"packet",
                      "payloadRef":"semantic-packet://a/9",
                      "payloadSha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
                    }
                    """);
            }
            return Json(HttpStatusCode.OK, """{"status":"FAILED_LOCAL"}""");
        });

        using var http = new HttpClient(handler);
        using var client = new HttpOperatorBridgeClient(
            http,
            Configuration,
            startStatusPolling: false);

        var action = await client.ClaimNextAsync(CancellationToken.None);
        Assert.IsNotNull(action);
        await client.RecordLocalFailureAsync(
            action.Identity,
            "CLIPBOARD_FAILED",
            CancellationToken.None);

        using var failed = JsonDocument.Parse(requests[1].Body);
        Assert.AreEqual(
            "LOCAL_FAILURE",
            failed.RootElement.GetProperty("failureCode").GetString());
        Assert.AreEqual(
            "CLIPBOARD_FAILED",
            failed.RootElement.GetProperty("failureMessage").GetString());
        Assert.AreEqual(
            9L,
            failed.RootElement.GetProperty("generation").GetInt64());
    }

    [TestMethod]
    public void AuthorizationHeaderOnInjectedClientIsRejected()
    {
        using var http = new HttpClient(new StubHandler(_ =>
            Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK))));
        http.DefaultRequestHeaders.Authorization =
            new System.Net.Http.Headers.AuthenticationHeaderValue(
                "Bearer",
                "forbidden");

        Expect<ArgumentException>(() =>
            new HttpOperatorBridgeClient(
                http,
                Configuration,
                startStatusPolling: false));
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

    private static async Task ExpectAsync<TException>(
        Func<Task> action)
        where TException : Exception
    {
        try
        {
            await action();
        }
        catch (TException)
        {
            return;
        }

        throw new InvalidOperationException(
            $"Expected exception {typeof(TException).Name}.");
    }

    private static HttpResponseMessage Json(
        HttpStatusCode status,
        string json) =>
        new(status)
        {
            Content = new StringContent(
                json,
                Encoding.UTF8,
                "application/json")
        };

    private sealed class StubHandler :
        HttpMessageHandler
    {
        private readonly Func<
            HttpRequestMessage,
            Task<HttpResponseMessage>> _handler;

        public StubHandler(
            Func<HttpRequestMessage, Task<HttpResponseMessage>> handler)
        {
            _handler = handler;
        }

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken) =>
            _handler(request);
    }
}
