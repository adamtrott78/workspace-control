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

### Isolated-runner visibility

If the scientific runner is intentionally isolated with controls such as `ProtectProc=invisible`, a normal operator shell may be unable to see the runner process arguments or job-local result directories even though `nvidia-smi` shows the GPU is busy.

In that case, the preferred fallback is a **read-only elevated host observer**:

- run the exact reviewed dashboard script with `sudo`;
- use root only to read the isolated process table and project job/result directories;
- make no network/API calls;
- do not change runner permissions, groups, ACLs, workflow authority, process state, or systemd state;
- write only the dashboard's persistent user cache, and keep that cache owned by the invoking operator;
- label unprivileged invisibility as `HIDDEN`, never as `WAITING`.

This is preferable to weakening runner isolation or granting the operator durable read access to candidate job trees. The elevated observer is observational only.

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
- when runner isolation hides exact state, invoke the reviewed dashboard with `sudo -E python3 <dashboard>` rather than adding provider polling or weakening isolation;
- GitHub/provider API calls in refresh loop: **0**;
- preferred quick exit: `Ctrl+C` detaches the current tmux client while keeping the dashboard/session alive;
- standard tmux detach remains `Ctrl+B`, then `D`;
- reattach: `tmux attach -t <session>`;
- when a dedicated dashboard implements the `Ctrl+C` detach convention, stopping the renderer requires explicitly killing that observer session or process rather than pressing `Ctrl+C`.

Do not substitute an empty persistent shell when the operator asks for the experiment dashboard.

### Zero-provider tmux launch pattern

The tmux session itself must execute only the reviewed host-local dashboard. Do **not** put `gh run view`, `gh api`, `curl api.github.com`, GitHub GraphQL, or any provider-status command inside `watch`, a shell loop, a Python refresh loop, or tmux status hooks.

Preferred reusable launcher shape:

```bash
SESSION=experiment-dashboard
DASH=/absolute/path/to/reviewed_local_dashboard.py

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" "sudo -E python3 '$DASH'"
tmux attach -t "$SESSION"
```

The elevated process is a **read-only host observer**. It may read `ps`, `nvidia-smi`, and the isolated runner's local result tree, and may write only the operator-owned persistent dashboard cache. It must not mutate the scientific runner or provider state.

A one-time `git fetch` used to obtain the reviewed dashboard source is outside the dashboard refresh loop and does not consume GitHub REST API quota. Once the dashboard starts, its network/provider request count must remain zero.

For a dedicated dashboard, prefer a checked-in tmux launcher beside the renderer so the operator does not need to reconstruct the command manually.

#### Current PA3-PA8/t007 identical-rerun observer

Renderer:

```text
scripts/mth602_t007_rerun_local_dashboard.py
```

Launcher:

```text
scripts/mth602_t007_rerun_tmux.sh
```

From a current Workspace Control checkout:

```bash
chmod +x scripts/mth602_t007_rerun_tmux.sh
./scripts/mth602_t007_rerun_tmux.sh
```

If the execution host does not already have a convenient current checkout, materialize only the reviewed observer files with ordinary Git transport. This is a one-time source sync, not dashboard polling and not GitHub REST:

```bash
set -u
BRANCH=mth602-final-multisurrogate-dqnguard-resume-20261116-v1
SRC="$HOME/.cache/workspace-control/t007-observer-source"
OBS="$HOME/.cache/workspace-control/t007-observer"

mkdir -p "$SRC" "$OBS"
if [ ! -d "$SRC/.git" ]; then
  git init -q "$SRC"
  git -C "$SRC" remote add origin https://github.com/adamtrott78/workspace-control.git
fi

git -C "$SRC" fetch --force --depth=1 origin "$BRANCH"
git -C "$SRC" show FETCH_HEAD:scripts/mth602_t007_rerun_local_dashboard.py > "$OBS/mth602_t007_rerun_local_dashboard.py"
git -C "$SRC" show FETCH_HEAD:scripts/mth602_t007_rerun_tmux.sh > "$OBS/mth602_t007_rerun_tmux.sh"
chmod +x "$OBS/mth602_t007_rerun_tmux.sh"
"$OBS/mth602_t007_rerun_tmux.sh"
```

After the one-time `git fetch`, the tmux dashboard refresh loop is entirely host-local.

This observer displays local epoch/batch progress, overall completion percentage, process elapsed time, extrapolated ETA, projected local finish time, validation metrics when locally available, GPU utilization/memory, and immutable run/job identifiers. It performs **zero `gh` calls and zero GitHub/provider API calls**.

For this dedicated observer, `Ctrl+C` is intentionally rebound inside the renderer to detach the current tmux client without terminating the dashboard. Re-enter with `tmux attach -t mth602-t007`. Outside tmux, `Ctrl+C` retains normal process-interrupt behavior.

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


## Accepted live reference — MTH602 H1 wave0

Validated by the operator on 2026-11-18 at approximately 14:02 EST using the elevated local observer.

Observed properties:

- fixed alternate-screen rendering; no scrollback spam;
- 1-second display refresh;
- zero GitHub API calls;
- both isolated scientific GPU lanes visible simultaneously;
- local GPU utilization/memory visible;
- live per-run epoch, progress percentage, process elapsed, and extrapolated ETA;
- terminal success and infrastructure-OOM states retained in the persistent operator-owned cache;
- immutable provider run IDs displayed only as identity metadata.

Representative validated state:

```text
SUCCESS  8   INFRA-OOM  6   RUNNING  2   WAITING  8

PA3-PA8 t003   G1   RUNNING   3/8   28.9%   05:51   ~14:22
PA3-PA8 t006   G0   RUNNING   1/8   11.8%   03:42   ~27:44
```

At the same instant, host-local GPU telemetry showed both GPUs actively utilized, confirming the root observer could see both isolated scientific lanes correctly.

This implementation is the reusable default for future experiment-wave dashboards unless a future execution backend provides an equally local, read-only telemetry surface with stronger provenance.


## Unified t007 full-matrix observer — 2026-11-22

When the t007 program expanded from the three-pair pilot to all ten canonical PA pairs, the operator requested a single wave view "as if scheduled all at once."

Renderer:

```text
scripts/mth602_t007_fullmatrix_local_dashboard.py
```

Launcher:

```text
scripts/mth602_t007_fullmatrix_tmux.sh
```

Session:

```text
mth602-t007-wave
```

The view contains all ten canonical pairs in one immutable table. Completed pilot pairs are seeded from provenance-valid terminal evidence; active and newly admitted pairs transition using host-local process/result evidence only.

Additional unified-wave semantics:

- pair-weighted wave completion treats each canonical pair as one equal work unit;
- per-run ETA uses local process age and local epoch/batch fraction;
- approximate whole-wave ETA uses the median observed t007 pair duration and the known lane assignment to estimate remaining lane backlogs;
- the whole-wave ETA explicitly excludes provider queue overhead and unrelated OSR/evaluator work;
- an admitted row with no local process/result evidence is labeled `ADMITTED`, not `QUEUED`, because provider queue position is not locally observable;
- terminal rows are retained in the persistent local cache after ephemeral runner cleanup;
- `Ctrl+C` detaches the tmux client and leaves the dashboard alive;
- provider/network calls per refresh: **0**.

Bootstrap from any host checkout follows the same ordinary-Git-transport pattern as the dedicated t007 observer: fetch the reviewed branch once, materialize the renderer and launcher, then run the launcher. The live refresh loop remains entirely host-local.
