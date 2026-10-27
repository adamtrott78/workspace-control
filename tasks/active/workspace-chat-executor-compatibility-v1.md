<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-chat-executor-compatibility-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-chat-executor-compatibility-v1
- Title: Chat-mode executor compatibility and delegated-context containment v1
- Status: SUSPENDED
- Capsule schema: v2

## Goal

Empirically verify that future Chat-mode model transitions preserve the full workspace-control operating experience with equal or better accuracy, precision, durability, and operational safety. Build a frozen GPT-5.6 Sol Chat golden baseline and run the same black-box benchmark corpus in GPT-6 Chat, with special emphasis on whether individual tool operations or internally delegated execution steps lose procedural context and whether workspace-control/GitRunner deterministic authority boundaries contain such losses safely. The supported operator surface remains ordinary Chat mode; Work/Codex or other token-metered execution surfaces are not acceptable substitutes for compatibility.

## Current disposition

- Intentionally suspended. Do not let this task interrupt GitRunner P1 or current system restoration.
- Resume after critical functionality is restored, or earlier only if GPT-5.6 Sol availability becomes time-sensitive for golden-baseline capture.

## Next safe action

Do not execute benchmark work now. Return immediately to the active GitRunner/system-restoration task. When this compatibility task is deliberately resumed, first verify current ordinary Chat model availability and product behavior, then freeze the benchmark/scoring contract before capturing any golden baseline. If GPT-5.6 Sol removal becomes imminent before core restoration is complete, perform only the minimum frozen baseline capture needed to preserve a valid reference, then suspend again.

## Remaining work

- After core system restoration, survey the then-current ordinary Chat model/harness behavior and freeze a black-box benchmark contract.
- Select representative real workspace-control tasks plus adversarial context-fragmentation cases.
- Define exact scoring for reasoning quality, tool-context continuity, deterministic authority containment, recovery fidelity, and operational economics.
- Capture the GPT-5.6 Sol Chat golden baseline in fresh sessions with exact starting states and durable receipts.
- Run the identical corpus in GPT-6 Chat.
- Classify every difference by reasoning, harness/context continuity, containment, or recovery failure.
- Open bounded hardening tasks for evidence-supported gaps without weakening existing authority boundaries.
- Rerun until critical cases meet equal-or-better accuracy/precision and zero unsafe authority violations.
- Freeze CHAT_EXECUTOR_COMPATIBILITY_V1 certification and Chat-mode migration/rollback procedure.

## Blockers / gates

- Intentionally suspended until critical system functionality, especially GitRunner P1, is restored enough that benchmark work will not derail recovery.
- Golden GPT-5.6 Sol baseline must be captured while that model remains selectable; resume earlier if availability becomes time-sensitive.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
`tasks/active/workspace-chat-executor-compatibility-v1.json`

Task ID: `workspace-chat-executor-compatibility-v1`

Start from the normal `workspace-control` root route.
Treat the authoritative task capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced evidence as the complete handoff.
Do not rely on previous conversation state.
This task is intentionally suspended unless the operator explicitly resumes it or GPT-5.6 Sol availability becomes time-sensitive for golden-baseline capture.
Do not substitute Work/Codex/API execution for ordinary Chat mode.
Follow the capsule's `next_safe_action`.
