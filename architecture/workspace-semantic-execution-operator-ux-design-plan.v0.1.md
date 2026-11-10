# Workspace Semantic Execution Operator UX Design Plan v0.1

Status: **PROPOSED / EXECUTION ROADMAP**

Parent task: `workspace-semantic-execution-migration-v1`

Companion artifacts:
- `architecture/workspace-semantic-execution-operator-ux.v0.1.md`
- `architecture/workspace-semantic-execution-operator-state-machine.v0.1.md`
- `architecture/workspace-semantic-execution-orchestrator-implementation-plan.v0.1.md`

## 1. Goal

Design the human-operated Chat Instant bridge as a first-class software subsystem before implementation.

The target operator experience is:

```text
Ctrl+B
Ctrl+V
Enter

Ctrl+B
Ctrl+V
Enter
...
```

Workspace Control decides everything else: which worker is next, whether to reuse/create/rotate/retire a session, what packet belongs in the clipboard, and whether a real judgment gate exists.

The UX design is not complete until it is specific enough that the native helper, Firefox extension, orchestrator/session broker, and test harness can be implemented from explicit contracts rather than informal chat decisions.

## 2. Design principles

- Human attention is a scarce resource and an explicit optimization target.
- One routine worker-service cycle must require at most one global hotkey + Ctrl+V + Enter.
- The same hotkey means “perform the next scheduler-selected non-content action.”
- The operator must not read tab headers, choose workers, edit packets, relay SHAs/JSON/results, or interpret scheduler state.
- Chrome remains the normal browser; a dedicated Firefox profile is the worker appliance.
- ChatGPT page-content automation is out of scope for v0.
- Browser/session state is cached execution state; durable Workspace Control state is authoritative.
- Core/domain logic is platform independent and adapters sit behind explicit ports.
- Unknown or ambiguous state fails closed.
- Every design decision should produce a durable artifact or testable contract.

## 3. Workstream structure

Each numbered UX slice below is intentionally large enough to require at least one substantial design/review conversation. Do not collapse multiple slices merely to finish faster. Each slice ends with durable artifacts and an explicit acceptance gate.

---

## UX-00 — Requirements baseline and UX success metrics

### Questions to settle

- What exact manual actions are unavoidable under the conservative OpenAI boundary?
- Which actions can be automated outside the ChatGPT content surface?
- What counts as a routine service cycle versus a real human judgment gate?
- What operator burden is acceptable?
- What RAM/startup/responsiveness constraints matter on the user's laptop?
- What telemetry may be collected locally for UX measurement without creating unnecessary privacy risk?

### Decisions to make

- normative interaction target;
- initial service rhythm: Ctrl+B → Ctrl+V → Enter;
- dedicated Firefox profile requirement;
- expected maximum active worker tabs;
- master toggle behavior;
- UX quantitative targets.

### Artifacts

1. `workspace-semantic-execution-operator-ux-requirements.v0.1.md`
2. `workspace-semantic-execution-operator-ux-metrics.v0.1.json`

### Acceptance gate

The requirements artifact clearly distinguishes:
- mandatory;
- preferred;
- non-goal;
- safety boundary;
- measurable UX target.

---

## UX-01 — Operator journey and task-flow inventory

### Questions to settle

Enumerate every operator-visible scenario, including:
- bridge OFF;
- bridge ON with zero work;
- service existing worker;
- create new worker;
- rotate worker;
- retire worker;
- retire-and-advance;
- Firefox closed;
- Firefox starting;
- tab discarded;
- tab lost;
- worker still generating;
- worker durable result arrives;
- worker never acknowledges;
- ChatGPT session logged out;
- creating a new ChatGPT tab triggers reauthentication and successful login refreshes/invalidates multiple or all worker tabs;
- model/configuration mismatch;
- multiple ready workers;
- judgment gate;
- scheduler blocked;
- normal non-Workspace clipboard use.

### Design work

For each scenario define:
- trigger;
- what the user sees;
- what Ctrl+B does;
- whether clipboard changes;
- whether focus changes;
- required durable acknowledgment;
- recovery path.

### Artifacts

1. `workspace-semantic-execution-operator-journeys.v0.1.md`
2. `workspace-semantic-execution-operator-flow-catalog.v0.1.json`

### Acceptance gate

Every currently known operator-visible path maps to a typed action/state-machine transition. No scenario depends on the user interpreting a tab title or scheduler internals.

---

## UX-02 — System context and architecture boundary design

### Questions to settle

- Exact responsibility split among orchestrator, native helper, Firefox extension, operator console, semantic graph, session broker, and human.
- Which process owns each piece of state?
- Which interfaces cross machine/process boundaries?
- What must survive restart?
- Which components can be replaced independently?

### Design work

Apply:
- ports and adapters / hexagonal architecture;
- dependency inversion;
- single source of truth;
- command/query separation;
- least privilege;
- event-driven integration.

### Artifacts

1. System context diagram.
2. Container/component diagram.
3. Interface ownership matrix.
4. ADR: native helper + Firefox WebExtension split.
5. ADR: dedicated Firefox worker profile.
6. ADR: durable scheduler state vs local cached browser state.

Suggested paths:
- `architecture/workspace-semantic-execution-operator-context.v0.1.md`
- `architecture/adr/operator-bridge-*.md`

### Acceptance gate

Every responsibility has exactly one owner and dependency direction is explicit.

---

## UX-03 — OperatorAction and state-machine contract

### Questions to settle

- Final action types.
- Action priority.
- Claiming and generation semantics.
- Idempotency and stale-action behavior.
- Local prepared vs durable acknowledged.
- Composite actions such as RETIRE_AND_ADVANCE.
- Retry semantics for unconfirmed dispatch.

### Design work

Refine the existing operator-state-machine candidate into an implementable schema.

### Artifacts

1. `schemas/operator_action.schema.json`
2. `schemas/operator_session.schema.json`
3. `architecture/workspace-semantic-execution-operator-state-machine.v0.2.md`
4. Transition truth table.
5. Invalid-transition catalog.

### Acceptance gate

Every state transition can be validated deterministically without Firefox or ChatGPT.

---

## UX-04 — Session-slot and tab-lifecycle design

### Questions to settle

- How many persistent logical worker slots exist?
- Which roles may share a slot?
- When is a session reused?
- When is a session rotated?
- When is a tab discarded versus closed?
- How do we recover Firefox tab/window IDs after restart?
- How do we handle ChatGPT logout or lost continuity without scraping page contents?
- How do role isolation and semantic task affinity affect reuse?

### Design work

Define:
- slot identity;
- generation;
- task/process affinity;
- context-budget estimate;
- health states;
- rotation reasons;
- discard/retire rules.

### Artifacts

1. `architecture/workspace-semantic-execution-session-broker.v0.1.md`
2. `schemas/executor_session.schema.json`
3. Session lifecycle diagram.
4. Session rotation decision table.

### Acceptance gate

Given durable scheduler state plus local browser inventory, the system can deterministically decide REUSE / CREATE / ROTATE / RETIRE / BLOCK.

---

## UX-05 — Global hotkey and clipboard interaction contract

### Questions to settle

- Final default hotkey and fallback bindings.
- Exact behavior when bridge is ON/OFF.
- What happens on rapid double press?
- When exactly is clipboard overwritten?
- Should previous clipboard content optionally be restorable?
- What happens if no work is ready?
- What happens if a judgment gate is next?
- What happens if Firefox startup is slow?

### Design work

Specify Ctrl+B as a command into the operator subsystem, not as a synthetic browser keystroke.

### Artifacts

1. `architecture/workspace-semantic-execution-hotkey-clipboard-contract.v0.1.md`
2. Hotkey dispatch sequence diagram.
3. Clipboard invariants/test matrix.

### Acceptance gate

Normal Ctrl+C/Ctrl+V use is unaffected outside explicit Workspace hotkey dispatch, and no repeated hotkey press can silently duplicate a worker packet.

---

## UX-06 — Tray indicator and operator-console information architecture

### Questions to settle

- What does the tray icon show at a glance?
- What is the primary pending count?
- Which secondary counts matter?
- How are judgment gates distinguished from mechanical work?
- What settings belong in the tray menu?
- What belongs in the full console?
- What details are hidden by default but available for debugging?

### Design work

Design:
- tray states/icons;
- badge semantics;
- menu hierarchy;
- console screens;
- ready/new/reuse/unconfirmed/gate/blocked indicators;
- notification policy.

### Artifacts

1. Low-fidelity wireframes.
2. `architecture/workspace-semantic-execution-operator-console-ia.v0.1.md`
3. Display-state table.
4. Notification policy.

### Acceptance gate

The user can tell “how much mechanical work is waiting” without opening Firefox or reading task state.

---

## UX-07 — Error, interruption, and recovery UX

### Questions to settle

Design the operator experience for:
- Firefox crash;
- helper crash;
- orchestrator unreachable;
- extension disconnected;
- tab closed manually;
- wrong browser/profile opened;
- ChatGPT logged out;
- packet sent but no durable ack;
- stale worker replies;
- worker transition rejected;
- clipboard packet overwritten before paste;
- machine sleep/reboot;
- Ctrl+B pressed while system is recovering.

### Design work

For each failure define:
- detection source;
- user-facing message;
- automatic recovery;
- whether a user action is required;
- whether the worker/session is preserved or rotated;
- whether the scheduler must fail closed.

### Artifacts

1. `architecture/workspace-semantic-execution-operator-recovery.v0.1.md`
2. Failure-mode and effects analysis (FMEA) table.
3. Recovery state diagram.

### Acceptance gate

Every single-component failure has a bounded recovery path and cannot create duplicate execution authority.

---

## UX-08 — Security, privacy, and OpenAI interaction-boundary review

### Questions to settle

- Exact extension permissions.
- Exact native helper privileges.
- Native Messaging host manifest scope.
- What data is stored locally?
- What data is never stored?
- What page-level access is forbidden?
- What automation remains outside ChatGPT content?
- What product/terms checks must occur before real-account testing?
- How is future expansion reviewed?

### Design work

Produce a threat model covering:
- malicious webpage;
- compromised extension;
- stale packet;
- clipboard exposure;
- confused deputy;
- tab ID reuse;
- arbitrary URL opening;
- local IPC abuse;
- secrets leakage;
- accidental consumer-UI automation creep.

### Artifacts

1. `architecture/workspace-semantic-execution-operator-threat-model.v0.1.md`
2. Permission matrix.
3. Security review checklist.
4. ADR: no ChatGPT DOM/content automation in v0.

### Acceptance gate

The bridge operates with least privilege and the reviewed design has no dependency on bot-like page interaction.

---

## UX-09 — Performance and RAM budget

### Questions to settle

- Actual Firefox vs Chrome memory under this workload.
- Base helper/extension overhead.
- Cost of 1/2/4 live ChatGPT tabs.
- Benefit of discarded tabs.
- Browser startup/focus latency.
- Clipboard/hotkey latency.
- Maximum active-session cap.

### Design work

Define benchmark scenarios and budgets before implementation optimization.

### Artifacts

1. `benchmarks/workspace-semantic-execution/operator_ux_performance_v1.json`
2. `architecture/workspace-semantic-execution-operator-performance-budget.v0.1.md`

### Acceptance gate

We have explicit memory and interaction-latency targets and a reproducible measurement procedure.

---

## UX-10 — Fake-ChatGPT simulation and prototype contract

### Questions to settle

- How do we test the full operator loop without touching the real ChatGPT site?
- What fake durable acknowledgments are required?
- How do we simulate slow workers, lost tabs, logout, crashes, stale completions, and concurrent ready workers?
- What observability is needed for debugging?

### Design work

Specify a local simulation harness:
- fake worker webpage;
- fake durable worker endpoint;
- fake scheduler actions;
- native helper;
- Firefox extension;
- deterministic scenario scripts.

### Artifacts

1. `architecture/workspace-semantic-execution-operator-simulator.v0.1.md`
2. Simulator fixture catalog.
3. End-to-end test scenarios.

### Acceptance gate

The complete Ctrl+B → Ctrl+V → Enter flow can be exercised safely without a ChatGPT account.

---

## UX-11 — Usability test design

### Questions to settle

- What constitutes a successful batch-service session?
- How many actions should be serviced without a wrong-tab/wrong-packet error?
- How do we measure cognitive interruption?
- How do we test Ctrl+B collisions during normal work?
- When should we switch hotkeys?
- What subjective friction should be recorded?

### Design work

Create trials for:
- 5-action batch;
- 20-action batch;
- mixed create/reuse/retire batch;
- interruptions between service cycles;
- normal Chrome/VS Code/Jupyter work while bridge enabled.

### Artifacts

1. `benchmarks/workspace-semantic-execution/operator_ux_usability_v1.json`
2. Usability test script.
3. Operator feedback form/checklist.

### Acceptance gate

The UX has objective usability thresholds before implementation is considered production-worthy.

---

## UX-12 — Implementation spike plan

### Questions to settle

- Native helper language/runtime.
- Windows tray/hotkey implementation.
- Firefox WebExtension manifest/version.
- Native Messaging protocol.
- Local IPC transport.
- Packaging/install/update model.
- Logging/diagnostics.
- Test/development workflow.

### Design work

Compare bounded implementation options and choose the smallest maintainable stack.

Potential candidates:
- Python helper + pystray/global-hotkey library;
- .NET helper;
- Rust helper;
- WebExtension JavaScript/TypeScript.

Do not select solely from familiarity; consider startup cost, packaging, RAM, Windows integration, maintainability, and security.

### Artifacts

1. ADR: native helper implementation stack.
2. ADR: extension implementation stack.
3. Native Messaging protocol schema.
4. Prototype implementation plan.

### Acceptance gate

Implementation stack and IPC contracts are frozen enough to begin code without architecture churn.

---

## UX-13 — Integrated design review and UX design freeze

### Review inputs

- requirements;
- journeys;
- architecture boundaries;
- state machine/schema;
- session lifecycle;
- hotkey/clipboard contract;
- tray/console IA;
- recovery design;
- security review;
- performance budget;
- simulator;
- usability plan;
- implementation ADRs.

### Review questions

- Can the operator service routine work without reading tabs?
- Is every non-content action behind the same hotkey?
- Can the bridge be disabled instantly?
- Is durable acknowledgment separated from local preparation?
- Can every failure recover without losing workflow truth?
- Is the browser adapter replaceable?
- Is ChatGPT content automation absent?
- Are memory and operator-attention budgets explicit?
- Can the implementation team code directly from these contracts?

### Artifacts

1. `architecture/workspace-semantic-execution-operator-ux-design-review.v0.1.md`
2. Resolved/open findings ledger.
3. UX design freeze checkpoint.

### Acceptance gate

No unresolved architecture/security/interaction blocker remains for the v0 operator bridge. Open non-blocking enhancements are deferred rather than expanding v0.

## 4. Artifact map

By UX design freeze, the workstream should contain at least:

```text
operator UX requirements
operator UX metrics
operator journeys
operator flow catalog
system/context architecture
architecture decision records
OperatorAction schema
ExecutorSession schema
operator state machine
session broker contract
hotkey/clipboard contract
tray/console information architecture
wireframes
recovery/FMEA artifact
security threat model
permissions matrix
performance budget
performance benchmark spec
simulator design
simulation fixtures
usability benchmark spec
implementation-stack ADRs
native messaging protocol
integrated design review
```

Artifacts should be text/JSON-first and version controlled. Visual diagrams/wireframes may be added when they materially clarify behavior, but must not become the only source of truth.

## 5. Execution order

Critical path:

```text
UX-00 Requirements
  ↓
UX-01 Journeys
  ↓
UX-02 Architecture boundaries
  ↓
UX-03 OperatorAction/state machine
  ├────────→ UX-04 Session lifecycle
  ├────────→ UX-05 Hotkey/clipboard
  └────────→ UX-06 Tray/console IA
                 ↓
        UX-07 Recovery design
                 ↓
        UX-08 Security review
                 ↓
        UX-09 Performance budget
                 ↓
        UX-10 Simulator design
                 ↓
        UX-11 Usability design
                 ↓
        UX-12 Implementation stack
                 ↓
        UX-13 Integrated design review/freeze
```

UX-04, UX-05, and UX-06 may proceed partly in parallel after UX-03, but their contracts must converge before UX-07.

## 6. Current checkpoint

Already-existing candidate artifacts provide useful inputs but are not considered the completed UX design:

- `workspace-semantic-execution-operator-ux.v0.1.md`
- `workspace-semantic-execution-operator-state-machine.v0.1.md`

They contain the initial product hypothesis:
- dedicated Firefox worker profile;
- Windows tray master toggle;
- Ctrl+B global service hotkey;
- one-hotkey browser/session action abstraction;
- Ctrl+V + Enter remain manual;
- no ChatGPT page-content automation;
- durable acknowledgment from Workspace Control state.

UX-00 is complete at the design-baseline level with:

- `architecture/workspace-semantic-execution-operator-ux-requirements.v0.1.md`
- `architecture/workspace-semantic-execution-operator-ux-metrics.v0.1.json`

The forced-login/all-tabs-refresh condition is recorded as mandatory recoverability requirement `SESSION_AUTH_REFRESH_ALL_TABS`, with detailed recovery owned by UX-07 and session-policy implications owned by UX-04.

UX-01 is complete at the design-baseline level with:

- `architecture/workspace-semantic-execution-operator-journeys.v0.1.md`
- `architecture/workspace-semantic-execution-operator-flow-catalog.v0.1.json`

The catalog covers 42 operator-visible journeys across normal service, session maintenance, authentication/continuity, acknowledgment/retry, helper/browser lifecycle, clipboard/focus races, scheduler/authority gates, executor mismatch, resource pressure and batch completion.

The next execution slice is **UX-02 System context and architecture boundary design**.
