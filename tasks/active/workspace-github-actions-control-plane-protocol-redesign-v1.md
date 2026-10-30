<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json`

## Current live boundary

**Do not repeat Inputs #1 or #2.**

- Input #1: **PASS**. Lambda has v3 source generation `09c46818252991f6a55aaeedbcf046c554e2ffee` installed and attested.
- Input #2: **PASS**. One-shot root authority `55f15dfe-a603-4901-b148-2aa11a2c0048` was consumed. `workspace-ci-v3-reconciler.service` and `workspace-ci-v3-provisioner.service` are active; all nine v3 class controllers remain inactive/disabled; Research GPU legacy containment remains intact.
- Input #3: **NOT COMPLETE**. No canary authority was consumed, no v2 controller was stopped, no v3 class controller was activated, and no canary workflow was dispatched.

Latest operator:
- PR #572 branch: `github-actions-control-plane-protocol-redesign-v1`
- operator head: `52b82bcb1c1fe8f9304be6c4e7cd7737b5c88227`
- operator script blob: `36e9a5419f0dcd7e45db8302bc41070cbe9137bc`
- Validation #1361 / run `41018340472`: **SUCCESS**
- installed live generation remains `09c46818252991f6a55aaeedbcf046c554e2ffee`

Latest Input #3 attempt passed root/class preflight, installed-generation binding, exact migration-helper Git-object materialization, and Go 1.26.3 archive verification. It then printed Go module downloads and returned silently before `V3_WORKSPACE_CONTROL_CREDENTIAL=PASS`. In operator-code order this is before `CANARY_AUTHORITY_CREATED`, `GENERATION_EXCLUSION=BEGIN`, `--apply-canary`, or `gh workflow run`.

## Next safe action

Inspect `scripts/lambda_ci_v3_first_canary_live.sh` at `52b82...`. Diagnose the exact silent failure around the Go `v3-canary-preflight` build / immediately following ephemeral `gh auth token` credential staging. Do **not** blindly rerun the same operator.

Before the next live retry, prove:
1. reconciler + provisioner are still active and not boot-enabled;
2. all nine v3 class controllers are inactive;
3. `workspace-ci-controller@research-engine-gpu.service` remains inactive;
4. no canary authority consumption marker, transaction receipt, or canary run was created by the failed attempts;
5. workspace-control v3 credential staging is clean or deliberately recreated.

Then make the corrected operator fail loudly at each pre-transaction command, validate its exact head in CI, and retry **only** `workspace-control-control-small-v1`.

## Hard boundaries

Do not alter Research GPU quarantine/retry authority. Do not start the legacy Research GPU controller. Do not merge/cut over Research Engine PR #283. Do not advance other runner classes until the first bounded Workspace Control canary is accepted.

## Fresh-chat initialization

@GitHub @Heartbeat

https://github.com/adamtrott78/workspace-control

Resume durable task `workspace-github-actions-control-plane-protocol-redesign-v1`.

Read the authoritative capsule:
`tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json`

and this handoff:
`tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.md`

YOU ARE THE CONTINUING EXECUTOR. Perform the work yourself in this chat. Do not return another handoff unless explicitly asked. Start from the live boundary above; do not repeat completed live Inputs #1/#2.
