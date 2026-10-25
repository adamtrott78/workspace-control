<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-research-knowledge-ontology-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-research-knowledge-ontology-v1
- Title: Research Knowledge Ontology v1
- Status: IN_PROGRESS
- Capsule schema: v2
- Current stage: corrected_v0.2_independent_rereview_ready

## Goal

Build and validate a read-only, provenance-preserving scientific-state knowledge projection that reconstructs residuals, hypotheses, assumptions, mechanism families, frozen experiments, executions, results, interpretations, independent reviews, belief updates, authority boundaries, and candidate next actions from durable workspace-control and research-engine evidence—without becoming a new source of scientific truth, policy authority, EXTRACT behavior, or executor permission.

## Review consumed

v0.1 independent review disposition:

`workspace-control@706957531271486b7df510933297fa9169134a65|design@9af5bea619ec5a2f83575b4c8d73d08922f05bdb|benchmark@45bd39a722fc4ec24c8f29ce6c1d4eacda8c7998:BLOCKING_FINDING`

The core ontology architecture was accepted. Five result-affecting replay-contract blockers were identified: missing positive INVALID_EXECUTION coverage; contradiction handling not non-vacuously tested; missing WHY_CURRENT_EXPERIMENT coverage; non-operational anti-hardcoding; and underspecified model-free scoring.

## Corrected frozen v0.2

- Ontology design: `architecture/research-knowledge-ontology.v0.2.json`
- Design blob: `039fd2f888fb1abfb663c841df3425e2aa69fb74`
- Replay benchmark: `benchmarks/research_knowledge/research-state-replay-benchmark.v0.2.json`
- Benchmark blob: `c73f6f531a05386c1177a2709690ad2b06739ea9`
- Base cases: 21
- Required query-family coverage: 10/10
- Evaluation variants: IDENTITY + RELABEL_A + RELABEL_B
- Total exact-scored instances: 63
- Positive INVALID_EXECUTION case: present
- Active contradiction case: present
- Same-query/different-graph adversarial pairs: 2
- Natural-language scoring: disabled
- Exact canonical JSON scoring: required

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: research-knowledge-ontology-v02-corrections
- Remote checkpoint: b9305c7c2146fcbfc01409e26eacafdce7facb90
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 15c2f98feb980f18fac255b74c6a39db5da4ef30
- Remote verified: true
- Benchmark historical source snapshot remains intentionally frozen at research-engine@13a129ef820c611adf6a6ca70598df1e67d56efc.

## Next safe action

Engage an independent reviewer on architecture/research-knowledge-ontology.v0.2.json blob 039fd2f888fb1abfb663c841df3425e2aa69fb74 and benchmarks/research_knowledge/research-state-replay-benchmark.v0.2.json blob c73f6f531a05386c1177a2709690ad2b06739ea9. Re-review must specifically verify closure of all five v0.1 blockers: positive INVALID_EXECUTION coverage; contradiction fixture plus contradiction zero-count gate; 10/10 required query-family coverage including WHY_CURRENT_EXPERIMENT; operational same-query/different-graph + relabel anti-hardcoding; and exact deterministic canonical scoring with no natural-language grading. No implementation before disposition.

## Remaining work

- Obtain independent re-review of exact corrected v0.2 design and benchmark.
- If and only if NO_BLOCKING_FINDING, implement the read-only deterministic projection and exact model-free replay evaluator in workspace-control.
- Validate implementation before executing the 21-case / 63-instance frozen benchmark.
- Do not integrate with live EXTRACT or production semantic-control in this task.

## Blockers / gates

- Corrected v0.2 design blob 039fd2f888fb1abfb663c841df3425e2aa69fb74 and benchmark blob c73f6f531a05386c1177a2709690ad2b06739ea9 require independent re-review before any projection implementation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
`tasks/active/workspace-research-knowledge-ontology-v1.json`

Task ID:
`workspace-research-knowledge-ontology-v1`

Start from the normal workspace-control root route.
Treat the owner capsule, exact durable Git state, v0.1 blocking review, and exact corrected v0.2 design/benchmark blobs as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
Do not implement until corrected v0.2 receives independent NO_BLOCKING_FINDING.
