# Stage 09 Performance Harness

This directory implements the account-free mechanical benchmark tier for
`impl_09_performance_benchmark_execution`.

It is test/integration infrastructure only. It is not referenced by the
production solution or Stage-08 production package.

The harness uses:

- the real WorkspaceOperator Native Messaging proxy;
- the real LocalIpcServer / IpcBrowserPort transport;
- the real production Firefox adapter core;
- a test-only Firefox background wrapper whose only deviation is the reviewed
  loopback fake-worker start URL;
- the deterministic SimulatorWorld action/session authority;
- a write-only STA clipboard adapter backed by the production
  WinFormsClipboardWriter;
- OS process telemetry only.

No DOM, page text, accessibility tree, screenshot, raw URL, cookie, credential,
token, localStorage, IndexedDB, synthetic paste, Enter, Send, or mouse input is
used.

## Evidence classes

`run-stage09-ci.ps1` is a shortened GitHub-hosted Windows regression smoke.
Its output is explicitly `GITHUB_HOSTED_WINDOWS_CI` and
`target_contract_complete=false`. It may validate collector behavior and
catch gross regressions, but it is not the UX-09 target-workstation result.

The frozen UX-09 target-machine gate still requires the exact Windows operator
workstation, 60-second warm-up, 120-second 1 Hz steady-state windows, three
complete browser replicates with Firefox/Chrome order alternation, the frozen
latency repetition counts, Chrome Memory Saver parity control, and the
environment-noise rejection rules.

The current helper also has no reviewed browser-process launcher. Therefore the
frozen cold-Firefox-start Ctrl+B -> LOCAL_PREPARED budget is recorded by this
harness as an implementation gap rather than fabricated timing evidence.
