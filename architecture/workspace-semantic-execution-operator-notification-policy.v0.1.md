# Workspace Semantic Execution Operator Notification Policy v0.1

Status: **UX-06 NOTIFICATION POLICY CANDIDATE**

## 1. Principle

The bridge should be **pull-oriented** for routine mechanical work.

Ready work normally updates the tray indicator silently.

The system should not interrupt the user merely because another worker becomes ready.

## 2. Notification classes

### SILENT

Default for:
- READY count increase;
- durable worker acknowledgment;
- worker completion;
- local session discard;
- external wait completion that merely creates new routine work.

Effect:
- tray/badge updates only.

### QUIET_LOCAL

Allowed for:
- Ctrl+B when no work exists;
- Ctrl+B while local dispatch is BUSY;
- successful bridge ON/OFF;
- optional “ready to paste” confirmation.

Effect:
- non-modal toast/overlay or tray feedback;
- no sound by default;
- short-lived;
- does not steal focus.

### ATTENTION

Used for:
- recovery required;
- judgment gate requiring user action;
- hotkey registration failure;
- extension/helper connection failure that blocks service.

Default:
- tray state changes immediately;
- one Windows notification MAY be emitted;
- no repeated notifications while the same condition remains active.

### CRITICAL

Reserved for local bridge integrity/security problems where continued operation is unsafe.

Examples:
- corrupted protocol/identity state;
- repeated unknown local side-effect outcomes;
- helper unable to verify its own bridge state.

Effect:
- bridge may switch OFF/fail closed;
- one high-priority notification;
- operator console directs recovery.

## 3. Anti-noise rules

- Do not notify once per worker acknowledgment.
- Do not notify once per ready action.
- Do not repeatedly notify unchanged recovery/gate conditions.
- Coalesce multiple ready-action arrivals.
- Acknowledging/opening a notification should not itself claim work.
- Notification dismissal must not mutate task/action state.

## 4. User-configurable modes

### Quiet
Only recovery, judgment, blocked bridge, and critical notifications.

### Default
Quiet mode plus local Ctrl+B feedback.

### Verbose
May add batch-complete and major session-recovery status notifications.

Routine ready-action arrivals remain non-interruptive even in verbose mode unless explicitly enabled later.

## 5. Batch completion

When READY transitions from >0 to 0 after user servicing:

Default behavior:
- tray count updates to 0;
- no modal popup.

Optional verbose notification:
`Mechanical queue serviced; waiting on N acknowledgments.`

This avoids distracting the user after they deliberately return to other work.

## 6. Judgment/recovery distinction

Judgment notification wording must indicate:
- a real decision is needed.

Recovery notification wording must indicate:
- task state is preserved;
- local/session continuity needs attention.

Neither should imply task data loss unless durable evidence proves it.

## 7. No unsupported claims

Notifications must use evidence-safe terms:

Allowed:
- prepared;
- acknowledged;
- ready;
- waiting;
- recovery required;
- blocked.

Avoid unless durably established:
- sent;
- delivered;
- received by ChatGPT;
- thinking;
- running.

