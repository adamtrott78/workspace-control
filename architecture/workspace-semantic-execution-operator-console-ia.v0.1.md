# Workspace Semantic Execution Operator Console Information Architecture v0.1

Status: **UX-06 INFORMATION ARCHITECTURE CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Companions:
- `architecture/workspace-semantic-execution-operator-console-wireframes.v0.1.md`
- `architecture/workspace-semantic-execution-operator-display-state-table.v0.1.json`
- `architecture/workspace-semantic-execution-operator-notification-policy.v0.1.md`

## 1. UX objective

The operator should be able to answer one question at a glance:

> How many mechanical service cycles can I perform right now?

Routine operation must not require opening a dashboard or interpreting worker state.

Primary persistent display:

`READY_MANUAL_CYCLES`

The operator console exists for:
- judgment gates;
- recovery;
- blocked states;
- settings;
- diagnostics;
- optional inspection.

It is not required for normal batch service.

## 2. Presentation hierarchy

### Level 0 — tray icon / persistent indicator

Always available while helper is running.

Must convey:
- bridge ON/OFF;
- primary ready count;
- exceptional state presence.

No task names, worker names, SHAs, or verbose status are required at this level.

### Level 1 — tray tooltip / compact menu

One interaction away.

Shows:
- Ready;
- New;
- Reuse;
- Rotate/Retire;
- Sent/Unconfirmed;
- Gates;
- Recovery/Blocked.

Also exposes high-frequency commands.

### Level 2 — operator console

Used when:
- judgment is required;
- recovery is required;
- blocked state needs explanation;
- user opens it intentionally;
- settings/diagnostics are needed.

### Level 3 — diagnostics

Explicitly hidden from routine use.

Contains:
- action IDs;
- worker slot/generation;
- payload hashes;
- browser binding details;
- durable checkpoint refs;
- component connectivity;
- timestamps;
- local receipts.

## 3. Primary ready count semantics

`READY_MANUAL_CYCLES` counts only actions that can be serviced by a deliberate Ctrl+B now.

Include:
- SERVICE_EXISTING;
- CREATE_AND_SERVICE;
- RESTORE_AND_SERVICE;
- local-only maintenance that can safely drain into a ready human-service action.

Exclude:
- AWAITING_DURABLE_ACK;
- judgment gates;
- recovery actions;
- blocked actions;
- waiting external events;
- machine-only deterministic work.

This count answers:

> How many Ctrl+B → Ctrl+V → Enter cycles can I do right now?

## 4. Secondary counters

### NEW

Ready cycles expected to create a fresh worker conversation.

### REUSE

Ready cycles expected to use an existing trusted worker.

### ROTATE/RETIRE

Local maintenance pending.

This is informational and does not necessarily equal additional human cycles because maintenance may drain inside one Ctrl+B dispatch.

### SENT/UNCONFIRMED

Worker-service actions locally prepared and waiting for durable acknowledgment.

These are not READY.

### GATES

Substantive human judgment/authority gates.

These are not mechanical paste cycles.

### RECOVERY

Recovery interactions requiring user attention.

### BLOCKED

Work that cannot safely progress under current state/authority.

## 5. Tray icon state model

The tray icon must have one dominant semantic state at a time.

Precedence:

```text
HELPER_ERROR
> RECOVERY_REQUIRED
> JUDGMENT_REQUIRED
> BLOCKED_ONLY
> READY
> WAITING_UNCONFIRMED
> IDLE
> BRIDGE_OFF
```

Bridge OFF remains visually obvious even if work is pending.

Suggested semantic labels:

- OFF
- READY
- WAITING
- GATE
- RECOVERY
- BLOCKED
- ERROR

Exact colors/icons are deferred to implementation/UI polish; semantics are frozen here.

## 6. Badge/count behavior

If the platform supports a tray overlay/badge:
- display READY_MANUAL_CYCLES;
- cap display at `99+`;
- zero may be hidden or shown as `0` depending on OS ergonomics;
- exceptional states may replace the numeric badge with a symbol if the numeric count would be misleading.

Examples:
- `5` = five mechanical cycles ready;
- `!` = recovery/judgment requiring attention when no routine action should be implied;
- no badge = idle/off depending on icon state.

Firefox extension badge is optional and mirrors the helper projection. It is not authoritative.

## 7. Tray menu

Recommended compact menu:

```text
Workspace Worker Bridge        ON

Ready now                       5
  New                           1
  Reuse                         4
Sent / unconfirmed              2
Judgment gates                  0
Recovery                        0
Blocked                         0

Service next                    Ctrl+B
Open Operator Console
Open Worker Firefox

Pause New Worker Creation       OFF
-----------------------------------
Settings
Diagnostics
Exit Helper
```

When bridge OFF:

```text
Workspace Worker Bridge        OFF

Ready waiting                   5
Sent / unconfirmed              2
Judgment gates                  0
Recovery                        0

Enable Bridge
Open Operator Console
Settings
Exit Helper
```

No command should require the operator to select a worker by name.

## 8. Service-next command

The tray menu MAY expose `Service next` as a clickable equivalent of Ctrl+B.

It must call the same application use case and obey the same single-flight/idempotency rules.

This provides:
- accessibility fallback;
- debugging fallback;
- recovery if the hotkey conflicts.

The primary path remains the keyboard hotkey.

## 9. Operator console top-level screens

### Dashboard

Purpose:
- show current workload and health without exposing implementation noise.

Contents:
- bridge state;
- READY count;
- secondary counters;
- one primary action when needed;
- session pool summary;
- latest durable activity summary.

### Judgment

Purpose:
- present substantive human decisions.

Contents:
- exact question;
- why user input is required;
- relevant constraints/evidence;
- allowed choices;
- owning authority path;
- consequences if known.

Must not mix unrelated routine actions into the judgment panel.

### Recovery

Purpose:
- guide user through bounded local/session recovery.

Contents:
- what failed or became unknown;
- what the system already preserved;
- the smallest user action needed;
- affected session count;
- whether old generations are fenced;
- what happens after recovery.

Exact flows are UX-07.

### Sessions

Purpose:
- optional inspection only.

Shows:
- logical slot;
- generation;
- class/role;
- task affinity;
- continuity;
- local state ACTIVE/DISCARDED/LOST;
- outstanding acknowledgment state.

Not required for routine operation.

### Settings

Contains:
- bridge startup mode;
- global hotkey binding;
- start helper with Windows;
- notification level;
- worker Firefox launch/profile settings;
- pause new-worker creation preference.

### Diagnostics

Contains low-level details hidden from normal views.

## 10. Dashboard information priority

Top to bottom:

1. `Ready now`
2. `Needs your judgment/recovery` if nonzero
3. `Sent / waiting`
4. worker session pool summary
5. blocked reasons
6. recent activity
7. diagnostics link

The dashboard should never lead with logs or worker IDs.

## 11. Judgment-gate presentation

When a judgment gate exists:

- tray state becomes GATE if it is the next user-required action;
- READY mechanical count remains separately visible;
- Ctrl+B behavior follows scheduler priority policy;
- opening the gate shows one decision, not a mixed queue.

If independent routine actions are still eligible and policy allows them before the gate, the READY count may remain nonzero.

The console must distinguish:
- mechanical work available;
- substantive decision required.

## 12. Recovery presentation

When recovery is required:

The console should say, conceptually:

```text
Worker session continuity cannot be trusted.

Your task state is preserved.
3 worker sessions are affected.
Old session generations are fenced.

Required action:
[recovery-specific instruction]

After recovery, use Ctrl+B normally.
```

It must not ask the user to:
- inspect all worker tabs;
- identify which worker was which;
- copy task state;
- decide checkpoint generations.

## 13. Blocked presentation

Blocked states must identify:
- blocker category;
- affected task/action count;
- whether user action can resolve it;
- smallest next action.

Examples:
- orchestrator unreachable;
- hotkey registration failed;
- extension disconnected;
- authority missing;
- executor mismatch;
- continuity unknown pending recovery.

Blocked does not imply failed task work.

## 14. Sent/unconfirmed presentation

Routine display:

`Sent / unconfirmed: N`

Do not label these:
- running;
- delivered;
- thinking;
- failed.

The system intentionally does not know whether Ctrl+V/Enter occurred.

Optional details view may show:
- worker slot;
- local preparation timestamp;
- packet/action ref;
- duration waiting.

## 15. Session pool summary

Compact example:

```text
Worker sessions
2 active · 1 discarded · 0 recovery
```

Expanded view:

```text
instant-general-1  gen 8  trusted   active
instant-general-2  gen 3  trusted   waiting ack
critic-1           gen 2  trusted   discarded
```

This is inspection, not routing UI.

## 16. Recent activity

Optional low-priority view:

```text
20:41  instant-general-2 prepared
20:40  instant-general-1 acknowledged
20:38  critic-1 discarded
```

Activity text must avoid implying unsupported knowledge.

Use:
- prepared;
- acknowledged;
- retired;
- recovery required.

Avoid:
- message sent;
- ChatGPT received;
- worker is thinking;
unless supported by durable evidence.

## 17. Settings hierarchy

### General
- bridge start ON/OFF;
- launch helper at Windows login.

### Hotkey
- current binding;
- test binding;
- conflict status.

### Browser
- dedicated Firefox executable/profile;
- open worker Firefox;
- worker pool target display.

### Notifications
- quiet/default/verbose modes.

### Advanced
- pause new-worker creation;
- diagnostics;
- local telemetry export/reset where allowed.

## 18. Hidden-by-default data

Do not show routinely:
- action IDs;
- Git SHAs;
- payload hashes;
- raw durable JSON;
- tab IDs/window IDs;
- lease IDs;
- timestamps with subsecond precision;
- internal policy scores.

These belong in diagnostics.

## 19. Accessibility and keyboard operation

The console SHOULD:
- be fully keyboard navigable;
- expose the same primary commands without mouse;
- avoid color-only status distinctions;
- keep one obvious primary action per exceptional screen.

The core workflow must remain usable even if tray graphics are inaccessible.

## 20. UX-06 acceptance assessment

The information architecture now defines:
- primary READY count;
- secondary count semantics;
- tray state precedence;
- compact menu hierarchy;
- operator console screens;
- judgment/recovery/blocked separation;
- sent/unconfirmed wording;
- session inspection;
- settings;
- diagnostic disclosure boundaries.

Routine operation still requires no console visit.

