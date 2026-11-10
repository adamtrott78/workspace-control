# Workspace Semantic Execution Operator Journeys v0.1

Status: **UX-01 JOURNEY BASELINE / DESIGN CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Companions:
- `architecture/workspace-semantic-execution-operator-ux-requirements.v0.1.md`
- `architecture/workspace-semantic-execution-operator-ux-metrics.v0.1.json`
- `architecture/workspace-semantic-execution-operator-flow-catalog.v0.1.json`

## 1. Purpose

Define every currently known operator-visible journey before implementation.

Each journey specifies:
- trigger;
- operator-visible state;
- Ctrl+B behavior;
- focus effect;
- clipboard effect;
- human action;
- durable acknowledgment;
- recovery ownership;
- failure-closed behavior.

The catalog deliberately does **not** solve later-slice mechanics such as exact session-rotation algorithms, login-refresh detection, hotkey collision policy, tray wireframes, or security implementation details. It defines what the operator experience must become.

## 2. Journey classes

### ROUTINE
The operator remains in the low-attention service loop:

```text
Ctrl+B
Ctrl+V
Enter
```

### LOCAL_ONLY
The operator invokes Ctrl+B, but no paste is required because the queued action is purely local browser/session maintenance.

Whenever safe, LOCAL_ONLY maintenance SHOULD be fused with the next ROUTINE action so it does not consume an extra operator cycle.

### NO_WORK
No serviceable mechanical work exists. Ctrl+B does not disturb the user's current application or clipboard.

### RECOVERY
Normal routing cannot continue until local/session continuity is re-established.

### JUDGMENT
A substantive human choice or authority decision is required. The routine paste rhythm stops explicitly.

### BLOCKED
The bridge cannot safely act and must fail closed.

## 3. Normal operation journeys

### J-001 — Bridge disabled

**Class:** NO_WORK

**Trigger:** Native helper is running but `Workspace Worker Bridge = OFF`.

**Visible state:** Tray shows bridge OFF and pending counts may continue to update.

**Ctrl+B:** Not intercepted by Workspace Control. The foreground application receives its normal Ctrl+B behavior.

**Focus:** No change.

**Clipboard:** No change.

**Human action:** None unless the operator chooses to enable the bridge from the tray.

**Durable acknowledgment:** Not applicable.

**Recovery owner:** UX-06 tray/console design.

---

### J-002 — Bridge enabled, zero ready actions

**Class:** NO_WORK

**Trigger:** Bridge ON; `READY_MANUAL_CYCLES = 0`.

**Visible state:** Tray/badge shows 0 ready.

**Ctrl+B:** Helper queries fresh scheduler state, receives NO_ACTION, returns a quiet local indication.

**Focus:** MUST remain on current application.

**Clipboard:** MUST remain unchanged.

**Human action:** None.

**Durable acknowledgment:** Not applicable.

---

### J-003 — Reuse existing active worker

**Class:** ROUTINE

**Trigger:** Scheduler selects a ready packet whose compatible worker slot maps to a live Firefox tab.

**Visible state before service:** READY count > 0; worker identity need not be visible unless console/debug details are opened.

**Ctrl+B:**
1. claim fresh OperatorAction;
2. focus dedicated Firefox worker window;
3. activate exact mapped worker tab;
4. write exact worker packet to clipboard;
5. indicate `READY TO PASTE`.

**Focus:** Correct worker tab.

**Clipboard:** Replaced with exact packet at dispatch time.

**Human action:** `Ctrl+V`, `Enter`.

**Durable acknowledgment:** Expected worker-authored durable state transition for that action/generation.

**After dispatch:** Action becomes SENT/UNCONFIRMED; repeated Ctrl+B may service independent workers.

---

### J-004 — Reuse discarded/parked worker

**Class:** ROUTINE

**Trigger:** Scheduler selects an existing compatible worker whose Firefox tab is known but unloaded/discarded.

**Ctrl+B:**
1. reactivate/reload mapped tab;
2. wait only for local browser readiness required for manual paste;
3. focus it;
4. load packet to clipboard.

**Focus:** Restored worker tab.

**Clipboard:** Exact packet.

**Human action:** `Ctrl+V`, `Enter`.

**Durable acknowledgment:** Normal durable worker transition.

**Detailed reload/readiness policy:** UX-04/UX-09.

---

### J-005 — Create new worker while Firefox is already running

**Class:** ROUTINE

**Trigger:** Scheduler requires a new worker slot; dedicated Firefox profile/window is healthy.

**Ctrl+B:**
1. create a new ChatGPT tab;
2. bind browser tab identity to a new logical session generation;
3. focus tab;
4. load bootstrap/resume packet.

**Focus:** Newly created tab.

**Clipboard:** Bootstrap/resume packet.

**Human action:** `Ctrl+V`, `Enter`.

**Durable acknowledgment:** First valid worker transition under the new slot/generation.

**Constraint:** No DOM automation is used to choose models, authenticate, paste, or submit.

---

### J-006 — Create first worker while Firefox is stopped

**Class:** ROUTINE with cold-start preparation

**Trigger:** Scheduler requires a Chat worker and dedicated Firefox profile is STOPPED.

**Ctrl+B:**
1. launch dedicated `WorkspaceWorkers` Firefox profile;
2. establish extension/native-helper handshake;
3. create or recover designated worker window;
4. create target ChatGPT worker tab;
5. bind slot generation;
6. focus tab;
7. load packet.

**Focus:** New worker tab after local startup.

**Clipboard:** Exact packet.

**Human action:** `Ctrl+V`, `Enter`.

**Durable acknowledgment:** First worker durable transition.

**Performance ownership:** UX-09.

---

### J-007 — Multiple independent workers ready

**Class:** ROUTINE batch

**Trigger:** Several worker actions are simultaneously serviceable.

**Visible state:** READY count reflects only serviceable manual cycles.

**Ctrl+B:** Claims exactly one fresh action according to scheduler priority.

**Human action:** `Ctrl+V`, `Enter`.

**Next Ctrl+B:** Fetches fresh state and services another independent action; it MUST NOT blindly revisit the previous SENT/UNCONFIRMED worker.

**Operator requirement:** No manual queue ordering or worker selection.

---

### J-008 — Previous worker sent/unconfirmed, another worker ready

**Class:** ROUTINE batch

**Trigger:** Worker A is SENT/UNCONFIRMED; worker B is READY.

**Ctrl+B:** Service B.

**Clipboard:** B packet only.

**Focus:** B worker tab.

**Human action:** `Ctrl+V`, `Enter`.

**Forbidden:** Automatic resend to A solely because A has not yet acknowledged.

---

### J-009 — Worker durable result arrives while operator is doing something else

**Class:** background machine event, no operator interruption

**Trigger:** Durable worker transition arrives.

**Effect:** Orchestrator validates and recomputes ready queue.

**Focus:** No change.

**Clipboard:** No change.

**Visible state:** Tray/badge counts update.

**Human action:** None until the operator chooses to press Ctrl+B.

---

### J-010 — Worker requests external wait

**Class:** background machine flow

**Trigger:** Worker persists WAITING_EXTERNAL/request state.

**Effect:** Deterministic control plane services or observes the authorized external event.

**Focus:** No change.

**Clipboard:** No change.

**Human action:** None while waiting.

**When result is durably published:** Scheduler may create a new ready manual cycle.

**Invariant:** No model/manual polling just to ask whether the external event finished.

## 4. Session maintenance journeys

### J-011 — Retire completed worker with no immediate next service action

**Class:** LOCAL_ONLY

**Trigger:** Scheduler marks a worker RETIRE_REQUIRED and no higher-priority routine packet is currently serviceable.

**Ctrl+B:** Verify slot generation, close/remove designated worker tab, clear local mapping.

**Focus:** SHOULD remain on current application if Firefox need not be shown.

**Clipboard:** No change.

**Human action:** None.

**Optimization:** This maintenance action SHOULD usually be deferred/fused with a later service action unless RAM/session policy requires prompt retirement.

---

### J-012 — Retire old worker and immediately advance

**Class:** ROUTINE composite

**Trigger:** Obsolete worker must be retired and another worker packet is serviceable.

**Ctrl+B:**
1. retire exact old slot/generation;
2. fetch/revalidate next scheduler action;
3. focus/create next worker;
4. load next packet.

**Focus:** Next serviceable worker.

**Clipboard:** Next packet.

**Human action:** `Ctrl+V`, `Enter`.

**Partial-failure rule:** Retirement success is recorded independently; it is never replayed blindly if next-worker preparation fails.

---

### J-013 — Rotate worker due to context/session policy

**Class:** ROUTINE composite

**Trigger:** Session broker decides current slot requires rotation.

**Ctrl+B:**
1. retire/park old tab according to policy;
2. advance logical session generation;
3. create replacement tab;
4. bind replacement;
5. load durable resume packet;
6. focus replacement.

**Human action:** `Ctrl+V`, `Enter`.

**Operator requirement:** User does not decide whether rotation is needed.

**Detailed policy owner:** UX-04.

---

### J-014 — User manually closes an idle/active worker tab

**Class:** RECOVERY

**Trigger:** Extension/browser inventory no longer contains mapped tab.

**Visible state:** Slot becomes LOST or mapping-invalid.

**Ctrl+B:** MUST NOT guess another tab by title. Scheduler/session broker decides whether to recreate/rotate or block.

**Clipboard:** Only changed if the resulting recovery action produces a valid replacement worker packet.

**Human action:** Ideally remains `Ctrl+B → Ctrl+V → Enter` if replacement is safe.

**Detailed recovery:** UX-07.

## 5. Authentication and continuity journeys

### J-015 — New worker tab opens normally, account remains authenticated

**Class:** ROUTINE

This is the happy-path form of J-005/J-006.

No additional operator steps beyond `Ctrl+B → Ctrl+V → Enter`.

---

### J-016 — New worker tab requires ChatGPT reauthentication before paste

**Class:** RECOVERY

**Trigger:** Newly created ChatGPT tab presents a login/reauthentication requirement.

**Constraint:** v0 cannot detect this from ChatGPT DOM/content automatically.

**Required UX property:** The system must have a bounded way for the operator to report/enter recovery without reconstructing scheduler state manually.

**Clipboard:** The intended packet may already be present, but must not be considered delivered.

**Durable state:** Action remains unacknowledged.

**Detailed operator choreography:** Deferred to UX-07.

**Design goal for UX-07:** return to one-hotkey/paste service as quickly as possible after the user completes unavoidable authentication.

---

### J-017 — Login refreshes/invalidates all existing worker tabs

**Class:** RECOVERY / continuity-loss event

**Trigger:** Reauthentication causes multiple/all existing ChatGPT worker tabs to refresh, reload, sign out/in, or otherwise lose trusted continuity.

**Required system behavior:**
- mark affected local session continuity UNKNOWN until revalidated/replaced;
- do not assume persistent-chat context survived;
- do not use tab titles as evidence;
- do not replay already completed durable work;
- recover every affected process from its durable checkpoint;
- advance/rotate generations where continuity cannot be proven;
- rebuild serviceable worker actions.

**Operator target:** after unavoidable login itself, recovery should be driven by repeated use of the same scheduler hotkey rather than manual tab triage.

**Clipboard:** No automatic background mutation.

**Detailed detection/recovery algorithm:** UX-04 + UX-07.

---

### J-018 — Existing worker tab is visibly logged out when focused

**Class:** RECOVERY

**Trigger:** Operator presses Ctrl+B, lands on assigned tab, but manual visual observation shows account is logged out.

**System knowledge:** The bridge cannot know this from page contents in v0.

**Required user escape hatch:** A minimal explicit recovery command must exist; exact control is deferred to UX-07/UX-06.

**Forbidden:** User manually editing task state or deciding which durable checkpoint to use.

---

### J-019 — Persistent chat continuity lost but durable task state is intact

**Class:** RECOVERY

**Trigger:** Session loss, logout, browser refresh, or manual report means chat continuity cannot be trusted.

**Required behavior:** Session broker treats conversation as disposable cache and creates a replacement from durable semantic/task state.

**Operator target:** recovery packet is prepared automatically; operator interaction returns to `Ctrl+B → Ctrl+V → Enter`.

## 6. Dispatch acknowledgment and retry journeys

### J-020 — Packet prepared, user has not pasted/submitted yet

**Class:** SENT/UNCONFIRMED local-prepared state

**Trigger:** Ctrl+B completed browser focus + clipboard write.

**System knowledge:** LOCAL_PREPARED only.

**System MUST NOT claim:** message sent or worker running.

**Next Ctrl+B:** May service another independent READY action; must not automatically duplicate current packet.

---

### J-021 — Packet pasted/submitted, worker has not acknowledged yet

**Class:** SENT/UNCONFIRMED

**Trigger:** Human performed Ctrl+V/Enter, but no durable worker state change exists yet.

**System knowledge:** Still cannot distinguish this from J-020 using prohibited page/keystroke observation.

**Behavior:** Wait for durable acknowledgment; continue servicing independent ready workers.

**No auto resend.**

---

### J-022 — Durable acknowledgment arrives

**Class:** machine completion transition

**Trigger:** Expected worker-authored durable state change with correct action/generation.

**Effect:** Mark action ACKNOWLEDGED/COMPLETED as appropriate; update session affinity/checkpoint; recompute queue.

**Operator interruption:** None.

---

### J-023 — No acknowledgment for an extended period

**Class:** RECOVERY observation, not automatic failure

**Trigger:** Action remains SENT/UNCONFIRMED beyond configured informational threshold.

**Visible state:** SENT_UNCONFIRMED count may increase; optional quiet warning.

**Forbidden:** Automatic resend.

**Available recovery paths:** explicit Retry Last Unconfirmed, rotate/lost-session workflow, or continue waiting.

**Detailed threshold/UI:** UX-06/UX-07.

---

### J-024 — Explicit retry of unconfirmed dispatch

**Class:** RECOVERY

**Trigger:** Operator or scheduler-approved recovery selects retry.

**Required behavior:** Revalidate action generation and durable state first. If already acknowledged/superseded, retry becomes no-op/rejected. If still valid, prepare the exact retry action.

**Duplicate prevention:** Required.

**Detailed semantics:** UX-03/UX-07.

## 7. Firefox/native-helper lifecycle journeys

### J-025 — Native helper starts with Windows, bridge default OFF

**Class:** NO_WORK/local startup

**Trigger:** Windows login/startup.

**Visible state:** Tray helper available; OFF means Ctrl+B remains normal.

**Focus/clipboard:** No changes.

**Recommended initial test default:** OFF.

---

### J-026 — Native helper crashes/restarts

**Class:** RECOVERY

**Trigger:** Helper process failure/restart.

**Required behavior:** Restore local service state from orchestrator/session registry; do not assume previous hotkey dispatch completed merely because local helper state disappeared.

**Ctrl+B after recovery:** Uses fresh scheduler state.

**Detailed recovery:** UX-07.

---

### J-027 — Firefox crashes/restarts

**Class:** RECOVERY

**Required behavior:** Browser inventory is re-established; mapped sessions become revalidated, LOST, or replacement-required. Durable task state remains intact.

**Operator target:** eventual repeated Ctrl+B recovery, no manual tab-title reconstruction.

---

### J-028 — Extension/native-messaging connection unavailable

**Class:** BLOCKED

**Ctrl+B:** Must fail closed before clipboard mutation if browser preparation cannot be completed.

**Focus:** Do not send user to an unknown/incorrect tab.

**Visible state:** BLOCKED with concise reason.

**Recovery:** Reconnect/restart component via UX-07-defined path.

---

### J-029 — Wrong Firefox profile is open

**Class:** RECOVERY/BLOCKED

**Trigger:** Ordinary Firefox profile is running but dedicated WorkspaceWorkers profile/window is absent or incorrect.

**Ctrl+B:** Must target/launch the dedicated profile; must not adopt arbitrary ChatGPT tabs from another profile.

**Detailed profile discovery/launch:** UX-02/UX-12.

## 8. Clipboard and focus journeys

### J-030 — User has valuable clipboard content before service

**Class:** ROUTINE

**Trigger:** Ctrl+B on a valid service action.

**Behavior:** Packet intentionally replaces clipboard as specified by UX-00.

**Potential restore feature:** Deferred to UX-05; no automatic clipboard surveillance.

**User expectation:** Ctrl+B is the explicit consent point for clipboard replacement.

---

### J-031 — User presses Ctrl+B rapidly twice

**Class:** concurrency/idempotency journey

**Required behavior:** Second press cannot claim or dispatch the same action generation twice.

Possible UX outcome:
- first dispatch wins;
- second press obtains the next independently serviceable action or receives a local busy/no-action response.

**Exact debounce/claim behavior:** UX-03/UX-05.

---

### J-032 — User presses Ctrl+B while Firefox cold-start is still in progress

**Class:** LOCAL_BUSY

**Required behavior:** No duplicate Firefox/profile launch and no duplicate action claim.

**Possible outcome:** quiet `PREPARING` indication or service another action only if architecture proves safe.

**Detailed concurrency:** UX-03/UX-05.

## 9. Scheduler, blocking, and judgment journeys

### J-033 — Real human authority/judgment gate is next

**Class:** JUDGMENT

**Ctrl+B:** Open operator console to exact gate.

**Clipboard:** Do not overwrite with a worker packet.

**Focus:** Operator console.

**Human action:** Make the substantive decision through the owning authority path.

**After decision:** Scheduler recomputes.

---

### J-034 — Mechanical work exists but is authority-blocked

**Class:** BLOCKED

**Trigger:** Candidate work lacks required permission/review/authority.

**READY_MANUAL_CYCLES:** Must exclude blocked action.

**Ctrl+B:** Services another eligible action if one exists; otherwise quiet BLOCKED/no-action indication.

**Invariant:** The bridge cannot convert availability into authority.

---

### J-035 — Orchestrator unreachable

**Class:** BLOCKED

**Ctrl+B:** Fail closed.

**Focus:** No browser focus change.

**Clipboard:** No change.

**Visible state:** Concise `ORCHESTRATOR UNREACHABLE`.

**Forbidden:** Use stale local queue as authority.

---

### J-036 — Scheduler action became stale between indicator update and Ctrl+B

**Class:** normal race recovery

**Ctrl+B:** Fetch fresh state; stale cached count/action is discarded.

**Outcome:** Claim new valid action or NO_ACTION.

**Operator:** No manual recovery.

## 10. Model/executor mismatch journeys

### J-037 — Scheduler requires different role/model/toolset than current slot

**Class:** ROUTINE or RECOVERY depending on policy

**Required behavior:** Session broker selects CREATE/ROTATE rather than silently reusing incompatible session.

**Operator target:** same `Ctrl+B → Ctrl+V → Enter` rhythm.

**Detailed compatibility matrix:** UX-04.

---

### J-038 — Model configuration cannot be automatically verified

**Class:** RECOVERY/JUDGMENT-LIKE setup condition

**Constraint:** v0 avoids ChatGPT DOM inspection.

**Required behavior:** Do not fabricate executor identity. Exact method for manual setup/confirmation is deferred to UX-04/UX-07/UX-08.

**Routine operation goal:** Once a slot is established, model-selection decisions should not recur each turn.

## 11. RAM/resource journeys

### J-039 — Too many live worker tabs under session policy

**Class:** LOCAL_ONLY maintenance / ROUTINE composite

**Trigger:** Session pool exceeds active-resource policy.

**Behavior:** Scheduler/session broker selects discard/retire candidates based on durable slot state; user does not inspect memory or choose tabs.

**Ctrl+B:** May fuse maintenance with next routine action.

**Detailed resource policy:** UX-04/UX-09.

---

### J-040 — Discarded worker becomes next scheduled action

Covered by J-004; no additional operator workflow is required.

## 12. End-of-batch journeys

### J-041 — Last ready worker dispatched

**Class:** ROUTINE

**After Ctrl+B → Ctrl+V → Enter:** READY count may reach 0 while SENT_UNCONFIRMED remains > 0.

**Meaning:** There is nothing else the operator can mechanically service now.

**Operator:** Return to normal work.

---

### J-042 — All current work complete

**Class:** NO_WORK

**Visible state:** READY 0; SENT_UNCONFIRMED 0; GATES 0; BLOCKED 0.

**Focus/clipboard:** No changes.

**Operator:** Nothing to do.

## 13. Journey-level invariants

Across all journeys:

1. The user never selects the next worker manually.
2. The user never identifies workers by ChatGPT tab title.
3. The user never manually relays durable system state.
4. Ctrl+B never causes background page-content automation.
5. Clipboard changes only from explicit service dispatch requiring a packet.
6. Focus changes only from explicit operator command.
7. SENT/UNCONFIRMED is not treated as worker completion.
8. Unknown continuity fails closed.
9. Login/session loss does not erase task progress.
10. Recovery is driven from durable state, not chat-memory reconstruction.
11. Blocked/judgment work is not counted as routine READY work.
12. Routine normal-path UX remains Ctrl+B → Ctrl+V → Enter.

## 14. UX-01 acceptance assessment

The current known operator-visible domain is represented across:
- enable/disable/no-work;
- existing worker reuse;
- discarded worker reuse;
- new worker creation;
- cold Firefox startup;
- multi-worker batches;
- external waits;
- retire/rotate/composite maintenance;
- lost tabs;
- authentication/login refresh;
- persistent continuity loss;
- unconfirmed dispatch/retry;
- helper/Firefox/extension failures;
- clipboard/focus races;
- scheduler races;
- authority/judgment gates;
- model incompatibility;
- memory/session pool pressure;
- batch completion.

No journey requires the operator to inspect tab titles or manually reconstruct scheduler state.

Detailed algorithms remain intentionally delegated to UX-03 through UX-09.

