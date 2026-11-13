# Workspace Semantic Execution — Instant Executor Contract v0.1

Status: **DESIGN FOUNDATION / CALIBRATION REQUIRED**

Parent task: `workspace-semantic-execution-migration-v1`

Current production calibration target: **OpenAI ChatGPT / GPT-6 Sol / Instant**

Logical executor selector: `OPENAI_CHAT_INSTANT_CURRENT`

## 1. Purpose

Define what the orchestrator may safely assume about ChatGPT Instant and what it must measure rather than guess.

The backend MUST NOT encode an undocumented hypothesis such as “Instant has N hidden reasoning tokens” or “Instant equals API low effort.” It routes against an empirically calibrated execution envelope.

The current concrete target is GPT-6 Sol / Instant. The architecture remains model-generation-independent so a future GPT-6.x, GPT-7, or other replacement can be adopted through registry resolution + fresh calibration rather than scheduler redesign.

## 2. Evidence classes

Every Instant property used by routing MUST carry one of:

- **DOCUMENTED** — explicitly stated in current OpenAI product/API documentation.
- **EMPIRICALLY_OBSERVED** — demonstrated by exact, reproducible Workspace Control evidence.
- **UNKNOWN_CALIBRATE** — not published or not yet established strongly enough to become a scheduler invariant.

Model inference, anecdote, or presumed provider economics MUST NOT silently become a routing fact.

## 3. Documented current facts

As of 2026-11-13:

1. On eligible paid ChatGPT plans, selecting GPT-6 uses **GPT-6 Sol** for Instant, Medium, High, and Extra High. Pro uses GPT-6 Pro / GPT-6 Astra.
2. The thinking setting controls how much ChatGPT thinks: Instant is the fast setting; Medium is standard reasoning; High is extended reasoning; Extra High is the highest selectable GPT-6 Sol reasoning level.
3. On Plus and Pro, Instant does not automatically promote itself to a higher thinking level for difficult prompts. Automatic switching may still occur for safety.
4. OpenAI reasoning documentation states that lower reasoning effort favors speed/lower reasoning-token usage while higher effort permits more complete reasoning; reasoning models may adapt the amount of reasoning within an effort level.
5. OpenAI does **not** document a ChatGPT Instant hidden-reasoning-token ceiling, an exact Instant-to-API-`reasoning.effort` mapping, or a fixed per-turn tool-call budget.
6. Product/tool availability is surface/plan/workspace/plugin dependent. Capability must therefore be probed/recorded per executor session instead of inferred from the word “Instant.”
7. GPT-6 can interleave reasoning/answer construction and tool use on supported surfaces; the orchestrator must judge completed durable effects/results, not assume that first visible output means reasoning is finished.

Primary current references:
- https://help.openai.com/en/articles/20001354-gpt-6-and-other-models-in-chatgpt
- https://help.openai.com/en/articles/6825453-chatgpt-release-notes
- https://developers.openai.com/api/docs/guides/reasoning
- https://developers.openai.com/api/docs/guides/deployment-checklist
- https://developers.openai.com/api/docs/guides/latest-model
- https://openai.com/index/gpt-6-for-everyone/

## 4. Empirically observed Workspace Control facts

Historical GPT-5.6 Instant mechanics remain useful mechanics evidence but MUST NOT define the current model capability envelope.

Current GPT-6 Instant evidence includes:

- GPT-6 Instant successfully used connected GitHub tooling through the ChatGPT chat surface.
- GPT-6 Instant P0 protocol screening completed three bounded reasoning invocations, two experiment requests, zero retries, zero frontier escalations, zero model polling, zero manual state relay, and zero authority/provenance violations with objective score 1.0.
- Under the clarified P0 protocol, GPT-6 Instant and GPT-5.6 Sol Instant independently reached the same validated diagnosis/experiment sequence with the same invocation/request counts and zero violations.
- These are non-claim-bearing bounded-screening results. They establish protocol/tool operability and bounded reasoning competence, not equivalence to GPT-6 High or Extra High.

The already-validated queue/CAS/lease/recovery/multi-worker mechanics remain architecture evidence independent of which Instant generation is current.

## 5. Unknowns that matter to orchestration

The following MUST remain UNKNOWN_CALIBRATE until measured:

- exact hidden reasoning budget at ChatGPT Instant;
- whether ChatGPT Instant corresponds to any specific API reasoning-effort value;
- how much reasoning effort adapts upward/downward within Instant;
- how prompt complexity, input length, tool depth, or service load affect the effective reasoning envelope;
- maximum reliable integration width before omission/premature convergence increases materially;
- maximum reliable synthesis fan-in;
- maximum reliable independent tool-chain depth;
- how much persistent-chat continuity improves performance versus fresh durable resume;
- validator-feedback repair efficiency before a stronger effort becomes preferable;
- exact plan/message limits and fallback behavior applicable to the active account at runtime;
- whether a model/surface update changes any of the above without changing the logical “Instant” label.

## 6. Failure model

The orchestrator MUST classify observable failure rather than infer hidden compute.

Primary failure phenotypes to measure:

- **HORIZON_OVERFLOW** — task has too many independent steps/branches but low coupling; decompose.
- **CONTEXT_OVERLOAD** — too much irrelevant/raw context; shrink packet or retrieve progressively.
- **INTEGRATION_OVERLOAD** — too many mutually dependent facts/constraints must be held together; candidate for stronger effort after reasonable decomposition.
- **SYNTHESIS_OVERLOAD** — validated leaf outputs are individually correct but fan-in synthesis loses constraints/relations.
- **TOOL_CHAIN_OVERLOAD** — reliability falls with long serial tool/action chains.
- **PREMATURE_CONVERGENCE** — worker commits to an answer before discriminating evidence is gathered.
- **VALIDATOR_REPAIR_LOOP** — repeated objective failures persist despite bounded feedback/repair.
- **TOOL_OR_TRANSPORT_FAILURE** — not a reasoning failure; repair/retry surface.
- **AUTHORITY_BLOCKED** — no model tier may proceed.
- **WAITING_EXTERNAL** — no model should be burning reasoning while waiting.

## 7. Routing foundation

The scheduler routes to the logical class `OPENAI_CHAT_INSTANT_CURRENT`.

Runtime resolution records:

- provider;
- exact surface-reported model family/version;
- ChatGPT thinking configuration;
- plan/workspace class where relevant;
- connected tool/plugin capability set;
- session/continuity mode;
- calibration profile version;
- calibration timestamp/source head.

Current resolution target:
- provider: OpenAI
- surface: ChatGPT Chat
- model: GPT-6 Sol
- configuration: Instant
- logical selector: OPENAI_CHAT_INSTANT_CURRENT

A model generation change MUST NOT alter task-tree/state-machine semantics. It invalidates or ages the capability calibration profile and triggers focused re-characterization.

## 8. Core scheduler rules

1. **Instant-first is capability-gated, not ideological.**
2. **TOO_LARGE is not INTRINSICALLY_DIFFICULT.** Decompose horizon/context/branching failures before increasing reasoning effort.
3. Prefer multiple small Instant leaves when dependencies permit independent objective validation.
4. Preserve tightly coupled residuals instead of decomposing away the decision that actually requires integration.
5. Use deterministic validators/critics after leaves; worker self-confidence is not evidence.
6. A failed Instant attempt must be classified before retry/escalation.
7. Bounded validator feedback/repair is allowed; repeated unchanged failure becomes evidence for decomposition or stronger effort.
8. Stronger GPT-6 Sol effort is selected for empirically high-coupling residuals, not merely because a task is important.
9. Chat continuity is a cache/optimization. Durable state remains the recovery boundary.
10. The orchestrator never relies on undocumented hidden compute budgets.

## 9. Recalibration triggers

A focused Instant characterization run is required when any materially relevant identity changes:

- GPT model family/version;
- Instant semantics documented by OpenAI;
- ChatGPT surface/harness;
- plugin/tool capability set;
- memory/temporary-chat semantics;
- significant system/prompt harness change;
- validator/packet compiler change that alters task presentation.

Historical profiles remain provenance; they do not silently transfer to a new executor identity.

## 10. Architecture consequence

Backend APIs should ask:

- Is this work inside the **calibrated Instant execution envelope**?
- If not, is the cause decomposable size/horizon/context/tool-chain load?
- After decomposition, is the residual genuinely high-coupling/intrinsically difficult?
- What objective evidence supports a stronger-effort route?

They should NOT ask:

- “How many hidden tokens does Instant get?”
- “Is Instant a weak model?”
- “Is this task important enough for High?”

The provider may change its implementation. Observable capability + durable validation is the stable contract.
