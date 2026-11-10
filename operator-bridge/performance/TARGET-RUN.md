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

## Current cold-start blocker

The frozen requirement UX-P003 requires Ctrl+B while the dedicated worker
profile is stopped to reach a ready worker within 8000 ms p95. The current
production helper does not own a reviewed worker-environment launch path, so
that metric cannot yet be measured faithfully. The benchmark records this as
an implementation gap rather than manufacturing a launcher inside measurement
code.

Stage 10 usability work and later promotion remain blocked until the complete
target result exists and every failing mechanical budget is corrected or
explicitly accepted through the owning review authority.
