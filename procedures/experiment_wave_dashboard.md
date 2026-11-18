# Experiment Wave Dashboard

Purpose: standard operator-facing terminal view for long-running multi-experiment scientific waves.

This format was adopted during task `mth602-final-multisurrogate-dqnguard-v1` on 2026-11-18 after the H1 weak-backbone HPO wave0 run. It is intentionally compact, tmux-friendly, and designed for repeated use across future experiment campaigns.

## Required view

Render one row per immutable experiment admission.

```text
<PROGRAM> — <WAVE> LIVE DASHBOARD
<N> immutable experiments | refresh 1s | <local timestamp>
Successful-run median: GPU0=<time> GPU1=<time> (used only for RUNNING ETA)

EXPERIMENT          GPU  STATUS        ELAPSED   ETA LEFT      TOTAL       RUN ID
--------------------------------------------------------------------------------
PAIR/TRIAL          G0   RUNNING       0:42:13     ~18:05          -  123456789
PAIR/TRIAL          G1   SUCCESS             -          -    1:02:44  123456790
PAIR/TRIAL          G0   FAILURE             -          -      06:18  123456791
PAIR/TRIAL          G1   QUEUED          31:22          -          -  123456792
--------------------------------------------------------------------------------
SUCCESS nn   FAILED nn   RUNNING nn   QUEUED nn   OTHER nn
```

## Column semantics

- `EXPERIMENT`: stable human-readable experiment identity, normally pair + trial or equivalent immutable job key.
- `GPU`: execution lane/GPU assigned by the admitted request.
- `STATUS`: normalized `SUCCESS`, `FAILURE`, `RUNNING`, `QUEUED`, or `OTHER`.
- `ELAPSED`:
  - RUNNING: wall time since actual run start.
  - QUEUED: wall time since admission/creation.
  - completed jobs: use `-`; completed duration belongs in TOTAL.
- `ETA LEFT`: only for RUNNING jobs. Estimate from median completed successful runtime for the same execution lane when available. Prefix estimates with `~`. If elapsed already exceeds the median, display `>median` rather than fabricating a negative ETA.
- `TOTAL`: completed job wall time from actual start through terminal completion.
- `RUN ID`: durable provider/workflow run identifier.

## Status rules

Use provider truth as authoritative.

For GitHub Actions:

- `status=completed, conclusion=success` -> SUCCESS
- `status=completed, conclusion!=success` -> FAILURE (or preserve a more precise terminal label if useful)
- `status=in_progress` -> RUNNING
- `status=queued` -> QUEUED
- anything else -> OTHER

The dashboard is an observation surface only. It does not create retry, promotion, merge, cancellation, or process-kill authority.

## Critical retrieval invariant

Never infer that an experiment is missing merely because it is absent from one collection page.

The first implementation used:

```bash
gh api repos/OWNER/REPO/actions/runs?event=issue_comment\&per_page=100
```

and four older valid runs incorrectly rendered as `NOT FOUND` after they fell beyond the first 100 results.

Required implementation behavior:

1. Start from the exact immutable set of admitted run IDs.
2. Resolve every admitted run ID independently with:
   ```bash
   gh api repos/OWNER/REPO/actions/runs/RUN_ID
   ```
   or fully paginate the collection until every admitted ID is resolved.
3. Only display `NOT FOUND` when the provider returns a genuine not-found result for that exact run ID.
4. A collection-page miss is `UNRESOLVED`, not evidence that the experiment does not exist.

Direct-by-ID resolution is preferred for small/medium fixed waves because it is simple and fail-closed.

### Reference paginated GitHub implementation

For dashboards that refresh frequently, avoid 24 direct API calls every refresh. Paginate the workflow collection until all immutable admitted IDs are resolved, then stop early:

```python
RUN_IDS = {rid for _, _, _, rid in RUNS}

def fetch_runs():
    found = {}
    page = 1

    while True:
        raw = subprocess.check_output(
            [
                "gh", "api", "-X", "GET",
                f"repos/{REPO}/actions/runs",
                "-f", "event=issue_comment",
                "-F", "per_page=100",
                "-F", f"page={page}",
            ],
            text=True,
            stderr=subprocess.PIPE,
        )
        data = json.loads(raw)
        batch = data.get("workflow_runs", [])

        for r in batch:
            rid = int(r["id"])
            if rid in RUN_IDS:
                found[rid] = r

        if RUN_IDS.issubset(found):
            break
        if not batch or len(batch) < 100:
            break

        page += 1

    return found
```

This preserves a low request count (normally one or two collection requests per refresh) while preventing false `NOT FOUND` rows caused by first-page truncation.

Render refresh and provider polling are separate clocks: render the terminal every 1 second so elapsed/ETA counters move smoothly, but poll GitHub every 5 seconds by default. This gives a 1-second dashboard without wasting API quota on unchanged workflow state.

## ETA policy

ETA is presentation-only and must be explicitly approximate.

Preferred estimator:

```text
baseline(gpu_lane) = median(total_runtime of SUCCESS jobs on same lane)
eta_left = baseline - current_elapsed
```

If there are no successful completed jobs on that lane, show `?`.
If current elapsed exceeds baseline, show `>median`.

Do not mix failed infrastructure runtimes into successful scientific runtime estimates unless the dashboard explicitly labels that estimator.

## tmux usage

Preferred behavior is a persistent named tmux session containing only the dashboard.

Example:

```bash
SESSION="experiment-wave-dashboard"

tmux has-session -t "$SESSION" 2>/dev/null || \
  tmux new-session -d -s "$SESSION"

tmux send-keys -t "$SESSION" \
  "python3 /tmp/experiment_wave_watch.py" C-m

tmux attach -t "$SESSION"
```

Operator controls:

- detach without stopping dashboard: `Ctrl+B`, then `D`
- reattach: `tmux attach -t experiment-wave-dashboard`
- stop dashboard only: `Ctrl+C`

Do not substitute an empty persistent shell when the operator requests the experiment dashboard.

## Current MTH602 reference instance

Wave: H1 weak-backbone HPO wave0.

Immutable size: 24 experiments = 8 trial vectors x 3 weak pairs.

Pairs:

- PA2-PA3
- PA2-PA8
- PA3-PA8

Trial IDs:

- t000 through t007

Lane convention for this wave:

- even trials: GPU0
- odd trials: GPU1

The reference display was accepted by the operator on 2026-11-18.

## Reuse checklist

When a future worker is asked for "the same tmux/dashboard format":

1. Identify the exact immutable experiment admissions from durable state.
2. Build one row per admission.
3. Bind each row to the provider's exact durable run/job ID.
4. Resolve run IDs directly or paginate exhaustively.
5. Show normalized status, lane, running/queued elapsed, approximate running ETA, completed total runtime, and run ID.
6. Refresh in place every 1 second by default; allow a slower override when provider/API limits require it.
7. Keep the view read-only.
8. Preserve tmux detach/reattach behavior.


## Provider failure handling

A provider/API failure must not cause the dashboard to hammer the provider every render tick.

- Render clock: 1 second.
- Normal provider poll clock: 5 seconds.
- On provider poll failure: preserve the last good snapshot, surface the provider error in a compact status line, and wait at least 5 seconds before the next provider attempt.
- Capture and display stderr from `gh api`; a non-zero exit code alone is not a diagnosis.
- For GitHub CLI GET requests with query parameters, prefer explicit `-f/-F` fields over manually concatenating the query string. This avoids shell/CLI parsing ambiguity and makes failures easier to inspect.
