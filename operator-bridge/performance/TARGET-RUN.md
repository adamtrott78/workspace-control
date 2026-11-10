# Stage 09 target-workstation execution

Stage 09 is not complete until the frozen UX-09 contract is executed on the
actual Windows operator workstation. GitHub-hosted Windows evidence is
regression evidence only.

## Frozen target validity

A complete target result must use:

- AC power with the Windows power mode recorded;
- the exact OS build and Firefox/Chrome versions recorded;
- no unrelated Firefox/Chrome processes in the benchmark user session;
- sustained unrelated total CPU no greater than the frozen rejection
  threshold;
- 60 seconds warm-up and 120 seconds of steady-state sampling at 1 Hz;
- three complete Firefox/Chrome resource replicates with browser order
  alternated;
- Chrome Memory Saver disabled and its state recorded;
- 5 discard/restore resource replicates;
- latency repetitions: reuse 50, restore 30, create 30, cold start 10, local
  primitives 100;
- OS process telemetry only and no page/content inspection.

A complete result must satisfy
`stage09-target-evidence.schema.json`. Partial collectors may emit useful
evidence but may not set `target_contract_complete=true`.

## Full target matrix runner

`../tools/run-stage09-target-matrix.ps1` is the canonical Stage-09 target
orchestrator. In full mode it:

- rejects pre-existing Firefox, Chrome, or WorkspaceOperator processes;
- requires explicit AC-power and Chrome-Memory-Saver-disabled confirmations;
- runs three Firefox/Chrome resource replicates in F->C, C->F, F->C order;
- runs three Firefox zero-worker baselines without the extension for bridge
  overhead attribution;
- runs five Firefox discard/restore replicates;
- runs exactly one full 50/30/30/10/100 latency suite and uses resource-only
  Firefox replicates for the remaining resource trials;
- rejects measured windows whose mean unrelated system CPU exceeds 20%;
- evaluates every frozen UX-09 latency/resource budget;
- validates the final content-free result with
  `validate-stage09-target.py` before accepting it.

Full mode requires the two explicit switches
`-ConfirmAcPower -ConfirmChromeMemorySaverDisabled`. Those switches are
operator assertions about the benchmark environment; they do not grant bridge
execution authority.

`-PlanOnly` emits the exact target matrix without touching browsers. CI runs
this mode to syntax-check the orchestrator and freeze its order/counts, but that
output remains non-target evidence and cannot complete Stage 09.

## Opt-in self-hosted target execution

The existing `Operator Bridge Validation` workflow also exposes an explicit
workflow-dispatch target job. It never runs on pull requests or ordinary
workflow dispatches unless `run_target_benchmark=true`.

The target workstation must first be registered by the operator as a GitHub
self-hosted Windows x64 runner with the additional label
`workspace-operator-target`. The runner must be started interactively under
the same Windows user that owns the `WorkspaceWorkers` Firefox profile and
Stage-08 HKCU Native Messaging registration; a Session-0/service runner is
rejected.

Dispatch also requires explicit `confirm_ac_power=true` and
`confirm_chrome_memory_saver_disabled=true`. The target job depends on the
normal exact-head validation job, checks out exactly `github.sha`, executes
the full matrix, and uploads `stage09-target-evidence.json` even when a frozen
budget fails.

During the target run, the matrix temporarily points the dedicated HKCU Native
Messaging host key at the exact checked-out Release helper, then restores the
prior Stage-08 registration in its cleanup path. No Firefox profile files,
credentials, cookies, tokens, or ChatGPT content are copied or inspected.

## Firefox partial target collector

`../tools/run-stage09-target-firefox.ps1` executes the Firefox/helper portion
against the installed, dedicated `WorkspaceWorkers` Firefox profile. The
profile must already contain the reviewed signed extension and the Stage-08
native-host registration must already exist.

The script fails closed if Firefox is already running. It does not kill or
adopt unrelated browser processes, edit the Firefox profile, read page content,
or synthesize ChatGPT input. It serves only the local fake worker and launches
the dedicated profile with Firefox's profile-selection command line.

The collector uses the full 60-second / 120-second windows and full repetition
counts, but its output remains `TARGET_MODE_PARTIAL` because the full contract
also requires the Chrome parity replicates and the cold-start requirement.

## Cold-start target probe

The frozen requirement UX-P003 requires Ctrl+B while the dedicated worker
profile is stopped to reach a ready worker within 8000 ms p95. The production
helper now has a bounded chrome-level launch adapter for the fixed
`WorkspaceWorkers` profile. The target Firefox collector follows its
steady-state run with a dedicated `cold-target` mode that executes exactly
10 cold-start dispatch trials through that production launch adapter.

The cold probe records the PID returned by the reviewed launcher and terminates
only that owned Firefox process tree between repetitions. If any other Firefox
process exists before a trial or remains after owned-process cleanup, the run
fails closed rather than killing or adopting it.

Stage 10 usability work and later promotion remain blocked until the complete
target result exists and every failing mechanical budget is corrected or
explicitly accepted through the owning review authority.
