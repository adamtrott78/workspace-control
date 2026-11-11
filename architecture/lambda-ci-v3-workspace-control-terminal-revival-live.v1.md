# Workspace-control V3 terminal REST revival live transaction v1

## Purpose

This transaction is the separate live authority boundary required after the accepted PR #602 code/state-machine review. It is intentionally narrower than a general V3 controller refresh.

It targets only `workspace-control-control-small-v1`, run **#389** (`42881495845`), job `130058639814`, and the durable ledger key for that exact job. The transaction does **not** write the scheduler ledger. The reviewed V3 controller remains the only actor permitted to revive the record after re-attesting GitHub REST state.

## Frozen source authority

The transaction accepts controller semantics only from the independently accepted PR #602 head:

- controller head: `4196934cad14ddf3238c4637da4229b8d5e0fc60`
- `controller.go` blob: `5823ffbf922ebc367c973a921f28963ea726ffa1`
- `controller_test.go` blob: `8404791b6ffdde9a63fb70978b3403e350478bf6`
- accepted disposition: comment `6801586149`
- automated consumption: comment `6801591386`

The live operator itself additionally requires a **new authority-sensitive independent review** for the exact live-transaction PR head. The operator recomputes the automated request digest, requires exact request key coverage, and requires exactly one bound disposition and exactly one bound automated consumption receipt. Every task/PR/head/review-kind/sensitivity/request-digest field must cross-bind exactly. Any duplicate or conflicting disposition/consumption fails closed. Caller-provided review prose is not authority.

## Exact live preconditions

Immediately before mutation the operator requires:

- production V3 service `workspace-ci-v3-controller@workspace-control-control-small-v1.service` is loaded, active/running, and runs as `ci-ctl-wc-control:ci-gh-workspace-control`;
- V3 provisioner is loaded and active/running with a positive MainPID, while the V3 installed-generation reconciler is validated according to its declared `Type=oneshot`, `RemainAfterExit=yes` steady state: loaded, active/exited, MainPID 0, Result=success, ExecMainStatus=0;
- retired V2 `workspace-ci-controller@workspace-control-cpu.service` is not active;
- production controller policy binds repository `adamtrott78/workspace-control`, scale set `lambda-workspace-control-control-small`, max runners 1, and trusted workflow blob `7e361db3a8ead667c047e9dc3fe12908c10eb96a`;
- GitHub run `42881495845` / job `130058639814` is still queued, has the target scale-set label, and is runner-unbound;
- the run remains issue-comment run #389 at workflow path `.github/workflows/lambda-ci-workspace-control-validation.yml` and head `3bee43a810d739cb199c5091024b8d91115aa5d6`;
- the exact target ledger bytes still hash to `39c5ed5b4b3337433fc8608a82f7d2a767ebd575ab0aa507cf3bbaa70a5fb5b9`;
- the ledger binds the exact job/run/workflow/policy provenance and old request/runner identity recorded by the incident;
- no prior class-specific executable/drop-in override exists;
- the detached transaction checkout is completely clean, including untracked files.

Any drift stops before host mutation and requires fresh review. The controller binary is **not built from the transaction working tree**: the operator materializes `controller/lambda-ci-controller` from a Git archive of the accepted PR #602 controller head and builds that isolated tree with `GOWORK=off`, `GOENV=off`, and empty `GOFLAGS`. Untracked or ambient workspace files therefore cannot influence the accepted controller binary.

## Mutation scope

The operator builds the accepted controller source with pinned Go 1.26.3 and installs it at a **class-specific** override path:

`/opt/workspace-ci/v3/controller-overrides/workspace-control-control-small-v1/lambda-ci-controller-v3`

It installs one target-specific systemd drop-in that overrides only `ExecStart` for:

`workspace-ci-v3-controller@workspace-control-control-small-v1.service`

Then it performs exactly:

1. one `systemctl daemon-reload`;
2. one restart of the target V3 workspace-control controller;
3. observation of the first controller-owned durable ledger change.

It never replaces the shared V3 controller executable and never restarts PADataset or research-engine V3 controllers.

## Revival proof

The first durable ledger mutation must preserve the entire REST provenance tuple and must:

- increment `provision_attempt` exactly once;
- mint a new `request_id`;
- mint a new `runner_name`;
- retain `scheduler_state=REST_ATTESTED_QUEUED_RETRY`.

The operator records the resulting identity in a root-owned transaction receipt. It does not claim the workflow validation succeeded; run #389 completion and exact candidate validation remain a later GitHub evidence gate.

## Rollback boundary

Rollback first stops the target controller and waits until systemd proves it is fully inactive/dead with MainPID 0. **Only after that quiescence** does the operator re-read the scheduler ledger.

If the ledger is still byte-identical to the pre-mutation record, rollback may remove the target drop-in and class-specific executable, daemon-reload, and start the original target service.

If the ledger changed at any point before quiescence completed, the operator **refuses rollback across scheduler state**: it retains the accepted override, leaves the target controller quiesced, records `POST_REVIVAL_FAIL_CLOSED_NO_ROLLBACK`, and never restores old ledger bytes. A failure to quiesce or re-attest the ledger also retains the accepted override and fails closed.

## Explicit non-authority

This transaction has no authority to:

- dispatch, rerun, or cancel any GitHub workflow;
- write or restore the scheduler ledger;
- modify the shared V3 controller executable;
- restart or modify PADataset or research-engine controllers;
- activate or mutate retired V2 workspace-control infrastructure;
- alter runner-class policy, workflow pins, scale sets, credentials, root provisioner, or reconciler.
