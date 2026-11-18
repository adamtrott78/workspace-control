# Experiment Wave Dashboard

Purpose: standard operator-facing terminal view for long-running scientific experiment waves.

## Architecture invariant

**Primary telemetry MUST be host-local when the operator is already on the execution machine.**

The dashboard refresh loop must not call `gh`, GitHub REST, GitHub GraphQL, or any other provider API.

Use local execution evidence instead:

- process table / process age;
- local runner temp/result directories;
- `train_progress.json`;
- `history.json`;
- `train_complete.json`;
- `train_error.json`;
- a persistent local dashboard cache outside ephemeral runner temp directories;
- GPU telemetry such as `nvidia-smi`.

GitHub/provider state is control-plane evidence, not the live telemetry source. If later reconciliation is needed, perform it separately and explicitly; do not put it in the dashboard refresh loop.

This rule was adopted after a 2026-11-18 MTH602 HPO dashboard exhausted the authenticated user's GitHub REST quota by polling workflow runs too aggressively.

## Required view

Render one row per immutable experiment admission.

```text
<PROGRAM> — <WAVE> LOCAL DASHBOARD
<N> immutable experiments | refresh 1s
Source: LOCAL HOST ONLY — GitHub API calls: 0

EXPERIMENT          GPU  STATUS      EPOCH    PROG    ELAPSED   ETA LEFT      TOTAL       RUN ID
-------------------------------------------------------------------------------------------------
PAIR/TRIAL          G0   RUNNING       6/8   74.3%    1:17:42     ~26:51          -  123456789
PAIR/TRIAL          G1   SUCCESS         -       -          -          -      34:15  123456790
PAIR/TRIAL          G0   INFRA-OOM       -       -          -          -       00:18  123456791
PAIR/TRIAL          G1   WAITING         -       -          -          -          -  123456792
```

## Status semantics

- `RUNNING`: a matching local experiment process is active.
- `SUCCESS`: local `train_complete.json` exists or a previously observed terminal success is in the persistent cache.
- `INFRA-OOM`: local `train_error.json` contains CUDA/out-of-memory evidence.
- `ERROR`: other local terminal training error.
- `INCOMPLETE`: nonterminal local progress exists but no matching active process and no terminal record exists.
- `WAITING`: immutable admitted experiment is not currently visible on the host and has no terminal cache record.

**Do not label a host-invisible experiment `QUEUED` unless a local scheduler/runner queue provides that fact.** Host-local telemetry cannot infer the remote provider queue merely from absence.

## Timing semantics

Use local scientific runtime, not provider workflow wall time.

- RUNNING `ELAPSED`: local process age.
- RUNNING `ETA LEFT`: extrapolate from the current overall training fraction when available.
- terminal `TOTAL`: `elapsed_sec` written by `pa_train_one.py` in `train_complete.json` or `train_error.json`.

Never mix GitHub workflow wall time with local training elapsed under the same column.

## Progress and ETA

Preferred overall fraction:

```text
overall_fraction = ((epoch - 1) + step / steps) / epochs
eta_left = process_elapsed * (1 - overall_fraction) / overall_fraction
```

Only show ETA when the fraction is meaningful. Prefix estimated values with `~`.

## Ephemeral runner results and persistent cache

Current PADataset scientific workflows write live results under:

```text
/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/scientific-results/backbone/<run_name>/
```

Runner temp data may disappear after job cleanup. Therefore the dashboard must keep a user-owned persistent terminal cache, for example:

```text
~/.cache/workspace-control/experiment-dashboards/<wave>.json
```

When a terminal local result is observed, immediately persist its status and `elapsed_sec` to the cache. On restart, load that cache before scanning live runner state.

## Immutable identity

The dashboard may retain provider run IDs as immutable identity metadata for operator reference, but it must not query those IDs during normal rendering.

The admission set should come from durable task state or a frozen local dashboard manifest.

## GPU telemetry

Display local GPU utilization/memory when available using `nvidia-smi`. GPU telemetry is observational only and does not authorize process termination, retry, or resource reallocation.

## tmux behavior

The preferred dashboard runs in a persistent named tmux session.

- display refresh: 1 second;
- renderer: use the terminal alternate screen and cursor-home redraws so each refresh overwrites one fixed frame instead of appending to tmux scrollback;
- GitHub/provider API calls in refresh loop: **0**;
- detach: `Ctrl+B`, then `D`;
- reattach: `tmux attach -t <session>`;
- stop dashboard only: `Ctrl+C`.

Do not substitute an empty persistent shell when the operator asks for the experiment dashboard.

## Current MTH602 implementation

Reference script:

```text
scripts/mth602_wave0_local_dashboard.py
```

Current wave:

- task: `mth602-final-multisurrogate-dqnguard-v1`
- 24 immutable H1 weak-backbone screen experiments;
- pairs: PA2-PA3, PA2-PA8, PA3-PA8;
- trials: t000 through t007;
- even trials: lane G0;
- odd trials: lane G1;
- exact provider run IDs retained only as display identity;
- no `gh` or GitHub API calls.

## Reuse checklist

When a future worker is asked for "the same dashboard/tmux format":

1. Read the durable immutable admission set.
2. Build one row per experiment.
3. Prefer local process and artifact telemetry.
4. Persist terminal observations outside ephemeral runner temp.
5. Refresh the screen every second.
6. Use local progress for ETA.
7. Use `WAITING`, not `QUEUED`, when queue state is not locally observable.
8. Keep provider IDs as metadata only.
9. Make **zero automatic provider API calls** from the dashboard.
10. Keep the dashboard read-only; it must not retry, cancel, kill, promote, merge, or otherwise mutate execution state.
