# Workspace Semantic Execution Experiment Taxonomy v0.1

Status: **DESIGN CANDIDATE / NOT FROZEN**

Parent task: `workspace-semantic-execution-migration-v1`

Machine-readable contract:
`benchmarks/workspace-semantic-execution/experiment_taxonomy_v1.json`

## Decision

Use a **faceted experimental taxonomy**, not a single task hierarchy.

A benchmark record should keep four things separate:

1. **Experiment question** — the causal question being tested.
2. **Fixture phenotype** — what properties the task itself has.
3. **Executor treatment** — model/provider/surface/harness/continuity/resource configuration.
4. **Outcome/validator** — what constitutes success, safety, reliability, and efficiency.

This avoids invalid comparisons such as treating “long,” “research,” “hard,” “tool-using,” and “frontier-worthy” as synonyms.

## Why a tree is insufficient

A tree such as:

`research -> long -> hard -> frontier`

bakes the routing conclusion into the task label. It cannot distinguish:

- a long task that is easy once decomposed;
- a short task with a genuinely difficult coupled residual;
- a tool-heavy task whose difficulty is orchestration rather than reasoning;
- a safe analytical task from an identical reasoning problem with an authority boundary;
- poor performance caused by hidden-state recovery from poor performance caused by reasoning quality.

The benchmark therefore uses orthogonal facets and a coverage matrix.

## Five benchmark suites

### S1 — Reasoning-quality boundary

This is the primary scientific question.

It tests:

- persistent vs stateless continuation;
- decomposition benefit;
- independent critique;
- lower-tier vs frontier residual reasoning;
- hybrid escalation calibration.

Only this suite may support claims about Instant/frontier reasoning capability.

### S2 — Orchestration mechanics

This covers:

- CAS ownership;
- leases/generation fencing;
- stateless resume;
- external waits;
- recovery;
- concurrency;
- durable checkpoints.

PRs #574–#589 primarily belong here.

Success in S2 is necessary infrastructure evidence, but it does **not** imply frontier-equivalent reasoning.

### S3 — Authority and provenance safety

This covers:

- authority-firewall preservation;
- exact provenance;
- stale-owner rejection;
- consequence boundaries;
- adversarial candidate actions.

Failures are hard gates. Higher model capability never creates missing authority.

### S4 — Open-world generalization

This is the unseen-workflow extension proof.

A new workflow/domain must be addable without:

- core-kernel modification;
- a closed domain enum;
- lossy generic wrappers;
- authority leakage.

This remains an architecture-freeze gate.

### S5 — Resource routing

This asks which execution strategy minimizes scarce resources **after quality and safety gates pass**.

Metrics include:

- frontier invocations/allowance;
- Instant/local invocations;
- context volume;
- tool/compute work;
- repeated work;
- wall-clock work excluding deliberate waits.

Efficiency never compensates for failing the quality or authority gates.

## Experiment-question taxonomy

The machine-readable taxonomy defines ten causal question classes:

- `Q0_mechanics`
- `Q1_horizon_externalization`
- `Q2_decomposition_effect`
- `Q3_intrinsic_reasoning_boundary`
- `Q4_independent_critique`
- `Q5_escalation_calibration`
- `Q6_async_wait_recovery`
- `Q7_authority_provenance`
- `Q8_open_world_extension`
- `Q9_resource_efficiency`

The critical separation is:

`Q2` asks whether decomposition solves **size/horizon**.

`Q3` asks whether a residual still needs **stronger integrated reasoning after decomposition**.

That is the empirical distinction between `TOO_LARGE` and `INTRINSICALLY_DIFFICULT`.

## Fixture facets

Every serious fixture should carry a sidecar profile with the following axes.

### Domain/workflow

Domain is an open extension tag. Examples can include research, software engineering, tutoring, document production, operations, or future unseen domains, but the kernel does not own a closed list.

### Reasoning primitives

Multi-label examples:

- retrieve;
- hypothesize;
- causal discrimination;
- plan;
- implement;
- debug;
- experiment;
- interpret;
- optimize;
- critique;
- synthesize;
- prove;
- teach;
- decide under uncertainty.

### Horizon/load

Measure size directly where possible:

- estimated human-equivalent completion time;
- expected reasoning quanta;
- initial context bytes;
- evidence count;
- expected tool actions;
- dependency DAG depth/width;
- external waits;
- environment/repository count.

Human-equivalent duration is useful, but it is only one covariate. METR's time-horizon work motivates measuring it while also showing that task-suite properties matter.

### Decomposability

Record:

- separability;
- independently validatable leaf fraction;
- synthesis coupling.

A high-horizon, highly separable task is the canonical `TOO_LARGE` challenge.

### Reasoning stressors

Record observable stressors rather than an author-declared “hard” label:

- competing hypotheses;
- conflicting evidence;
- causal identification;
- novelty;
- non-local constraints;
- proof/derivation depth;
- uncertainty;
- search-space size;
- distractor density.

An `INTRINSICALLY_DIFFICULT` label is assigned **from evidence after lower-tier attempts/decomposition**, not from importance or author intuition.

### Observability / messiness

Separate:

- full vs partial/noisy observation;
- misleading observations;
- stale evidence;
- specification completeness;
- environmental drift;
- multi-objective tradeoffs.

This matters because realistic “messy” tasks can be materially harder even at similar apparent horizon.

### State/continuity stress

Examples:

- single quantum;
- persistent continuation;
- stateless resume;
- external wait;
- lease recovery;
- concurrent workers;
- critic branch/merge.

### Tool/environment

Record:

- read-only vs reversible mutation vs bounded durable mutation;
- deterministic vs seeded/live stochastic environment;
- tool categories;
- multi-repo requirement;
- build/test/experiment loop.

### Authority/consequence

Authority is independent of reasoning difficulty.

Record:

- analysis-only;
- fixture execution;
- sandbox mutation;
- bounded repo mutation;
- reviewed privileged helper;
- external/irreversible action.

Benchmark routing must fail closed when authority is absent.

### Validator strength

Preferred order:

1. exact terminal-state/oracle validation;
2. deterministic tests/invariants;
3. quantitative continuous score;
4. blinded human rubric;
5. model judge as auxiliary evidence.

A model judge alone should not establish an Instant/frontier equivalence claim.

### Contamination/generalization

Record whether the fixture is:

- public existing;
- private existing;
- freshly authored;
- generated/ephemeral;
- an unseen real workflow.

Also record oracle exposure separately.

The current public GitHub pilot is useful for mechanics, but strong capability claims should move toward fresh hidden or ephemeral evaluator state.

## Four core fixture phenotypes

Do **not** build the full Cartesian product. Stratify around four phenotypes:

### P0 — Easy control

Low horizon, low reasoning stress.

Purpose: detect harness or tool failures.

### P1 — Horizon-heavy / decomposable

High horizon, mostly separable, low-to-medium reasoning stress.

Expected signal: decomposition/stateless continuation should close much of the gap without frontier escalation.

### P2 — Reasoning-heavy / coupled

Low-to-medium horizon, strongly coupled, high reasoning stress.

Expected signal: candidate intrinsic-difficulty boundary.

### P3 — Mixed long + hard

High horizon, partially coupled, high reasoning stress.

Expected signal: decompose first, then escalate only a surviving residual if objective evidence justifies it.

This 2×2 conceptual grid is the cleanest way to separate “too large” from “too difficult.”

## Experimental design

### Paired fixtures

When comparing arms, use the exact same frozen fixture instance, tools, validator, resource envelope, and initial information. Change only the treatment factor.

Examples:

- B vs C isolates persistent vs stateless continuity.
- C vs D isolates decomposition/critic scaffolding.
- D residual vs frontier residual isolates reasoning tier.
- D vs E measures escalation policy rather than task selection.

### Replicates

Model behavior is stochastic. One successful run is insufficient.

For pilot work:

- deterministic mechanics: one exact run can prove a mechanism;
- reasoning comparisons: start with at least three independent trials per arm/fixture;
- reliability claims: increase replication until confidence intervals/failure-mode distributions are informative.

Report both ordinary success rate/pass@1 and an all-`k` reliability statistic. τ-bench's `pass^k` idea is useful because repeated reliability is a different property from occasional success.

### Execution ordering

Randomize or interleave arms when practical so model releases, service drift, or infrastructure changes do not systematically favor one treatment.

### Matched affordances

Comparisons are only meaningful if arms receive equivalent task information and tool affordances, except for the intended treatment.

### Quality before cost

Use lexicographic evaluation:

1. authority/provenance hard gates;
2. objective quality;
3. reliability;
4. routing correctness;
5. efficiency/resource use.

Do not collapse everything into one weighted score where cheaper execution can compensate for being wrong.

## Recommended initial coverage

Before any architecture freeze, the first serious matrix should cover at least:

- research/evaluate/iterate;
- architecture diagnosis;
- artifact revision;
- software debug/repair;
- one unseen-workflow extension.

For the first three established families, include P0–P3 where feasible. The unseen extension is primarily S4.

The existing `research_iterate` pilot should be treated as one fixture instance, not “the benchmark.”

## Benchmark contamination policy

Public static benchmarks can become misleading capability measures once models have seen their tasks or solutions. The recent SWE-bench Verified contamination finding is a direct warning for this program.

Therefore:

- mechanics fixtures may remain public and deterministic;
- scored reasoning fixtures should prefer fresh authored or ephemeral instances;
- oracle data must never enter worker context;
- authoring sessions that saw the oracle are excluded from scored arms;
- stronger claims should use hidden/ephemeral evaluators or externally blinded evaluation.

## External methodology informing this design

- **HELM**: separate scenarios from metrics and make missing coverage explicit.
- **METR task-completion time horizons**: human-equivalent task duration is a useful covariate, but not the sole definition of difficulty.
- **RE-Bench**: realistic iterative environments, matched human/agent affordances, resource budgets, and quantitative scoring.
- **τ-bench**: terminal-state evaluation and repeated-trial reliability.
- **SWE-bench contamination analyses**: public benchmark exposure can destroy the validity of capability inference.

## Architecture consequence

The production router should not carry a field such as:

`difficulty = HIGH -> frontier`

Instead it should reason from evidence such as:

```text
scope/horizon pressure
+ decomposability
+ lower-tier validated attempts
+ residual reasoning stress
+ authority/capability requirements
+ resource state
-> execute / decompose / wait / block / escalate
```

This keeps importance, size, difficulty, authority, and resource scarcity as separate concepts.
