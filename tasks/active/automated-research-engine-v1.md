<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/automated-research-engine-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: automated-research-engine-v1
- Title: Automated research engine v1
- Status: BLOCKED_RUNTIME
- Capsule schema: v2

## Goal

Design and prove a provenance-preserving automated research engine that turns scholarly literature into structured evidence, durable knowledge, challenged research gaps, fundable research programs, and workspace-control-executable research projects.

## Workflow

- Repository: workspace-control
- Path: policies/OPERATOR_WORKFLOW.md
- Checkpoint: 2ee1f6584178df68d1f01a219fb526d4745707bf

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: automated-research-engine-v1
- Remote checkpoint: 33339103d1a21842ff7479bd72782ab4dc42f9b9
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ee702eb61740456306c9768dc6aca2c854571617
- Remote verified: true

## Recovery restore point

- Identity: ee702eb61740456306c9768dc6aca2c854571617
- stage=model_backed_acceptance_v1
- last_validated_boundary=research-engine/main@ee702eb61740456306c9768dc6aca2c854571617; production_daemon_v1 fully validated; canonical main CI 36820703111 PASS
- agentic_research_v1=complete and CI-validated through durable scheduler, deterministic/semantic workers, source hydration/materialization, live search provenance, knowledge checkpoints, novelty arbitration, crash recovery, budgets, and human gate
- boundary=requires user's Lambda host and host-only OPENAI_API_KEY; connected ChatGPT tooling has no authorized SSH/runtime credential surface
- resume=deploy exact main checkpoint on Lambda, initialize/start PostgreSQL+daemon, run one real model-backed autonomous research topic with conservative budget, verify durable usage/evidence/checkpoint/novelty state reaches WAITING_HUMAN, then mark model_backed_acceptance_v1 VALIDATED

## Next safe action

Genuine runtime/human-secret boundary. On the user's Lambda, deploy exact research-engine/main@ee702eb61740456306c9768dc6aca2c854571617, store OPENAI_API_KEY only in ~/adamArchives/Adam/.research-engine/research-engine.env, start the Docker Compose daemon stack, and run one conservative-budget autonomous research topic to WAITING_HUMAN. Return only non-secret command output/health/report data. Do not paste the API key into chat.

## Remaining work

- Deploy research-engine/main@ee702eb61740456306c9768dc6aca2c854571617 on the Lambda with persistent PostgreSQL/artifact storage and host-only OpenAI credentials.
- Run one real model-backed autonomous research cycle with a conservative per-run budget and verify it reaches durable WAITING_HUMAN with source-grounded evidence, model usage ledger, knowledge checkpoint, novelty challenge state, and human-review payload.
- After model-backed acceptance passes, use the daemon—not manual chat orchestration—to resume deferred RF corpus expansion and begin 24/7 research operation.
- Tune worker concurrency/model-tier budgets from observed cost/latency/quality after the first real run rather than before.

## Blockers / gates

- The remaining acceptance test requires the user's Lambda runtime plus a valid OPENAI_API_KEY stored only on that host. Current connected tooling cannot SSH to the Lambda or obtain/use the user's private API credential.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
