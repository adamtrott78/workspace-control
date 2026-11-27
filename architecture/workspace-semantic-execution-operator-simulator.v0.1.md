# Workspace Semantic Execution Operator Simulator v0.1

Status: **UX-10 SIMULATOR CONTRACT CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Companions:
- `architecture/workspace-semantic-execution-operator-simulator-fixture-catalog.v0.1.json`
- `architecture/workspace-semantic-execution-operator-simulator-e2e-test-matrix.v0.1.json`
- `benchmarks/workspace-semantic-execution/operator_ux_performance_v1.json`

## 1. Purpose

Define a deterministic fake-ChatGPT environment that can exercise the complete operator bridge without a ChatGPT account, without ChatGPT page-content automation, and without weakening the UX-03 through UX-09 contracts.

The simulator must prove that these boundaries work together:

```text
durable scheduler/action/session state
        ↓
native helper
        ↓
browser adapter
        ↓
fake worker surface
        ↓
human Ctrl+V + Enter
        ↓
fake durable worker transition
        ↓
durable acknowledgment observer
```

The simulator is not a fake LLM. It is a deterministic worker/session/acknowledgment environment.

## 2. Design goals

The simulator MUST support:

- literal human-operated `Ctrl+B → Ctrl+V → Enter` without any ChatGPT account;
- deterministic automated control-state testing in CI;
- exact OperatorAction and logical-session schemas;
- browser-adapter neutrality;
- Firefox/WebExtension testing against a local fake worker;
- future custom-worker-shell testing against the same fixtures;
- controlled acknowledgment delay/drop/duplicate/late behavior;
- browser/tab/profile/auth-domain fault injection;
- helper/adapter/orchestrator crash and restart boundaries;
- generation fencing and stale-result tests;
- concurrent ready-worker scenarios;
- UX-09 latency/resource instrumentation;
- content-free bridge observability.

It MUST NOT require:
- ChatGPT DOM compatibility;
- actual model inference;
- network access to OpenAI;
- credentials;
- browser cookies/tokens;
- synthetic interaction with a production browser page.

## 3. Two execution modes

### 3.1 HUMAN_IN_LOOP

Purpose:
- validate the real physical operator sequence;
- validate OS hotkey registration;
- validate real clipboard staging;
- validate actual browser focus;
- validate a human paste and Enter boundary.

Flow:

```text
operator presses Ctrl+B
→ helper claims/prepares one simulator action
→ helper stages synthetic packet
→ exact fake worker surface gains focus
→ operator presses Ctrl+V
→ operator presses Enter
→ fake worker page submits to simulator worker service
→ fake worker service emits configured durable worker transition
→ durable ack observer completes action
```

The extension/browser adapter still never reads the page content.

The fake page may visibly show test-only state for the human, but no production bridge code may depend on that state.

### 3.2 DETERMINISTIC_CI

Purpose:
- run state-machine, recovery, scheduling, and failure scenarios automatically;
- avoid OS/browser nondeterminism where it is not under test;
- preserve the production human/content boundary.

CI does **not** synthesize browser typing or clicks.

Instead, at an explicit fixture-defined human boundary, a simulator-only test driver invokes:

`SIM_HUMAN_SUBMIT(action_id, worker_slot_id, generation, payload_sha256)`

directly on the fake worker service.

This call represents the human having completed Ctrl+V + Enter. It exists only in the simulator namespace and is not part of BrowserPort, ClipboardPort, Native Messaging, or the production helper.

Rule:

> No production component may call or depend on `SIM_HUMAN_SUBMIT`.

## 4. Component model

### 4.1 Simulator Scenario Controller

Owns:
- deterministic fixture loading;
- virtual/real clock mode;
- initial durable state;
- deterministic fault schedule;
- expected terminal predicates;
- scenario seed/version;
- trace assembly.

It does not grant production authority. It is a test fixture owner.

### 4.2 Fake Operator Application Service

Implements the production application contract in a bounded local test service:
- `GetOperatorStatus`;
- `GetReadyManualCycleCount`;
- `ClaimNextOperatorAction`;
- `RecordLocalPrepared`;
- `RecordLocalFailure`;
- `RequestSessionRecovery`.

It uses the same action/session transition rules as the production design.

### 4.3 Fake OperatorAction Store

Stores synthetic OperatorActions conforming to:
`architecture/workspace-semantic-execution-operator-action-schema.v0.1.json`.

Properties:
- deterministic CAS claim behavior;
- deterministic queue ordering;
- immutable terminal states;
- retry-by-replacement;
- configurable claim expiry;
- exact stale/superseded behavior.

### 4.4 Fake Logical Session Registry

Stores records conforming to:
`architecture/workspace-semantic-execution-operator-session-schema.v0.2.json`.

It models:
- slot + generation identity;
- continuity state;
- lifecycle intent;
- task/role/process affinity;
- outstanding action;
- last acknowledged checkpoint;
- discard/rotate/retire.

It never stores browser tab IDs as durable identity.

### 4.5 BrowserAdapter test interface

The simulator defines one adapter-neutral interface used by:
- an in-memory deterministic fake adapter;
- the UX-12 Firefox/WebExtension spike;
- any UX-12 custom worker browser/shell spike.

Required operations:

```text
EnsureWorkerSurface()
CreateWorkerBinding(slot, generation)
ActivateWorkerBinding(slot, generation)
ReloadOrRestoreWorkerBinding(slot, generation)
DiscardWorkerBinding(slot, generation)
CloseWorkerBinding(slot, generation)
InventoryManagedBindings()
GetOriginClassification(slot, generation)
```

Required result fields:
- protocol version;
- request/correlation ID;
- operation;
- slot;
- generation;
- local binding ID if any;
- outcome: APPLIED / NOT_APPLIED / UNKNOWN;
- normalized error class;
- monotonic timestamp.

Forbidden adapter methods:
- read page text;
- read response;
- inspect composer;
- submit page content;
- inspect cookies/tokens;
- infer durable completion.

### 4.6 Fake Worker Surface

A local test webpage/surface representing one worker conversation.

It is intentionally simple:
- one visible submission field;
- Enter submits;
- optional visible test status for the human;
- no model response is required for correctness.

The worker surface is associated with:
- local simulated worker binding;
- logical slot;
- generation;
- expected synthetic payload SHA.

The browser adapter does not learn these facts by scraping the page. Binding identity comes from its own managed binding metadata.

### 4.7 Fake Worker Service

Receives a submitted synthetic packet.

In HUMAN_IN_LOOP mode:
- fake page computes or forwards the submitted payload bytes;
- service hashes them;
- service compares the hash to the expected current packet hash for the slot/generation.

In DETERMINISTIC_CI:
- `SIM_HUMAN_SUBMIT` supplies the expected payload SHA directly.

A valid submission schedules a fixture-configured worker outcome.

Invalid payload:
- produces no valid durable acknowledgment;
- may emit a simulator diagnostic event;
- cannot mutate production-like durable state.

### 4.8 Fake Durable Event Store

Authoritative **within the simulator only** for test worker transitions.

Supported worker-event classes:
- `WORKER_TRANSITION`;
- `EXTERNAL_RESULT`;
- `VALIDATION_COMPLETED`;
- `STALE_OLD_GENERATION_EVIDENCE`.

Event identity includes:
- event ID;
- action ID;
- worker slot;
- generation;
- durable checkpoint ref;
- event sequence;
- synthetic event payload ref/hash;
- created-at/monotonic sequence.

No browser/page completion inference is accepted as a durable event.

### 4.9 Fake Durable Ack Observer

Maps fake durable events to OperatorAction acknowledgment under the same generation/action conditions as production.

It MUST:
- ignore mismatched generations for control advancement;
- preserve late old-generation evidence;
- deduplicate replayed events;
- accept only fixture-authorized durable event classes;
- never inspect fake page state.

### 4.10 Fault Injector

Faults are injected at named deterministic checkpoints rather than arbitrary sleep timing whenever possible.

Checkpoint examples:
- BEFORE_CLAIM;
- AFTER_CLAIM;
- BEFORE_BROWSER_STEP;
- AFTER_BROWSER_EFFECT_BEFORE_RECEIPT;
- BEFORE_CLIPBOARD_WRITE;
- AFTER_CLIPBOARD_WRITE;
- BEFORE_LOCAL_PREPARED_RECORD;
- AFTER_LOCAL_PREPARED;
- BEFORE_HUMAN_SUBMIT;
- AFTER_HUMAN_SUBMIT;
- BEFORE_DURABLE_EVENT;
- AFTER_DURABLE_EVENT_BEFORE_OBSERVER;
- DURING_RECOVERY_STEP_N.

Fault classes:
- helper process loss;
- browser adapter disconnect;
- browser process loss;
- tab close;
- binding ambiguity;
- orchestrator unavailable;
- clipboard failure;
- stale action/generation;
- auth-domain invalidation;
- ack delay/drop/duplicate;
- old-generation late ack;
- wrong profile;
- sleep/restart;
- executor identity unproven.

## 5. Synthetic packet contract

Simulator packets are intentionally non-sensitive.

Canonical fixture packet:

```text
WORKSPACE_SIM_PACKET_V1
action_id=<synthetic action id>
worker_slot_id=<synthetic slot>
session_generation=<n>
payload_ref=<synthetic payload ref>
nonce=<fixture-local non-secret nonce>
body=<bounded synthetic text>
```

The packet body exists only to validate clipboard/paste integrity.

The production bridge still records only:
- payload ref;
- SHA-256;
- action/session identity.

It does not log the packet text.

## 6. Human boundary semantics

The simulator distinguishes:

- `LOCAL_PREPARED`: browser target/focus/clipboard preparation succeeded;
- `SIM_HUMAN_SUBMIT`: human boundary occurred in simulator;
- `WORKER_TRANSITION`: fake worker produced durable evidence;
- `ACKNOWLEDGED`: observer matched durable evidence;
- `COMPLETED`: action terminal state.

A human submit does not directly acknowledge an action.

This preserves the production invariant:

> submission is not completion evidence.

## 7. Clock model

### Virtual clock

Used for deterministic CI:
- claim expiration;
- ack delay;
- recovery delay;
- event ordering;
- timeout-display behavior.

Virtual time advances only by fixture/test commands.

### Real monotonic clock

Used for:
- UX-09 hotkey/clipboard/focus latency;
- browser startup;
- restore/create timing;
- resource sampling.

A scenario declares which clock it uses. Performance acceptance cannot be measured with virtual time.

## 8. Fault schedule model

A fixture defines ordered fault rules:

```json
{
  "trigger": "AFTER_BROWSER_EFFECT_BEFORE_RECEIPT",
  "match": {
    "action_id": "sim-action-03",
    "operation": "CREATE_TAB"
  },
  "effect": "HELPER_CRASH",
  "once": true
}
```

Rules are deterministic and evaluated by fixture order.

No random fault injection is claim-bearing for acceptance. Optional fuzz/property testing may exist later, but every failure must be reducible to a recorded seed/event trace.

## 9. Authentication-refresh simulation

The simulator does not imitate ChatGPT login DOM.

Instead it models the security-reviewed browser metadata boundary.

A managed worker binding has origin classification:
- `WORKER_ORIGIN`;
- `OFF_WORKER_ORIGIN`;
- `UNKNOWN`.

To simulate login/all-tab refresh:

```text
managed worker(s)
→ origin classification OFF_WORKER_ORIGIN/UNKNOWN
→ AUTH_NAVIGATION_DETECTED
→ auth-domain recovery incident
→ affected logical continuity UNKNOWN
→ durable ack reconciliation
→ unresolved old actions superseded
→ generation advance
→ replacement sessions from durable checkpoints
```

The scenario controller can later emit `AUTH_RETURN_ORIGIN_OBSERVED`, but this is not continuity proof.

No auth credentials or fake DOM selectors are involved.

## 10. Browser-adapter neutrality

The simulator must not encode Firefox-specific tab semantics in the control plane.

Adapter capability descriptor:

```text
adapter_id
adapter_kind = IN_MEMORY | FIREFOX_EXTENSION | CUSTOM_SHELL
supports_discard
supports_persistent_binding_metadata
supports_origin_classification
supports_profile_or_user_data_isolation
supports_cold_start_measurement
supports_resource_process_group
```

A scenario can declare required capabilities.

If a custom shell uses suspend/unload instead of Firefox `tabs.discard`, it maps that local primitive to the same logical `DiscardWorkerBinding` semantics.

## 11. Observability

Every simulator trace event is content-free.

Allowed fields:
- scenario ID/version;
- trace sequence;
- virtual/monotonic timestamp;
- component;
- event type;
- action ID/generation;
- slot/generation;
- operation enum;
- result enum;
- payload ref/hash;
- durable event ID;
- recovery ID/scope;
- normalized error/fault ID;
- performance timing.

Forbidden:
- arbitrary clipboard text;
- fake page field contents;
- future ChatGPT content;
- credentials;
- raw auth URLs;
- mouse/keystroke streams.

The trace is the primary deterministic debug artifact.

## 12. Required simulator assertions

Every E2E scenario may assert:

### Durable/control state
- exact action terminal state;
- exact session generation;
- exact continuity state;
- outstanding action set;
- replacement/supersession links;
- durable ack accepted/ignored.

### Local effects
- number of create/activate/reload/discard/close calls;
- whether clipboard was written;
- number of clipboard writes;
- final focus target;
- local binding inventory;
- local operation outcome.

### Negative assertions
- no duplicate claim;
- no duplicate generation advance;
- no stale action advancement;
- no focus steal on background ack;
- no clipboard change without explicit dispatch;
- no automatic resend;
- no DOM/content adapter calls.

## 13. Performance instrumentation

UX-10 supplies a deterministic workload for UX-09 mechanical measurements.

Simulator runs may measure:
- helper idle overhead;
- adapter/extension overhead;
- hotkey-to-callback;
- action claim;
- browser activation/create/restore;
- clipboard write;
- final focus;
- LOCAL_PREPARED recording;
- no-work completion.

The fake worker is deliberately lightweight, so simulator browser RAM is **not** a substitute for real ChatGPT page RAM.

Therefore:
- simulator mechanical latency/resource measurements are regression evidence;
- target-machine ChatGPT browser RAM remains an explicit UX-12/UX-13 calibration requirement.

Firefox and any custom shell must run identical simulator fixtures.

## 14. Test layers

### Layer 0 — Pure contract tests
No browser/helper.
- action transitions;
- session policy;
- durable ack mapping;
- generation fencing;
- retry/supersession.

### Layer 1 — In-memory adapter integration
- fake BrowserAdapter;
- fake ClipboardPort;
- fake HotkeyPort;
- virtual clock;
- all deterministic failure fixtures.

### Layer 2 — Real local helper + fake worker
- actual native helper;
- actual OS clipboard/hotkey;
- in-memory or local browser adapter;
- fake durable services.

### Layer 3 — Real browser adapter + fake worker
- Firefox/WebExtension or custom shell;
- local fake worker origin;
- real lifecycle/focus/discard/restore;
- no ChatGPT account.

### Layer 4 — Human-in-loop physical UX
- user physically runs Ctrl+B → Ctrl+V → Enter;
- fake worker emits durable ack;
- batch and recovery trials.

No layer before the later real-account calibration needs OpenAI access.

## 15. Build separation

Simulator-only capabilities MUST be structurally isolated from production.

At minimum:
- simulator namespace/module;
- explicit `SIMULATOR_MODE`;
- fake worker origin allowlist distinct from production origin;
- no simulator endpoint enabled in production packaging;
- no `SIM_HUMAN_SUBMIT` symbol reachable through production BrowserPort/Native Messaging protocol;
- release tests verify simulator-only endpoints are absent/disabled.

The simulator may have privileged test controls over its own synthetic state. Those controls do not imply production authority.

## 16. Deterministic terminal report

Each scenario produces:

```json
{
  "scenario_id": "...",
  "fixture_version": 1,
  "mode": "DETERMINISTIC_CI",
  "result": "PASS",
  "final_action_states": {},
  "final_session_states": {},
  "durable_events": [],
  "browser_effect_counts": {},
  "clipboard_write_count": 1,
  "generation_advances": {},
  "violations": [],
  "trace_sha256": "..."
}
```

A scenario passes only if all required predicates and all negative invariants pass.

## 17. UX-10 acceptance assessment

**PASS at simulator-contract design level** when the companion fixture and E2E catalogs are durable.

The design supports:
- literal human Ctrl+B → Ctrl+V → Enter against a safe local worker;
- deterministic CI without production browser input automation;
- durable ack semantics;
- stale/late/recovery/failure tests;
- concurrent workers;
- browser-adapter-neutral Firefox/custom-shell testing;
- UX-09 instrumentation;
- no dependency on a ChatGPT account or page-content access.

Implementation of the simulator is intentionally owned by the later implementation spike. UX-10 freezes what must be built and tested.
