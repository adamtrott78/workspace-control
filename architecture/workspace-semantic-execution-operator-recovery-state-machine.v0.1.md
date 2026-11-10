# Workspace Semantic Execution Recovery State Machine v0.1

Status: **UX-07 DESIGN CANDIDATE**

## Global recovery state

```mermaid
stateDiagram-v2
    [*] --> HEALTHY

    HEALTHY --> SUSPECTED: anomaly signal
    SUSPECTED --> FROZEN: scope classified / affected work frozen
    FROZEN --> RECONCILING: start durable reconciliation

    RECONCILING --> WAITING_USER_AUTH: authentication required
    RECONCILING --> WAITING_USER_SIGNAL: explicit confirmation/report required
    RECONCILING --> REBUILDING: enough evidence for automatic recovery
    RECONCILING --> BLOCKED: dependency/side-effect outcome unsafe

    WAITING_USER_AUTH --> RECONCILING: auth-return signal or reviewed fallback
    WAITING_USER_SIGNAL --> RECONCILING: explicit operator recovery signal

    REBUILDING --> READY_TO_RESUME: generations/actions reconciled
    READY_TO_RESUME --> HEALTHY: first normal post-recovery dispatch available/accepted

    BLOCKED --> RECONCILING: dependency repaired / safe evidence supplied
```

## Authentication refresh sequence

```mermaid
sequenceDiagram
    actor U as Operator
    participant H as Native Helper
    participant F as Firefox Adapter
    participant O as Orchestrator
    participant D as Durable State

    U->>H: Ctrl+B
    H->>O: claim/create worker
    H->>F: prepare new worker tab
    F-->>H: authentication navigation observed
    H->>O: AUTH_DOMAIN recovery signal
    O->>D: freeze affected sessions / mark continuity UNKNOWN
    O->>D: reconcile outstanding durable acknowledgments
    H-->>U: focus authentication flow
    U->>F: complete login manually
    F-->>H: auth-return origin/lifecycle signal
    H->>O: resume recovery
    O->>D: supersede unresolved old actions
    O->>D: advance generations / build replacements
    O-->>H: recovery READY_TO_RESUME
    U->>H: Ctrl+B
    H->>O: claim fresh replacement service
    H->>F: prepare exact replacement worker
    H-->>U: ready to paste
    U->>U: Ctrl+V, Enter
```

The auth-return browser signal never restores old sessions to TRUSTED. It merely allows reconciliation/rebuild to proceed.

## Scoped recovery rule

```text
if recovery.scope in [ACTION_SCOPED, SESSION_SCOPED]
and independent READY work exists:
    Ctrl+B may service independent READY work
else:
    Ctrl+B advances/focuses recovery
```

For `AUTH_DOMAIN_SCOPED` or `LOCAL_BRIDGE_GLOBAL` recovery, no Chat browser service is allowed until recovery reaches READY_TO_RESUME.

## Recovery idempotency

Recovery state is durable enough to survive helper restart:

```text
recovery_id
scope
affected_session_generations
trigger_signals
durable_reconciliation_checkpoint
completed_steps
next_safe_step
status
```

A repeated recovery command resumes the next incomplete step; it does not replay completed generation advances or supersessions.
