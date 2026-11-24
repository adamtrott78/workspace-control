# ADR — .NET 10 Windows Operator Helper v0.1

Status: **ACCEPTED FOR UX-12 IMPLEMENTATION BASELINE**

Parent: `workspace-semantic-execution-migration-v1`

Companions:
- `architecture/workspace-semantic-execution-operator-implementation-stack-comparison.v0.1.json`
- `architecture/workspace-semantic-execution-operator-native-messaging-protocol.v0.1.json`
- `architecture/workspace-semantic-execution-operator-implementation-plan.v0.1.md`

## Context

The local helper must own the system-global scheduler hotkey, tray/master toggle, write-only clipboard staging, local operator/recovery presentation, redacted local receipts, browser-adapter invocation, and UX-09 latency/resource instrumentation.

The helper must run as a standard interactive Windows user and must not:
- synthesize keyboard/mouse input;
- read arbitrary clipboard contents;
- scrape UI/accessibility state;
- read browser credentials/cookies;
- expose an unauthenticated listener;
- become execution authority.

## Decision

Implement the v0 Windows helper in **C# on .NET 10 LTS**.

Runtime shape:

```text
WorkspaceOperator.exe
  ├─ primary mode: tray/hotkey/clipboard/operator UI + OperatorBridge client
  └─ native-host proxy mode: Firefox Native Messaging stdio ↔ current-user named pipe
```

The same installed executable may run in both modes. Firefox starts a separate native-host process through its Native Messaging manifest; that process is only a bounded proxy to the already-running primary helper.

The primary helper remains independent of Firefox lifetime.

## Why .NET 10

Reviewed 2026-11-09:

- .NET 10 is the active LTS release, supported through November 2028.
- WinForms provides a mature notification-area `NotifyIcon`.
- WinForms clipboard APIs support Unicode text and can live on the same STA UI thread as the tray shell.
- Win32 `RegisterHotKey` provides the exact system-wide hotkey primitive required by UX-05.
- .NET named pipes expose `PipeOptions.CurrentUserOnly`; on Windows this checks both account and elevation level.
- self-contained, single-file `win-x64` publishing is documented and removes a machine-wide .NET runtime prerequisite.

References:
- https://dotnet.microsoft.com/en-us/platform/support/policy
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey
- https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.notifyicon?view=net-10.0
- https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.clipboard.settext
- https://learn.microsoft.com/en-us/dotnet/api/system.io.pipes.pipeoptions?view=net-10.0
- https://learn.microsoft.com/en-us/dotnet/core/deploying/single-file/overview

## Process model

### Primary helper mode

Owns:
- `RegisterHotKey` / `UnregisterHotKey`;
- bridge ON/OFF;
- tray icon/menu;
- small WinForms operator/recovery window;
- STA-thread write-only clipboard adapter;
- local dispatch single-flight lock;
- BrowserPort request coordinator;
- redacted JSONL diagnostics;
- performance timestamps;
- configured launch of the dedicated worker browser/profile.

It does **not** expose TCP/HTTP.

### Native-host proxy mode

Firefox Native Messaging launches the installed executable using the host manifest.

The process:
1. validates it was invoked as the configured native host;
2. opens a same-user named pipe to the primary helper;
3. enforces the v1 protocol frame limit;
4. forwards JSON frames between Native Messaging stdin/stdout and the pipe;
5. exits when Firefox closes the native port or the helper disconnects.

It never:
- claims OperatorActions;
- writes clipboard;
- owns durable state;
- creates browser authority;
- caches packet bodies.

## Local IPC

Use a duplex Windows named pipe.

Candidate logical name:

`WorkspaceControl.OperatorBridge.v1.<user-scope-hash>`

Requirements:
- `PipeOptions.CurrentUserOnly | PipeOptions.Asynchronous`;
- one primary helper server;
- native-host proxy is a client;
- 4-byte little-endian unsigned frame length followed by UTF-8 JSON;
- hard application frame cap: **64 KiB**;
- protocol-version negotiation before browser commands;
- unknown message/version fails closed;
- no credentials or packet body cross the browser IPC.

The helper must not lower integrity/elevation merely to permit a peer. If the helper and Firefox are running at different elevation levels, the connection fails and recovery explains the mismatch.

## Clipboard

Use `System.Windows.Forms.Clipboard.SetText` only on an STA thread.

The helper:
- writes only after action/generation/browser revalidation;
- never calls `GetText` for routine dispatch;
- never snapshots/restores prior clipboard content;
- logs only payload ref/hash and result enum.

## Hotkey

Use `RegisterHotKey`.

Implementation rules:
- configurable binding;
- one registered scheduler command while bridge ON;
- fully unregister while bridge OFF;
- `MOD_NOREPEAT` where supported plus application edge/single-flight suppression;
- registration failure is visible and blocks bridge ON;
- hotkey handler posts into the application queue; it does not execute browser or clipboard work inside the window-message callback.

UX-11 decides whether the default physical binding remains Ctrl+B.

## Tray/operator UI

Use WinForms rather than WinUI/WPF for v0.

Reason:
- required UI is small;
- WinForms already supplies the tray and clipboard primitives;
- no separate Windows App SDK/runtime/package model is needed;
- operator console is not the product's main interaction surface.

The UI remains derived/non-authoritative.

## Packaging

Prototype/release baseline:
- target `net10.0-windows`;
- runtime identifier `win-x64`;
- `PublishSingleFile=true`;
- `SelfContained=true`;
- Release build;
- deterministic version stamped into executable/protocol hello;
- helper stored under a per-user `%LOCALAPPDATA%\WorkspaceControl\OperatorBridge\<version>\` tree;
- a stable launcher/current pointer may be introduced only if atomic upgrade needs it.

No administrator requirement.

## Install/update model

v0 deliberately has **no unattended self-updater**.

A reviewed per-user install/update script:
- verifies expected release hashes/signature metadata;
- requires bridge OFF for replacement;
- installs helper files;
- writes the Firefox Native Messaging manifest;
- writes the HKCU NativeMessagingHosts registry value;
- optionally configures user-login startup for the primary helper;
- never touches browser credential/profile databases.

Updates are explicit and auditable. Automatic update may be considered later only after a separate supply-chain review.

## Diagnostics

Default redacted JSONL:
`%LOCALAPPDATA%\WorkspaceControl\OperatorBridge\logs\`

Allowlisted fields only:
- timestamp;
- component/version;
- request/correlation ID;
- action ID/generation;
- slot/generation;
- operation/result;
- normalized error class;
- payload ref/hash;
- origin classification enum;
- duration/resource metric.

No:
- packet text;
- clipboard contents;
- page/response content;
- raw URLs;
- credentials/tokens.

Prototype retention target:
- 7 days;
- 10 MiB per file;
- oldest-first deletion.

## Alternatives

### Rust

Retained as a fallback if measured .NET helper resource usage violates UX-09 after ordinary optimization.

It likely wins on raw footprint/startup, but v0 does not currently justify the extra Windows UI/tray/clipboard integration and dependency-selection burden.

### Python

Rejected for the Windows helper. Existing repository Python remains appropriate for orchestration/testing, but packaged tray/hotkey/native-host execution would add interpreter/bundler and third-party runtime variability.

## Consequences

The helper stack is implementation-frozen enough to code.

Reopen only if:
- UX-09 measurements show the helper cannot meet the 100 MiB working-set / 1% idle-CPU budget after bounded optimization;
- a supported Windows API limitation invalidates a required UX contract;
- security review finds the selected packaging/IPC model insufficient.
