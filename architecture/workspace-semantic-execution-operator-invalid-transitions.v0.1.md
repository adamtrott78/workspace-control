# Workspace Semantic Execution Operator Invalid Transition Catalog v0.1

Status: **UX-03 DESIGN CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Companions:
- `architecture/workspace-semantic-execution-operator-action-schema.v0.1.json`
- `architecture/workspace-semantic-execution-operator-session-schema.v0.1.json`
- `architecture/workspace-semantic-execution-operator-transition-table.v0.1.json`
- `architecture/workspace-semantic-execution-operator-state-machine.v0.2.md`

## 1. Purpose

List transition and identity patterns that the deterministic operator core must reject.

An invalid transition must fail closed and must not be repaired by guessing from browser/UI state.

## 2. Invalid action transitions

The following are always invalid:

- `QUEUED -> LOCAL_PREPARED` without an atomic claim.
- `QUEUED -> AWAITING_DURABLE_ACK`.
- `QUEUED -> ACKNOWLEDGED`.
- `QUEUED -> COMPLETED` for any persisted action.
- `CLAIMED_LOCAL -> AWAITING_DURABLE_ACK` without a confirmed local-prepared receipt.
- `CLAIMED_LOCAL -> COMPLETED` for an action requiring human paste or durable acknowledgment.
- `LOCAL_PREPARED -> ACKNOWLEDGED` without first arming the exact durable acknowledgment condition.
- `LOCAL_PREPARED -> QUEUED`.
- `AWAITING_DURABLE_ACK -> QUEUED`.
- `AWAITING_DURABLE_ACK -> CLAIMED_LOCAL`.
- `AWAITING_DURABLE_ACK -> FAILED_LOCAL` merely because time elapsed.
- any terminal state -> any nonterminal state.
- `COMPLETED -> *`, `STALE -> *`, `SUPERSEDED -> *`, `FAILED_LOCAL -> *`, `CLAIM_EXPIRED -> *`, or `BLOCKED -> *`.

A retry or recovery creates a new action and preserves its predecessor.

## 3. Invalid claim behavior

Reject:

- claim of an action not in `QUEUED`;
- two successful concurrent claims for the same action generation;
- claim with stale task/session generation;
- claim after `stale_after`;
- claim before `not_before`;
- local browser execution without a valid claim;
- reuse of an expired claim ID;
- helper instance reporting success for a claim owned by another helper instance unless a reviewed recovery protocol proves ownership transfer.

## 4. Invalid acknowledgment behavior

Reject for control progression:

- durable ack with wrong action ID;
- durable ack with wrong task/process/session generation;
- ack from an untrusted/unaccepted provenance path;
- ack that does not satisfy the exact typed `durable_ack_condition`;
- ChatGPT DOM/page state used as durable ack;
- human assertion “I pasted it” used as durable worker completion;
- timing-based inference used as durable worker completion;
- late ack for a `SUPERSEDED`, `STALE`, or other terminal predecessor.

Late/stale acknowledgments may be preserved as evidence but cannot advance current control state.

## 5. Invalid retry behavior

Reject:

- resetting `FAILED_LOCAL` back to `QUEUED`;
- resetting `CLAIM_EXPIRED` back to `QUEUED`;
- resetting `SUPERSEDED` or `STALE`;
- automatic resend because an informational no-ack timeout elapsed;
- reusing an old action ID for a retry;
- retrying before durable state is checked for a late acknowledgment.

Required retry pattern:

```text
predecessor preserved
→ fresh durable state check
→ new action_id
→ fresh generation/eligibility check
→ supersedes_action_id = predecessor
```

## 6. Invalid session identity behavior

Reject:

- treating Firefox `tabId` as durable worker identity;
- treating ChatGPT visible title as worker identity;
- adopting a visually similar tab after restart without a reviewed local binding/recovery protocol;
- reusing a logical session whose continuity is `UNKNOWN` or `LOST`;
- decrementing/reusing a session generation;
- accepting worker output from an older generation as current;
- marking continuity `TRUSTED` merely because the tab loaded successfully.

## 7. Invalid composite behavior

The v0 durable action model intentionally avoids opaque `RETIRE_AND_ADVANCE` or multi-effect mutable actions.

Invalid:
- one durable action that closes an old tab, creates a new worker, sends a packet, and hides which sub-effect failed;
- automatic replay of an entire compound sequence after only one sub-effect failed;
- embedding a stale “next worker” packet behind a local maintenance action without re-querying scheduler state.

Required pattern:

```text
Ctrl+B dispatch transaction
→ claim atomic local-only action
→ complete it
→ fresh scheduler query
→ claim next atomic action
→ stop at first human-interaction action
```

This preserves the one-hotkey UX without sacrificing provenance or partial-failure recovery.

## 8. Invalid bridge-toggle behavior

Turning the bridge OFF must not:
- cancel running workers;
- reset queued durable actions;
- mutate session generations;
- mark SENT/UNCONFIRMED actions failed;
- close Firefox tabs automatically unless a separate authorized action requires it.

Turning the bridge ON must not:
- replay cached actions;
- mutate clipboard;
- focus Firefox
until the user explicitly invokes Ctrl+B.

## 9. Invalid authority behavior

Reject:
- creating OperatorAction solely from model prose without required scheduler/authority checks;
- converting CandidateAction into executable operator work without permission/review gates;
- treating a browser/session capability as execution authority;
- using UX recovery as a reason to widen task scope or permissions.

## 10. UX-03 testing implications

Every invalid category above should become a deterministic unit-test family before implementation promotion.

