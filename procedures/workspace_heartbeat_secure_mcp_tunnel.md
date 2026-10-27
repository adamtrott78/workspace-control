# Workspace Heartbeat Secure MCP Tunnel: evidence-first recovery (2026-10-26)

Status: DISCOVERY ONLY. Do not deploy, restart, cut over, or retire ngrok from this document. Scope: `workspace-heartbeat-secure-mcp-tunnel-v1`.

## Verified provenance and transport
- GitHub task capsule: `tasks/active/workspace-heartbeat-secure-mcp-tunnel-v1.json`, blob `eec9ee8ca936724ee6bcab43a367368bf9fc6759`; existing parent capsule blob `9d09017f6f9eae102141b8514b306a67bd353717`.
- The repository-side Heartbeat plugin identifies version `0.4.7`; `package.json` requires Node >=20 and lists `npm start` as `node server.js`. Source `server.js` uses MCP Streamable HTTP on `/mcp` with default PORT=8787; localhost URL `http://localhost:8787/mcp`. GitHub source is **not** a fresh Lambda process/provenance inspection.
- Existing parent task reports a *historically accepted* v0.4.7 Lambda deployment at `workspace-control@9e5858738a4fd11801510e2839b0f94f19541506`, Node v20.20.2, process CWD `/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v047/plugins/workspace-heartbeat`; port 8787; isolated port 8788 and v0.4.6 rollback. These are past acceptance receipts, not verified current runtime truth.
- The current ChatGPT Heartbeat `heartbeat_begin_turn` fails at MCP transport probe: HTTP 403 via ngrok-free.dev, consistent with operator-observed `ERR_NGROK_725` and 1.02 GB / 1 GB transfer-out. No new Heartbeat turn/ID was created.
- Current Lambda process PID, exact current checkout SHA, npm/Node versions, systemd/launcher, tunnel startup command, network binding, and rollback artifact **remain unverified**. No Lambda shell/SSH action is exposed in this task's available connectors; do not claim live runtime recovered.

## Traffic-path source audit
- `heartbeat_touch(task_id, turn_id)` is model-only, returns `{acknowledged:true}`, and does not mutate semantic history; `heartbeat_begin_turn`, `heartbeat_update`, `heartbeat_get` are separate model-invoked MCP calls.
- The live card independently invokes app-only `tools/call` `heartbeat_snapshot(task_id, turn_id)` from `public/heartbeat-live-card.html`; only active, visible turns poll. In the retrieved source, the post-completion scheduled delay is 1500 ms for working and 3500 ms otherwise (actual rate includes request duration); operator-observed ~1-second freshness needs live transport measurement.
- `server.js` snapshot invokes `store.observeUi`, which updates `last_ui_seen_at` and returns `getTurnSnapshot`: latest heartbeat, latest-three `recent`, **full current-turn `turn_history` (up to 50)**, state flags and freshness timestamps/ages. The app rerenders history only when latest sequence/timestamp changes but **still downloads it on every successful poll**.
- Current `server.js` HTTP request logging records method/path/status/latency, but does not record application payload sizes or status-specific bytes. Counting raw bytes requires isolated instrumentation, not a production restart.

## Deterministic transfer budget, not incident attribution
For a hypothetical continuously mounted working card on a 31-day month:
- 1 poll/second = 2,678,400 responses. A **single 400-byte response payload** corresponds to 1.071 GB decimal outbound, excluding other calls and envelope/headers.
- The retrieved 1500 ms schedule provides an upper-bound rate (ignoring duration) of 1,785,600 polls/month. At that rate, 560 B outgoing per poll corresponds to approximately 1.00 GB decimal. Actual concurrent visible cards, active duration, protocol overhead, request latency, other ngrok traffic and counted billing direction must be measured.
- At 1 KB outgoing response each, 1500-ms continuous polling would be ~1.79 GB/month payload alone. **These are scenarios, not observed bytes or proof of incident source.**

## Official Secure MCP Tunnel evidence
Documentation: https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- `tunnel-client` reaches `api.openai.com:443` `/v1/tunnel/*` via outbound HTTPS, or optional `mtls.api.openai.com:443`; it forwards to an internal stdio or HTTP MCP server.
- Requires Platform tunnel ID, runtime API key, matching organization/ChatGPT workspace association, Tunnels Read+Manage to create/configure, Read+Use to run/select; ChatGPT custom plugin access remains independently permissioned.
- Defaults: 600 MCP requests/minute (10 sustained requests/sec per tunnel+app), 10 MiB serialized request or response envelope, 120 sec absolute deadline, 1000 queued requests. These are limits **not** liveness latency guarantees. Run `tunnel-client doctor --profile ... --explain`, inspect local health/ready/admin and confirm actual ChatGPT app tool call.
- IMPORTANT UNVERIFIED GATE: prove that the existing MCP Apps embedded card's app-only `tools/call` `heartbeat_snapshot` works over the tunnel, continuously, at the required freshness. MCP tool transport support alone is not proof of MCP Apps resource delivery, host polling, or effective freshness. Keep existing ngrok plugin until live tested.

## Proposed bounded next design (not implementation approval)
1. Read-only Lambda shell recovery: `systemctl` unit/config, process CWD/executable and version, exact `git rev-parse`, socket listener and local `/mcp`, ngrok process/launch, rollback directory and service definitions; redact secrets. **No process restart for discovery**.
2. Isolated copy on a separate port. Instrument the app-only snapshot call counts and serialized response bytes (plus transport envelope if available), and distinguish model tool traffic. Measure at least empty, 1, 5, 6 and 50 history entries; verify overhead and normal 1.5s/3.5s cadence.
3. Introduce minimal app-only **delta/lightweight snapshot** with immutable task/turn identity, latest semantic sequence, executor touch timestamp, UI seen timestamp and active/completed flags; transmit full history only for initial hydration or on sequence change, with bounded catch-up for gaps. Preserve turn fencing, no stale-owner takeover, semantic policy, and 5/6 sizing UI. Verify stale card cannot discover another task.
4. Validate full Node suite and workspace-control CI, isolated Lambda HTTP server and tunnel-client profile, ChatGPT tool and app-resource discovery, and live one-card executor/semantic/UI separation at ~1-second operator usefulness. Record observed latency distribution rather than equating configured interval with actual freshness.
5. Keep ngrok settings and previous runtime as rollback until accepted. Disable ngrok on the normal path only after a verified live ChatGPT tunnel acceptance; document emergency fallback explicitly.

## Gates
**No tunnel cutover and no claim of completed runtime recovery.** Current host inspection, actual byte measurements, credentials/tunnel permissions, embedded-app channel acceptance, rollback and live tests are open.


## Fresh live Lambda recovery — operator evidence 2026-10-26T21:49-04:00

Read-only operator output now verifies the following **current** runtime facts without a restart:

- Host: `gokhan-Lambda-Vector`; observation time `2026-10-26T21:49:27-04:00`.
- Active process chain includes `sh -c node server.js` PID 1847969 and child `node server.js` PID 1847970, both started 20:56:17 local; ngrok PID 1847986 started one second later with `ngrok http --domain=kabob-retool-unstopped.ngrok-free.dev 8787`.
- TCP 8787 is listening in the Node process. A direct local GET to `http://127.0.0.1:8787/` returned HTTP 200 and `workspace-heartbeat MCP server`, proving the server is alive locally while the public ngrok path is unavailable.
- Runtime CWD resolved from the first matching launcher shell to `/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v047/plugins/workspace-heartbeat`; checkout HEAD is exactly `9e5858738a4fd11801510e2839b0f94f19541506`; package metadata is `workspace-heartbeat 0.4.7`, Node requirement `>=20`.
- Runtime checkout has only untracked `node_modules/` and `package-lock.json` in the reported status.
- No Heartbeat/ngrok systemd service was reported. ngrok snap mount units exist. Launcher/supervisor ancestry remains to be identified.
- Rollback/runtime directories v0.3 through v0.4.7 are present, including explicit `workspace-heartbeat-runtime-v046` and current `workspace-heartbeat-runtime-v047`.
- Login-shell `node --version` is `v12.22.9` and npm is `8.5.1`. This does **not** establish the running child Node version because the inspection accidentally selected launcher shell PID 1847969. Resolve `/proc/1847970/exe` and run that executable with `--version` before claiming Node runtime provenance.

This evidence upgrades current local server/source/ngrok/rollback recovery from historical to live, but leaves two baseline items open: exact child Node executable/version and launcher ancestry. Payload bytes are still unmeasured.
