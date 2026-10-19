# Evidence-First Solution Research

## Purpose

Use this procedure before committing to a materially uncertain implementation
direction when external evidence could change which architecture, model, library,
service, or decomposition should be built.

The procedure exists to prevent expensive implementation-first trial-and-error.
It turns a vague engineering question into:

```text
problem framing
→ recover known-good and failed local evidence
→ current external research
→ architecture-family synthesis
→ system-boundary impact review
→ bounded shortlist
→ benchmark / promotion contract
→ implementation handoff
```

It is workspace-level coordination. It does not own project-specific scientific,
course, application, or implementation truth.

## When to trigger

Use this workflow when one or more of the following is true:

- multiple materially different implementation architectures are plausible;
- a new model, framework, service, runtime, or dependency family would be costly
  to integrate or evaluate;
- previous implementation attempts have produced repeated dependency/runtime/
  quality failures without resolving the underlying design question;
- the problem is unfamiliar enough that current external research could
  materially change the plan;
- the decision has a large downstream blast radius;
- the task involves selecting between local, remote, deterministic, model-based,
  agentic, or hybrid approaches;
- a current implementation works but the user is explicitly reopening the
  design space for a better architecture.

Do **not** force this workflow for:

- trivial bug fixes;
- deterministic implementation directly specified by an owning contract;
- routine dependency updates with no architecture choice;
- already-decided implementation where the only remaining work is execution;
- emergencies where the owning project explicitly prioritizes a bounded repair
  over design research.

If uncertainty is small, use the normal operator workflow instead.

## Authority boundary

The owning project remains authoritative for:

- problem/domain truth;
- accepted baselines;
- project-specific constraints;
- existing failure evidence;
- benchmark data;
- scientific or business meaning;
- production promotion decisions.

workspace-control owns only the reusable mechanics for researching and deciding
how to approach a materially uncertain implementation problem.

## Stage 1 — Frame the actual problem

Before searching for products or models, rewrite the request as a capability
problem.

Record:

- what the current system does;
- what is unsatisfactory;
- what must remain unchanged;
- what a successful replacement/improvement would accomplish;
- hard resource, latency, cost, privacy, license, platform, or authority
  constraints;
- what measurements would demonstrate success;
- which current implementation is the known-good rollback baseline.

Avoid prematurely framing the problem as:

> Which model/library should we use?

Prefer:

> What capability is missing, what evidence must it preserve, and what classes
> of architecture could provide it under the owning constraints?

## Stage 2 — Recover local evidence first

Read the owning project/task state before external research.

Build a compact **reuse / exclusion matrix**:

### Reuse

Record components that already work and should be preserved unless new evidence
directly justifies replacing them.

Examples:

- deterministic parsers;
- provenance systems;
- caches;
- broker/scheduler infrastructure;
- validation gates;
- known-good production fallbacks;
- existing model runtimes that could be reused in a narrower role.

### Exclusions

Record approaches already tested and rejected.

For each rejection, preserve the *reason*:

- quality failure;
- resource failure;
- runtime incompatibility;
- licensing failure;
- architecture mismatch;
- zero production coverage;
- provenance failure;
- excessive complexity;
- other measured reason.

Do not rerun a failed approach merely under a new name or with cosmetic prompt
changes.

A rejected approach may be reconsidered only when new evidence changes the
failed premise. Record the changed premise explicitly.

## Stage 3 — Conduct current external research

Search for **similar problems and solution patterns**, not just candidate
products.

Use the best available evidence surfaces for the question:

- current web sources;
- scholarly literature;
- open-source repositories and model cards;
- official documentation;
- benchmarks;
- practitioner/production reports;
- connected project/file sources when applicable.

Prefer multiple evidence classes when the decision is important.

Research questions should include:

1. Who has solved the same or adjacent problem?
2. What architecture did they use?
3. Which part of the problem did each component own?
4. What did they deliberately *not* ask one model/tool to do?
5. How did they preserve grounding, provenance, validation, or rollback?
6. What resource/runtime envelope did the solution require?
7. What failure modes remained?
8. How was confidence or fallback handled?
9. What current implementations are actually runnable under the owning
   environment?
10. Which results are benchmark evidence versus marketing claims?

Prioritize recent evidence when model/library/runtime capabilities evolve
quickly.

## Stage 4 — Synthesize architecture families

Do not collapse the survey immediately into a ranked model list.

First identify materially different **architecture families**.

Examples may include:

- deterministic pipeline;
- specialized-model cascade;
- retrieval + reranking + structured extraction;
- tool-using local agent;
- ensemble / independent verifier;
- local-first + remote fallback;
- teacher/student distillation loop;
- human-in-the-loop residual handling.

For each family, describe:

- decomposition;
- authority/provenance model;
- expected quality;
- expected resource cost;
- operational complexity;
- expected failure mode;
- fallback behavior;
- compatibility with reusable local components.

The goal is to discover whether the problem should be decomposed differently,
not merely to replace one implementation with a larger version of itself.

## Stage 5 — Review system-boundary impact

Before selecting a candidate, ask whether the new architecture changes adjacent
pipeline stages.

Review:

- upstream inputs;
- downstream consumers;
- verification stages;
- materialization/commit points;
- caches and artifact contracts;
- telemetry/accounting;
- rollback path;
- human-review gates.

When a current stage is already production-accepted, preserve it as the known
working baseline until the replacement/simplification is independently
validated.

Do not optimize away a safety/verification layer merely because the new design
appears to duplicate it. First measure whether the new layer makes the old layer
redundant, complementary, or still necessary.

## Stage 6 — Produce a bounded shortlist

Select a small number of candidates or architecture variants.

A useful shortlist normally contains:

- one cheapest/minimal architecture;
- one stronger alternative if the minimal version fails;
- at most one or two residual-specific heavyweight candidates.

For every shortlisted option record:

- why it survived the survey;
- which local components it reuses;
- new dependencies/weights/runtimes;
- license constraints;
- expected resource footprint;
- what specific residual justifies its cost.

Do not download or integrate every interesting candidate.

## Stage 7 — Define the benchmark and promotion contract

Before implementation or heavyweight runtime work, define:

- evaluation dataset/cases;
- current known-good control;
- hard correctness/safety gates;
- quality metrics;
- completeness/coverage metrics;
- provenance/grounding metrics;
- runtime/resource metrics;
- cost/remote-call metrics;
- fallback policy;
- stop conditions;
- promotion threshold;
- rollback condition.

If a local-first design retains a remote fallback, measure:

- eligible cases;
- local-pass cases;
- local-abstain/fail cases;
- remote fallback cases;
- remote calls/tokens avoided;
- quality of locally accepted cases;
- quality of the combined local+fallback system.

Do not assume the fallback will be rare. Measure it.

## Stage 8 — Implementation handoff

Only after the research and benchmark contract are durable should the owning
implementation task begin substantial integration.

The handoff should identify:

- selected architecture;
- preserved known-good baseline;
- excluded approaches;
- first implementation slice;
- smallest new dependency/model set;
- validation plan;
- next escalation that is authorized only if the first slice fails.

Bind the exact workflow identity in a durable task capsule when the task uses
this workflow formally.

## Learning loop

When a fallback, human correction, or stronger model resolves a case that the
cheap/local path could not, consider retaining that result as versioned
training/evaluation evidence if the owning domain permits it.

Possible uses include:

- reranker relevance labels;
- classifier/span labels;
- confidence calibration;
- student-model fine-tuning;
- regression tests;
- benchmark expansion.

Never treat fallback output as ground truth without the owning domain's normal
verification/authority rules.

Preserve holdout cases so improvements are measured on unseen examples rather
than on training data.

## Required outputs

The workflow should leave enough durable evidence to answer:

- What problem are we actually solving?
- What current implementation remains known-good?
- What already failed, and why?
- What comparable systems did we find?
- What architecture families exist?
- Which architecture is preferred and why?
- How could it affect adjacent stages?
- What is the smallest first implementation?
- What metrics determine promotion?
- What remains fallback?
- What would cause us to escalate to the next candidate?

These outputs may live in the owning project's task capsule, design document,
benchmark contract, or other project-owned artifacts.

## Scope discipline

External research may reveal attractive adjacent improvements. Apply the normal
Scope Closure Gate.

Classify findings as:

- required correction;
- bounded enabling change;
- explicitly authorized scope expansion;
- deferred follow-up.

Do not turn a research survey into an uncontrolled implementation program.

## Executor portability

This procedure names capability classes, not one vendor/tool.

An executor may satisfy the research stages using any authorized combination of
web search, scholarly search, repository tools, connected files/apps, local
browsing, or human-provided evidence.

Changing the research surface must not change:

- the problem framing;
- authority boundaries;
- evidence requirements;
- reuse/exclusion discipline;
- shortlist discipline;
- benchmark-before-heavyweight-work rule.
