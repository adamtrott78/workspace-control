# Stage 12 Real-Instant Retry Procedure v1.15

Status: **REVIEWED PROCEDURE CANDIDATE / NON-AUTHORITY**

Parent task: `workspace-semantic-execution-migration-v1`

## Purpose

Repeat the bounded D4 real-Instant calibration once with the Q2 continuity probe repaired so the continuity evidence value is validator-only and cannot appear in the Q2 worker packet.

## Frozen implementation basis

- Repair source head: `3058e98bc95087d3759631cd9b2c23065c8b1da4`
- Candidate baseline: `d9f636ef508245459b3dd0a35b8d5587f533bac6`
- Calibration harness blob: `8b0f3a11e39e47417ea46487791e4b7e5cdb577a`
- Linux transaction blob: `a25ec2594fce96a20e3d8fdff8346c274f2056bb`
- Stage-12 real-Instant test blob: `fe53eb4d2016b44aa072a214570a60ae1fbca8ec`
- Stage-12 static regression blob: `ea35516d7c73f5a22673c94a054f62120debcf45`
- Accepted A7 frontend checkpoint: `a9532ca8b86b7839822939a970e16af1d4a41864`
- A7 frontend source tree: `51480cc44f62d661421e975e67af127ecd0b0417`
- A7 dev harness blob: `ac035d2fc898274c32cad43954ce44c15b198207`
- WOP wrapper blob: `87e2b22d010adcefde075089156ec4c8d3974964`
- Remote bootstrap blob: `905d1f8e21c45c78fd244f1192a420ff457f221c`

Exact repair validation:
- Workspace Control #3158 — SUCCESS
- Semantic Execution #460 — SUCCESS
- Operator Bridge #731 — SUCCESS

## Operator command

After a separately persisted exact v1.15 one-shot authority is 3/3 green and branch-stable:

```powershell
wop d4
```

Do not manually edit worker packets. Do not press Tab to resolve plugin mentions. The normal human loop remains:

`Ctrl+Space -> Ctrl+V -> Enter`

## Required pre-consumption gates

1. `STAGE12_CANDIDATE_BASELINE=PASS`
2. `TAILSCALE_STAGE12_ROUTE_ABSENT=PASS`
3. `STAGE12_SEMANTIC_LIVE_BINDING=PASS`
4. `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`

Any abort before step 4 does not consume the live attempt. Any success or failure after step 4 consumes it.

## Corrected Q2 continuity contract

Q1 places a fresh `continuity:stage12-continuity-...` evidence value only in the managed conversation and explicitly tells the worker to retain it.

Before Q2 becomes serviceable, the harness MUST prove:

`STAGE12_Q2_CONTINUITY_TOKEN_HIDDEN=PASS`

The exact Q2 compiled packet MUST NOT contain the continuity token value. If it does, the harness fails closed with:

`q2_continuity_token_disclosed_in_worker_packet`

The validator still expects Q2 to publish both:
- the Q2 marker; and
- the continuity evidence value recovered from the immediately preceding conversation.

Success then requires `STAGE12_PERSISTENT_SESSION_REUSE=PASS`.

## Q3 replacement contract

The generation-0 stale action is deterministically fenced, a replacement session generation is created, and the replacement worker publishes only the generation-1 Q3 candidate. A stale result must not mutate durable state.

## Connected-tool mention contract

The packet objective supports literal connected-tool mentions. GitHub remains empirically proven as raw `@github` without autocomplete selection, Tab, or click.

Literal `@Workspace Shell` is implemented as a supported packet prefix but is **not yet a live-proven invocation spelling**. Do not rely on it for consequential execution in this D4 retry. Its first proof should be a harmless read-only Workspace Shell leaf in the subsequent integrated research-iterate system test.

## Success boundary

D4 is accepted only when the corrected run proves:
- Q1 exact candidate observation and durable ingest;
- Q2 token-hidden marker before Q2 service;
- Q2 durable acceptance with true preceding-conversation continuity;
- stale-generation fencing;
- generation-1 Q3 replacement publication and durable ingest;
- final Stage-12 calibration success marker;
- cleanup of the reviewed private route/runtime.

No silent retry is permitted after live-authority consumption.
