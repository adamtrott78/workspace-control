# Adam Workspace Control Plane

This private repository owns cross-project operating policy for the working
environment under:

`~/adamArchives/Adam`

It is a **control plane**, not a super-repository and not a replacement for the
context owned by individual projects.

Project repositories retain authority for their own scientific, course,
application, and artifact-specific truth.

## Purpose

The control plane exists to make workflows portable across executors.

The control plane supports multiple reasoning executors and operation surfaces,
including ChatGPT with connected tools, Codex, human-operated terminals, browser
ingress, project runtimes, and specialized external tools.

v2 distinguishes:

- reasoning executor;
- operation surface;
- execution topology/data locality;
- authority;
- consequence level.

Changing executors or surfaces may change the degree of automation, but it must
not change project authority, evidence requirements, validation, or the canonical
workflow.

## Start here

For workspace-level work:

1. read this file;
2. read `architecture/control-plane-v2.md` for v2 architecture work;
3. read `policies/PORTABILITY_CONTRACT.md`;
4. read `policies/OPERATOR_WORKFLOW.md` when execution, mutation, Git, runtime,
   artifact validation, or task-transition routing is involved, and always
   before emitting or requesting execution of a `HUMAN_TERMINAL` shell block;
5. read `policies/TUTORING_CONTRACT.md` when building or operating a
   repository-backed course tutor;
6. inspect `repos.json`;
7. follow only the project/workflow/task route relevant to the work;
8. observe current state relevant to the actual execution topology before
   mutation.

Routing is continuous rather than startup-only. When a conversation materially
changes task ownership, return to the owning project route and load the new owner
before acting.

Do not recursively ingest all project repositories merely because they are
registered here.

## Ownership boundary

This repository owns:

- workspace topology;
- cross-repository operating policy;
- executor-portability requirements;
- future shared deterministic procedures;
- future agent adapters and Skills;
- future cross-project task coordination.

This repository does **not** own:

- PADataset scientific truth;
- MTH 602 course truth;
- project-specific experiment provenance;
- project-specific build or artifact semantics;
- copies of project repositories.

Those remain with their owning repositories.

## Architecture

The intended stack is:

```text
project-local domain authority
        ↓
shared behavioral / portability contracts
        ↓
workspace coordination + durable task state
        ↓
thin executor adapters / routing
        ↓
reasoning executors + operation surfaces
```

Essential knowledge must remain usable if the agent-adapter layer disappears.

## Shared policy contracts

The control plane now has two provisional reusable policy contracts in addition
to the portability contract:

- `policies/OPERATOR_WORKFLOW.md` owns executor-neutral mutation, runtime,
  validation, Git synchronization, and mid-conversation rerouting semantics;
- `policies/TUTORING_CONTRACT.md` owns reusable repository-backed tutoring
  semantics, including learning/completion modes, mastery evidence, pedagogical
  persistence, report provenance, and deadline recovery.

Project repositories should route to these shared owners and retain only their
own domain-specific supplements. They should not copy the complete shared
contracts into each project.

These contracts are integrated into the v2 candidate architecture. Existing
projects retain their pinned compatibility checkpoints until an explicit project
migration is performed.

For new course-tutor projects:

- start from `templates/COURSE_TUTOR_ADAPTER.md` and fill only the local
  course-specific mappings and exceptions;
- validate the result with `procedures/TUTOR_EVALUATION.md`;
- keep the shared contracts in this repository rather than copying them into each
  course repository.

## Reusable course, document, and solution-research workflows

Reusable executor-neutral mechanics live in `workflows/` and route to shared
owners under `procedures/`.

The set covers course bootstrap/migration, content ingestion, assessment
preparation, study sessions, assignment work, cheat-sheet build, communications
ingestion, generic document-artifact build/QA, and evidence-first solution
research.

For a materially uncertain architecture/model/library/service decision, route to
`procedures/evidence_first_solution_research.md` and
`workflows/evidence-first-solution-research.v1.json` **before** beginning a
broad implementation or heavyweight bakeoff. This workflow is intended for
decisions where current external evidence could materially change the design; it
is not required for trivial fixes or already-specified implementation work.

The evidence-first workflow requires the executor to recover the project's
known-good baseline and prior failed approaches, research comparable solutions,
synthesize architecture families, review adjacent pipeline impacts, define a
bounded shortlist, and declare benchmark/promotion gates before expensive
implementation. Project repositories retain all domain truth and final
promotion authority.

These descriptors use workflow-descriptor v1 and are bound by exact Git identity
when a concrete v2 task depends on them. A v2 task still binds **at most one**
workflow descriptor; composition happens inside that descriptor through stages
and procedure routing.

workspace-control owns reusable mechanics only. Course/application repositories
retain facts, source authority, mastery state, artifact content, deterministic
project commands, and submission semantics. Existing active tasks and project
compatibility locks do not migrate automatically.

## Repository registry

`repos.json` records stable repository identity, ownership, and mutation policy.

It intentionally does not record volatile facts such as current branch, HEAD,
dirty state, running processes, or ahead/behind counts. Those must be observed
from the actual checkout when needed.

A logical repository may have multiple Git worktrees. Worktree instances are
runtime state, not separate repository identities.

JSON is used deliberately for the registry so the initial control-plane tooling
can parse it with the Python standard library and remain independent of
project-specific Python environments or third-party YAML packages.

## Deterministic control tooling

`scripts/workspace_control.py` is the initial executor-neutral control-plane CLI.

Its first commands are:

```text
workspace_control.py status
workspace_control.py preflight
```

The corresponding operating contracts live under `procedures/`.

These tools observe state. They do not fetch, clean, switch, stash, reset, stage,
commit, push, or otherwise normalize project repositories.

Mutation preflight performs a read-only `git ls-remote` query when mutation is
proposed directly on a registered canonical branch. This checks the advertised
remote branch SHA without updating local Git refs.

### Risk-tiered validation planning

`scripts/validation_plan.py` computes a fail-closed validation tier from an
exact changed-path set plus a project-owned profile.

For workspace-control, use:

```bash
python scripts/validation_plan.py \
  --profile policies/workspace-control.validation-profile.v1.json \
  --changed-path path/to/change \
  --json
```

The planner escalates unknown or mixed-risk changes and supports
`--force-full`. See `procedures/validation_routing.md` and
`architecture/throughput-ci-efficiency-v1.md`.

For routed mutation work, a reviewed project validation profile is normative: consult it before launching CI. If a repository has no reviewed profile, preserve the owning project's existing/full validation rather than inferring a cheaper tier.

## Scope adherence and heavyweight runtime recovery

For substantial multi-step work, use the Wave-3 control-plane gates before
expanding the task:

- `procedures/scope_closure.md` and `scripts/scope_control.py` classify new
  findings as required corrections, bounded enabling changes, explicitly
  authorized scope expansion, or deferred follow-up work;
- once the owning objective is durably satisfied and required validation passes,
  the Scope Closure Gate requires `CHECKPOINT_AND_STOP` when only non-blocking
  follow-ups remain;
- `procedures/runtime_certification.md` and
  `scripts/runtime_certification.py` provide staged C0-C4 heavyweight-runtime
  certification, typed invalidation, idempotent recovery, structured process
  identity, and compact failure envelopes.
- `procedures/progress_heartbeat.md` and
  `scripts/progress_heartbeat.py` keep long-running work operator-visible by
  reporting bounded objective, milestone progress, current critical-path
  operation, remaining execute-now scope, next durable milestone, and external
  waits; repeated polling is summarized rather than presented as progress;


Do not implement adjacent non-blocking improvements merely because they are
discovered during current work. Record them as follow-ups unless the owning task
explicitly expands scope.

## Durable task capsules

Long-running or executor-switchable work is represented by machine-readable
task capsules under `tasks/`.

The structural contract is `schemas/task_capsule.schema.json`, and the operating
contract is `procedures/task_capsule.md`.

The executor-neutral CLI now also provides:

- `workspace_control.py task-validate`
- `workspace_control.py handoff-check`

`task-validate` checks capsule structure and registry policy.

`handoff-check` combines the capsule with current Git/filesystem state and
reports whether the task is actually `HANDOFF_SAFE`.

A task capsule coordinates work; it does not become a source of project-domain
truth.

## Current maturity

Status: `V2 CANDIDATE`

The v2 architecture is being integrated and regression-tested before promotion
to the canonical branch. Executor-specific adapters remain non-authoritative.


## Operator-visible temporary artifacts

Operator-facing temporary, benchmark, diagnostic, and handoff artifacts that a
human may need to browse or download must be written beneath the visible
workspace path:

`~/adamArchives/Adam/workspace-control-tmp/`

Do not create new human-facing artifacts under a dot-prefixed hidden directory
by default. This keeps artifacts accessible from JupyterLab and similar file
browsers that do not expose hidden paths.

Existing `~/adamArchives/Adam/.workspace-control/tmp/` artifacts remain valid
legacy inputs and recovery evidence. Do not move, delete, or regenerate them
merely to satisfy this convention. New workflows may read legacy hidden inputs
while writing all new outputs to the visible temporary root.

A workflow may honor `WORKSPACE_CONTROL_TMP_ROOT` when an explicit alternate
visible scratch root is needed.
