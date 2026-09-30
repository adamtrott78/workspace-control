# Workspace Control Plane v2 — Implementation Plan

Status: **draft for review**

Architecture baseline:

`control-plane-v2-refactor@07075963f2d56f1bf76d562de3f6a6dc0d16c43d`

Current reviewed architecture file:

`architecture/control-plane-v2.md`

## 1. Implementation principles

The implementation must preserve five properties throughout the refactor:

1. **Backward evidence preservation.** Existing v1 task-capsule behavior and
   Phase-4 evidence remain interpretable.
2. **No project-domain migration.** PADataset, MTH602, EAS501, CIS560, and other
   project repositories are not modified during control-plane implementation.
3. **Compatibility before cleanup.** Add v2 support alongside v1 behavior before
   removing or renaming any v1 path.
4. **One bounded phase at a time.** Each phase has an explicit path set,
   validation gate, and coordination checkpoint.
5. **Executor neutrality.** Codex, ChatGPT DIRECT_TOOL, human terminal, browser
   ingress, local runtimes, and future surfaces remain consumers of the same
   canonical contracts.

## 2. Branch/evidence strategy

Do not merge the experimental branches wholesale.

Preserve these as immutable evidence:

- `main@cb8368cd50de2d364c2aade8843276aab0b02420`
- `shared-operator-tutor-contract@450eebeef6b76a674913949863082277b6bdb811`
- `phase4-codex-adapters@9d2c088e1929a6a1cdc2aaca6ec1393c3e1e6859`
- `phase4-chatgpt-to-codex-handoff@726c31f855d723943cc24b8d31448cf5eaa5532e`

Implement v2 deliberately on:

`control-plane-v2-refactor`

Coordinate it from:

`control-plane-v2-coordination`

When concepts are imported from an evidence branch, adapt them to the reviewed
v2 architecture rather than blindly cherry-picking overlapping files such as
`README.md`.

## 3. Proposed target tree

The exact tree may change during bounded implementation, but the smallest useful
target is:

```text
README.md
AGENTS.md
repos.json

architecture/
  control-plane-v2.md
  control-plane-v2-implementation.md

policies/
  PORTABILITY_CONTRACT.md
  OPERATOR_WORKFLOW.md
  TUTORING_CONTRACT.md

procedures/
  workspace_status.md
  repo_preflight.md
  worktree_prepare.md
  workflow_descriptor.md
  task_capsule.md
  codex_adapter.md
  TUTOR_EVALUATION.md

schemas/
  task_capsule.schema.json
  task_capsule.v1.schema.json
  task_capsule.v2.schema.json
  workflow_descriptor.v1.schema.json

scripts/
  workspace_control.py

templates/
  COURSE_TUTOR_ADAPTER.md
  WORKFLOW_DESCRIPTOR.example.json

adapters/
  codex/
    global/
      AGENTS.md

.agents/
  skills/
    workspace-control/
      SKILL.md

tasks/
  README.md
  active/
  archive/

tests/
  fixtures/
  test_workspace_control.py
```

The test layout is new and should be added before broad CLI mutation.

## 4. Compatibility model

### 4.1 Task capsule schema versions

Do not mutate v1 semantics in place and call them v2.

Preserve the current schema exactly as:

`schemas/task_capsule.v1.schema.json`

Add:

`schemas/task_capsule.v2.schema.json`

Use:

`schemas/task_capsule.schema.json`

as the current dispatch/documentation schema after v2 support exists. It may
reference both supported versions through JSON Schema composition, but the
deterministic Python validator remains authoritative for workspace-control
semantics.

### 4.2 Validator dispatch

`workspace_control.py task-validate` must dispatch on `schema_version`.

Requirements:

- existing schema_version 1 capsules remain valid under v1 rules;
- schema_version 2 capsules use v2 rules;
- unknown schema versions fail explicitly;
- no v1 capsule is silently interpreted as v2.

### 4.3 Handoff dispatch

`handoff-check` must preserve v1 behavior for v1 capsules.

For v2 capsules, handoff semantics become topology-aware.

This lets Phase-4 evidence remain reproducible while v2 gains remote-only and
composed handoff semantics.

## 5. v2 capsule minimum model

The v2 capsule should remain a recoverable snapshot rather than a giant event
log.

Minimum new concepts to represent:

- exact workflow identity/version when a reusable workflow is used;
- task execution topology;
- parent task/execution owner;
- current stage;
- completed validated stages;
- suspended stage and resume condition when applicable;
- checkpoint or checkpoint bundle;
- remote repository checkpoints;
- local/runtime checkpoint identities when required;
- validations;
- artifacts and relevant lifecycle/provenance identities;
- blockers/gates;
- remaining work;
- next safe action;
- last executor/surface as descriptive observations, not task identity.

Detailed execution history may remain in referenced durable logs/records.

## 6. Workflow descriptor v1

Add a deliberately small project-owned descriptor contract.

The first schema should support only what has repeated empirical evidence:

- schema version;
- workflow ID;
- title/purpose;
- owning repository/context;
- exact entry route;
- stage definitions;
- dependencies/order;
- required authority owners/context paths;
- capability/surface requirements rather than hard-coded executors;
- deterministic project entrypoints when they exist;
- expected artifacts;
- artifact lifecycle declarations;
- validation requirements;
- human/external-tool gates;
- forbidden mutation paths;
- optional idempotency identity.

A workflow descriptor must not contain live task state.

A task capsule referencing it must pin:

```text
repository
path
Git checkpoint/content identity
```

No silent workflow-version migration.

## 7. Artifact lifecycle implementation

Do not add a global artifact database.

Artifact lifecycle should initially be represented inside workflow descriptors
or project-local workflow context.

Support orthogonal properties rather than one exclusive class:

- role;
- origin;
- persistence;
- regeneration;
- review requirement.

The validator should validate structure only.

Project-owned validators determine semantic correctness.

## 8. Preflight evolution

Keep the current command valid:

```text
workspace_control.py preflight --repo <name> --intent <read|mutate>
```

Its default behavior remains local-checkout preflight for backward compatibility.

Add an explicit topology/mode option rather than replacing the command.

Conceptually:

```text
--topology local
--topology remote
```

A composed task performs the required local and remote checks and records the
synchronization boundary rather than using one opaque "hybrid" preflight.

### 8.1 Remote preflight

Validate, when applicable:

- logical repo registry identity;
- expected remote;
- branch/ref;
- advertised SHA;
- expected parent;
- writable policy;
- mutation scope;
- requested operation consequence;
- required connector/write capability.

Do not manufacture a local checkout.

### 8.2 Local preflight

Preserve v1 checks and extend only as needed.

### 8.3 Composed transition check

Before moving between remote and local stages, verify:

- expected remote checkpoint;
- expected local checkpoint;
- required synchronization direction;
- dirty state;
- no assumption that remote writes moved local state.

## 9. Worktree preparation command

Add a new deterministic command, tentatively:

```text
workspace_control.py worktree-prepare ...
```

The exact name may change during implementation review.

It should be read-only by default.

Possible result classes:

- READY;
- CREATE_AVAILABLE;
- NEEDS_REVIEW;
- BLOCKED_DIRTY;
- BLOCKED_DIVERGED;
- BLOCKED_IDENTITY;
- BLOCKED_POLICY.

Creating a new isolated worktree requires explicit mutation intent such as
`--create`.

It must never automatically:

- clean;
- reset;
- stash;
- force checkout;
- rewrite unrelated refs;
- overwrite unrelated files.

## 10. HANDOFF_SAFE and EXECUTION_READY

### 10.1 HANDOFF_SAFE

For v2, evaluate durable recoverability according to topology.

Remote-only tasks do not require local checkout state.

Local tasks require the relevant local state.

Composed tasks require all identities needed for the first incomplete stage.

If a reusable workflow is used, the exact workflow version must resolve.

### 10.2 EXECUTION_READY

Add a separate assessment concept for a proposed executor/surface.

This may initially be a reported field/result rather than a separate CLI command.

It evaluates transient capability such as:

- connector availability;
- credentials/authorized connection presence;
- runtime availability;
- hardware;
- required external artifact;
- outstanding human gate.

Never persist secret material.

## 11. Human-readable handoff rendering

Add deterministic rendering support.

Tentative command:

```text
workspace_control.py task-render \
  --file tasks/active/<task>.json \
  --output tasks/active/<task>.md
```

Requirements:

- JSON capsule remains authoritative;
- rendered Markdown identifies source capsule;
- includes exact current checkpoints;
- includes next safe action;
- includes blockers/gates;
- includes fresh-chat initialization text;
- deterministic ordering/output;
- supports v1 and v2 where practical.

The operating procedure should require regeneration after material capsule
changes.

A later atomic task-update helper may combine validation + render, but v2 should
not require one initially.

## 12. Shared contract integration

### 12.1 PORTABILITY_CONTRACT

Generalize from:

`Codex <-> ChatGPT-assisted human`

to executor-neutral portability across reasoning executors, operation surfaces,
and topologies.

Preserve all proven v1 safety invariants.

### 12.2 OPERATOR_WORKFLOW

Import/refine the provisional bridge contract.

Keep:

- continuous routing;
- DIRECT_TOOL first-class support;
- HUMAN_TERMINAL;
- browser ingress/human gates as distinct surfaces/gates;
- dirty-work protection;
- validation/evidence rules;
- narrow staging;
- remote verification;
- post-push reread;
- failure inspection before retry.

Update terminology to the reviewed v2 vocabulary.

### 12.3 TUTORING_CONTRACT

Import the proven generalized tutoring contract substantially intact.

Do not turn tutoring semantics into generic control-plane state.

Keep:

`artifact completion != student mastery`

inside the tutoring domain.

### 12.4 Course adapter/evaluation

Bring in:

- `templates/COURSE_TUTOR_ADAPTER.md`;
- `procedures/TUTOR_EVALUATION.md`;

and update only the references/terminology required by v2.

## 13. Codex adapter integration

Bring in the proven thin adapter layer:

- `AGENTS.md`;
- `.agents/skills/workspace-control/SKILL.md`;
- `adapters/codex/global/AGENTS.md`;
- `procedures/codex_adapter.md`.

Do not make these files authoritative.

Update them to route through:

`README -> PORTABILITY_CONTRACT -> OPERATOR_WORKFLOW -> relevant procedure`

and through the task capsule/workflow descriptor when appropriate.

No Codex-only workflow semantics may be introduced.

## 14. README/root routing

The root README should become the smallest stable route.

It should explain:

- control-plane role;
- project-local authority boundary;
- normal start route;
- when to read portability/operator/tutoring contracts;
- when to inspect workflow descriptors;
- when to use task capsules;
- that routing is continuous;
- that adapters are thin.

Avoid volatile project status in README.

## 15. Deterministic tests

Add standard-library tests before or alongside CLI changes.

Minimum fixture categories:

### v1 compatibility

- valid v1 capsule;
- invalid v1 capsule;
- v1 handoff-safe local checkpoint fixture;
- v1 non-handoff-safe fixture.

### v2 capsule structure

- remote-only task;
- local task;
- composed task;
- workflow version binding;
- checkpoint bundle;
- suspension/resume;
- unknown schema version;
- invalid secret-like field if the schema prohibits it structurally.

### preflight

- remote expected SHA match/mismatch;
- dirty local checkout;
- divergent local/remote;
- non-writable repo;
- isolated task branch.

### handoff

- remote-only HANDOFF_SAFE;
- local HANDOFF_SAFE;
- composed HANDOFF_SAFE;
- missing workflow version;
- unresolved runtime identity;
- HANDOFF_SAFE but receiver not EXECUTION_READY.

### rendering

- deterministic Markdown output;
- refresh after capsule checkpoint change;
- no authority inversion.

## 16. Implementation phases and gates

### Phase 1 — architecture + plan

Paths:

- `architecture/control-plane-v2.md`
- `architecture/control-plane-v2-implementation.md`

Gate:

- reviewed;
- coordination capsule checkpointed;
- no other target changes.

### Phase 2 — compatibility scaffolding

Paths to add:

- v1 schema copy;
- v2 schema skeleton;
- workflow descriptor schema skeleton;
- tests/fixtures;
- test harness.

Do not change CLI behavior yet.

Gate:

- v1 schema equivalence established;
- schema fixtures parse;
- exact diff reviewed.

### Phase 3 — shared contracts

Integrate:

- portability;
- operator;
- tutoring;
- course tutor adapter/evaluation;
- README routing.

Gate:

- no executor-specific authority;
- no project-domain authority moved;
- v1 procedure references still resolvable.

### Phase 4 — validator + task-render

Modify:

- `workspace_control.py`;
- task-capsule procedure;
- tasks README;
- tests.

Implement:

- schema-version dispatch;
- v2 task validation;
- deterministic human-readable rendering.

Gate:

- all v1 tests pass;
- v2 structural tests pass;
- this v2 coordination task can be rendered deterministically.

### Phase 5 — topology-aware preflight

Implement remote/local topology handling while preserving old CLI invocation.

Gate:

- local v1 behavior unchanged for existing calls;
- remote preflight proven against an isolated workspace-control task branch;
- no local checkout manufactured for remote-only validation.

### Phase 6 — topology-aware handoff + EXECUTION_READY

Implement v2 handoff semantics.

Gate:

- v1 handoff behavior preserved;
- remote-only HANDOFF_SAFE proven;
- local HANDOFF_SAFE proven;
- composed fixture proven;
- receiver-specific readiness distinguished.

### Phase 7 — worktree preparation

Add non-destructive preparation command and tests.

Gate:

- missing isolated worktree can be proposed/created only with explicit authority;
- dirty/diverged states stop safely;
- no normalization behavior.

### Phase 8 — workflow descriptor validation

Add procedure/template/validator support.

Gate:

- exact version binding;
- no live task state in workflow descriptors;
- project-local ownership preserved.

### Phase 9 — Codex adapters

Integrate thin adapter files and rerun read-only adapter discovery validation.

Gate:

- removing adapter layer still leaves workflow conceptually operable.

### Phase 10 — real regression workflows

Run the architecture regression matrix.

Use workspace-control itself first for remote-only tests.

Use a bounded non-PADataset local fixture/worktree for local/runtime mechanics if
possible.

Only after generic mechanics pass, select one existing real workflow as a
reference regression.

MILCOM is a strong candidate because its historical flow is known:

`DIRECT_TOOL -> pushed SHA -> local build/render -> QA/human gate -> source repair`

Do not migrate PADataset's operator architecture during the initial regression.

### Phase 11 — promotion decision

Before merging/promoting:

- all required regression evidence recorded;
- task capsule COMPLETE/HANDOFF_SAFE under v2;
- Codex both-direction handoff rerun;
- no unexplained v1 regression;
- reviewed exact integration diff;
- explicit user decision to promote.

## 17. Initial mutation scope after this plan is approved

Do not authorize every file at once.

The next implementation checkpoint should authorize only Phase 2 compatibility
scaffolding.

Suggested first implementation path set:

```text
schemas/task_capsule.v1.schema.json
schemas/task_capsule.v2.schema.json
schemas/workflow_descriptor.v1.schema.json
tests/test_workspace_control.py
tests/fixtures/**
```

Do not modify `scripts/workspace_control.py` in that same first implementation
step.

This preserves a clean boundary between defining compatibility fixtures and
changing executable behavior.

## 18. Review questions

Before Phase 2 begins:

1. Does the v1/v2 coexistence strategy preserve all prior evidence?
2. Is the proposed workflow descriptor intentionally small?
3. Is artifact lifecycle embedded at the project/workflow level rather than
   centralized?
4. Does task-render solve the human handoff problem without creating authority
   duplication?
5. Is remote-only preflight/handoff added without weakening local safeguards?
6. Are HANDOFF_SAFE and EXECUTION_READY kept distinct?
7. Are secrets excluded from durable task/workflow state?
8. Are implementation phases narrow enough to diagnose regressions?
9. Is PADataset still untouched until generic v2 mechanics are proven?
10. Is the first code-changing phase small enough to review independently?
