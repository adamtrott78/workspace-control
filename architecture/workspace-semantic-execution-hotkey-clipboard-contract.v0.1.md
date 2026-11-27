# Workspace Semantic Execution Hotkey and Clipboard Contract v0.1

Status: **UX-05 INTERACTION CONTRACT CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Companions:
- `architecture/workspace-semantic-execution-operator-state-machine.v0.2.md`
- `architecture/workspace-semantic-execution-session-broker.v0.1.md`
- `architecture/workspace-semantic-execution-hotkey-dispatch-sequence.v0.1.md`
- `architecture/workspace-semantic-execution-hotkey-clipboard-test-matrix.v0.1.json`

## 1. Purpose

Specify the exact physical interaction contract for the single global scheduler command.

Preferred v0 binding:

`Ctrl+B`

Semantic meaning:

> perform the next scheduler-selected non-content operator action.

The binding is configurable. The semantic command is not.

## 2. Normative routine rhythm

The normal worker-service loop remains:

```text
Ctrl+B
Ctrl+V
Enter

Ctrl+B
Ctrl+V
Enter
...
```

The operator does not select the worker, create/close tabs manually, construct the packet, or relay durable state.

## 3. Master toggle semantics

### Bridge OFF

The native helper MUST:
- unregister the global Workspace hotkey;
- allow normal application Ctrl+B behavior;
- not start a new operator dispatch;
- not focus/create/close/discard Firefox tabs;
- not mutate clipboard.

Durable orchestration may continue and ready manual actions may accumulate.

### Bridge ON

The helper registers the configured global command.

Bridge ON alone MUST NOT:
- focus Firefox;
- change clipboard;
- claim an OperatorAction;
- replay cached work.

Only an explicit hotkey press initiates a dispatch transaction.

### Toggle OFF during an in-flight local dispatch

The helper MUST stop at the earliest safe local cancellation boundary.

Rules:
- no new OperatorAction may be claimed after OFF is requested;
- local steps not yet started are skipped;
- if no local side effect occurred, record a definite local abort/failure and preserve retry eligibility through a replacement action;
- if some side effects occurred and their outcome is known, persist exact receipts and stop before any further user-visible step where possible;
- if local side-effect outcome is unknown, fail closed as BLOCKED and require reconciliation;
- an already LOCAL_PREPARED/AWAITING_DURABLE_ACK action is not rewound merely because the bridge is turned OFF.

The UI wording for this edge case belongs to UX-06/UX-07.

## 4. Global hotkey registration

### Default

Preferred candidate:
`Ctrl+B`

Rationale:
- comfortable from normal keyboard position;
- close to Ctrl+V;
- supports a simple repeated motor pattern.

### Requirements

The hotkey MUST:
- work while another application has focus;
- be configurable;
- be completely released when bridge OFF;
- register on a distinct physical keypress edge;
- suppress OS key-repeat from a held key;
- never synthesize Ctrl+B into Firefox/ChatGPT.

If global registration fails because another application/system owns the binding:
- bridge ON must fail visibly rather than silently operate without the shortcut;
- user may choose a different binding in settings.

Hotkey conflict/usability evaluation is owned by UX-11.

## 5. Single-flight dispatch

Only one local hotkey dispatch transaction may execute at a time per helper instance.

### While DISPATCHING/PREPARING

Additional Ctrl+B presses:
- MUST NOT claim duplicate work;
- MUST NOT queue a blind second browser operation;
- MUST NOT overwrite clipboard;
- SHOULD be coalesced/ignored with a quiet BUSY indication.

### After local preparation completes

Once a worker action reaches LOCAL_PREPARED/AWAITING_DURABLE_ACK and control has returned to the human, a later deliberate Ctrl+B press may service another independent READY action.

This remains true even though the system cannot know whether the previous Ctrl+V/Enter occurred.

The previous action remains SENT/UNCONFIRMED until durable acknowledgment.

## 6. Double-press and held-key behavior

The helper MUST distinguish:
- OS key-repeat generated while Ctrl+B remains held;
- a new deliberate Ctrl+B press after key release.

Held-key repeat MUST never cause additional dispatch.

A second deliberate press after the first dispatch transaction has returned to the human is allowed to advance to another independently serviceable action.

This means an accidental quick second deliberate press can replace the clipboard with the next packet; therefore:
- the previous packet remains durably recoverable by action/payload ref;
- no acknowledgment is inferred;
- explicit retry/recovery can restage it;
- UX-11 must test whether an additional ergonomic debounce is warranted.

No arbitrary timing-based “message was sent” inference is permitted.

## 7. Clipboard write timing

For actions requiring a packet, clipboard mutation happens at the **last safe moment**.

Required order:

```text
1. claim action
2. prepare/verify browser target
3. complete all browser operations that may fail
4. verify action/generation still current
5. write exact packet to clipboard
6. verify clipboard write success
7. focus/activate the final target worker tab
8. record LOCAL_PREPARED
9. return control to human
```

Why:
- avoids replacing the user's clipboard during long Firefox startup/tab creation;
- if the operator sees the worker tab come forward, the packet should already be staged;
- clipboard failure occurs before final focus handoff.

If the clipboard write fails:
- do not present the worker as READY TO PASTE;
- record local failure;
- do not infer delivery.

## 8. Previous clipboard policy

### v0 decision: no automatic snapshot/restore

The bridge MUST NOT read or persist arbitrary pre-existing clipboard content merely to restore it later.

Reasons:
- privacy minimization;
- clipboard may contain secrets;
- v0 deliberately does not observe the user's paste/Enter sequence, so there is no trustworthy automatic restore point;
- timeout-based restoration could replace the packet before the user pastes it.

Therefore:
- pressing Ctrl+B is explicit consent to replace the current clipboard;
- the packet remains available through its durable payload ref if restaging is needed;
- automatic previous-clipboard restoration is out of scope for v0.

A future opt-in feature may be reviewed separately, but it must not become a v0 requirement.

## 9. No-work behavior

If fresh scheduler state contains no serviceable action:

Ctrl+B MUST:
- leave focus unchanged;
- leave clipboard unchanged;
- claim nothing;
- avoid launching Firefox;
- produce at most a quiet local indication.

No-action feedback details belong to UX-06.

## 10. Judgment-gate behavior

If the highest-priority operator action is `OPEN_JUDGMENT_GATE`:

Ctrl+B MUST:
- open/focus the operator console at the exact gate;
- leave clipboard unchanged;
- not focus a ChatGPT worker;
- not fabricate a paste packet.

The operator exits the routine paste rhythm until the substantive decision is made through the owning authority path.

## 11. Recovery behavior

If the next action is `OPEN_RECOVERY`:

Ctrl+B MUST:
- open/focus the recovery surface defined by UX-07;
- leave clipboard unchanged unless a later explicit recovery step creates a valid service action;
- not select an arbitrary worker tab;
- not guess session continuity.

After recovery produces a valid worker action, the operator returns to the normal Ctrl+B → Ctrl+V → Enter loop.

## 12. Cold Firefox startup

If Firefox `WorkspaceWorkers` is stopped and the selected action requires a browser target:

Ctrl+B begins one single-flight dispatch.

During startup:
- helper state is PREPARING;
- repeated Ctrl+B presses do not launch another Firefox instance or claim more actions;
- clipboard remains unchanged until the target browser operation has succeeded;
- no foreground focus is required until the final target is ready.

On success:
- packet is written;
- exact target is focused;
- control returns to human.

On failure:
- clipboard remains unchanged;
- action records definite failure or BLOCKED if outcome is ambiguous.

## 13. Local-only action draining

One Ctrl+B dispatch may execute scheduler-selected atomic local-only actions such as:
- DISCARD_SESSION;
- RETIRE_SESSION;

with `COMPLETE_AND_REQUERY`, then fresh-query and claim the next action.

Rules:
- clipboard remains unchanged during local-only maintenance;
- if a human-service action is found, its packet is written only after its browser target is ready;
- if maintenance fails, stop/fail closed rather than skipping to later work with ambiguous browser state;
- a configurable safety cap prevents an unbounded local-only drain loop.

The operator still experiences one Ctrl+B.

## 14. Focus contract

A worker tab may be brought to foreground only when:
- the user explicitly pressed Ctrl+B;
- a valid claimed action requires that target;
- final browser preparation and clipboard staging succeeded.

Focus MUST NOT be changed:
- for background durable acknowledgments;
- for ready-count changes;
- for no-action;
- while bridge OFF;
- merely because Firefox started;
- because a worker finished.

Judgment/recovery actions may focus the operator console instead.

## 15. Clipboard packet integrity

Every staged worker packet MUST be bound to:
- action ID;
- action generation;
- worker slot ID/generation;
- payload ref;
- content SHA-256.

Immediately before clipboard write, the helper/application MUST verify the claimed action is still current.

The clipboard text itself does not need hidden metadata.

Telemetry records the payload hash/ref, not the packet contents.

## 16. Packet restaging

Because v0 cannot know whether the user actually pasted/submitted:

- packets are recoverable from durable payload refs;
- a retry must re-check durable acknowledgment first;
- if no acknowledgment exists and retry is authorized, a new replacement OperatorAction restages the packet;
- the old action is preserved/superseded according to UX-03.

No special clipboard history is required.

## 17. Hotkey dispatch pseudocode

```text
on_global_hotkey():
    if bridge != ON:
        pass_through_or_not_registered

    if local_dispatch_in_flight:
        show_quiet_busy
        return

    begin_single_flight()

    loop up to local_only_safety_cap:
        snapshot = query_fresh_operator_state()

        if snapshot.no_action:
            finish_without_focus_or_clipboard()
            return

        action = atomic_claim(snapshot.next_action)

        if action is OPEN_JUDGMENT_GATE:
            open_operator_console(action)
            record_local_completion(action)
            return

        if action is OPEN_RECOVERY:
            open_recovery_surface(action)
            record_local_completion(action)
            return

        execute_browser_steps_before_clipboard(action)

        if action failed or became stale:
            record_exact_outcome()
            return

        if action.human_requirement == NONE:
            complete_local_action(action)
            if action.post_local_success == COMPLETE_AND_REQUERY:
                continue
            return

        revalidate_claim_and_generation()
        write_clipboard(action.packet)
        verify_clipboard_success()
        focus_exact_target()
        record_local_prepared_and_arm_ack(action)
        return
```

## 18. UX-05 acceptance assessment

The interaction contract now defines:
- bridge ON/OFF;
- in-flight disable;
- Ctrl+B registration/failure;
- held-key repeat suppression;
- single-flight dispatch;
- deliberate second-press semantics;
- exact clipboard timing;
- no automatic previous-clipboard restore;
- no-work behavior;
- judgment/recovery behavior;
- cold-start behavior;
- local-only draining;
- focus invariants;
- packet integrity/restaging.

No rule requires observing or automating ChatGPT content.

