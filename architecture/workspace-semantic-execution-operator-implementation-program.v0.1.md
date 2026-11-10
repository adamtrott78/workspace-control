# Workspace Operator Bridge Implementation Program v0.1

Status: **IMPLEMENTATION PROGRAM / STAGE CONTRACT FROZEN FOR EXECUTION**

Owning task: `workspace-operator-bridge-implementation-v1`

Parent design task: `workspace-semantic-execution-migration-v1`

Design freeze source:
- workspace-control@`0a110b570410d6d3310afc8ef4591e4aa383c0b8`
- `architecture/workspace-semantic-execution-operator-ux-freeze.v0.1.json`
- `architecture/workspace-semantic-execution-operator-ux-design-review.v0.1.md`
- `architecture/workspace-semantic-execution-operator-implementation-plan.v0.1.md`

Companions:
- `architecture/workspace-semantic-execution-operator-implementation-stage-plan.v0.1.json`
- `architecture/workspace-semantic-execution-operator-implementation-traceability.v0.1.json`

## 1. Purpose

Translate the frozen UX architecture into production-quality implementation through bounded, independently verifiable engineering stages.

This program is the construction contract. It does not redesign the UX.

The frozen routine operator interaction remains:

```text
scheduler hotkey
Ctrl+V
Enter
```

The implementation program answers:
- what code is created;
- where it lives;
- in what order it is built;
- what dependencies are permitted;
- what tests prove each contract;
- which empirical gates must run;
- what evidence allows the next stage to begin;
- when implementation must stop and reopen architecture instead of improvising.

## 2. Governing engineering principles

### 2.1 Frozen design is input, not editable implementation clay

The child implementation task consumes the UX-13 design freeze.

If implementation evidence contradicts a frozen contract:
1. stop the affected stage;
2. record the exact evidence;
3. mark the stage BLOCKED/FAILED as appropriate;
4. reopen the owning architecture/security decision through a separate reviewed change;
5. do not silently modify behavior to make code easier.

### 2.2 One stage, one bounded objective

Every stage has:
- exact inputs;
- exact mutation scope;
- deliverables;
- required tests;
- exit criteria;
- rollback/recovery boundary.

Do not combine adjacent stages merely because implementation is convenient.

### 2.3 Tests precede promotion

A stage is not complete because code exists.

A stage is complete only when:
- required tests pass;
- repository validation passes at the exact head;
- durable task evidence records the result;
- no REQUIRED_CORRECTION or BOUNDED_ENABLING_CHANGE remains for that stage.

### 2.4 Ports inward, adapters outward

Implementation dependency direction follows the frozen hexagonal architecture.

Core/application code may depend on:
- domain records;
- application interfaces;
- abstract ports.

It must not depend directly on:
- Firefox APIs;
- Win32 clipboard/hotkey calls;
- WebView2;
- ChatGPT;
- GitHub SDKs;
- simulator-only controls.

Platform adapters implement ports.

### 2.5 Authority remains external

No helper, browser adapter, simulator, model output, UI state, or local cache can:
- claim OperatorActions without the authorized OperatorBridge application service;
- create Permission;
- remove Prohibition;
- mint durable completion;
- widen task mutation scope.

### 2.6 Fake-worker first

No real ChatGPT account is required or permitted for early implementation.

Stages 01-08 operate against:
- pure/in-memory ports;
- UX-10 fake worker;
- deterministic simulator;
- local Firefox test profile.

Real-account calibration occurs only after the explicit Stage 12 gate.

## 3. Authorized implementation tree

The child task authorizes only the following new implementation surfaces:

```text
operator-bridge/
  src/
    WorkspaceOperator/
    FirefoxAdapter/
    SharedContracts/
  simulator/
    FakeWorker/
    Scenarios/
  tests/
    WorkspaceOperator.Tests/
    Protocol.Tests/
    Integration.Tests/
    Simulator.Tests/
  install/
  tools/
  README.md

.github/workflows/operator-bridge-validation.yml
benchmarks/workspace-semantic-execution/operator_bridge/**
tests/test_workspace_semantic_execution_operator_bridge*.py
```

The task also owns only its own task capsule/handoff plus the three implementation-program architecture artifacts.

Frozen UX-00..UX-13 artifacts are read-only inputs to this task.

## 4. Selected implementation baseline

### Windows helper

- C# / .NET 10 LTS;
- WinForms;
- `RegisterHotKey`;
- STA write-only clipboard;
- `NotifyIcon`;
- `PipeOptions.CurrentUserOnly` named pipe;
- self-contained single-file `win-x64` publish.

### Firefox baseline

- Firefox ESR 153+;
- Manifest V3;
- plain JavaScript;
- permissions: `nativeMessaging`, `tabs`, `sessions`;
- no content scripts;
- no host permissions;
- no automatic input/content/output access.

### Browser IPC

```text
Firefox extension
  → Native Messaging stdio
  → helper native-host proxy mode
  → CurrentUserOnly named pipe
  → primary helper
```

Protocol source:
`architecture/workspace-semantic-execution-operator-native-messaging-protocol.v0.1.json`

The implementation copy/schema must remain byte- or canonical-content-equivalent to the frozen protocol contract, with a regression test preventing drift.

### Simulator

The UX-10 simulator is implemented as a test-only subsystem.

`SIM_HUMAN_SUBMIT` and fault controls must be unreachable from production package/protocol surfaces.

## 5. Repository/build strategy

### .NET solution

Create one solution under `operator-bridge/` with bounded projects:
- `WorkspaceOperator`: production helper;
- `SharedContracts`: local typed contracts only;
- `WorkspaceOperator.Tests`;
- `Protocol.Tests`;
- `Integration.Tests`;
- simulator projects as justified by Stage 05.

Prefer BCL/Windows APIs first.

Any new NuGet/runtime package beyond test infrastructure or WebView2 requires:
- exact purpose;
- version pin;
- security/maintenance rationale;
- stage evidence.

### Firefox JavaScript

Start with:
- `manifest.json`;
- `background.js`;
- small pure helper modules only when needed.

Do not introduce a bundler/runtime dependency in v0 unless code size/maintainability creates measured need.

Browser-protocol static tests may be driven from the existing repository Python test harness and/or a pinned Node test runtime. Production extension code has no npm runtime dependency.

### CI

Stage 01 creates `.github/workflows/operator-bridge-validation.yml`.

It must be path-filtered to the child implementation surfaces and initially run:
- task/program contract checks;
- .NET restore/build/test;
- protocol-schema drift checks;
- Firefox manifest/permission static checks;
- simulator separation checks as they become available.

CI must never require:
- ChatGPT credentials;
- browser account cookies;
- OpenAI account login;
- secrets for fake-worker tests.

## 6. Configuration strategy

Production configuration is local and bounded.

Allowed examples:
- helper startup preference;
- configured scheduler hotkey;
- Firefox executable path;
- WorkspaceWorkers profile path/name;
- log retention settings;
- explicitly authorized OperatorBridge endpoint/transport configuration when later supplied.

Forbidden dynamic configuration:
- arbitrary task/model-supplied browser URL;
- arbitrary executable path from worker packet;
- browser profile/cookie/token database location;
- privileged command templates;
- authority policy.

## 7. Logging and diagnostics

Use content-free structured events.

Every log event must be generated from an allowlisted record type.

Never log:
- packet text;
- clipboard contents;
- raw URLs;
- ChatGPT page/output content;
- credentials/tokens;
- global keystroke streams;
- unrelated process/browser history.

Stage tests must verify redaction, not merely document it.

## 8. Testing pyramid

### L0 — Pure contracts/domain
Fast deterministic tests:
- protocol parsing;
- action/generation identity;
- idempotency keys;
- state classification;
- origin enum reduction;
- configuration validation.

### L1 — Application with fake ports
- hotkey dispatch state machine;
- clipboard timing;
- BrowserPort outcomes;
- local receipts;
- no-work/judgment/recovery routing.

### L2 — OS-local helper integration
- RegisterHotKey;
- bridge ON/OFF;
- named pipe;
- native-host proxy framing;
- clipboard write behavior;
- process restart.

### L3 — Firefox + fake worker
- Native Messaging;
- tab/view lifecycle;
- sessions metadata;
- origin classification;
- discard/restore;
- adapter crash/reconnect.

### L4 — Human-in-loop simulator
- literal scheduler hotkey → Ctrl+V → Enter;
- UX-11 trials.

### L5 — Bounded real-account calibration
Only after explicit Stage 12 gate.

## 9. Stage promotion discipline

The machine-readable stage plan is authoritative for dependencies and gates.

General rule:

```text
IMPLEMENT
→ UNIT/CONTRACT TEST
→ INTEGRATION TEST
→ EXACT-HEAD CI
→ RECORD EVIDENCE
→ PROMOTE NEXT STAGE
```

A failed stage does not automatically authorize broader refactoring.

Classify findings using the scope-closure procedure:
- REQUIRED_CORRECTION;
- BOUNDED_ENABLING_CHANGE;
- AUTHORIZED_SCOPE_EXPANSION;
- DEFERRED_FOLLOWUP.

## 10. Rollback/recovery

Every implementation stage must leave:
- exact Git recovery head;
- test evidence;
- task-capsule stage state;
- next safe action.

No stage may depend on conversation memory.

Installer/update stages must additionally prove:
- install ownership;
- uninstall ownership;
- rollback to previous helper/XPI;
- no deletion of unrelated Firefox/profile/user data.

## 11. Real-account boundary

Before Stage 12:
- no real-account page automation;
- no production ChatGPT data extraction;
- no browser credential import;
- no private endpoint use.

Stage 12 requires all of:
- signed Firefox XPI/native host installation;
- target-host API smoke PASS;
- UX-08 implementation security checklist PASS;
- fresh OpenAI terms/product review;
- normal manual authentication;
- explicitly authorized production OperatorBridge transport.

If any gate fails, stop. Do not evade.

## 12. Production-promotion definition

Production promotion is a separate final decision.

It requires:
- all required implementation stages validated;
- UX-09 empirical budgets evaluated;
- UX-11 human-in-loop trials pass;
- zero hard safety/correctness failures;
- install/update/rollback evidence;
- bounded real-account calibration;
- no open blocking security/authority finding.

The WebView2 candidate is optional. Failure to promote it does not block Firefox v0.

## 13. Stage-zero decision

This artifact plus the companion stage plan and traceability matrix establish the construction program.

Stage 00 is complete only after:
- the child task capsule exists;
- its mutation scope exactly covers the implementation surfaces above and no more;
- parent UX freeze is pinned by exact SHA;
- repository CI validates the new task/program artifacts;
- the child capsule/handoff is synchronized.

Then Stage 01 may begin.
