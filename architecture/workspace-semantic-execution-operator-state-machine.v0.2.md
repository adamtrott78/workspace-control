# Workspace Semantic Execution Operator State Machine v0.2

Status: **UX-03 IMPLEMENTABLE CONTRACT CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Supersedes for operator-action semantics:
`architecture/workspace-semantic-execution-operator-state-machine.v0.1.md`

Companions:
- `architecture/workspace-semantic-execution-operator-action-schema.v0.1.json`
- `architecture/workspace-semantic-execution-operator-session-schema.v0.1.json`
- `architecture/workspace-semantic-execution-operator-transition-table.v0.1.json`
- `architecture/workspace-semantic-execution-operator-invalid-transitions.v0.1.md`

## 1. Core refinement

v0.2 separates three concepts that v0.1 partially conflated:

1. **OperatorAction** — one durable atomic operator intent.
2. **Hotkey dispatch transaction** — one Ctrl+B invocation that may drain local-only actions and end at one human-interaction action.
3. **Logical Operator Session** — durable slot/generation/continuity identity independent of Firefox tab IDs.

This preserves the desired one-hotkey UX while keeping partial failures and retries explicit.

## 2. Atomic OperatorAction types

Persisted v0 action types:

- `SERVICE_EXISTING`
- `CREATE_AND_SERVICE`
- `RESTORE_AND_SERVICE`
- `DISCARD_SESSION`
- `RETIRE_SESSION`
- `OPEN_JUDGMENT_GATE`
- `OPEN_RECOVERY`

There is intentionally no durable `RETIRE_AND_ADVANCE` action.

“Retire and advance” is an application-level dispatch behavior:

```text
Ctrl+B
→ claim RETIRE_SESSION
→ complete RETIRE_SESSION
→ fresh scheduler query
→ claim SERVICE_EXISTING / CREATE_AND_SERVICE / ...
→ prepare worker
→ return control to human for Ctrl+V + Enter
```

## 3. OperatorAction lifecycle

```text
QUEUED
  │ atomic claim
  ▼
CLAIMED_LOCAL
  ├─ definite local failure ───────────────→ FAILED_LOCAL
  ├─ claim expires ────────────────────────→ CLAIM_EXPIRED
  ├─ generation stale, no effects ─────────→ STALE
  ├─ local outcome unknown ────────────────→ BLOCKED
  │
  └─ confirmed local preparation
       ▼
LOCAL_PREPARED
  ├─ local-only action ────────────────────→ COMPLETED
  ├─ superseded before ack ────────────────→ SUPERSEDED
  │
  └─ durable ack required
       ▼
AWAITING_DURABLE_ACK
  ├─ matching authoritative event
  │      ▼
  │  ACKNOWLEDGED
  │      ▼
  │  COMPLETED
  │
  └─ explicit recovery replacement ────────→ SUPERSEDED

QUEUED may also terminate as:
STALE / SUPERSEDED / BLOCKED
```

Terminal states are immutable:
- COMPLETED
- FAILED_LOCAL
- CLAIM_EXPIRED
- BLOCKED
- STALE
- SUPERSEDED

Retry means a new action.

## 4. Meaning of LOCAL_PREPARED

`LOCAL_PREPARED` means only:

- required browser operations succeeded;
- the intended target was prepared;
- clipboard write succeeded if required;
- local idempotency receipts exist.

It does **not** mean:
- Ctrl+V happened;
- Enter happened;
- ChatGPT received the packet;
- a model is reasoning.

Because those content interactions are intentionally not observed in v0.

For a worker-service action, the application immediately arms the exact durable acknowledgment condition and enters `AWAITING_DURABLE_ACK`.

That state means “we are waiting for authoritative evidence after successful local preparation,” not “we know the message was sent.”

## 5. Claim semantics

A claim is a durable CAS operation:

```text
QUEUED + current generation + eligible
    → CLAIMED_LOCAL(claim_id, helper_instance_id, expires_at)
```

Properties:
- only one helper may own a claim;
- local browser effects require a valid claim;
- claim expiry never automatically requeues;
- if local effects cannot be proven absent after claim loss, fail closed;
- a replacement action may be created after reconciliation.

This avoids duplicate tab creation/closure after helper crashes.

## 6. Idempotent local-plan semantics

Every local-plan step carries an `idempotency_key`.

Browser/helper adapters must be able to answer whether a step:
- was not applied;
- was applied;
- has unknown outcome.

Examples:
- `CREATE_TAB` must not create two tabs for the same action/step if retried locally;
- `CLOSE_TAB` must treat already-closed exact managed target as idempotent success where identity is proven;
- `WRITE_CLIPBOARD` is repeatable only while the same action remains current;
- raw tab IDs never substitute for logical slot + generation.

## 7. Hotkey dispatch transaction

One Ctrl+B invocation executes the following application algorithm:

```text
1. Verify bridge ON.
2. Query fresh operator state.
3. Atomically claim highest-priority eligible action.
4. Execute local_plan.
5. Record local result.

6. If action is local-only and post_local_success=COMPLETE_AND_REQUERY:
      complete action;
      fresh query;
      repeat from step 3.

7. If action requires PASTE_AND_SUBMIT:
      arm durable ack;
      focus prepared tab;
      return to human.

8. If action opens judgment/recovery UI:
      complete local open action;
      stop.

9. If no action / blocked / safety cap:
      stop without additional focus or clipboard mutation.
```

This means a single Ctrl+B may transparently:
- retire one obsolete tab;
- discard another idle tab;
- then focus/create the actual worker;
- load its packet;

while the operator still experiences only:

```text
Ctrl+B
Ctrl+V
Enter
```

## 8. Queue ordering

The orchestrator assigns:
- `priority_rank` — lower is earlier;
- `queue_sequence` — deterministic monotonic tie-break.

The local helper never invents semantic priority.

Final deterministic order:
1. lowest `priority_rank`;
2. lowest `queue_sequence`;
3. lexicographically smallest `action_id`.

Priority assignment policy itself remains an orchestrator concern and may consider task dependencies, recovery scope, judgment gates, and independent ready work.

## 9. Retry semantics

No dispatched/terminal action is reset.

Retry flow:

```text
durable state re-check
→ determine whether predecessor already acknowledged
→ if still eligible, create replacement action
→ new action_id
→ current generation
→ supersedes_action_id = predecessor
→ predecessor becomes SUPERSEDED when appropriate
```

No-ack timeouts are informational only.

## 10. Late acknowledgment semantics

Only `AWAITING_DURABLE_ACK` can advance from a durable worker acknowledgment.

If an acknowledgment arrives for:
- SUPERSEDED;
- STALE;
- FAILED_LOCAL;
- CLAIM_EXPIRED;
- BLOCKED;
- COMPLETED;

the event may be retained as evidence but cannot advance current control state.

This prevents old tabs from winning after recovery/rotation.

## 11. Logical session contract

Logical session identity is:

```text
worker_slot_id + generation
```

The durable session record contains:
- executor requirement;
- observed executor identity ref when available;
- role;
- task/process affinity;
- continuity state;
- lifecycle intent;
- last acknowledged checkpoint;
- approximate context budget;
- rotation reason.

It does not contain Firefox `tabId` or `windowId`.

Continuity states:
- NOT_ESTABLISHED
- TRUSTED
- UNKNOWN
- LOST

A session with continuity UNKNOWN/LOST is not reusable.

Generation is monotonic and never reused.

## 12. Authentication-refresh consequence

If reauthentication refreshes/invalidates existing worker tabs:

```text
affected logical sessions
→ continuity UNKNOWN
→ no reuse
→ session broker selects rotate/recreate
→ new generation(s)
→ fresh worker packets from durable state
```

Exact detection and operator recovery choreography remain UX-07 work.

UX-03 establishes the control invariant: no old-generation worker can later advance current state.

## 13. Action-type contracts

### SERVICE_EXISTING
- human: PASTE_AND_SUBMIT
- ack: DURABLE_WORKER_TRANSITION
- local plan: activate exact managed worker + clipboard write
- post local: AWAIT_DURABLE_ACK

### CREATE_AND_SERVICE
- human: PASTE_AND_SUBMIT
- ack: DURABLE_WORKER_TRANSITION
- local plan: ensure profile, create exact managed tab, bind locally, clipboard write
- post local: AWAIT_DURABLE_ACK

### RESTORE_AND_SERVICE
- human: PASTE_AND_SUBMIT
- ack: DURABLE_WORKER_TRANSITION
- local plan: reload/restore exact managed tab, activate, clipboard write
- post local: AWAIT_DURABLE_ACK

### DISCARD_SESSION
- human: NONE
- ack: NONE
- post local: COMPLETE_AND_REQUERY

### RETIRE_SESSION
- human: NONE
- ack: NONE
- post local: COMPLETE_AND_REQUERY

### OPEN_JUDGMENT_GATE
- human: SUBSTANTIVE_DECISION
- ack for this UI-opening action: NONE
- post local: COMPLETE_AND_STOP
- judgment itself completes through the owning authority path, not by mutating this action.

### OPEN_RECOVERY
- human: RECOVERY_INTERACTION
- ack for UI-opening action: NONE
- post local: COMPLETE_AND_STOP
- recovery may generate new session/actions afterward.

## 14. Bridge OFF semantics

Turning the bridge OFF:
- unregisters the global hotkey locally;
- does not mutate queued action state;
- does not cancel SENT/UNCONFIRMED workers;
- does not alter session generation;
- does not close tabs;
- does not change clipboard.

Turning it ON:
- only registers the local operator command;
- does not dispatch until Ctrl+B.

## 15. Deterministic test obligations

UX-03 contracts imply tests for:
- double claim;
- stale generation;
- expired claim;
- helper crash before receipt;
- helper crash after local effect with unknown receipt;
- duplicate CREATE_TAB step;
- duplicate RETIRE_SESSION;
- local-only drain followed by service;
- local-only partial failure;
- no-ack informational timeout;
- explicit retry after late ack;
- stale old-generation ack;
- session continuity UNKNOWN;
- bridge OFF/ON with queued work;
- judgment/recovery actions stopping dispatch loop.

## 16. UX-03 acceptance assessment

The v0.2 contract now specifies:
- atomic action types;
- exact statuses;
- deterministic claim semantics;
- monotonic terminal behavior;
- local preparation vs durable acknowledgment;
- retry-by-replacement;
- late-ack handling;
- logical session generation;
- one-hotkey local-only draining;
- invalid transition classes.

The state machine can be implemented and unit-tested without Firefox or ChatGPT.

