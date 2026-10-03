<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-document-pipeline-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-document-pipeline-v1
- Title: Research Engine Local Document Intelligence and Compute Offload v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, benchmark, and integrate a provenance-preserving local document-intelligence pipeline that converts content-addressed research PDFs into reusable LLM-ready paper packages, minimizes paid/plan semantic usage and repeated PDF interpretation, and systematically evaluates every research-engine stage for safe deterministic or local-model offload before production deployment on the Lambda.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 134d60630a1bf16499fee169f28456a670de343f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: e9ed7d17e91a8a221aa9f8c4b80793b6f5ce0198
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 1442e787317a94998a60a78d2a2f7582b6192170
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead. On Lambda verify the research-engine checkout is clean on main@1442e787317a94998a60a78d2a2f7582b6192170, fetch origin/main, require origin/main=e9ed7d17e91a8a221aa9f8c4b80793b6f5ce0198, and fast-forward only to that commit. Then run bash deploy/run-paddle-table-fallback-gate.sh. It must derive exactly the 3 persistent TableFormer empty-grid targets, render only their authoritative-PDF table bboxes, run one resident PaddleOCR 3.7.0 General Table Recognition v2 pipeline across those crops, evaluate only those 3 references, keep the daemon stopped, and write user-facing outputs beneath visible ~/adamArchives/Adam/workspace-control-tmp/. Return the compact PADDLE TABLE FALLBACK summary or any ERROR line.

## Remaining work

- Fast-forward Lambda research-engine main to e9ed7d17e91a8a221aa9f8c4b80793b6f5ce0198 with the daemon stopped.
- Run deploy/run-paddle-table-fallback-gate.sh once on exactly the 3 persistent empty-grid targets.
- If Paddle passes its explicit quality gate, promote it only as the persistent-empty-grid table fallback; otherwise characterize that residual before opening another component.
- Integrate CodeFormulaV2 as equation-only escalation, then advance to shared local inference/concurrency and EXTRACT/VERIFY package-consumption validation.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@1442e787317a94998a60a78d2a2f7582b6192170 while canonical remote main is e9ed7d17e91a8a221aa9f8c4b80793b6f5ce0198; fast-forward before the Paddle fallback gate.
- The crop-level Paddle table fallback is CI-gated but unmeasured on Lambda and is not production-promoted yet.
- CodeFormulaV2 passed its quality gate but still awaits shared-serving/concurrency integration and final deployment/license review.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
