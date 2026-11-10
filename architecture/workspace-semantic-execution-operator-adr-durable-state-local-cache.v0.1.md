# ADR — Durable Scheduler/Session State vs Local Browser Cache v0.1

Status: **ACCEPTED FOR UX DESIGN BASELINE**

Parent: `workspace-semantic-execution-migration-v1`

## Context

Persistent Chat sessions improve efficiency, but browser tabs are fragile:
- tabs may be closed;
- Firefox may restart/crash;
- reauthentication may refresh all tabs;
- browser-local IDs may change;
- conversations may lose trusted continuity.

The system must recover without making the human reconstruct task state.

## Decision

Treat logical task/session/action state as durable control-plane state and Firefox/helper state as disposable local cache.

Durable identity includes:
- task/process;
- logical worker slot;
- session generation;
- executor requirement;
- continuity classification;
- last acknowledged durable checkpoint;
- OperatorAction lifecycle.

Local cache may include:
- Firefox `windowId`;
- Firefox `tabId`;
- local connection state;
- local dispatch timestamps/receipts;
- tray presentation cache.

Browser-local IDs MUST NOT define worker authority or durable identity.

If continuity is uncertain:
- fail closed;
- preserve completed durable work;
- rotate/recreate from the last durable checkpoint;
- never reconstruct truth by scraping/reading ChatGPT tabs.

## Consequences

Positive:
- crashes/logouts/restarts do not lose task progress;
- persistent chats remain an optimization rather than a reliability dependency;
- session rotation is safe;
- local adapter implementations are replaceable.

Costs:
- requires durable session registry and action lifecycle;
- recovery may discard useful but unverified conversational context;
- explicit reconciliation logic is required.

## Rejected alternatives

### Browser tabs as source of truth
Rejected because tab/process state is volatile and cannot carry authority/provenance safely.

### Conversation transcript as task continuity boundary
Rejected because the benchmark already demonstrates durable externalized continuity and because transcript-only recovery is fragile.

### Best-effort adoption of any matching-looking tab
Rejected because visible titles/content are not trustworthy identity and this creates confused-deputy risk.

## Revisit conditions

Only revisit if a future supported Chat platform exposes durable, typed session identity and acknowledgment semantics strong enough to serve as an explicit authoritative adapter contract. Even then, project/task authority remains outside the chat session.

