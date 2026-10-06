<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-plugin-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-plugin-v1
- Title: Workspace Heartbeat MCP Plugin v1
- Status: COMPLETED
- Current stage: accepted_v041_chronology
- Exact v0.4.1 source: `568acaaf1e8350bb6c781415668d2e965af46f00`
- Branch: `heartbeat-v2-smoke-checkpoint`
- PR: #69

## Current v0.4.1 design

- Routine `heartbeat_update` is a data-only MCP tool with no custom UI resource binding.
- Its ordinary MCP `content` contains the heartbeat prose followed by task ID, sequence, and state.
- This is deliberate: ChatGPT owns inline MCP UI placement, and current documented inline surfaces are host-positioned before the generated model response rather than at an exact tool-call location.
- `heartbeat_get` remains the separate explicit history/sidebar surface using `ui://workspace-heartbeat/panel-v7.html`.
- No polling, reconciliation timer, duplicate render tool, database, or durable heartbeat sink is introduced.
- The old v0.4 update-card source remains historical but is no longer bound to routine heartbeat updates.

## Evidence

- User field evidence showed v0.4 single-message cards were visually correct but collected at the bottom of the thinking/tool block, making chronological interpretation harder.
- Official OpenAI plugin UI guidance exposes no supported metadata for pinning an inline MCP iframe to its exact tool-call position.
- v0.4.1 source regression asserts `heartbeat_update` has no `resourceUri`, emits the heartbeat message in normal content, and leaves `heartbeat_get` as the history UI owner.
- Repository-wide CI remains independently blocked before heartbeat tests by the unrelated schema-invalid `research-engine-local-document-pipeline-v1.json` task capsule.

## Next safe action

Deploy exact Workspace Heartbeat v0.4.1 source checkpoint `568acaaf1e8350bb6c781415668d2e965af46f00` to Lambda, run `npm test`, restart/refresh the custom plugin so the tool descriptor is rediscovered, and perform one long-chat chronology smoke.

Pass requires routine heartbeat result text to stay in chronological order relative to surrounding tool calls. `heartbeat_get` should continue to provide explicit historical/sidebar inspection.

If that passes, checkpoint/close heartbeat and transfer to:

`tasks/active/workspace-lambda-github-tooling-optimization-v1.json`

Before mutating shared Lambda/GitHub tooling, rehydrate:

`tasks/active/workspace-lambda-self-hosted-execution-v1.json`

because its P3/P4/P5 state may have advanced independently.


## Final acceptance — 2026-10-05

- Lambda runtime deployed from exact v0.4.1 source `568acaaf1e8350bb6c781415668d2e965af46f00`.
- Dedicated `workspace-heartbeat-node` runtime reported Node v20.20.2.
- Live custom-plugin descriptor was refreshed after deployment.
- Acceptance sequence passed in one ChatGPT turn: `heartbeat_update` → ordinary GitHub tool call → `heartbeat_update` → explicit `heartbeat_get`.
- Routine heartbeat updates remained ordinary transcript/tool results rather than host-hoisted custom cards.
- `heartbeat_get` retained explicit bounded history/timeline inspection.
- Heartbeat side project is accepted and closed at v0.4.1. Do not reopen UI/card placement work unless new field evidence shows a functional regression.

## Transfer

Resume:

`tasks/active/workspace-lambda-github-tooling-optimization-v1.json`

Before mutating shared Lambda/GitHub tooling, rehydrate:

`tasks/active/workspace-lambda-self-hosted-execution-v1.json`

and use its current durable state rather than the older heartbeat-era snapshot.
