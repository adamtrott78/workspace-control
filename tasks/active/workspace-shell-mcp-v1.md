<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-mcp-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-mcp-v1
- Title: Workspace Shell MCP v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Give ChatGPT durable, auditable, least-privilege command-execution access to the Lambda workspace through a separate private MCP/plugin so workspace-control tasks can execute and inspect bounded shell operations directly without using the operator as a copy/paste terminal relay, while preserving explicit provenance, credential isolation, rollback boundaries, and independently reviewable privileged authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: a802c417ffcc0bea604263ad029ed1b17f94656a
- Remote verified: true

## Next safe action

DEFERRED. Do nothing until the operator explicitly resumes workspace-shell-mcp-v1. On resume, start with read-only recovery of the current Lambda and private-MCP transport topology and freeze a threat model/tool-authority design before implementing any command-execution endpoint.

## Remaining work

- When resumed, recover the exact current Lambda/Heartbeat/Secure-MCP transport state without mutating it.
- Research the current supported private MCP connection path and freeze the Workspace Shell tool schema, authentication model, filesystem policy, process model, output limits, audit/receipt contract, and emergency disable path.
- Design the unprivileged execution identity and a separate minimal privileged helper/sudo boundary; explicitly enumerate allowed privileged operations needed by workspace-control.
- Independently review the exact frozen threat model and authority contract before implementation.
- Implement and adversarially test the private Workspace Shell MCP in isolation.
- Perform isolated Lambda acceptance with no production authority, then separately gate live ChatGPT connection.
- After acceptance, document how durable workspace-control tasks may invoke Workspace Shell without bypassing task-specific mutation/review gates.
- Use the completed control-plane incident chain as an acceptance scenario: reproduce a bounded exact-SHA read/execute/receipt workflow without requiring the operator to relay terminal commands manually.

## Blockers / gates

- Implementation is explicitly deferred by the operator.
- No current connected ChatGPT plugin provides general SSH/terminal execution against the Lambda host.
- The future command-execution and privileged-authority threat model has not yet been frozen or independently reviewed.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
