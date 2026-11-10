# Workspace Semantic Execution Operator State Machine v0.1

Status: **PROPOSED / NON-AUTHORITATIVE ARCHITECTURE**

Parent task: `workspace-semantic-execution-migration-v1`

Companions:
- `architecture/workspace-semantic-execution-operator-ux.v0.1.md`
- `architecture/workspace-semantic-execution-orchestrator-implementation-plan.v0.1.md`

## 1. Architectural principles

### Single source of truth
The Workspace Control orchestrator owns scheduler/operator action truth.
Firefox tab state and native-helper state are cached execution state, not authority.

### Separation of concerns
- orchestrator: decides WHAT operator action is next;
- native helper: owns global hotkey, clipboard, tray and local dispatch;
- Firefox extension: performs browser chrome/tab operations;
- human: performs the minimum unsupported content interaction (paste + submit);
- worker: reasons and writes durable state;
- validator/control plane: validates durable transitions.

### Ports and adapters
The operator bridge is an adapter behind a typed `OperatorAction` interface.
Replacing Firefox, the hotkey helper, or a future supported Chat invocation surface must not change scheduler semantics.

### Explicit state over implicit behavior
Every pending action and session has a typed state. No behavior depends on tab title, chat prose, timing guesses, or hidden DOM state.

### Fail closed
Unknown browser/session state, executor mismatch, lost tab mapping, stale action generation, or authority ambiguity MUST stop the affected action rather than guess.

### Idempotency
Repeated local dispatch of a browser-management command should be safe or rejected by action ID/generation.
No automatic repeated worker submission is allowed.

### Event driven
Worker completion is observed from durable GitHub/control state. No reasoning/model polling and no browser-page polling.

### Least privilege
The extension receives only tab/window/native-messaging permissions required for browser management. v0 does not require ChatGPT page-content access.

### Human attention as a scarce resource
Mechanical human transport is explicitly measured and minimized. Genuine judgment gates remain distinct from mechanical service actions.

### Recoverability
Helper restart, Firefox restart, tab loss, or worker continuity loss must be recoverable from durable orchestrator state and session mappings.

## 2. Master toggle ownership

The **Windows system-tray native helper** owns the master operator toggle.

There is exactly one authoritative local mode switch:

`Workspace Worker Bridge: ON / OFF`

### OFF
- global Ctrl+B hotkey is unregistered;
- no clipboard mutation;
- no Firefox focus/create/close/discard commands;
- orchestrator may continue deterministic/machine work;
- pending human-service actions accumulate visibly;
- tray icon remains available.

### ON
- global hotkey is registered;
- helper may service scheduler-selected operator actions only when Ctrl+B is explicitly pressed;
- no background focus stealing;
- no background clipboard mutation.

Firefox toolbar UI may MIRROR state and open the console, but MUST NOT own a second conflicting enable/disable state.

Optional startup preference:
- Start helper with Windows: configurable;
- Bridge starts ON or OFF: configurable;
- recommended initial default during testing: helper starts, bridge OFF.

## 3. Tray menu

Minimum tray menu:

```text
Workspace Worker Bridge   [ON/OFF]
Pending actions: 6
  New chats: 2
  Existing chats: 4
  Judgment gates: 0

Open Operator Console
Open Worker Firefox
Retry Last Unconfirmed Dispatch
Pause New Worker Creation
Settings
Exit Helper
```

Only the master ON/OFF toggle controls Ctrl+B interception.

`Pause New Worker Creation` is a scheduling preference, not a second master toggle. Existing sessions may still be serviced if policy allows.

## 4. System-level bridge states

```text
DISABLED
  │ toggle ON
  ▼
ENABLED_IDLE ───────────────┐
  │ ready action exists     │ no ready action
  ▼                         │
ENABLED_READY ──────────────┘
  │ Ctrl+B
  ▼
DISPATCHING
  ├─ local success + human paste required → AWAITING_DURABLE_ACK
  ├─ local-only action completed          → ENABLED_READY / ENABLED_IDLE
  ├─ judgment gate                        → JUDGMENT_REQUIRED
  └─ failure                              → BLOCKED

AWAITING_DURABLE_ACK
  ├─ durable worker transition observed   → ACKNOWLEDGED
  │                                         ↓
  │                                   ENABLED_READY / ENABLED_IDLE
  ├─ no ack yet                           → remains AWAITING_DURABLE_ACK
  └─ explicit retry requested             → RETRY_REVIEW

JUDGMENT_REQUIRED
  └─ human resolves gate in operator console → scheduler recomputes

BLOCKED
  └─ deterministic recovery / human repair → scheduler recomputes

any enabled state
  │ toggle OFF
  ▼
DISABLED
```

Turning the bridge OFF never mutates durable task state and never cancels already-running workers.

## 5. OperatorAction contract

Each action is immutable by ID/generation once dispatched.

Minimum fields:

```text
action_id
generation
action_type
priority
created_at
task_id
reasoning_process_id
worker_slot_id
executor_requirement
browser_operation
clipboard_payload_ref
requires_human_paste
durable_ack_condition
stale_after
supersedes_action_id
status
```

Statuses:

```text
QUEUED
CLAIMED_LOCAL
LOCAL_PREPARED
AWAITING_DURABLE_ACK
ACKNOWLEDGED
COMPLETED
FAILED_LOCAL
STALE
SUPERSEDED
BLOCKED
```

## 6. Typed action state machines

### SERVICE_EXISTING

```text
QUEUED
→ CLAIMED_LOCAL
→ verify slot mapping
→ focus worker Firefox window
→ activate exact tab
→ write packet to clipboard
→ LOCAL_PREPARED
→ human Ctrl+V, Enter
→ AWAITING_DURABLE_ACK
→ durable worker state changes as required
→ ACKNOWLEDGED
→ COMPLETED
```

The system does NOT claim to know when Ctrl+V/Enter occurred.
It only knows local preparation succeeded and later durable acknowledgment occurred.

### CREATE_AND_SERVICE

```text
QUEUED
→ CLAIMED_LOCAL
→ ensure dedicated Firefox profile/window
→ create ChatGPT tab
→ bind tab ID to logical worker slot generation
→ focus tab
→ write bootstrap packet
→ LOCAL_PREPARED
→ human Ctrl+V, Enter
→ AWAITING_DURABLE_ACK
→ worker writes durable state
→ ACKNOWLEDGED
→ COMPLETED
```

If the user has not yet completed required manual model/account setup in the new chat, the action remains unacknowledged; the system does not inspect the page to guess.

### RETIRE

```text
QUEUED
→ CLAIMED_LOCAL
→ verify tab mapping generation
→ close/discard tab per policy
→ clear mapping
→ COMPLETED
```

No human paste is required.

### RETIRE_AND_ADVANCE

Composite convenience action executed atomically from the operator perspective:

```text
retire old slot
→ fetch/revalidate next scheduler action
→ prepare next worker
→ clipboard packet
→ human Ctrl+V, Enter
```

If retirement succeeds but next preparation fails, the state records the partial local result and does not replay retirement blindly.

### ROTATE_AND_SERVICE

```text
QUEUED
→ verify old slot
→ retire/park old tab
→ advance slot generation
→ create replacement tab
→ bind new tab
→ focus
→ clipboard resume packet
→ human Ctrl+V, Enter
→ AWAITING_DURABLE_ACK
```

### JUDGMENT_GATE

```text
QUEUED
→ Ctrl+B or console notification
→ open operator console
→ do not modify clipboard unless explicitly requested
→ human decision persisted through owning authority path
→ scheduler recomputes
```

## 7. Ctrl+B dispatch algorithm

On every Ctrl+B press while bridge ON:

1. obtain current orchestrator action snapshot;
2. reject stale local cached action;
3. if no serviceable action:
   - do not focus Firefox;
   - do not modify clipboard;
   - show quiet `0 ready` notification;
4. if a judgment gate has priority:
   - open operator console;
5. otherwise atomically claim one operator action;
6. execute only its permitted local browser operation;
7. if packet required, write clipboard at the last possible moment;
8. focus the prepared worker tab;
9. show a minimal confirmation such as:
   - `instant-general-2 · ready to paste`;
10. persist local dispatch receipt;
11. return control to human.

The next Ctrl+B press fetches fresh scheduler state. It does not assume the previous worker has completed.

## 8. Multiple outstanding workers

A dispatched worker may remain `AWAITING_DURABLE_ACK` while independent workers are serviceable.

Ctrl+B should skip unacknowledged workers unless:
- their durable state explicitly requests another message;
- the user explicitly chooses Retry Last Unconfirmed Dispatch;
- the scheduler supersedes/reissues the action.

This allows batch servicing:

```text
worker A sent/unconfirmed
worker B ready
worker C ready

Ctrl+B → B
Ctrl+B → C
```

without accidentally pasting the same packet twice into A.

## 9. No-ack and mistake recovery

Because v0 does not inspect ChatGPT content, the user can theoretically forget Ctrl+V/Enter or paste into the wrong place.

The system therefore distinguishes:
- LOCAL_PREPARED: tab/clipboard operation succeeded;
- ACKNOWLEDGED: expected durable worker transition observed.

No acknowledgment after a configurable interval is an observation, not proof of failure.

The tray may show:
- `SENT/UNCONFIRMED: 1`

It MUST NOT automatically resend.

Recovery options:
- Retry Last Unconfirmed Dispatch;
- Mark Tab Lost / Rotate;
- Open action details;
- wait longer.

A later durable acknowledgment completes the original action by action ID/generation.

## 10. Firefox/profile lifecycle states

Dedicated profile states:

```text
STOPPED
STARTING
READY
DEGRADED
UNAVAILABLE
```

Worker slot states:

```text
UNALLOCATED
CREATING
ACTIVE
IDLE
DISCARDED
ROTATE_REQUIRED
RETIRE_REQUIRED
LOST
RETIRED
```

Browser lifecycle is local execution state, not workflow authority.

If Firefox is closed and next action needs a worker:
- Ctrl+B may launch the dedicated profile;
- helper waits only for local extension handshake;
- then prepares the exact scheduled action.

If Firefox crashes:
- no workflow state is lost;
- tab mappings are revalidated;
- missing sessions become LOST;
- scheduler decides reuse/recreate/rotate.

## 11. Indicator model

The always-visible primary count is:

`READY MANUAL CYCLES`

Secondary counts:
- NEW
- REUSE
- RETIRE/ROTATE
- SENT_UNCONFIRMED
- GATES
- BLOCKED

Example:

```text
WC 5
Ready: 5
New: 1
Reuse: 4
Sent/unconfirmed: 2
Gates: 0
```

The primary count MUST exclude workers already dispatched and awaiting durable acknowledgment.

## 12. Software architecture boundaries

### Domain/core
Pure state-transition and scheduling logic.
No Firefox, Windows, clipboard, ChatGPT, or GitHub SDK calls.

### Application layer
Use cases:
- GetNextOperatorAction
- ClaimOperatorAction
- RecordLocalDispatch
- RecordDurableAck
- RotateSession
- RetireSession
- ResolveOperatorGate

### Ports
Interfaces:
- OperatorActionStore
- SessionRegistry
- DurableStateObserver
- BrowserPort
- ClipboardPort
- NotificationPort
- HotkeyPort
- ClockPort

### Adapters
- GitHub/control-state adapter
- Firefox WebExtension adapter
- Windows native helper adapter
- system tray adapter
- future supported Chat invocation adapter

Dependency direction:
adapters depend inward on ports/core; core never imports browser/platform logic.

## 13. Testing strategy

### Pure deterministic tests
- every valid/invalid state transition;
- stale generation rejection;
- double hotkey dispatch;
- no-action behavior;
- partial composite action failure;
- durable ack arriving after helper restart;
- disable toggle while action awaiting ack;
- multiple independent ready workers;
- session lost during create/focus;
- retry does not duplicate completed action.

### Adapter contract tests
- native helper ↔ orchestrator;
- native helper ↔ Firefox Native Messaging;
- extension tab create/focus/remove/discard;
- clipboard changed only by explicit hotkey.

### Simulation
Use a local fake ChatGPT page and fake durable worker endpoint before touching the real ChatGPT account.

### Real-account smoke test
Only after:
- page-content automation is absent;
- permissions reviewed;
- current OpenAI terms rechecked;
- local tests pass.

## 14. v0 acceptance criteria

- system tray is the single authoritative master toggle;
- OFF unregisters Ctrl+B and prevents browser/clipboard actions immediately;
- ON never steals focus or clipboard without Ctrl+B;
- routine action requires at most Ctrl+B → Ctrl+V → Enter;
- no tab-title inspection by user;
- no duplicate dispatch from repeated hotkey presses;
- worker submission remains unconfirmed until durable ack;
- helper/Firefox restart is recoverable;
- no ChatGPT DOM/content automation;
- all state-machine transitions are deterministically testable;
- core scheduler is browser/platform independent.
