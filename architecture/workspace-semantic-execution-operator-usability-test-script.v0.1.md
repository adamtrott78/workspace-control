# Workspace Semantic Execution Operator Usability Test Script v0.1

Status: **UX-11 USABILITY TEST CONTRACT CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Companion:
- `benchmarks/workspace-semantic-execution/operator_ux_usability_v1.json`
- `architecture/workspace-semantic-execution-operator-usability-feedback-checklist.v0.1.md`

## 1. Objective

Test whether the operator can service work as a low-attention mechanical queue rather than as manual tab orchestration.

The benchmark is not trying to prove that the operator can understand the internal scheduler. Success means the opposite: routine operation should not require that understanding.

The normal physical loop remains:

```text
scheduler hotkey
Ctrl+V
Enter
```

The default candidate hotkey is `Ctrl+B`, but the semantic scheduler command is the requirement. The physical binding is replaceable.

## 2. Hard-stop rules

Stop the affected trial immediately for:
- wrong worker;
- wrong packet/hash;
- stale generation advancing;
- automatic resend without durable ack;
- unexpected background focus steal;
- background clipboard mutation;
- any need to weaken UX-08 security boundaries.

These are system defects, not operator mistakes to average away.

A hotkey collision is different: it rejects the binding, not the bridge architecture.

## 3. Test environment

Use:
- UX-10 fake worker/simulator;
- the actual native helper once UX-12 provides it;
- the selected browser adapter under test;
- normal workstation keyboard/mouse;
- normal foreground applications for collision trials.

Do not use:
- real ChatGPT for initial usability acceptance;
- synthetic typing/paste/Enter;
- DOM/page-content instrumentation;
- screen or keystroke recording unless separately reviewed.

Automatic traces may contain only the existing telemetry allowlist.

## 4. Trial preparation

Before each trial:

1. Record adapter ID/version and configured scheduler hotkey.
2. Reset simulator fixture to its exact initial state.
3. Verify bridge starts in the required ON/OFF state.
4. Verify no unrelated managed-worker tabs/surfaces are present.
5. Zero manual observation counters.
6. Start content-free simulator/helper trace.
7. Do not preview the scheduler's worker-selection sequence unless the trial explicitly requires it.

The operator may know the trial category, but should not manually choose which worker receives each packet.

## 5. Counting operator-attention events

### Count an interpretation event when

The operator stops the routine rhythm to inspect tray/console/browser/task state to answer:
- which worker should I use?
- which packet comes next?
- did that worker finish?
- which session survived?

Do **not** count:
- noticing the primary ready count;
- following an explicit recovery instruction;
- making a genuine substantive judgment at a judgment gate.

### Count manual tab search when

The operator visually scans or manually selects tabs/surfaces to locate the intended worker.

A tab accidentally visible after the helper focuses it does not count.

### Count abandoned cycle when

The operator has invoked or is about to invoke the service loop but stops because the target, packet, or next required physical action is unclear.

## 6. UT-01 — Five-action clean batch

Run five deterministic actions containing reuse, create, and restore.

For every serviceable action:
1. press scheduler hotkey;
2. after target preparation returns, press Ctrl+V;
3. press Enter;
4. do not inspect worker state to determine what to do next;
5. repeat when another cycle is ready.

Pass requires:
- five valid durable acknowledgments;
- zero hard failures;
- zero tab searches;
- zero interpretation events;
- zero abandoned cycles.

This is the basic motor-model sanity test.

## 7. UT-10 — Twenty-cycle motor rhythm

Run twenty simple service-ready cycles with minimal fault complexity.

Purpose:
- test whether the three-keystroke pattern becomes mechanically repeatable;
- reveal accidental double scheduler presses;
- reveal whether the binding itself is awkward.

The operator should not race the helper. Each scheduler press occurs after the prior local dispatch has returned control.

Pass:
- zero sequence errors;
- zero unintended extra dispatches;
- routine rhythm friction <=2/7;
- worker-selection confidence >=6/7.

## 8. UT-02 — Twenty-action mixed batch

Run the deterministic mixed fixture containing:
- reuse;
- create;
- restore;
- local-only retire/discard draining;
- at least two independent unconfirmed workers.

Do not inspect tabs or task state.

Pass:
- zero wrong worker;
- zero wrong packet;
- zero manual tab search;
- zero routine interpretation event;
- zero manual durable-state relay;
- zero abandoned cycle.

This is the primary v0 usability gate.

## 9. UT-03 — Interruption trial

Inject five interruptions between completed local dispatch returns.

Examples:
- edit code for 30-60 seconds;
- switch to a terminal;
- read a document;
- short idle;
- intentionally open and close operator console.

On return, the operator should resume with the scheduler hotkey rather than remembering a worker.

Pass:
- zero worker/packet error;
- zero manual tab search;
- zero background focus/clipboard mutation;
- next cycle requires no reconstruction.

## 10. UT-04 — Multiple SENT/UNCONFIRMED workers

Allow two independent workers to remain unconfirmed while more work becomes ready.

The operator must not be required to remember:
- which worker was serviced first;
- which has acknowledged;
- which one to use next.

The tray/console counts may be viewed if the operator intentionally wants status, but routine worker selection must remain automatic.

## 11. UT-05 — Judgment gate

When the fixture promotes a judgment gate:
- press scheduler hotkey;
- verify the operator console opens to the exact gate;
- verify clipboard is unchanged;
- make the test judgment through its owning simulator authority path;
- return to routine operation.

Pass requires no attempt to service a worker while a substantive decision is required.

## 12. UT-06 / UT-07 / UT-08 — Recovery trials

Run separately:
- managed worker tab/surface loss;
- simulated profile-wide auth refresh;
- helper/browser restart.

The operator follows only explicit recovery UI instructions.

The operator must not manually inspect all tabs or task state to determine what survived.

Pass:
- zero state-reconstruction events;
- zero old-generation reuse;
- no duplicate generation advance;
- no duplicate local effects;
- no more than three distinct operator instruction steps before return to routine, excluding the time spent performing unavoidable authentication itself.

After recovery, the next routine worker must again be serviced by:
```text
scheduler hotkey
Ctrl+V
Enter
```

## 13. UT-12 — No-work/background acknowledgment

Exercise:
- scheduler hotkey with no ready action;
- worker acknowledgment while foreground focus is in another app.

Pass:
- no-work press does not launch/focus browser or alter clipboard;
- background ack updates counts only;
- no focus steal;
- no interpretation required.

## 14. UT-11 — Bridge OFF

Turn bridge OFF.

Verify:
- scheduler global binding is unregistered;
- foreground application receives its normal shortcut;
- no bridge clipboard/focus action occurs.

This test runs before collision testing so the operator has a known baseline for application-local shortcut behavior.

## 15. UT-09 — Representative-work hotkey collision trial

This decides whether `Ctrl+B` survives.

Run 60 minutes of representative work across the normal application mix, with only simulator work available to the bridge.

Record:
- intentional scheduler-hotkey presses;
- attempts to use the same physical shortcut for an application-local function;
- accidental scheduler invocations;
- subjective interference.

Examples of normal work surfaces should include the user's usual:
- browser;
- VS Code/editor;
- Jupyter/notebook;
- terminal;
- document/editor workflow.

### Binding acceptance

Retain `Ctrl+B` only if:
- unintended scheduler dispatches = 0;
- required native shortcut collisions = 0;
- interference <=2/7.

If any condition fails:
1. choose a new configurable binding;
2. change only the physical binding;
3. rerun UT-01, UT-02, UT-03, UT-09, and UT-10;
4. keep all scheduler semantics unchanged.

There is no requirement to defend `Ctrl+B` if another binding is better.

## 16. Subjective questions

After each relevant trial, capture only the short ratings in the companion checklist.

The most important questions are:
- Did I ever have to decide which worker/tab was next?
- Did I ever worry that the clipboard held the wrong packet?
- Did I need to reconstruct state after an interruption?
- Did recovery tell me exactly what I had to do?
- Did the global hotkey interfere with normal work?
- Did the routine loop feel mechanical rather than interpretive?

Free-text comments are optional and should avoid including packet/ChatGPT content.

## 17. Evidence and scoring

Correctness/safety thresholds are binary, not averaged.

Subjective thresholds are evaluated per required trial:
- friction/interference: <=2/7;
- confidence/clarity: >=6/7.

A failed subjective threshold does not authorize weakening correctness/security behavior. It triggers a UX/binding/presentation revision and rerun.

## 18. UX-11 design acceptance

The design is complete when:
- objective thresholds are durable;
- all required trial procedures are reproducible;
- the hotkey retention rule is explicit;
- recovery/judgment trials are separated from routine service;
- empirical results remain clearly NOT_RUN until the simulator/helper/browser spike exists.

Production usability acceptance is not claimed until the required human-in-loop trials actually pass.
