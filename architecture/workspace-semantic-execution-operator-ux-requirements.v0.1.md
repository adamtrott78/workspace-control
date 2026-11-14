# Workspace Semantic Execution Operator UX Requirements v0.1

Status: **UX-13 INTEGRATED REQUIREMENTS / IMPLEMENTATION DESIGN FROZEN**

Parent task: `workspace-semantic-execution-migration-v1`

Design workstream:
`architecture/workspace-semantic-execution-operator-ux-design-plan.v0.1.md`

Metrics companion:
`architecture/workspace-semantic-execution-operator-ux-metrics.v0.1.json`

## 1. Product objective

The operator bridge exists to make human-launched Chat Instant workers mechanically serviceable at high repetition without requiring the operator to understand or manage scheduler state.

The normative routine interaction is:

```text
Ctrl+B
Ctrl+V
Enter
```

Repeated as many times as serviceable worker actions remain.

The system, not the operator, decides:
- which worker is next;
- whether to reuse/create/rotate/retire a worker session;
- which exact packet belongs in the clipboard;
- whether a worker is awaiting durable acknowledgment;
- whether a real human judgment/authority gate exists.

## 2. Requirement classes

- **MUST**: required for v0 acceptance.
- **SHOULD**: strongly preferred; deviation requires documented rationale.
- **MAY**: optional.
- **NON-GOAL**: deliberately excluded from v0.
- **DEFERRED DESIGN**: required eventually, but detailed behavior belongs to a later UX slice.

## 3. Mandatory interaction requirements

### UX-M001 — Single routine scheduler command

The bridge MUST expose one primary global scheduler hotkey.

Initial preferred binding:
`Ctrl+B`

Its semantic meaning is always:

> perform the next scheduler-selected non-content operator action.

The human MUST NOT need action-specific hotkeys for create/reuse/rotate/retire/focus.

### UX-M002 — Routine service-cycle upper bound

A normal worker service cycle MUST require no more than:

1. global scheduler hotkey;
2. Ctrl+V;
3. Enter.

No other required click, tab search, prompt edit, copy operation, confirmation, or scheduler inspection is allowed on the routine path.

### UX-M003 — Zero manual worker selection

The operator MUST NOT:
- read tab titles to identify the next worker;
- choose which worker should run next;
- decide whether to reuse or replace a worker;
- manually navigate a list of worker tabs.

The scheduler/session broker owns those decisions.

### UX-M004 — Zero manual prompt construction

The operator MUST NOT edit, compose, merge, annotate, or otherwise transform a scheduler-generated worker packet during routine service.

### UX-M005 — Zero manual state relay

The operator MUST NOT manually transport:
- SHAs;
- JSON state;
- experiment results;
- CI output;
- logs;
- task status;
- worker completion state
between workers and the orchestrator.

Durable system state is the transport.

### UX-M006 — Clipboard isolation

The bridge MUST NOT alter the system clipboard in the background.

The clipboard may be changed only as the direct result of an explicit operator service action such as Ctrl+B when the claimed action requires a worker packet.

Ordinary Ctrl+C/Ctrl+V behavior outside the bridge MUST remain unaffected.

### UX-M007 — No background focus stealing

The helper/browser bridge MUST NOT steal foreground focus unless the operator explicitly invokes the scheduler hotkey or explicitly opens the operator console.

### UX-M008 — Master enable/disable control

The Windows native helper system tray MUST own one authoritative local master toggle:

`Workspace Worker Bridge: ON / OFF`

When OFF:
- the global hotkey is unregistered;
- clipboard is untouched;
- the managed worker browser/shell is not focused/created/closed/discarded by the bridge;
- machine/deterministic orchestrator work may continue;
- pending manual actions may accumulate.

### UX-M009 — Persistent workload indicator

The operator MUST be able to see, without opening Firefox, how many mechanical service cycles are ready.

The primary count is:
`READY_MANUAL_CYCLES`

Secondary counts SHOULD include:
- NEW;
- REUSE;
- ROTATE/RETIRE;
- SENT_UNCONFIRMED;
- JUDGMENT_GATES;
- BLOCKED.

### UX-M010 — Durable acknowledgment separation

The bridge MUST distinguish:
- local preparation of tab + clipboard;
- actual durable worker acknowledgment.

It MUST NOT infer message submission or worker completion from timing, focus, keyboard activity, tab state, or ChatGPT page state.

### UX-M011 — Independent batch servicing

If worker A is already dispatched and awaiting durable acknowledgment while independent workers B/C are serviceable, repeated scheduler-hotkey presses MUST be able to advance to B/C rather than resending A.

### UX-M012 — Judgment gates are not disguised as routine transport

A substantive authority or judgment gate MUST open a distinct operator-console path and MUST NOT be represented as an ordinary paste cycle.

## 4. Browser and session requirements

### UX-M013 — Dedicated managed worker environment

The user's normal/default browser remains outside operator-bridge management.

Chat Instant worker sessions MUST use a dedicated managed worker environment isolated from ordinary browsing.

The frozen v0 production baseline is a dedicated Firefox profile named:
`WorkspaceWorkers`

A purpose-built custom worker shell MAY replace Firefox only if it implements the same BrowserPort semantics and passes the UX-08 security, UX-09 performance, UX-10 adapter-parity, UX-11 usability, and normal-authentication promotion gates.

The dedicated environment is an isolated execution appliance rather than the user's general browsing environment.

### UX-M014 — Persistent workers are preferred

The session broker SHOULD reuse compatible persistent worker conversations across multiple reasoning quanta.

New chats SHOULD be created only for explicit reasons such as:
- no compatible slot;
- role isolation;
- context rotation;
- continuity loss;
- model/toolset change;
- policy requirement;
- user request.

### UX-M015 — Bounded live-session pool

The v0 system MUST use a bounded worker pool rather than unbounded live tabs/views.

Frozen UX-09 policy:
- default live GENERAL_PERSISTENT worker cap: 2;
- absolute v0 live managed worker burst ceiling: 4;
- role-isolated workers are allocated only when workflow/recovery requirements justify the burst;
- trusted idle sessions above the default cap SHOULD be discarded/unloaded rather than retired when safe.

The default cap MUST NOT be raised above 2 until target-machine measurements pass the four-live resource budget.

### UX-M016 — Inactive-session memory control

Idle compatible worker tabs SHOULD be discardable/unloaded when safe and restorable when scheduled.

Completed sessions SHOULD be retired promptly unless retained evidence/recovery policy says otherwise.

### UX-M017 — Browser/session identity is not authority

Logical worker/session slots MUST be identified by durable slot/generation metadata.

Visible ChatGPT tab titles MUST NOT be used as authoritative worker identity.

## 5. Recovery requirements

### UX-M018 — Local component restart recovery

Native helper restart, managed browser/adapter restart, Firefox extension restart, and managed tab/view loss MUST NOT destroy durable workflow state.

The bridge MUST rebuild local mappings from durable scheduler/session state plus current browser inventory.

### UX-M019 — Login/refresh continuity loss is recoverable

The design MUST support the case where:
- opening a new ChatGPT tab triggers reauthentication;
- completing login refreshes or invalidates multiple/all existing worker tabs;
- persistent conversation continuity can no longer be trusted.

The system MUST fail closed on unknown continuity and recover from durable state rather than requiring manual reconstruction.

Detailed detection and one-hotkey recovery behavior is **DEFERRED DESIGN** to UX-07, with session lifecycle implications in UX-04.

### UX-M020 — No duplicate automatic resend

Lack of durable acknowledgment MUST NOT automatically trigger packet resend.

Retry requires an explicit scheduler/recovery decision or explicit operator retry action.

### UX-M021 — Machine sleep/reboot recovery

A Windows sleep/reboot or browser shutdown MUST leave the task recoverable from durable state without manual SHA/state relay.

Detailed recovery choreography is deferred to UX-07.

## 6. Safety and OpenAI-interaction boundary

### UX-M022 — No ChatGPT content automation in v0

The v0 bridge MUST NOT:
- inject text into the ChatGPT composer;
- click Send;
- synthesize keyboard/mouse input into ChatGPT;
- read/scrape model responses from ChatGPT DOM;
- inspect hidden page/network state for completion;
- mimic human timing or cursor behavior;
- attempt to bypass provider restrictions, rate limits, safeguards, or usage controls.

### UX-M023 — Browser automation is chrome-level only

The managed browser adapter MAY:
- launch/focus the dedicated worker environment;
- create managed tabs/views;
- activate managed tabs/views;
- close managed tabs/views;
- discard/unload/reload managed tabs/views;
- maintain local non-authoritative binding mappings.

The Firefox baseline implements these operations with supported WebExtension browser-chrome APIs.

### UX-M024 — Worker completion comes from durable state

The orchestrator MUST detect worker progress/completion from authorized durable state transitions, not consumer ChatGPT page inspection.

### UX-M025 — Terms/product review gate

Before first real-account integration test and before any future expansion of browser-facing behavior, current OpenAI product documentation/terms MUST be re-reviewed.

### UX-M026 — Least privilege

The native helper and Firefox extension MUST request only privileges necessary for the reviewed v0 behavior.

Page-content permissions for ChatGPT SHOULD be absent in v0.

## 7. Architecture requirements

### UX-M027 — Ports and adapters

The operator subsystem core MUST remain independent of:
- Firefox;
- Windows APIs;
- clipboard implementation;
- ChatGPT;
- GitHub SDK details.

Platform integrations exist behind typed ports/adapters.

### UX-M028 — Single source of truth

Workspace Control durable state owns scheduling/operator-action truth.

Native-helper state and Firefox tab/window mappings are recoverable caches.

### UX-M029 — Explicit state machines

Routine behavior MUST derive from typed states/transitions rather than:
- UI text;
- tab titles;
- timing heuristics;
- remembered chat context;
- implicit process state.

### UX-M030 — Fail closed

Unknown/stale generation, missing slot mapping, executor mismatch, ambiguous continuity, or authority ambiguity MUST stop the affected operation rather than guess.

### UX-M031 — Idempotent local operations

Repeated/replayed local browser commands MUST either be safe/idempotent or rejected using action ID/generation.

## 8. Semantic graph integration requirements

### UX-M032 — UX packets derive from bounded semantic state

The worker packet prepared for each manual service cycle SHOULD be generated from the semantic/ontology projection and exact durable evidence rather than full conversation history.

### UX-M033 — UX does not create authority

The operator bridge, session broker, semantic packet compiler, Firefox extension, and native helper MUST NOT manufacture or widen execution authority.

## 9. Performance and responsiveness requirements

The following are the **frozen UX-09 v0 acceptance budgets**. They remain design requirements, not measured facts. Empirical target-machine evidence is still NOT_RUN and blocks production promotion, not implementation design freeze.

### UX-P001 — Routine focus/clipboard preparation

When Firefox worker profile is already running and the target tab exists:

- target p50 from Ctrl+B to ready-for-paste: <= 250 ms;
- target p95: <= 750 ms;
- hard provisional ceiling: 1500 ms.

### UX-P002 — New-tab preparation

When Firefox is already running:

- target p95 from Ctrl+B to new tab focused + clipboard ready: <= 2000 ms.

### UX-P003 — Cold Firefox startup

When the worker profile is stopped:

- target p95 from Ctrl+B to worker tab ready: <= 8000 ms.

Cold start may exceed routine-path budgets and is not expected for every service cycle.

### UX-P004 — Helper/browser idle CPU

With bridge ON and no operator action:
- native helper idle CPU mean MUST remain <= 1% of one logical CPU;
- Firefox with two live idle workers MUST remain <= 5% of one logical CPU mean.

### UX-P005 — Helper/extension memory

Frozen local-control-plane budgets:
- native helper Working Set p95 <= 100 MiB;
- helper + Firefox extension incremental Working Set p95 <= 150 MiB.

### UX-P006 — Worker Firefox memory

Frozen baseline budgets:
- Firefox with 2 live worker tabs Working Set p95 <= 1536 MiB;
- Firefox with 4 live worker tabs Working Set p95 <= 2560 MiB;
- discarding 3 of 4 idle tabs SHOULD reduce total Working Set by at least 25%.

If a custom shell is considered, it runs the same measurement matrix and may replace Firefox only through the frozen UX-09 review trigger.

These are acceptance budgets, not acceptance facts, until measured on the target machine.

## 10. Operator-effort metrics

### UX-Q001 — Manual transcription

Acceptance target:
`0` manual transcription events per routine workflow.

### UX-Q002 — Manual scheduler decisions

Acceptance target:
`0` manual decisions about which worker/session to service during routine operation.

### UX-Q003 — Routine service keystrokes

Acceptance target:
one scheduler hotkey + Ctrl+V + Enter per worker packet.

### UX-Q004 — Manual tab searches

Acceptance target:
`0`.

### UX-Q005 — Wrong-worker dispatch

Pre-production acceptance target:
`0` wrong-worker packet dispatches across a 20-cycle mixed usability trial.

### UX-Q006 — Session reuse

Measurement requirement:
record percentage of Chat reasoning quanta serviced through an existing compatible session.

No fixed acceptance threshold is frozen in UX-00; UX-04/UX-11 will set one after role/isolation needs are modeled.

### UX-Q007 — Human launch count

Record:
- new chat creations per completed workflow;
- session rotations per completed workflow;
- forced-login recoveries per completed workflow.

Optimization direction is downward, but correctness/isolation outrank minimizing launches.

## 11. Local telemetry requirements

The helper MAY record local UX telemetry needed for evaluation:
- action ID/type;
- scheduler hotkey timestamp;
- local preparation duration;
- browser create/focus/close outcome;
- clipboard-write success/failure;
- durable acknowledgment latency;
- worker slot/generation;
- bridge ON/OFF state changes;
- recovery/error classification;
- RAM/CPU measurements during explicit performance trials.

It MUST NOT record:
- arbitrary clipboard contents;
- ChatGPT response text scraped from the page;
- passwords/authentication secrets;
- keystroke streams;
- mouse trajectories;
- unrelated browsing history.

Packet content SHOULD NOT be duplicated into telemetry when an exact durable packet/content hash is sufficient.

## 12. Preferred requirements

The v0 bridge SHOULD:
- expose a tray icon and optional Firefox badge;
- start the native helper with Windows only if the user enables it;
- allow configurable bridge startup ON/OFF state;
- allow the global hotkey to be rebound;
- use Ctrl+B as the first ergonomic candidate;
- support explicit “Open Worker Firefox” and “Open Operator Console” commands;
- provide a quiet no-action response without stealing focus;
- support an explicit retry path for unconfirmed dispatch;
- make debug details available without showing them in the routine path.

## 13. Non-goals for v0

v0 does NOT aim to:
- automate paste/send into ChatGPT;
- infer ChatGPT response completion from the page;
- manage the user's normal Chrome browsing;
- provide a general browser automation framework;
- preserve every Chat conversation forever;
- guarantee uninterrupted ChatGPT login/session continuity;
- optimize every possible browser or OS;
- replace durable task/workflow state with extension state;
- solve account login/reauthentication automatically;
- guarantee provider policies never change;
- build final visual polish before behavior is correct.

## 14. Integrated design resolution and remaining empirical gates

UX-01 through UX-12 have completed their design responsibilities and UX-13 has integrated them.

No unresolved v0 architecture/security/interaction design item remains before fake-worker implementation.

Remaining gates are evidence/execution gates rather than deferred design:

### Implementation authority
The current task does not authorize new helper/extension code paths. A separate authority-owned implementation scope is required before coding.

### UX-09 empirical evidence
Run the frozen performance/resource benchmarks after implementation. Real ChatGPT page memory is calibrated only after the real-account security/policy gate.

### UX-11 empirical evidence
Run the required human-in-loop simulator trials. Production promotion requires zero hard correctness/safety failures.

### Real-account gate
Before any real-account test:
- pass implementation security checklist;
- pass Firefox/native-host target-host smoke tests;
- use signed extension/install state;
- re-review current OpenAI Terms/product guidance;
- verify normal manual authentication;
- bind only to an explicitly authorized Workspace Control transport.

### Conditional custom shell
WebView2 authentication/performance evidence blocks only custom-shell promotion. Firefox remains the production baseline if the shell is incompatible or not materially better.

## 15. UX-00 acceptance decision

UX-00 is complete when:

- mandatory, preferred, non-goal, safety, performance, telemetry and deferred requirements are separately represented;
- routine interaction target is explicit;
- conservative ChatGPT automation boundary is explicit;
- dedicated Firefox worker profile and tray master-toggle requirements are explicit;
- forced-login/all-tabs-refresh is recorded as a mandatory recovery requirement without prematurely designing its recovery flow;
- measurable UX metrics exist in the companion JSON artifact;
- later UX slices have clear ownership for unresolved design questions.

