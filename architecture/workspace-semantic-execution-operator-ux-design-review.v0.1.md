# Workspace Semantic Execution Operator UX Integrated Design Review v0.1

Status: **UX-13 IMPLEMENTATION DESIGN FREEZE — PASS / PRODUCTION EVIDENCE GATES OPEN**

Parent task: `workspace-semantic-execution-migration-v1`

Freeze companion:
- `architecture/workspace-semantic-execution-operator-ux-findings-ledger.v0.1.json`
- `architecture/workspace-semantic-execution-operator-ux-freeze.v0.1.json`

Reviewed inputs:
- UX-00 requirements/metrics;
- UX-01 journey/flow catalog;
- UX-02 context, ownership, and ADRs;
- UX-03 OperatorAction/state-machine contracts;
- UX-04 session broker/lifecycle;
- UX-05 hotkey/clipboard contract;
- UX-06 tray/console IA;
- UX-07 recovery/FMEA/state machine;
- UX-08 security/privacy/interaction boundary;
- UX-09 performance budget;
- UX-10 simulator/fixtures/E2E matrix;
- UX-11 usability benchmark/script/checklist;
- UX-12 stack ADRs/protocol/prototype plan.

## 1. Review decision

The v0 operator-bridge **design is frozen for implementation**.

There are no unresolved architecture, authority-model, security-boundary, recovery-model, interaction-model, browser-replaceability, or protocol-design defects that require another UX design slice before a fake-worker prototype may be built.

This is **not** a production-readiness declaration.

Three categories remain deliberately open:

1. **Implementation authority gate** — the current durable task does not authorize new operator-bridge code paths outside the existing architecture/benchmark/test scope.
2. **Empirical promotion gates** — UX-09 measurements and UX-11 human-in-loop usability trials are specified but not run.
3. **Real-account gates** — signed Firefox implementation smoke tests, current policy/product review, normal authentication, and the security checklist must pass before real ChatGPT calibration.

A conditional WebView2 custom shell is not a blocker for the Firefox v0 baseline.

## 2. Integrated product contract

The frozen routine operator experience is:

```text
scheduler hotkey
Ctrl+V
Enter
```

The initial physical binding is Ctrl+B, but UX-11 may reject and replace that key without changing scheduler semantics.

Routine service requires:
- zero manual tab search;
- zero manual worker selection;
- zero manual prompt editing;
- zero manual durable-state relay;
- zero routine scheduler-state interpretation.

Workspace Control decides:
- action ordering;
- session reuse/create/restore/rotate/retire;
- exact packet;
- worker slot/generation;
- durable acknowledgment;
- whether judgment/recovery interrupts the routine loop.

## 3. Authority and state review

**PASS.**

Authoritative classes remain outside the local UX adapter:
- task/workflow truth;
- OperatorAction lifecycle;
- logical session slot/generation;
- authority decisions;
- durable worker acknowledgment;
- validation results.

Local helper/browser state remains non-authoritative cache.

Confirmed invariants:
- browser IDs do not become workflow identity;
- semantic/model inference does not create Permission or widen authority;
- local preparation does not imply submit/completion;
- durable acknowledgment is the only completion evidence;
- unknown continuity fails closed;
- old generations cannot advance current state;
- retry is replacement/supersession, not reset-in-place.

No UX artifact grants the local helper or browser adapter independent execution authority.

## 4. OperatorAction/session review

**PASS.**

The action/session model is implementable without browser-specific semantics:
- atomic action types are frozen;
- claims use CAS/generation fencing;
- local effects carry idempotency keys;
- LOCAL_PREPARED and AWAITING_DURABLE_ACK are distinct;
- late/stale acknowledgments are fenced;
- persistent/general, role-isolated, fresh-per-quantum, and recovery session classes are explicit;
- continuity TRUSTED/UNKNOWN/LOST controls reuse;
- one outstanding packet per conversation is the default;
- task/role/process affinity prevents accidental cross-context reuse.

The local-only drain behavior permits one scheduler hotkey to retire/discard maintenance state and then fresh-query one human service action.

## 5. Browser replaceability review

**PASS after UX-13 requirement convergence.**

UX-00 originally said Chat workers MUST use Firefox. UX-09/UX-12 later made browser replacement an explicit architecture requirement.

The integrated rule is now:

> Chat workers MUST use a dedicated managed worker environment isolated from ordinary browsing. Firefox WorkspaceWorkers is the frozen v0 production baseline. A custom shell may replace it only through the same BrowserPort and only after its explicit security/authentication/performance/usability promotion gates pass.

This preserves:
- dedicated environment isolation;
- Firefox as a concrete implementation target;
- custom-shell replaceability;
- no scheduler-core dependency on Firefox.

The historical dedicated-Firefox ADR remains provenance, but implementation selection is governed by the UX-12 browser-adapter ADR.

## 6. Interaction and attention review

**PASS at design level; empirical UX-11 trial remains open.**

The hotkey/clipboard contract prevents:
- duplicate held-key dispatch;
- background clipboard mutation;
- background focus steal;
- clipboard mutation before browser target readiness;
- automatic previous-clipboard capture/restore;
- automatic resend without durable ack.

Judgment/recovery paths leave the routine paste rhythm and open explicit operator UI.

The tray primary count is `READY_MANUAL_CYCLES`, so normal work does not require a dashboard.

UX-11 freezes the decisive empirical bar:
- 20-action mixed trial;
- zero wrong worker;
- zero wrong packet;
- zero tab searches;
- zero routine interpretation events;
- zero state relay;
- zero abandoned cycles.

Ctrl+B itself is provisional and is rejected on any required native-shortcut collision or unintended scheduler dispatch.

## 7. Recovery review

**PASS at design level.**

Recovery scopes are explicit:
- ACTION;
- SESSION;
- AUTH_DOMAIN;
- LOCAL_BRIDGE.

Critical profile-wide authentication recovery is bounded:
1. freeze affected reuse;
2. classify continuity UNKNOWN;
3. reconcile durable acknowledgments once;
4. supersede unresolved old-generation actions;
5. advance generation exactly once;
6. rebuild from last acknowledged checkpoint;
7. require manual authentication;
8. return to normal scheduler-hotkey → Ctrl+V → Enter service.

Origin return is never continuity proof.

Helper/browser restart, lost tabs, stale replies, sleep/reboot, unconfirmed packets, clipboard overwrite, and recovery re-entry all have fail-closed behavior.

## 8. Security/privacy/OpenAI boundary review

**PASS at design level; implementation checklist and fresh real-account review remain open.**

Frozen Firefox permissions:
- `nativeMessaging`;
- `tabs`;
- `sessions`.

Absent:
- host permissions;
- content scripts;
- activeTab;
- scripting;
- webNavigation;
- webRequest;
- cookies;
- extension clipboard access.

Frozen interaction boundary:
- no ChatGPT DOM/accessibility/screenshot/page-source/output inspection;
- no automatic paste;
- no synthetic keyboard/mouse;
- no Send click;
- no private consumer endpoint/replay;
- no cookie/token/password extraction;
- no safeguard/restriction/auth bypass.

The human remains responsible for:
- Ctrl+V;
- Enter;
- authentication;
- genuine substantive judgment.

The implementation security checklist remains a pre-real-account gate rather than design evidence.

## 9. Local implementation review

**PASS for implementation design.**

Frozen baseline:
- .NET 10 LTS/C# WinForms helper;
- Win32 RegisterHotKey;
- STA write-only clipboard;
- NotifyIcon/operator-recovery UI;
- same-user/elevation named pipe;
- Firefox Native Messaging proxy;
- Firefox ESR 153+ MV3 plain-JavaScript adapter;
- protocol v1.0 with 64 KiB frame cap;
- signed unlisted XPI;
- per-user helper/native-host install;
- no silent updater.

The BrowserPort carries only content-free lifecycle/binding/origin metadata.

The production OperatorBridge transport remains intentionally unfrozen because transport must bind to already-authorized Workspace Control infrastructure, not be invented by the local UX adapter.

## 10. Simulator/testability review

**PASS at contract level.**

UX-10 separates:
- HUMAN_IN_LOOP physical Ctrl+B → Ctrl+V → Enter;
- DETERMINISTIC_CI simulator-only `SIM_HUMAN_SUBMIT`.

Production code cannot invoke simulator submit.

The 38 fixtures/38 E2E obligations cover:
- normal create/reuse/restore;
- concurrent workers;
- slow/no ack;
- stale/late generation;
- helper/browser/adapter crashes;
- auth refresh;
- lost tabs;
- wrong profile;
- restart/recovery;
- payload mismatch;
- adapter parity.

No CI test needs a ChatGPT account.

## 11. Performance/resource review

**PASS as frozen budget contract; empirical results NOT_RUN.**

Frozen UX-09 policy:
- default two live GENERAL_PERSISTENT workers;
- four live managed workers absolute v0 burst ceiling;
- helper Working Set p95 <=100 MiB;
- helper + extension incremental p95 <=150 MiB;
- helper idle CPU mean <=1% of one logical CPU;
- Firefox two-live p95 <=1536 MiB;
- Firefox four-live p95 <=2560 MiB;
- discard 3 of 4 should reduce total Working Set >=25%;
- existing-worker ready p95 <=750 ms;
- restore p95 <=2500 ms;
- create with Firefox running p95 <=2000 ms;
- cold Firefox p95 <=8000 ms.

These are acceptance budgets, not measured facts.

Fake-worker measurements validate mechanical regressions only. Real ChatGPT page memory remains a later target-machine calibration gate.

## 12. Findings classification

### Design blockers

**None.**

The integrated design is sufficiently specific to implement.

### Blocks prototype implementation

**Implementation mutation authority.**

Current durable scope allows architecture/benchmark/test artifacts, but not the proposed new helper/extension implementation paths.

The design freeze cannot widen its own authority.

Smallest required next action:
- establish an authority-owned implementation task/capsule or equivalent reviewed scope that explicitly authorizes the selected code paths.

### Blocks real-account calibration

- implement and pass Firefox target-host smoke checks;
- use a signed extension/native-host install;
- execute UX-08 security checklist against built artifacts;
- re-review current OpenAI Terms/product guidance immediately before testing;
- verify normal manual ChatGPT authentication;
- bind the helper to an explicitly authorized production OperatorBridge transport.

### Blocks production promotion

- UX-09 empirical target-machine performance/resource results;
- UX-11 required human-in-loop usability results;
- zero hard correctness/safety usability failures;
- rollback/install/update smoke evidence;
- successful bounded real-account calibration under then-current product rules.

### Blocks custom-shell promotion only

- WebView2 normal-auth feasibility;
- WebView2 UX-10 adapter parity;
- UX-09 comparison trigger;
- UX-11 no-regression evidence;
- security/update review.

Failure of WebView2 does **not** block Firefox v0.

### Deferred enhancements

- TypeScript/bundler unless extension grows;
- Rust helper unless .NET misses resource budgets;
- silent/automatic updater;
- visual polish beyond required IA;
- additional browser engines beyond WebView2;
- optional clipboard-history/restore concepts;
- broader multi-operator usability research.

## 13. Umbrella-task separation

This UX freeze does not resolve or weaken unrelated umbrella blockers:
- evaluator-runtime isolation for claim-bearing resumable-reasoning benchmarks;
- independent architecture review of the broader semantic-execution design;
- Workspace Shell standing privileged-helper authority;
- claim-bearing replicated scoring/calibration.

Those remain authoritative blockers in the parent task.

## 14. Freeze verdict

```text
UX-00..UX-12 design contracts: COMPLETE
UX-13 integrated review: PASS
v0 operator UX implementation design: FROZEN
prototype code authority: NOT YET GRANTED
empirical UX-09 results: NOT RUN
empirical UX-11 results: NOT RUN
real-account security/policy/auth calibration: NOT RUN
production ready: NO
```

The next safe boundary is no longer another UX design conversation.

It is an authority gate: authorize the implementation paths, then execute UX-12 build slices against the fake-worker simulator before touching a real ChatGPT account.
