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

The `Operator Bridge Validation` workflow exposes two explicit target
triggers: workflow dispatch with `run_target_benchmark=true`, and the
one-shot `stage09-target` label event on PR #590. Ordinary synchronize/open
pull-request runs never schedule the target job.

The target workstation must first be registered by the operator as a GitHub
self-hosted Windows x64 runner with the additional label
`workspace-operator-target`. The runner must be started interactively under
the same Windows user that owns the Stage-09 `WorkspaceWorkers` benchmark
profile; a Session-0/service runner is rejected. The matrix may temporarily
create the per-user Native Messaging key when no prior registration exists and
removes it again during cleanup.

Dispatch also requires explicit `confirm_ac_power=true` and
`confirm_chrome_memory_saver_disabled=true`. The target job depends on the
normal exact-head validation job, checks out exactly `github.sha`, executes
the full matrix, and uploads `stage09-target-evidence.json` even when a frozen
budget fails.

During the target run, the matrix temporarily points the dedicated HKCU Native
Messaging host key at the exact checked-out Release helper. If a prior value
exists it is restored exactly; if no key existed the temporary key is removed.
No credentials, cookies, tokens, or ChatGPT content are copied or inspected.

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


## Stage-09 fake-worker target adapter gate

Target-machine Stage 09 remains **account-free and fake-worker-only**. Real ChatGPT
calibration remains deferred to `impl_12_real_account_calibration`.

The target benchmark MUST use the distinct Mozilla-signed performance adapter:

- extension ID: `workspace-control-operator@adamtrott78.local`
- extension version: `0.1.9`
- native HELLO adapter version: `0.1.9-perf`
- worker URL: `http://127.0.0.1:8765/fake-worker.html`

Hosted validation builds `stage09-performance-unsigned.xpi` as the exact Mozilla
signing input and publishes its source-SHA/hash manifest beside it. That XPI is
not target-ready until Mozilla signs it. The signed result is placed at:

`%LOCALAPPDATA%\WorkspaceControl\OperatorBridge\Stage09\workspace-control-operator-performance-signed.xpi`

Before any measured target run, `prepare-stage09-target-profile.ps1` verifies
the signed XPI payload against the exact checked-out repo source and rejects any
production ChatGPT worker URL. Firefox 74+ does not permit another desktop
application to silently sideload an extension, so profile setup intentionally
uses the normal Firefox install UI: run the prep script with
`-InteractiveInstall`, approve the signed add-on in the dedicated
`WorkspaceWorkers` profile, and close Firefox. Target execution then runs the
same script with `-VerifyOnly` and performs the native HELLO preflight. The
script refuses to mutate an existing profile without the Stage-09 ownership
marker.

The helper additionally fences the adapter during the native-messaging HELLO.
The target harness accepts only `FIREFOX_EXTENSION / 0.1.9-perf`; a production,
stale, or unknown adapter receives `ADAPTER_IDENTITY_REJECTED` before it can
receive a browser command. A short adapter preflight runs before the long
measurement matrix.

Target setup also temporarily:

- binds the HKCU native-messaging registration to the exact checked-out helper;
- enforces Chrome `HighEfficiencyModeEnabled=0` for the clean Chrome benchmark
  profile; and
- restores/removes both values to their exact pre-run state in cleanup.

The self-hosted workflow uses process-scoped PowerShell execution-policy bypass
only for the runner job so GitHub's Python tool setup can execute on machines
whose persistent Windows PowerShell policy blocks scripts. No persistent
execution-policy setting is changed.
