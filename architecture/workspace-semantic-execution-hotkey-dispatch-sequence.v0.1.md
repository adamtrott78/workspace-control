# Workspace Semantic Execution Hotkey Dispatch Sequences v0.1

Status: **UX-05 DESIGN CANDIDATE**

## Routine existing-worker service

```mermaid
sequenceDiagram
    actor U as Operator
    participant H as Native Helper
    participant O as Operator Service
    participant B as Firefox Adapter
    participant C as Clipboard

    U->>H: Ctrl+B
    H->>O: Get fresh state + claim next action
    O-->>H: SERVICE_EXISTING(action, slot, generation, packet ref)
    H->>B: Validate/activate managed target (without final focus)
    B-->>H: Target prepared
    H->>O: Revalidate action/generation
    O-->>H: Current
    H->>C: Write exact packet
    C-->>H: Success
    H->>B: Final focus/activate target
    B-->>H: Focused
    H->>O: Record LOCAL_PREPARED + arm durable ack
    H-->>U: Ready to paste
    U->>U: Ctrl+V, Enter
```

## Cold Firefox create-and-service

```mermaid
sequenceDiagram
    actor U as Operator
    participant H as Native Helper
    participant O as Operator Service
    participant B as Firefox Adapter
    participant C as Clipboard

    U->>H: Ctrl+B
    H->>O: Claim CREATE_AND_SERVICE
    O-->>H: action
    H->>B: Ensure WorkspaceWorkers profile
    Note over H,B: Clipboard unchanged while startup occurs
    H->>B: Create managed worker tab
    B-->>H: Target prepared
    H->>O: Revalidate action/generation
    H->>C: Write packet
    C-->>H: Success
    H->>B: Final focus
    H->>O: Record LOCAL_PREPARED + arm ack
    H-->>U: Ready to paste
    U->>U: Ctrl+V, Enter
```

## Local-only maintenance then service

```mermaid
sequenceDiagram
    actor U as Operator
    participant H as Native Helper
    participant O as Operator Service
    participant B as Firefox Adapter
    participant C as Clipboard

    U->>H: Ctrl+B
    H->>O: Claim RETIRE_SESSION
    O-->>H: retire action
    H->>B: Close exact managed retired tab
    B-->>H: Success
    H->>O: Complete retire action
    H->>O: Fresh query + claim next action
    O-->>H: SERVICE_EXISTING
    H->>B: Prepare next target
    H->>C: Write next packet
    H->>B: Final focus
    H->>O: Record LOCAL_PREPARED
    H-->>U: Ready to paste
    U->>U: Ctrl+V, Enter
```

## Second Ctrl+B while first dispatch is still preparing

```mermaid
sequenceDiagram
    actor U as Operator
    participant H as Native Helper

    U->>H: Ctrl+B
    H->>H: Enter single-flight PREPARING
    U->>H: Ctrl+B again
    H-->>U: BUSY / coalesced
    Note over H: No second claim, no clipboard write
```

## No work

```mermaid
sequenceDiagram
    actor U as Operator
    participant H as Native Helper
    participant O as Operator Service

    U->>H: Ctrl+B
    H->>O: Fresh operator state
    O-->>H: NO_ACTION
    H-->>U: Quiet 0-ready indication
    Note over U,H: Focus and clipboard unchanged
```

