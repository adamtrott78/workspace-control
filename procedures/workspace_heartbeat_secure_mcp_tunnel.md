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


### Child runtime and launcher ancestry verified — operator evidence 2026-10-26

A second read-only probe resolves the remaining Node/launcher ambiguity:

- Actual Node child PID `1847970`.
- Executable: `/home/atrott/miniforge3/envs/workspace-heartbeat-node/bin/node`.
- Running version: **Node v20.20.2**.
- CWD: `/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v047/plugins/workspace-heartbeat`.
- Launch ancestry: systemd PID 1 -> tmux server PID 1847946 -> `conda run --no-capture-output -n workspace-heartbeat-node` PID 1847947 -> temporary bash launcher PID 1847952 -> `npm start` PID 1847956 -> `sh -c node server.js` PID 1847969 -> Node PID 1847970.
- ngrok PID `1847986` is a sibling under the same tmux server and executes `/snap/ngrok/439/ngrok http --domain=kabob-retool-unstopped.ngrok-free.dev 8787`.
- ngrok's CWD is unrelated (`.../varMax/PADataset`); its explicit command line, not CWD, defines the Heartbeat forwarding target.
- The earlier login-shell Node v12.22.9 is irrelevant to the running service; runtime provenance is now exact.

This closes the live runtime/source/Node/launcher recovery gate. No restart or mutation occurred.


## Isolated payload measurement — PASS (operator run 2026-10-26)

An isolated v0.4.7 instance was launched on :8788 using the exact verified source `workspace-control@9e5858738a4fd11801510e2839b0f94f19541506` and Node v20.20.2. Live :8787 remained listening and returned the normal health string after the probe. The isolated instance was disposable and did not alter ngrok or the production process.

Measured Streamable HTTP `heartbeat_snapshot` sizes (request size shown by curl; outbound = response headers + response body):

| Turn history | Structured content | HTTP request | Response body | Response headers | Approx HTTP outbound | 31d at 1.5s |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1329 B | 386 B | 1398 B | 236 B | 1634 B | 2.918 GB |
| 5 | 3322 B | 386 B | 3391 B | 236 B | 3627 B | 6.476 GB |
| 6 | 3654 B | 386 B | 3723 B | 236 B | 3959 B | 7.069 GB |
| 50 | 18307 B | 386 B | 18376 B | 237 B | 18613 B | 33.235 GB |

The 10-poll sample at 50 history entries was stable at roughly 18,376–18,380 response-body bytes and ~2.9–8.1 ms local request latency. Request upload stayed 185 B. `heartbeat_touch` was much smaller: request 383 B, response body 90 B, response headers 234 B.

### Conclusion

The high-frequency live-card app poll is a confirmed bandwidth amplifier. It retransmits full immutable turn history on every successful poll even when semantic sequence is unchanged. A single continuously visible working card at the actual 1500 ms schedule exceeds a 1 GB/month tunnel allowance even at one history entry; history growth makes the effect much larger. This does not prove every byte of the operator's 1.02 GB ngrok meter came from Heartbeat, because ngrok's metering/framing/compression and actual visible-card duty cycle were not measured, but the observed path is independently sufficient in magnitude to exhaust the free allowance.

Do **not** mitigate by reducing liveness cadence. The payload shape is the defect.

## Frozen payload-efficiency design v1

Preserve `heartbeat_snapshot(task_id, turn_id)` for compatibility/debug and initial hydration, but move the live card's repeated polling to a new app-only, read-only `heartbeat_poll(task_id, turn_id, after_sequence)` contract:

- Return immutable `task_id` and `turn_id`, active/superseded/completed flags, `last_executor_touch_at`, `last_ui_seen_at`, and age fields every poll.
- Return semantic entries only when their sequence is greater than `after_sequence`; do not resend unchanged history.
- Include the current semantic sequence/latest heartbeat metadata needed for progress age/state without requiring full history retransmission.
- If the caller's `after_sequence` predates the retained 50-entry window, return a bounded resync indicator plus the retained current-turn history needed to reconstruct the card. Never fetch another task/turn.
- The live card starts from its mounted tool output/history, tracks the highest rendered sequence, calls `heartbeat_poll`, appends validated deltas, and preserves current grow-through-five / scroll-from-six / deliberate-scroll behavior.
- Poll schedule remains 1500 ms while working and 3500 ms otherwise, including existing hidden-document, teardown, in-flight, and failure-backoff behavior.
- `observeUi` / `last_ui_seen_at` semantics remain app-poll driven.
- `heartbeat_touch`, begin/update semantics, semantic history, turn ownership/fencing, and stale-owner behavior remain unchanged.
- Routine poll response target: bounded O(1) when no semantic delta. The exact byte budget must be measured after implementation; optimize field duplication if necessary, but do not weaken signal semantics.

Implementation must add contract tests for no-change poll, single/multi-entry delta, retained-window resync, stale/wrong turn failure, and live-card behavior. Existing Node test suite and isolated :8788 byte benchmark must pass before tunnel testing.


## Exact v0.4.8 Lambda Node validation — PASS; isolated benchmark interrupted

Operator validation on exact candidate `def7c5fe6498b1bd742d912c1490d1f7160cab5f` under Node v20.20.2 completed **34/34 Workspace Heartbeat Node tests PASS**.

The post-change byte benchmark did not execute because TCP `:8788` was already occupied. After reconnecting, the operator ran the existing `heartbeat-down` command, which stopped the production v0.4.7 `:8787` runtime. A subsequent rerun therefore failed its live precheck with connection refused on `:8787`. This is an operational interruption, not a v0.4.8 implementation/test failure.

Recovery gate:
1. restore only the previously verified v0.4.7 production runtime on :8787;
2. verify exact source SHA and Node executable/version;
3. identify (do not blindly kill) the process occupying :8788;
4. choose a free isolated port if necessary and complete the v0.4.8 no-change/delta/resync byte benchmark;
5. keep v0.4.8 out of the production launcher until isolated payload validation and Secure MCP Tunnel acceptance pass.


### Port ownership after interrupted benchmark — verified

Read-only operator recovery shows:
- production `:8787`: no listener after `heartbeat-down`;
- `:8788`: PID 1922601, exact v0.4.7 runtime `workspace-control@9e5858738a4fd11801510e2839b0f94f19541506`, package 0.4.7, Node v20.20.2, CWD `workspace-heartbeat-runtime-v047/plugins/workspace-heartbeat`, parent PID 1;
- `:8789`: no listener.

PID 1922601 is therefore the orphaned isolated v0.4.7 probe from the earlier :8788 measurement, not the production tmux-launched runtime. It may be terminated only after re-verifying those exact properties immediately before the kill. Use :8789 for the v0.4.8 benchmark to avoid coupling recovery to cleanup.


### Production v0.4.7 restoration — PASS

After the interrupted isolated benchmark, the existing operator launcher `/home/atrott/bin/heartbeat-up` was safety-checked for the v0.4.7 runtime, dedicated `workspace-heartbeat-node` environment, and port 8787, then executed.

Restored production evidence:
- local `:8787` health returns `workspace-heartbeat MCP server`;
- listener PID 1978095;
- CWD `/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v047/plugins/workspace-heartbeat`;
- Node executable `/home/atrott/miniforge3/envs/workspace-heartbeat-node/bin/node`, version v20.20.2;
- exact source SHA `9e5858738a4fd11801510e2839b0f94f19541506`;
- tmux session `workspace-heartbeat` has expected MCP and ngrok processes.

The earlier :8788 orphan was already gone. The next isolated port candidate :8789 was unexpectedly occupied, so the v0.4.8 byte benchmark remains pending. Do not kill the :8789 process until its identity is proven.


### :8789 orphan and wrapper false negatives — diagnosed

The :8789 listener is exact orphaned v0.4.8 validation state: PID 1973910, PPID 1, Node20 executable, CWD in the `heartbeat-v048-validate-def7c5fe6498` worktree, and exact Git SHA `def7c5fe6498b1bd742d912c1490d1f7160cab5f`. The previous safety predicate rejected it only because `/proc/<pid>/cmdline` reported the absolute Node executable path rather than literal `node server.js`.

The next wrapper aborted immediately after candidate checkout, before version reporting. The repository root does not ignore `node_modules`, so an existing dependency symlink inside the validation worktree can make `git status --porcelain` nonempty. Recovery must remove only a verified symlink resolving to the accepted v0.4.7 runtime's `node_modules`, prove no other worktree drift, then recreate the link for isolated execution.


### Exact candidate cleanliness — PASS; fixed-port selection retired

The exact v0.4.8 worktree was repaired by removing only the known `node_modules` symlink that resolved to the accepted v0.4.7 runtime dependency tree. After removal, the detached worktree at `def7c5fe6498b1bd742d912c1490d1f7160cab5f` had an empty `git status --porcelain`, proving no source drift. The dependency link was recreated only after that assertion passed.

The subsequent abort occurred only because hard-coded test port `:8790` was occupied. Since :8788, :8789, and now :8790 have each encountered leftover listeners from interrupted isolated probes, fixed-port selection is retired. The next run must safely clean only exact orphaned Heartbeat probes and choose a free ephemeral loopback port dynamically.


## v0.4.8 isolated payload-efficiency acceptance — PASS

Exact candidate: `def7c5fe6498b1bd742d912c1490d1f7160cab5f` (Workspace Heartbeat 0.4.8, Node v20.20.2).

Measured on an isolated dynamically selected local port while accepted production v0.4.7 remained unchanged on `:8787`:

| Case | Updates | Resync | Structured content | HTTP response body | Response headers | Response-side outbound |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| no change, history 1 | 0 | false | 240 B | 309 B | 235 B | 544 B |
| one semantic delta | 1 | false | 576 B | 645 B | 235 B | 880 B |
| no change, history 5 | 0 | false | 240 B | 309 B | 235 B | 544 B |
| no change, retained history 50 | 0 | false | 240 B | 309 B | 235 B | 544 B |
| forced retained-window resync | 50 | true | 17134 B | 17203 B | 237 B | 17440 B |

Ten additional steady no-change polls at retained history 50 were all exactly 544 B response-side outbound. Median local request latency was 0.003634 s.

Against the measured v0.4.7 50-history heartbeat_snapshot response-side outbound of 18613 B, steady v0.4.8 no-change polling at history 50 is a **97.08% reduction**, with **0 B size spread** between history depths 1, 5, and 50. This validates the O(1) no-change payload requirement without reducing the 1500 ms working cadence.

Residual bandwidth is intentionally recorded rather than hidden: at a 1.5 s schedule plus the measured median local latency, response-side traffic alone projects to about **0.969 GB / 0.902 GiB per 31 days** under hypothetical continuous 24/7 card visibility. Including the measured routine request side (~408 B/request) gives about **1.696 GB / 1.579 GiB of HTTP request+response traffic** before tunnel/protocol overhead. Therefore v0.4.8 eliminates the pathological history-amplification defect, but does not make a 1-GB-class metered public tunnel an acceptable continuous transport.

The forced-resync path remains intentionally large and bounded: exactly 50 retained updates, only when the caller falls outside the retained sequence window.

Production preservation check passed after the benchmark:
- PID 1978095
- CWD `workspace-heartbeat-runtime-v047/plugins/workspace-heartbeat`
- Node executable `workspace-heartbeat-node/bin/node`
- source SHA `9e5858738a4fd11801510e2839b0f94f19541506`
- local `:8787` health PASS

Payload-efficiency implementation stage is therefore **VALIDATED**. The next stage is isolated and live Secure MCP Tunnel acceptance; ngrok is not yet retired.


### Secure MCP Tunnel contract refresh — 2026-10-26

Current official OpenAI documentation was rechecked before tunnel acceptance. The accepted design remains aligned with the service contract:

- `tunnel-client` initiates outbound HTTPS to `api.openai.com:443` by default (or `mtls.api.openai.com:443` when control-plane mTLS is configured); no inbound internet listener is required.
- The client forwards queued MCP JSON-RPC work to a private local HTTP MCP URL or stdio target and returns responses over the same tunnel.
- Setup requires a `tunnel_id` plus a runtime API key. Platform tunnel permissions (Read/Use or Read/Manage) and ChatGPT custom-MCP/plugin permissions are separate.
- Documented preflight remains `tunnel-client doctor --profile <profile> --explain`; runtime remains `tunnel-client run --profile <profile>`.
- Default service limits remain 600 MCP requests/minute, 10 MiB serialized request or response, 120-second absolute request deadline, and 1000 queued pending requests.
- Latest public `openai/tunnel-client` release observed during this refresh is v0.0.18.

The next action is host-only read-only discovery. Do not print or commit credentials. Do not change the production Heartbeat listener or retire ngrok during this discovery.


### Lambda Secure MCP Tunnel host preflight — PASS

Read-only host discovery established:
- production Heartbeat unchanged on exact v0.4.7 SHA `9e5858738a4fd11801510e2839b0f94f19541506` at `:8787`;
- Ubuntu 22.04, x86_64 / amd64;
- no `tunnel-client` binary in PATH or common user/system locations;
- no tunnel configuration metadata discovered;
- `CONTROL_PLANE_API_KEY` and `OPENAI_API_KEY` unset;
- no HTTP(S)/all-proxy environment configured;
- `api.openai.com` DNS resolution PASS;
- unauthenticated HTTPS to `https://api.openai.com/v1/models` returned HTTP 401 with TLS verification success, proving outbound network reachability;
- no existing tunnel-client process.

Official v0.0.18 full-client Linux amd64 release asset:
`tunnel-client-v0.0.18-linux-amd64.zip`
published SHA-256:
`3c82307316acd93c88a384b62af1d81d3f4cb0efa975f9c0bfaef922866a04c4`.

Install only into a user-owned staging path first. Do not create a profile or store credentials until the binary digest and local CLI help are verified.


### Official tunnel-client v0.0.18 staging — PASS

The official full-client Linux amd64 release was staged into a user-owned tooling path without modifying production Heartbeat.

Verification:
- `SHA256SUMS.txt` digest matched `63f9996246424301c8b0680c943c67d0ea7fe2f0853a234649104f8062c67329`;
- `tunnel-client-v0.0.18-linux-amd64.zip` matched both the pinned and official-manifest SHA-256 `3c82307316acd93c88a384b62af1d81d3f4cb0efa975f9c0bfaef922866a04c4`;
- extracted binary is a statically linked Linux x86-64 ELF and reports `0.0.18+274a5588414819f063d27100a4fb1096aae3830f`;
- CLI quickstart confirms `CONTROL_PLANE_TUNNEL_ID` comes from Tunnels management and `CONTROL_PLANE_API_KEY` is a separate runtime key used by `doctor` and `run`;
- runtime-key principal requires Tunnels **Read + Use**; admin key is for tunnel CRUD and must not be used as the long-lived daemon credential;
- production Heartbeat remained unchanged on PID 1978095 / exact v0.4.7 SHA `9e5858738a4fd11801510e2839b0f94f19541506` / local `:8787`.

The next gate requires operator provisioning in OpenAI Platform. No credential value is to be pasted into chat or committed.


### Platform Secure MCP Tunnel provisioned — PASS

Provisioned tunnel:
`tunnel_6ae017d8655c8191976ef3bccc31f593`

The tunnel was created in the operator's only available OpenAI Platform organization and associated with the only available ChatGPT workspace. The optional "Restrict client network access" control was left disabled because no ChatGPT ingress-network allowlist was part of the accepted design.

Remaining account-side prerequisite: create a dedicated runtime API key whose principal has Tunnels **Read + Use** for this tunnel. The runtime key must be entered only on the Lambda host and must never be pasted into chat or committed.


### Dedicated tunnel runtime key provisioned — PASS

The operator created a dedicated runtime API key using **Restricted** permissions with only **Tunnels Read + Use** enabled. The secret value was not shared in chat and is not recorded in workspace-control.

Next gate: isolated exact-v0.4.8 profile initialization and `tunnel-client doctor --explain`. The key must be entered only in the Lambda terminal via hidden input/environment and unset after the validation.


### Isolated Secure MCP Tunnel doctor — PASS

Exact v0.4.8 candidate `def7c5fe6498b1bd742d912c1490d1f7160cab5f` was started on loopback `http://127.0.0.1:57799/mcp`. A non-secret `workspace-heartbeat-v048-isolated` tunnel-client profile was created for `tunnel_6ae017d8655c8191976ef3bccc31f593`; profile secret scan passed.

`tunnel-client doctor --profile workspace-heartbeat-v048-isolated --explain --json` exited 0 with `result: ok`. PASS checks covered configuration/profile loading, tunnel ID, runtime-key reference through `env:CONTROL_PLANE_API_KEY`, MCP target reachability, OAuth-metadata handling, and loopback ephemeral health listener. The optional Codex-plugin check was SKIP and is outside ChatGPT Heartbeat acceptance.

The runtime key was unset after the check. Production Heartbeat remained unchanged on PID 1978095 / exact v0.4.7 SHA `9e5858738a4fd11801510e2839b0f94f19541506` / local `:8787`.

Next gate: keep the exact v0.4.8 MCP endpoint and tunnel-client daemon running concurrently, prove `/readyz`, then perform ChatGPT connector discovery and live tool/app acceptance through Secure MCP Tunnel.


### Live ChatGPT Secure MCP Tunnel tool/app acceptance — PASS (visual sizing pending)

Temporary tunnel-backed personal plugin:
- plugin ID: `plugin_asdk_app_6ae01e3e9e708191b6639dc9bc556f43`
- name: `dev-6ae01e3e9e708191b6639dc9bc556f43`
- tunnel: `tunnel_6ae017d8655c8191976ef3bccc31f593`

From the live ChatGPT conversation, `heartbeat_begin_turn` succeeded through Secure MCP Tunnel and returned turn `31c6e972-58ba-4460-a497-e5a5df226c4c`; ChatGPT rendered the embedded Heartbeat UI. Five later `heartbeat_update` calls succeeded on the same turn through sequence 6. `heartbeat_get` returned the complete six-entry current-turn history and also rendered the app UI.

This proves model tool reachability and MCP App resource delivery through the tunnel-backed v0.4.8 acceptance path, independently of ngrok.

Remaining live UI gate is visual only: operator must confirm the rendered card preserves the accepted five-entry intrinsic height and that the sixth entry transitions to scrollable history while keeping the newest update visible. The assistant cannot inspect client-rendered card dimensions or scroll position directly.


### Live ChatGPT visual card acceptance — PASS

The operator visually confirmed the tunnel-backed v0.4.8 card preserves the accepted five-entry intrinsic height and transitions to scrollable history after the sixth entry while keeping current updates visible.

The separate full-history card visible during acceptance was caused by the assistant's explicit `heartbeat_get` diagnostic invocation. It is **not** part of the normal v0.4.8 live-card polling path. Normal operation must not invoke `heartbeat_get` merely to monitor progress; routine live behavior is:
- one `heartbeat_begin_turn` per turn;
- semantic-only `heartbeat_update`;
- silent `heartbeat_touch` for executor liveness;
- app-only `heartbeat_poll` delta refresh.

This completes Secure MCP Tunnel isolated + live ChatGPT acceptance. Production cutover remains a separate gate.


## Production Secure MCP Tunnel cutover — PASS / task complete

Production cutover executed successfully after the temporary acceptance daemon was stopped.

Final normal-path receipt:
- Heartbeat PID: `2083522`
- runtime: `/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v048/plugins/workspace-heartbeat`
- exact source SHA: `def7c5fe6498b1bd742d912c1490d1f7160cab5f`
- tunnel-client PID: `2083588`
- tunnel health: `http://127.0.0.1:41247`
- rollback helper: `/home/atrott/bin/heartbeat-rollback-v047-ngrok`
- local cutover marker: `WORKSPACE_HEARTBEAT_V048_TUNNEL_CUTOVER_LOCAL_GATE=PASS`

A fresh post-cutover ChatGPT `heartbeat_begin_turn` succeeded through the tunnel-backed plugin and rendered the compact live card; a subsequent `heartbeat_update` succeeded on the same new turn. This proves the normal production path is now ChatGPT -> OpenAI Secure MCP Tunnel -> exact v0.4.8 Lambda runtime.

### Normal operation and privacy boundary

Routine Heartbeat calls send only the explicit tool arguments required by the Heartbeat interface plus MCP/session metadata. The model-facing schemas do not expose a full-chat-transcript argument. The app-only `heartbeat_poll` path accepts only `task_id`, `turn_id`, and `after_sequence` and returns only bounded liveness/delta state.

Do **not** invoke `heartbeat_get` merely to monitor routine progress. It is an explicit task-history/sidebar diagnostic and renders a separate full-history panel. Normal live operation is `heartbeat_begin_turn` once per substantial response, semantic-only `heartbeat_update`, silent `heartbeat_touch`, and app-only `heartbeat_poll` delta refresh.

### Rollback policy

Ngrok is retired from the normal launcher path. The accepted v0.4.7/ngrok launcher is retained only as an explicit emergency rollback. Invoke `/home/atrott/bin/heartbeat-rollback-v047-ngrok` only for a real Secure MCP Tunnel production regression; it is not a parallel or routine fallback transport.

Task acceptance is complete.
