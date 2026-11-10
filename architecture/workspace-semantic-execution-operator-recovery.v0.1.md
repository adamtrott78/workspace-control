# Workspace Semantic Execution Operator Recovery UX v0.1

Status: **UX-07 RECOVERY DESIGN CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Companions:
- `architecture/workspace-semantic-execution-operator-recovery-fmea.v0.1.json`
- `architecture/workspace-semantic-execution-operator-recovery-state-machine.v0.1.md`
- `architecture/workspace-semantic-execution-operator-recovery-signal-catalog.v0.1.json`
- `architecture/workspace-semantic-execution-session-broker.v0.1.md`
- `architecture/workspace-semantic-execution-hotkey-clipboard-contract.v0.1.md`

## 1. Recovery objective

Failures in the human-launched Chat bridge must degrade **convenience**, not durable task correctness.

The recovery UX must preserve this invariant:

> After unavoidable recovery interaction, the operator returns to the same Ctrl+B → Ctrl+V → Enter service rhythm without manually reconstructing worker identity, task state, SHAs, prompts, or checkpoints.

Persistent chat continuity is useful but disposable.

## 2. Recovery principles

1. Durable task/process/action/session state survives local component loss.
2. Recovery never infers authority from browser state.
3. Unknown side effects or continuity fail closed.
4. No automatic resend of an unacknowledged worker packet.
5. Old session generations are fenced before replacement work is issued.
6. Recovery is scoped as narrowly as evidence permits.
7. Global/auth-domain failures may freeze all Chat worker service.
8. Session/action-scoped failures should not unnecessarily block independent workers.
9. Browser-chrome lifecycle signals may classify continuity risk; ChatGPT page content is never inspected.
10. User-authentication itself remains manual.
11. The user is never asked to inspect all worker tabs or decide which checkpoint is current.

## 3. Recovery scopes

### ACTION_SCOPED

One OperatorAction is uncertain.

Examples:
- packet staged but user may not have pasted;
- local claim outcome unknown;
- late acknowledgment ambiguity.

Independent sessions remain serviceable.

### SESSION_SCOPED

One logical worker generation is unavailable or untrusted.

Examples:
- its tab was manually closed;
- its exact local binding is lost;
- its conversation continuity is known lost.

Independent sessions remain serviceable.

### AUTH_DOMAIN_SCOPED

The dedicated `WorkspaceWorkers` authentication domain may have been refreshed/re-authenticated.

All logical sessions in that browser auth domain become continuity-suspect.

Routine Chat worker reuse is frozen until reconciliation/generation fencing is complete.

### LOCAL_BRIDGE_GLOBAL

The helper/browser adapter cannot safely service any worker.

Examples:
- native helper integrity failure;
- Firefox extension unavailable;
- orchestrator unreachable.

No manual Chat dispatch proceeds until the blocking dependency recovers.

## 4. Recovery severity

### NONBLOCKING

Affected action/session is isolated; independent READY work may continue.

### BLOCKING_CHAT

All Chat Instant browser service is frozen, but deterministic/local/API executors may continue.

### BLOCKING_OPERATOR_BRIDGE

No operator bridge action may be claimed.

### JUDGMENT_REQUIRED

Recovery itself needs a substantive user decision rather than mechanical repair.

## 5. Recovery control states

```text
HEALTHY
  │ anomaly signal
  ▼
SUSPECTED
  │ classify scope / freeze affected work
  ▼
FROZEN
  │ durable reconciliation
  ▼
RECONCILING
  ├─ automatic local repair possible ─────→ REBUILDING
  ├─ manual authentication required ──────→ WAITING_USER_AUTH
  ├─ explicit operator report needed ─────→ WAITING_USER_SIGNAL
  └─ cannot safely proceed ────────────────→ BLOCKED

WAITING_USER_AUTH
  │ browser-chrome auth-return signal / reviewed fallback
  ▼
RECONCILING

WAITING_USER_SIGNAL
  │ explicit recovery signal
  ▼
RECONCILING

REBUILDING
  │ replacement generations/actions created
  ▼
READY_TO_RESUME
  │ next Ctrl+B
  ▼
HEALTHY

BLOCKED
  │ dependency repaired / explicit safe recovery
  ▼
RECONCILING
```

For scoped recoveries, HEALTHY work outside the affected scope may continue in parallel.

## 6. Ctrl+B behavior during recovery

### No blocking recovery

Ctrl+B services the highest-priority eligible routine action normally.

Scoped recovery remains visible in the tray/console.

### ACTION/SESSION-scoped nonblocking recovery

If independent READY work exists:
- Ctrl+B may service that independent work;
- recovery action remains queued.

If no independent READY work exists:
- Ctrl+B opens/focuses the exact recovery surface.

### AUTH_DOMAIN_SCOPED or LOCAL_BRIDGE_GLOBAL recovery

Ctrl+B MUST NOT stage a worker packet.

It instead:
- advances any safe deterministic/local recovery step;
- or focuses the exact authentication/recovery surface;
- or shows the blocking condition.

Clipboard remains unchanged until a newly valid post-recovery service action exists.

### READY_TO_RESUME

The next Ctrl+B may:
- drain retirement/cleanup actions;
- create/rebuild the next valid worker generation;
- stage its resume/bootstrap packet;
- return the operator to Ctrl+V + Enter.

## 7. Authentication/reauthentication recovery

This is the primary exceptional path.

### 7.1 Detection model

v0 may use **browser-chrome lifecycle/navigation metadata**, subject to UX-08 permission review and UX-12 API validation.

Permitted design signals may include:
- a managed worker tab navigates from the normal ChatGPT worker origin into a recognized authentication origin;
- a managed tab is replaced/reloaded as part of browser-level auth navigation;
- multiple managed worker tabs receive correlated top-level navigation/reload events after authentication begins;
- Firefox profile/window lifecycle changes invalidate local bindings.

This is not ChatGPT content inspection.

The system MUST NOT:
- read login-page DOM;
- read conversation text;
- inspect hidden network state;
- infer success from visual page content.

If automatic browser-chrome detection is unavailable or ambiguous, an explicit operator recovery signal remains the fallback.

### 7.2 Entering auth recovery

On a strong auth-domain signal:

1. create one profile-scoped recovery incident;
2. freeze new reuse claims for all `WorkspaceWorkers` logical sessions;
3. mark affected continuity `UNKNOWN`;
4. preserve current durable task state;
5. re-check each outstanding OperatorAction exactly once against durable acknowledgments;
6. accept any acknowledgment that already exists;
7. leave unresolved actions unresent;
8. present/focus the authentication tab when operator attention is required.

### 7.3 User action

The operator completes unavoidable login manually.

No password, MFA token, or authentication secret is handled by Workspace Control.

### 7.4 Detecting return from authentication

Preferred design:
- browser-chrome metadata reports that the managed authentication flow has returned to an expected ChatGPT origin/profile context.

This means only:
`authentication flow appears to have returned`.

It does **not** prove old conversation continuity.

If this browser-chrome signal cannot be implemented safely, the operator console provides one explicit keyboard-accessible confirmation such as:
`Authentication complete — continue recovery`.

The fallback must not require inspecting individual worker tabs.

### 7.5 Rebuilding after auth

After auth-return:

1. re-read durable state;
2. supersede unresolved old-generation worker actions;
3. advance all affected logical session generations;
4. keep old tabs fenced/untrusted;
5. create replacement logical sessions from each last acknowledged durable checkpoint;
6. queue cleanup of old local tabs;
7. queue fresh service actions according to scheduler priority.

The operator does not manually decide which sessions survived.

### 7.6 Target operator experience

Ideal case:

```text
Ctrl+B
→ new worker requires login
→ login UI appears
→ user logs in
→ system detects auth return
→ old generations fenced/rebuilt automatically
→ Ctrl+B
→ exact replacement worker + packet
→ Ctrl+V
→ Enter
```

Subsequent replacements are serviced by repeated:

```text
Ctrl+B → Ctrl+V → Enter
```

until the READY count returns to zero.

## 8. Native helper crash/restart

Detection:
- helper process restart/startup identity differs from durable/local receipt state.

Recovery:

1. hotkey starts unregistered until helper initializes;
2. query fresh durable operator state;
3. reconcile old helper claims;
4. for each expired/in-flight claim:
   - if no local side effect can be proven, issue replacement only after durable reconciliation;
   - if side effect is proven applied, resume from recorded receipt;
   - if outcome is unknown, mark affected action BLOCKED/recovery required;
5. rebuild local presentation cache;
6. reconnect Firefox adapter;
7. register hotkey only after safe initialization.

No cached action is replayed merely because the helper restarted.

## 9. Firefox crash/restart

Detection:
- browser/extension connection loss and/or Firefox process lifecycle signal.

Recovery scope:
- normally AUTH_DOMAIN_SCOPED or SESSION_SCOPED depending on reviewed binding proof.

Default conservative policy:

1. stop new browser-dependent claims;
2. inventory/reconnect the dedicated profile;
3. attempt exact reviewed local binding restoration;
4. sessions with proven exact binding may be restored only if continuity policy permits;
5. any ambiguous session becomes continuity UNKNOWN;
6. UNKNOWN sessions rotate/recreate from durable checkpoints.

A restored browser window alone is not continuity proof.

## 10. Extension/native-messaging disconnect

If Firefox remains present but the extension/helper bridge disconnects:

- mark browser adapter unavailable;
- do not invalidate task state;
- do not change clipboard/focus;
- block new browser-dependent dispatches;
- reconnect automatically where safe.

If exact managed bindings are preserved and verified after reconnect:
- session continuity need not be rotated solely because IPC briefly failed.

If binding state cannot be proven:
- affected sessions become UNKNOWN.

## 11. Manual worker-tab closure

A close event for an exact managed tab is strong local evidence that the local binding is gone.

Policy:

1. mark that generation's local binding MISSING;
2. if no outstanding action: mark session LOST/ROTATE_REQUIRED;
3. if action is AWAITING_DURABLE_ACK:
   - re-check durable ack once;
   - if already acknowledged, complete it normally;
   - otherwise do not resend;
   - supersede only when replacement recovery is issued;
4. advance generation and recreate when scheduled.

Independent sessions continue.

## 12. Orchestrator unreachable

Ctrl+B:
- no action claim;
- no clipboard mutation;
- no Firefox focus;
- fail closed.

Recovery:
- retry connectivity in background at bounded local intervals or explicit user command;
- once reachable, fresh-query durable state;
- never use stale local queue as authority.

Exact retry transport policy belongs to implementation; no model reasoning is used for polling.

## 13. Packet staged but no durable acknowledgment

No-ack is not proof of failure.

Default behavior:
- keep action SENT/UNCONFIRMED;
- show count;
- service independent workers;
- do not resend automatically.

If the operator believes paste/submit was missed or clipboard was overwritten:
- invoke `Restage last unconfirmed` through the recovery/console path;
- application re-checks durable ack first;
- if ack exists: no resend;
- if no ack and action still eligible: create replacement action;
- restage through normal Ctrl+B service.

The recovery action never mutates the old action back to QUEUED.

## 14. Clipboard overwritten before paste

The bridge cannot observe this reliably.

Recovery is identical to unconfirmed restaging:
- durable ack re-check;
- replacement action if still eligible;
- normal service cycle.

No clipboard history or arbitrary prior clipboard capture is required.

## 15. Stale/late worker reply

If an old generation writes after replacement:

- preserve result/evidence where appropriate;
- mark it stale/orphaned for control purposes;
- never advance the new generation;
- do not notify the operator unless it creates a material conflict requiring judgment.

Generation fencing is the recovery mechanism.

## 16. Machine sleep/reboot

On sleep:
- no new local claims once the helper receives suspension notification where available;
- durable worker/external actions continue independently.

On resume/reboot:

1. helper initializes in safe mode;
2. query durable action/session state;
3. reconcile expired claims;
4. reconnect/inventory Firefox;
5. preserve exact bindings only where proof survives;
6. otherwise mark affected continuity UNKNOWN;
7. rebuild replacement actions as needed;
8. register Ctrl+B after initialization.

The operator resumes from the tray count, not from remembered tabs.

## 17. Wrong Firefox profile / arbitrary ChatGPT tabs

Recovery:
- never adopt arbitrary tabs;
- locate/start the dedicated `WorkspaceWorkers` profile;
- if dedicated profile cannot be proven, block browser-dependent service;
- normal Chrome and unrelated Firefox profiles remain untouched.

## 18. Model/configuration mismatch

If the system cannot prove the assigned executor configuration remains compatible:

- freeze affected session reuse;
- do not silently continue;
- rotate to a new session or open a bounded recovery/setup flow;
- exact model/tool configuration confirmation mechanism is reviewed in UX-08/UX-12.

No page scraping is used.

## 19. Recovery action idempotency

Each recovery incident has:
- `recovery_id`;
- scope;
- generation/affected sessions;
- triggering signal(s);
- durable reconciliation checkpoint;
- current recovery state;
- completed recovery steps.

Repeated Ctrl+B presses or helper restarts must not:
- advance generations twice;
- supersede the same action twice;
- create duplicate replacement sessions;
- close unrelated tabs.

Recovery commands use the same CAS/idempotency discipline as OperatorActions.

## 20. Recovery completion criteria

A recovery incident is complete only when:

- affected durable actions are reconciled;
- old generations are fenced;
- required generation advances are durable;
- replacement session intents exist where needed;
- local bridge/browser components are healthy enough for service;
- no unknown local side-effect outcome remains unresolved.

It does not require all replacement worker chats to have already been manually serviced.

Once the first replacement service action is READY, the user may return to the ordinary service rhythm while remaining replacements are queued.

## 21. UX-07 acceptance assessment

The recovery design now defines:
- recovery scopes and severity;
- recovery control states;
- Ctrl+B behavior during recovery;
- login/all-tabs-refresh recovery;
- helper/browser/extension restart handling;
- tab-loss reconciliation;
- orchestrator loss;
- unconfirmed/restage behavior;
- clipboard interruption;
- late reply fencing;
- sleep/reboot;
- wrong-profile and executor mismatch handling;
- idempotent recovery incidents.

No recovery path requires manual durable-state reconstruction or ChatGPT content scraping.
