# Workspace Control Plane v2 — Current Handoff

> **Derived human-readable view.**
>
> The authoritative task state is:
>
> `tasks/active/control-plane-v2-refactor.json`
>
> on branch:
>
> `control-plane-v2-coordination`
>
> If this file disagrees with the JSON capsule or actual Git state, trust the JSON capsule plus verified Git/runtime evidence.
>
> This Markdown should be regenerated whenever the capsule materially changes.

## Task

**ID:** `control-plane-v2-refactor`

**Title:** Workspace Control Plane v2

**Status:** `VALIDATING`

## Goal

Design, implement, and validate a workspace-control v2 architecture that generalizes the proven tutor, Codex, DIRECT_TOOL, human-gate, and PADataset/MILCOM workflow evidence into an executor-neutral, resumable multi-stage control plane without moving project-domain authority out of project repositories.

## Current target

- Repository: `workspace-control`
- Branch: `control-plane-v2-refactor`
- Base: `cb8368cd50de2d364c2aade8843276aab0b02420`
- Current checkpoint: `93c7cbbd82ed9d46e43c2ad38a57ba81165e8f3e`
- Pushed: `true`
- Current allowed mutation scope:
  - `architecture/control-plane-v2.md`

## Current architecture artifact

- `architecture/control-plane-v2.md`
- State: draft created and pushed; awaiting architecture review before broader implementation

## Next safe action

Review architecture/control-plane-v2.md at control-plane-v2-refactor@93c7cbbd82ed9d46e43c2ad38a57ba81165e8f3e. Do not broaden mutation scope or begin implementation until the architecture draft is reviewed against its ten review questions and the preserved experimental evidence.

## Remaining work

- Review architecture/control-plane-v2.md against its explicit review questions and the preserved MTH602, EAS501, CIS560, MILCOM/PADataset, and Phase-4 Codex evidence.
- Revise the architecture specification only if review finds a demonstrated ownership, vocabulary, portability, or scope defect.
- After architecture approval, update this capsule's allowed mutation scope before modifying policies, schemas, procedures, deterministic tooling, or adapters.
- Deliberately integrate the provisional shared operator/tutor bridge and proven Codex adapter concepts.
- Design and implement topology-aware coordination, workflow/stage semantics, remote-aware preflight/handoff, safe worktree preparation, and minimal workflow/artifact contracts.
- Run regression validation across direct-tool, local-runtime, human-gate, failure-recovery, and both Codex/ChatGPT handoff directions.
- Only after validation, decide promotion to main and later PADataset migration.

## Constraints that matter most

- Do not modify PADataset during the v2 architecture/refactor until the new control plane is validated and an explicit later migration consumes it.
- Do not modify MTH602, EAS501, CIS560, or other course repositories merely to implement workspace-control v2.
- Preserve phase4-codex-adapters at 9d2c088e1929a6a1cdc2aaca6ec1393c3e1e6859 and phase4-chatgpt-to-codex-handoff at 726c31f855d723943cc24b8d31448cf5eaa5532e as evidence; do not redo Phase 4C.
- Preserve shared-operator-tutor-contract at 450eebeef6b76a674913949863082277b6bdb811 as the provisional tutor/operator evidence branch until deliberate integration.
- Project/domain authority remains inside the owning project repository; workspace-control owns reusable coordination, portability, routing, and execution semantics only.
- Do not make LangGraph, Temporal, AutoGen, OpenAI Agents SDK, GitOps tooling, or another framework the canonical control plane; use external systems only as design references unless separately justified.
- Do not create a large permanent executor-capability database before the minimal v2 selection/validation requirements are clear.
- Do not blindly retry failed or ambiguous mutations; inspect actual durable state first.
- For the first implementation phase, mutate only the v2 architecture specification path on the refactor branch; expand mutation scope only after that specification is reviewed.

## Key decisions already made

- Use a separate coordination branch for the task capsule and a separate refactor branch for actual v2 mutations, following the pattern proven in Phase 4C.
- Treat project-local domain authority, shared behavioral contracts, workspace coordination/durable task state, thin executor adapters, and actual executors/surfaces as separate architectural layers.
- Treat DIRECT_TOOL as a first-class autonomous surface for operation classes that have empirical evidence, but keep trust operation-class specific.
- Distinguish reasoning executor from operation surface and from execution topology/data locality; do not encode current GitHub-versus-terminal limitations as permanent executor assignments.
- Treat HUMAN_BROWSER_INGRESS, HUMAN_TERMINAL, specialized external-tool execution, and substantive human judgment as different kinds of boundaries.
- Keep artifact completion separate from student mastery; this remains a tutoring-contract invariant rather than a generic control-plane state.
- Adopt the principle 'more verified stages per autonomous control cycle' rather than optimizing merely for fewer messages.
- Introduce reusable project-owned workflow descriptors as a v2 design target, distinct from live task capsules.
- Introduce stage-level validation and resumability as v2 design targets so completed stages are not replayed after suspension or partial failure.
- Use MILCOM/PADataset evidence to evaluate named deterministic project entrypoints, artifact lifecycle declarations, safe worktree preparation, and project-owned cross-authority consistency validators.
- Use external systems such as Anthropic workflow/agent guidance, Temporal, LangGraph, AutoGen, OpenAI Agents SDK, GitOps, and asset-oriented orchestration only as comparative design references.

## Validation state

- **Preserved evidence branches verified before v2 initialization:** `PASS`
  - GitHub branch endpoints matched the expected main, shared bridge, Codex target, and Phase-4 coordination SHAs.
- **New v2 branches created from exact baseline:** `PASS`
  - Both control-plane-v2-refactor and control-plane-v2-coordination were created from cb8368cd50de2d364c2aade8843276aab0b02420.
- **V2 architecture specification reviewed:** `NOT_RUN`
- **Integrated v2 implementation validated:** `NOT_RUN`
- **Cross-executor regression suite completed:** `NOT_RUN`
- **Initial v2 architecture draft created within authorized target scope:** `PASS`
  - Target branch changed only by architecture/control-plane-v2.md at 93c7cbbd82ed9d46e43c2ad38a57ba81165e8f3e.

## Blockers / known limitations

- The v1 HANDOFF_SAFE checker is local-worktree-centric. This capsule is durable remote coordination state, but formal v1 HANDOFF_SAFE validation requires an isolated local worktree at the recorded checkout path. Do not confuse this known v1 checker limitation with loss of the remote task state.

## Fresh-chat initialization

Use the following as the first message in a new chat:

```text
@GitHub

Continue the durable workspace-control task defined by:

Repository:
adamtrott78/workspace-control

Coordination branch:
control-plane-v2-coordination

Task capsule:
tasks/active/control-plane-v2-refactor.json

Treat the task capsule, the normal workspace-control root route, exact Git state, and the durable evidence referenced by the capsule as the handoff.

Do not rely on previous conversation state.

Follow the capsule's next_safe_action.

Current target branch:
control-plane-v2-refactor

Current target checkpoint:
93c7cbbd82ed9d46e43c2ad38a57ba81165e8f3e

Do not broaden mutation scope beyond the capsule.
```
