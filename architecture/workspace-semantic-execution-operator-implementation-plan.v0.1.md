# Workspace Semantic Execution Operator Implementation Plan v0.1

Status: **UX-12 IMPLEMENTATION STACK / PROTOTYPE PLAN FROZEN**

Parent task: `workspace-semantic-execution-migration-v1`

Selected stack:
- Windows helper: .NET 10 LTS / C# / WinForms;
- browser baseline: Firefox ESR 153+ Manifest V3 WebExtension / plain JavaScript;
- browser IPC: Firefox Native Messaging → bounded native-host proxy → current-user-only named pipe → primary helper;
- custom-browser spike: .NET 10 WinForms + Evergreen WebView2 behind the same BrowserPort;
- simulator orchestration/tests: existing repository Python test stack may drive fixtures, while local production binaries remain .NET/JavaScript.

Companions:
- `architecture/workspace-semantic-execution-operator-implementation-stack-comparison.v0.1.json`
- `architecture/workspace-semantic-execution-operator-adr-dotnet-helper.v0.1.md`
- `architecture/workspace-semantic-execution-operator-adr-browser-adapter-stack.v0.1.md`
- `architecture/workspace-semantic-execution-operator-native-messaging-protocol.v0.1.json`

## 1. Implementation boundary

UX-12 freezes implementation choices, not authorization to deploy to a real ChatGPT account.

The prototype must first run entirely against UX-10 fake-worker fixtures.

Real-account calibration remains gated by:
- UX-08 security checklist;
- current OpenAI policy re-check;
- signed extension install;
- target Firefox API smoke tests;
- normal authentication behavior;
- explicit operator-run UX-09/UX-11 tests.

## 2. Repository layout proposal

Keep implementation inside task-authorized paths when code authority is later granted. UX-12 itself does not widen the current task mutation scope.

Logical future layout:

```text
operator-bridge/
  WorkspaceOperator/
    WorkspaceOperator.csproj
    Program.cs
    Application/
    Ports/
    Windows/
    NativeMessaging/
    Diagnostics/
  firefox-extension/
    manifest.json
    background.js
  webview2-spike/
    WorkspaceWorkerShell.csproj
  simulator/
    fake_worker/
    scenarios/
  protocol/
    browser_adapter_v1.schema.json
```

Before creating a new top-level code directory, the implementation task must explicitly authorize that mutation path. The current UX task records design artifacts only.

## 3. Build slice A — .NET helper skeleton

Deliver:
- `net10.0-windows` WinForms executable;
- primary tray mode;
- bridge ON/OFF state;
- hidden/message-only window or normal WinForms message pump for `WM_HOTKEY`;
- `RegisterHotKey` wrapper;
- STA write-only clipboard wrapper;
- single-flight dispatch coordinator;
- content-free structured logger;
- monotonic clock/performance recorder.

Tests:
- hotkey register/unregister;
- registration conflict;
- held-repeat suppression;
- bridge OFF no side effects;
- clipboard write occurs only on explicit test dispatch;
- helper idle resource measurement.

Exit gate:
- UX-05 HK-001/002/005/016/018/019 pass against fake ports.

## 4. Build slice B — local IPC/native-host proxy

Deliver:
- same executable native-host proxy mode;
- Firefox native host manifest generator;
- HKCU registration installer;
- current-user-only named-pipe server in primary helper;
- v1 protocol parser/validator;
- 64 KiB frame cap;
- handshake/version negotiation;
- request correlation;
- disconnect/reconnect behavior.

Tests:
- wrong extension ID rejected by Firefox host manifest boundary;
- wrong protocol version fails closed;
- oversized/malformed JSON frame fails closed;
- duplicate idempotent request does not duplicate local browser effect;
- helper/host elevation mismatch produces bounded recovery;
- browser disconnect does not kill primary tray helper.

Exit gate:
- UX-10 adapter disconnect/helper restart fixtures can be driven with no browser.

## 5. Build slice C — Firefox WebExtension

Deliver exact MV3 permission set:
- `nativeMessaging`;
- `tabs`;
- `sessions`.

Manifest:
- Firefox ESR 153 minimum;
- explicit extension ID;
- `data_collection_permissions.required=["none"]`;
- background event page script;
- no host permissions;
- no content scripts.

Implement:
- connectNative lifecycle;
- HELLO/HELLO_ACK;
- managed binding creation;
- activation;
- reload/restore;
- discard;
- close;
- inventory;
- sessions tab-value binding metadata;
- managed-tab `tabs.onUpdated` origin classification;
- managed-tab close/discard events.

Do not implement:
- DOM access;
- scripting;
- keyboard/mouse input;
- page send;
- response observation.

Exit gate:
- UX-10 L3 fake-worker adapter-parity scenarios pass;
- raw URL never leaves extension;
- browser binding loss fails closed.

## 6. Build slice D — fake worker and physical simulator

Implement UX-10:
- local fake worker origin;
- HUMAN_IN_LOOP surface;
- DETERMINISTIC_CI `SIM_HUMAN_SUBMIT`;
- fake OperatorAction/session stores;
- fake durable event/ack observer;
- named deterministic fault points;
- content-free trace hashes.

Critical packaging rule:
- simulator-only endpoints/symbols are absent or disabled in production helper/browser builds.

Exit gate:
- UX-10 L0/L1 tests 100%;
- production-release separation test passes.

## 7. Build slice E — real helper + Firefox fake-worker integration

Run:
- UX-10 L2/L3;
- UX-09 mechanical latency measurements;
- helper/extension RAM/idle CPU;
- 1/2/4 fake-worker browser lifecycle;
- discard/restore behavior.

This does not substitute for real ChatGPT RAM calibration.

Exit gate:
- no correctness/security failure;
- helper/extension meets the UX-09 local-overhead budgets or produces a bounded optimization finding.

## 8. Build slice F — WebView2 custom-shell spike

Create a separate BrowserPort implementation using:
- .NET 10;
- WinForms;
- Evergreen WebView2;
- shared CoreWebView2Environment;
- one dedicated user-data folder;
- no DOM/script injection.

First test only UX-10 local fake worker:
- create/activate/close;
- suspend/unload equivalent to discard;
- origin classification from top-level navigation metadata;
- crash/process failure mapping;
- 1/2/4 view memory;
- cold start/reuse/restore.

Then, **only after security review**, perform the smallest real-auth feasibility check:
1. open ChatGPT login page manually;
2. operator uses their normal login path;
3. do not import cookies/tokens;
4. if an IdP rejects the embedded user-agent, stop and mark custom shell AUTH_INCOMPATIBLE;
5. do not spoof or bypass.

Promotion remains UX-13 evidence-driven.

## 9. OperatorBridge transport boundary

UX-12 freezes local browser IPC, but does not invent a new remote authority channel.

The helper depends on an `OperatorBridgeClient` application interface.

For simulator:
- use in-process/test implementation.

For production:
- bind only to an explicitly authorized Workspace Control transport when the orchestration implementation task provides it.
- do not embed GitHub credentials in the helper merely to fabricate a transport.
- do not open an inbound unauthenticated network listener.

This keeps transport authority with Workspace Control rather than the local UX adapter.

## 10. Packaging/install

### Helper

Publish:
```text
dotnet publish
  -c Release
  -r win-x64
  --self-contained true
  -p:PublishSingleFile=true
```

Installer prototype:
- reviewed `install.ps1`;
- per-user files under `%LOCALAPPDATA%\WorkspaceControl\OperatorBridge`;
- native-host JSON contains absolute helper path;
- HKCU `Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge`;
- optional user-login startup;
- uninstall removes only owned registry/files after bridge shutdown.

No admin elevation required.

### Extension

- AMO-sign MV3 as unlisted/self-distributed;
- install signed XPI into `WorkspaceWorkers`;
- keep extension ID fixed;
- no production unsigned-signature bypass.

### Updates

v0:
- explicit reviewed update;
- verify release hash/signature;
- bridge OFF;
- replace helper;
- install higher-version signed XPI when needed;
- run protocol/API smoke test;
- rollback to previous release on failure.

No silent auto-updater.

## 11. Development/test workflow

Recommended:
1. pure protocol/schema tests;
2. .NET unit tests with fake ports;
3. Python contract fixtures against emitted trace/result JSON where useful;
4. Firefox extension lint/unit tests;
5. UX-10 in-memory adapter;
6. Firefox temporary-development profile against fake worker;
7. signed-XPI dedicated-profile smoke test;
8. UX-09 mechanical benchmark;
9. UX-11 human-in-loop simulator trials;
10. only then bounded real-account calibration.

CI must not need a ChatGPT account.

## 12. Firefox implementation smoke checks

Before any real-account test verify on the target host:
- ESR 153+ or newer supported Firefox;
- MV3 extension loads;
- background event page starts;
- `runtime.connectNative` connects;
- host exact ID allowlist works;
- `tabs.onUpdated` yields managed URL metadata;
- raw URL is reduced locally to enum;
- `sessions.setTabValue/getTabValue` survives expected restore/restart behavior;
- `tabs.discard` behavior is understood for active/beforeunload cases;
- profile launch/coexistence behavior is deterministic;
- extension remains unable to read page content under its permissions.

## 13. Fresh policy gate before real-account calibration

Current Terms were reviewed during UX-12:
https://openai.com/policies/terms-of-use/

They prohibit automatic/programmatic extraction of data or Output and circumvention of restrictions/protective measures.

The real-account gate must re-check the then-current Terms/product guidance again immediately before testing.

If the product blocks this bridge behavior:
- stop;
- do not evade;
- record the blocker;
- continue using fake-worker/supported execution surfaces.

## 14. UX-12 acceptance assessment

**PASS at implementation-contract design level.**

We now have:
- selected native helper language/runtime;
- selected Windows UI/hotkey/clipboard primitives;
- selected Firefox manifest/API/version baseline;
- explicit custom-shell spike/rejection/promotion gate;
- frozen Native Messaging + local named-pipe protocol;
- packaging/install/update model;
- diagnostics policy;
- simulator boundary;
- ordered implementation slices and exit gates.

Code implementation is not claimed by UX-12. The next slice is UX-13 integrated review/design freeze, which must distinguish design completeness from still-unexecuted UX-09/UX-11/real-auth evidence.
