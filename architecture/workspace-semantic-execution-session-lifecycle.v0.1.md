# Workspace Semantic Execution Session Lifecycle v0.1

Status: **UX-04 DESIGN CANDIDATE**

```mermaid
stateDiagram-v2
    [*] --> UNALLOCATED

    UNALLOCATED --> CREATING: allocate generation
    CREATING --> ACTIVE: first durable ack / continuity TRUSTED
    CREATING --> CONTINUITY_UNKNOWN: auth/binding ambiguity
    CREATING --> LOST: creation/session definitively lost

    ACTIVE --> IDLE: no outstanding packet
    IDLE --> ACTIVE: SERVICE_EXISTING
    IDLE --> DISCARDED: memory policy
    DISCARDED --> ACTIVE: RESTORE_AND_SERVICE + valid ack

    ACTIVE --> CONTINUITY_UNKNOWN: auth refresh / binding ambiguity
    IDLE --> CONTINUITY_UNKNOWN: auth refresh / restart ambiguity
    DISCARDED --> CONTINUITY_UNKNOWN: continuity invalidation

    ACTIVE --> ROTATE_REQUIRED: hard/soft rotation trigger
    IDLE --> ROTATE_REQUIRED: hard/soft rotation trigger
    DISCARDED --> ROTATE_REQUIRED: incompatible/policy change
    CONTINUITY_UNKNOWN --> ROTATE_REQUIRED: recovery policy
    LOST --> ROTATE_REQUIRED: replacement required

    ROTATE_REQUIRED --> RETIRE_REQUIRED: replacement generation allocated
    RETIRE_REQUIRED --> RETIRED: local retirement complete or local remnant abandoned safely
    RETIRED --> [*]

    CONTINUITY_UNKNOWN --> ACTIVE: only if reviewed recovery proves exact continuity
    CONTINUITY_UNKNOWN --> LOST: continuity cannot be restored
```

## Continuity overlay

Session lifecycle state and continuity state are separate axes.

- `CREATING + NOT_ESTABLISHED`: new generation awaiting first durable ack.
- `ACTIVE/IDLE/DISCARDED + TRUSTED`: reusable subject to compatibility.
- `CONTINUITY_UNKNOWN + UNKNOWN`: frozen; no reuse.
- `LOST + LOST`: replacement required.
- `RETIRED`: generation permanently closed.

A successful page load alone never changes UNKNOWN to TRUSTED.

## Generation transition

```text
slot instant-general-1 generation 7
        │ hard rotation
        ▼
generation 7 continuity UNKNOWN/LOST
        │ allocate replacement
        ▼
slot instant-general-1 generation 8 CREATING
        │ first valid durable ack
        ▼
generation 8 ACTIVE + TRUSTED
```

Generation 7 can never become current again.

