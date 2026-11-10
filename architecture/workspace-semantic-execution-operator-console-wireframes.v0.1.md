# Workspace Semantic Execution Operator Console Wireframes v0.1

Status: **UX-06 LOW-FIDELITY WIREFRAMES**

These wireframes are behavioral, not visual-style specifications.

## 1. Tray tooltip — routine ready

```text
┌──────────────────────────────┐
│ Workspace Control            │
│ Bridge: ON                   │
│ Ready now: 5                 │
│ Sent/unconfirmed: 2          │
│ Ctrl+B to service next       │
└──────────────────────────────┘
```

## 2. Tray tooltip — idle

```text
┌──────────────────────────────┐
│ Workspace Control            │
│ Bridge: ON                   │
│ Ready now: 0                 │
│ Sent/unconfirmed: 0          │
│ Nothing needs service        │
└──────────────────────────────┘
```

## 3. Tray tooltip — bridge off with work waiting

```text
┌──────────────────────────────┐
│ Workspace Control            │
│ Bridge: OFF                  │
│ Ready waiting: 7             │
│ Ctrl+B is normal             │
└──────────────────────────────┘
```

## 4. Compact tray menu

```text
┌──────────────────────────────────┐
│ Workspace Worker Bridge      ON  │
│                                  │
│ Ready now                    5   │
│   New                        1   │
│   Reuse                      4   │
│ Sent / unconfirmed           2   │
│ Judgment gates               0   │
│ Recovery                     0   │
│ Blocked                      0   │
│                                  │
│ Service next             Ctrl+B  │
│ Open Operator Console            │
│ Open Worker Firefox              │
│                                  │
│ Pause New Worker Creation   OFF  │
│ ──────────────────────────────── │
│ Settings                         │
│ Diagnostics                      │
│ Exit Helper                      │
└──────────────────────────────────┘
```

## 5. Main console — normal operation

```text
┌────────────────────────────────────────────────┐
│ Workspace Control                    Bridge ON │
├────────────────────────────────────────────────┤
│ READY NOW                                      │
│                                                │
│                     5                          │
│                                                │
│          Press Ctrl+B to service next          │
│                                                │
│ New 1    Reuse 4    Sent/unconfirmed 2         │
├────────────────────────────────────────────────┤
│ Worker sessions                                │
│ 2 active · 1 discarded · 0 recovery            │
├────────────────────────────────────────────────┤
│ Needs attention                                │
│ None                                           │
├────────────────────────────────────────────────┤
│ Recent                                         │
│ general-1 acknowledged                         │
│ critic-1 discarded                             │
└────────────────────────────────────────────────┘
```

## 6. Main console — judgment required

```text
┌────────────────────────────────────────────────┐
│ Workspace Control                    Bridge ON │
├────────────────────────────────────────────────┤
│ DECISION REQUIRED                              │
│                                                │
│ Deploy candidate configuration?                │
│                                                │
│ Why: deployment authority requires user review │
│ Scope: <human-readable scope>                  │
│                                                │
│ [Approve through authority path]               │
│ [Reject]                                       │
│ [View evidence]                                │
├────────────────────────────────────────────────┤
│ Mechanical work still ready: 3                 │
└────────────────────────────────────────────────┘
```

## 7. Main console — recovery required

```text
┌────────────────────────────────────────────────┐
│ Workspace Control                              │
├────────────────────────────────────────────────┤
│ RECOVERY REQUIRED                              │
│                                                │
│ Worker session continuity cannot be trusted.   │
│                                                │
│ Task state is preserved.                       │
│ Affected sessions: 3                           │
│ Old generations fenced: yes                    │
│                                                │
│ Required action                                │
│ <UX-07 recovery instruction>                   │
│                                                │
│ [Start / Continue Recovery]                    │
├────────────────────────────────────────────────┤
│ After recovery: use Ctrl+B normally            │
└────────────────────────────────────────────────┘
```

## 8. Main console — blocked

```text
┌────────────────────────────────────────────────┐
│ Workspace Control                              │
├────────────────────────────────────────────────┤
│ BLOCKED                                        │
│                                                │
│ Orchestrator unreachable                       │
│                                                │
│ No worker action has been dispatched.          │
│ Clipboard unchanged.                           │
│                                                │
│ Smallest next action:                          │
│ restore orchestrator connectivity              │
│                                                │
│ [Retry connection]   [Diagnostics]             │
└────────────────────────────────────────────────┘
```

## 9. Sessions inspection

```text
┌─────────────────────────────────────────────────────────┐
│ Worker Sessions                                         │
├─────────────────────────────────────────────────────────┤
│ Slot                 Gen  Role        Continuity State  │
│ instant-general-1      8  general     trusted    active │
│ instant-general-2      3  general     trusted    wait   │
│ critic-1               2  critic      trusted    disc.  │
├─────────────────────────────────────────────────────────┤
│ [Show details]                                          │
└─────────────────────────────────────────────────────────┘
```

## 10. Diagnostics

```text
┌─────────────────────────────────────────────────────────┐
│ Diagnostics                                             │
├─────────────────────────────────────────────────────────┤
│ Orchestrator           connected                        │
│ Native helper          healthy                          │
│ Firefox extension      connected                        │
│ WorkspaceWorkers       ready                            │
│ Hotkey Ctrl+B          registered                       │
│                                                        │
│ Last action: <action-id>                                │
│ Slot/gen:   <slot>/<generation>                         │
│ Payload:    <sha256/ref>                                │
│ Browser:    <local binding detail>                      │
│                                                        │
│ [Copy diagnostic summary]                               │
└─────────────────────────────────────────────────────────┘
```

Diagnostics may expose technical data but must not become necessary for routine service.

