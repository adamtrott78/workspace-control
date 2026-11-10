# Workspace Semantic Execution Operator Performance Budget v0.1

Status: **UX-09 PERFORMANCE CONTRACT CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Companion benchmark:
- `benchmarks/workspace-semantic-execution/operator_ux_performance_v1.json`

## 1. Decision

UX-09 freezes a **performance contract and reproducible measurement procedure**, not fabricated benchmark results.

The bridge implementation does not yet exist, and the fake-ChatGPT simulator belongs to UX-10. Real-account ChatGPT calibration is additionally gated by UX-12 and the UX-08 requirement to re-check current OpenAI terms/product guidance immediately before real-account testing.

Therefore:

- numerical budgets are frozen now;
- the default live-worker policy is frozen now;
- actual target-machine Firefox/Chrome results are explicitly **NOT RUN**;
- those results are mandatory before UX-13 can treat the operator bridge as production-ready.

This satisfies the UX-09 design acceptance gate without pretending unmeasured numbers are evidence.

## 2. Measurement philosophy

The primary performance collector is **outside the page**.

On Windows, the benchmark sums OS process metrics for the isolated benchmark browser session:
- `WorkingSet64` as the primary resident-RAM metric;
- `PrivateMemorySize64` as a secondary committed/private-memory diagnostic;
- CPU-time deltas normalized to one logical CPU.

Microsoft documents working set as recently referenced resident memory exposed through process objects. Firefox's `about:processes` and Chrome's task manager remain useful manual diagnostics, but they are not the cross-browser source of truth because their attribution/accounting conventions differ.

Current references:
- Microsoft `Get-Process`: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-process
- Firefox Process Manager: https://support.mozilla.org/en-US/kb/task-manager-tabs-or-extensions-are-slowing-firefox

No benchmark step requires ChatGPT DOM/content inspection.

## 3. Browser comparison contract

Compare:

```text
Firefox WorkspaceWorkers benchmark profile
vs.
Chrome clean benchmark profile
```

under matched 0 / 1 / 2 / 4 live-worker-tab conditions.

For live-tab parity:
- use a clean Chrome profile;
- disable Chrome Memory Saver for the matched live-tab runs;
- record browser versions and settings;
- keep Firefox/Chrome free of unrelated extensions.

Chrome documents that Memory Saver may deactivate inactive tabs and reload them on access, so leaving it uncontrolled would make a 4-live-tab comparison ambiguous:
https://support.google.com/chrome/answer/12929150

The comparison reports both:
1. total browser-process memory; and
2. incremental memory above that browser's 0-worker-tab baseline.

### Firefox-selection review trigger

Reopen the dedicated-Firefox ADR when:

```text
Firefox two-live-tab p95 > 1536 MiB
AND
Firefox two-live-tab p95 > Chrome two-live-tab p95 × 1.25
```

or when Firefox exceeds Chrome by both:
- more than 25%; and
- more than 256 MiB absolute.

This is a review trigger, not an automatic architecture reversal. Isolation, security, extension capability, and recovery behavior still matter.

## 4. Frozen latency budgets

| Operation | Budget |
|---|---:|
| Hotkey edge → helper callback, p95 | ≤ 50 ms |
| Clipboard write call → success, p95 | ≤ 50 ms |
| Existing managed-tab activation, p95 | ≤ 300 ms |
| Reuse existing worker: Ctrl+B → ready for manual paste, p50 | ≤ 250 ms |
| Reuse existing worker: Ctrl+B → ready for manual paste, p95 | ≤ 750 ms |
| Reuse existing worker provisional hard ceiling | 1500 ms |
| Restore discarded worker: Ctrl+B → ready, p95 | ≤ 2500 ms |
| Create worker while Firefox is running: Ctrl+B → ready, p95 | ≤ 2000 ms |
| Cold Firefox start: Ctrl+B → ready, p95 | ≤ 8000 ms |
| No-work Ctrl+B → quiet completion, p95 | ≤ 250 ms |

"Ready" means:
- exact current action/generation revalidated;
- required browser operation succeeded;
- packet clipboard write succeeded;
- exact managed target is focused;
- `LOCAL_PREPARED` recorded.

It never means the bridge inferred that ChatGPT accepted or completed the prompt.

## 5. Frozen resource budgets

| Resource | Budget |
|---|---:|
| Native helper working set, p95 | ≤ 100 MiB |
| Helper + extension incremental overhead, p95 | ≤ 150 MiB |
| Helper idle CPU, mean of one logical CPU | ≤ 1% |
| Firefox profile with 2 live worker tabs, working-set p95 | ≤ 1536 MiB |
| Firefox profile with 4 live worker tabs, working-set p95 | ≤ 2560 MiB |
| Firefox 2-live-tab idle CPU, mean of one logical CPU | ≤ 5% |
| Discard 3 of 4 idle tabs: total working-set reduction | ≥ 25% |

The two-tab 1536 MiB target preserves the original UX-00 provisional budget. The four-tab value is an explicit ceiling for burst/role-isolated use, not a new default.

## 6. Active-session cap

### Default

```text
2 live GENERAL_PERSISTENT worker tabs
```

This is now the frozen v0 default.

Why:
- one worker may remain SENT/UNCONFIRMED while another independent worker is serviced;
- it matches the UX-04 session-broker design;
- it bounds memory before empirical calibration;
- it reduces pressure to create new chats while avoiding a permanently large live tab pool.

### Burst ceiling

```text
4 live managed worker tabs maximum in v0
```

Tabs 3-4 are permitted only for:
- workflow-required role isolation;
- explicit benchmark scenarios;
- temporary recovery needs where the session policy permits.

They do **not** justify raising the default pool to four.

No future change may raise the default above two until target-machine measurements pass the four-tab resource budget.

## 7. Discard policy

Firefox exposes `tabs.discard()`, which unloads inactive tab contents while retaining the tab so it can be restored when activated:
https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/discard

The active tab cannot be discarded.

Therefore the initial policy is:

- trusted idle sessions above the two-live-tab default are **discard candidates**;
- discard preserves the logical session/generation;
- retirement remains reserved for semantic/session lifecycle reasons;
- if discard fails to reclaim at least 25% of the total four-tab working set, or restore p95 exceeds 2500 ms, UX-13 must reconsider whether aggressive discard is worth the complexity.

## 8. Reproducible memory procedure

For each browser:

1. Use a clean benchmark profile.
2. Close every unrelated instance of that browser in the benchmark Windows user session.
3. Record OS build, physical RAM, logical CPU count, browser version, power mode, and relevant browser performance setting.
4. Start the required scenario.
5. Allow 60 seconds of warm-up.
6. Collect all benchmark browser processes at 1 Hz for 120 seconds.
7. Sum `WorkingSet64` and `PrivateMemorySize64` across those processes at each sample.
8. Report p50, p95, max, and mean.
9. Run three complete replicates.
10. Alternate Firefox-first vs Chrome-first replicate order.
11. Reject runs with auth/recovery incidents, browser updates/restarts, unrelated same-name browser processes, or sustained unrelated CPU noise above the benchmark threshold.

For discard:
- begin with four live managed worker tabs;
- leave one active;
- discard the other three;
- wait through the same settle window;
- resample;
- restore one, then all, and record memory/latency.

No page title, URL, response, or screenshot is needed for this procedure.

## 9. Reproducible latency procedure

Use monotonic timestamps at:
- hotkey edge received;
- action claim complete;
- browser command sent;
- browser command acknowledged;
- clipboard write begin/success;
- final focus success;
- `LOCAL_PREPARED` record success.

Trial counts:
- reuse: 50;
- restore: 30;
- create: 30;
- cold start: 10;
- primitive hotkey/clipboard/activate/no-work: 100 each.

The benchmark records IDs, generations, operation enums, hashes/refs, timestamps, and redacted result classes only. It records no ChatGPT page content.

## 10. Workload tiers

### Deterministic simulator tier

Once UX-10 exists, its fake worker page becomes the primary regression workload for:
- helper overhead;
- extension overhead;
- hotkey/focus/clipboard latency;
- create/reuse/restore mechanics;
- deterministic memory comparisons.

### Real ChatGPT calibration tier

Before UX-13 production freeze:
- re-check current OpenAI policies/product guidance;
- human performs authentication and any paste/Enter;
- use bounded standardized worker conversations;
- measure only OS/browser process metrics;
- never inspect or collect response content.

This calibration answers the roadmap's "actual Firefox vs Chrome memory under this workload" question.

## 11. Fail/reopen conditions

UX-13 must reopen the relevant architecture/session decision if any of these persist after implementation tuning:

- two-live-tab Firefox p95 > 1536 MiB;
- four-live-tab Firefox p95 > 2560 MiB;
- helper + extension incremental overhead > 150 MiB;
- helper idle CPU > 1% of one logical CPU;
- reuse p95 > 750 ms or frequent reuse exceeds 1500 ms;
- cold-start p95 > 8 seconds;
- discard reclaims <25% of four-tab working set;
- restore p95 > 2500 ms;
- Firefox-vs-Chrome review trigger fires.

A measurement must never be "fixed" by widening UX-08 permissions or adding ChatGPT content automation.

## 12. UX-09 acceptance assessment

**PASS at design-contract level.**

We now have:
- explicit RAM/CPU/latency budgets;
- reproducible Windows measurement semantics;
- a fair Firefox/Chrome comparison;
- discard/restore criteria;
- a frozen two-live-worker default and four-tab absolute v0 burst ceiling;
- exact downstream empirical gates.

Empirical results remain intentionally `NOT_RUN` until the v0 components/workload exist. That is recorded as required evidence for UX-13, not silently treated as completed measurement.
