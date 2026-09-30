# Workspace Control Plane v2 — Current Handoff

> **Derived human-readable view.**
>
> Authoritative task state: `tasks/active/control-plane-v2-refactor.json` on `control-plane-v2-coordination`.
>
> If this file disagrees with the v2 JSON capsule or verified Git/runtime state, trust the JSON capsule plus verified evidence.

## Task

- ID: `control-plane-v2-refactor`
- Schema: `v2`
- Status: `CHECKPOINTED`
- Current stage: `phase11_codex_rerun`
- Execution topology: `remote_only`

## Frozen implementation

- Branch: `control-plane-v2-refactor`
- Checkpoint: `b8aa52e242a07e6aa2036516e401864991183ad2`
- Remote verified: `true`

## Phase 11 completed gates

- Exact integration diff review: `PASS`
- v1 compatibility review: `PASS`
- Active v2 capsule validation: `PASS`
- v2 `HANDOFF_SAFE`: `PASS`

## Preserved history

Complete final v1 coordination history:

`tasks/evidence/control-plane-v2-refactor-v1-final.json`

## Pending gates

- standalone ChatGPT -> Codex -> ChatGPT read-only round-trip;
- explicit user promotion decision;
- if approved, promotion + final verification.

## TTY harness note

Do not launch interactive Codex or human `read` prompts from a shell whose stdin is an enclosing heredoc.

The failed Phase 11 Codex launch occurred only because Codex inherited heredoc stdin and reported:

`stdin is not a terminal`

The v2 capsule validation and HANDOFF_SAFE gate had already passed.

## Next safe action

Phase 11 v2 capsule validation and HANDOFF_SAFE have passed. Run only the final read-only Codex round-trip from a real terminal stdin (standalone command, outside any heredoc). Do not rerun the completed v2 validation. After Codex returns PASS, record the round-trip and request the user's explicit promotion decision.

## Exact coordination checkpoint

`71563dc20be3794e5a1f09bc3178e05a4327f2dc`

## Fresh-chat initialization

```text
@GitHub

Continue the workspace-control v2 promotion task from:

repository: adamtrott78/workspace-control
coordination branch: control-plane-v2-coordination
coordination checkpoint: 71563dc20be3794e5a1f09bc3178e05a4327f2dc
authoritative capsule: tasks/active/control-plane-v2-refactor.json
frozen target: control-plane-v2-refactor@b8aa52e242a07e6aa2036516e401864991183ad2

Phase 11 v2 capsule validation and HANDOFF_SAFE already passed.

Do not rerun those gates.
Run only the final standalone read-only Codex round-trip using real terminal stdin.
Then request explicit user promotion approval.
```
