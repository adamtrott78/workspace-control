# Workspace Semantic Execution — Recursive / Asynchronous Reasoning Research v0.1

Status: **DESIGN INPUT / REAL-WORKFLOW-FIRST**

Parent task: `workspace-semantic-execution-migration-v1`

Current target executor: `OPENAI_CHAT_INSTANT_CURRENT` → ChatGPT / GPT-6 Sol / Instant.

## 1. Core conclusion

There is substantial prior work supporting the central design hypothesis:

> Long-horizon reasoning can be improved by replacing one monolithic inference with repeated bounded reasoning cycles connected by explicit state, external memory, verification, replanning, and recursive/decomposed subcalls.

This is not equivalent to preserving a model's hidden internal reasoning state across turns. Each model invocation is a new inference conditioned on available context. What can persist is explicit state: observations, hypotheses, partial solutions, plans, critiques, validator results, and durable environment effects.

The architecture should therefore treat each Instant turn as one reasoning quantum in a larger externalized process.

## 2. Relevant prior work

### Self-Refine (Madaan et al., NeurIPS 2023)

Iterative generator → feedback → refinement loops improved task performance without model retraining. The same model can benefit from multiple test-time passes over its own output.

Source:
- https://arxiv.org/abs/2303.17651
- https://papers.nips.cc/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html

Implication:
- A bounded Instant result need not be terminal.
- Validator/critic feedback can be fed into a subsequent Instant quantum.

### Reflexion (Shinn et al., 2023)

Agents store verbal feedback/lessons in memory and use them to improve subsequent attempts. This is effectively externalized test-time learning without weight updates.

Source:
- https://arxiv.org/abs/2303.11366

Implication:
- Durable lessons from failures should be compact state, not buried in chat history.
- Retry should change the worker's state/premise, not repeat the same prompt.

### ReAct (Yao et al., 2022/2023)

Interleaves reasoning with environment actions and observations.

Source:
- https://arxiv.org/abs/2210.03629

Implication:
- Reasoning should be split at observation boundaries.
- External effects/results are first-class inputs to the next quantum.

### Tree of Thoughts (Yao et al., 2023)

Turns reasoning into explicit search over intermediate thought states rather than one linear generation.

Source:
- https://arxiv.org/abs/2305.10601

Implication:
- Parallel candidate exploration + evaluation can substitute for some deeper single-pass search.
- The orchestrator can own branch generation/evaluation rather than relying on one hidden reasoning trajectory.

### Test-time search / backtracking

Work on verifier-guided test-time search shows that additional inference-time compute is often better spent selectively revising weak branches than regenerating everything.

Examples:
- Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters: https://arxiv.org/abs/2408.03314
- Improving Test-Time Search with Backtracking Against In-Context Value Verifiers: ICLR 2025 / OpenReview.

Implication:
- Preserve validated partial work.
- Backtrack only to the failed decision boundary.
- Reasoning cycles should be incremental and state-addressable.

### RAFA — Reason for Future, Act for Now

The agent plans ahead, takes one action, stores feedback in memory, then reinvokes reasoning and replans from the updated state.

Source:
- https://proceedings.mlr.press/v235/liu24ab.html

Implication:
- Replanning every step is a legitimate long-horizon control architecture.
- One Instant quantum can produce only the next bounded action/plan segment rather than solving the full task.

### MEM1 (2025)

Shows long-horizon agents can maintain a compact evolving state instead of appending the entire interaction history, improving both efficiency and performance.

Source:
- https://arxiv.org/abs/2506.15841

Implication:
- Persistent chat history is useful but should not be treated as the primary memory substrate.
- Maintain a compact canonical working-state object and inject only relevant context.

### COMPASS (ACL 2026)

Separates tactical execution, strategic oversight, and context management. A Meta-Thinker asynchronously monitors progress while a Context Manager continually compresses/reorganizes history into stage-specific briefs.

Source:
- https://aclanthology.org/2026.acl-long.152/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC13682274/

Implication:
- Our worker / critic / context-manager split has direct precedent.
- Strategic review does not have to block every tactical worker step.
- Context curation is a control-plane responsibility.

### Recursive Language Models (Zhang, Kraska, Khattab, 2025/2026)

Treat long prompts as an external environment that a model can inspect, decompose, and recursively call itself over. Reported substantial gains over vanilla long-context and common agent scaffolds on long-context tasks.

Source:
- https://arxiv.org/abs/2512.24601

Implication:
- Recursive self-delegation is directly relevant to our task-tree design.
- Large context should be treated as an addressable external object, not blindly stuffed into one prompt.
- Recursive child calls can increase effective test-time compute while preserving bounded local contexts.

### Long-horizon surveys / "horizon gap"

Recent work distinguishes:
- long-context = token capacity;
- long-horizon = number/duration/interdependence of required steps;
- long-term memory = persistence across steps/sessions.

Source:
- https://arxiv.org/abs/2608.06663

Implication:
- A huge context window does not solve long-horizon execution.
- Reliability needs process-level state, validation, and checkpoints.

## 3. Persistent ChatGPT chats: what they give us and what they do not

Persistent chats are useful because prior visible context can condition later turns and reduce packet reconstruction overhead.

However, persistent chat is **not** equivalent to one uninterrupted long internal reasoning trace:

- hidden latent reasoning from a prior turn is not a durable state object available to the next turn;
- long histories can become distracting or be compacted/summarized;
- merely retaining every prior token can reduce reasoning quality;
- provider-side context handling may change over time.

Therefore:

> persistent chat = opportunistic working-memory cache;
> durable semantic state = authoritative reasoning continuity.

The orchestrator should maintain an explicit compact state even when reusing the same conversation.

## 4. Proposed recursive asynchronous reasoning loop

For one logical ReasoningProcess:

1. **LOAD**
   - Recover compact canonical state + relevant evidence.
2. **FOCUS**
   - Select one unresolved decision / bounded work quantum.
3. **REASON**
   - GPT-6 Instant proposes a next action, subproblem decomposition, hypothesis update, or candidate result.
4. **ACT**
   - Use tools / request experiments / produce artifact changes where authorized.
5. **OBSERVE**
   - Ingest durable results/events.
6. **VERIFY**
   - Run deterministic/domain validator or independent critic.
7. **CONSOLIDATE**
   - Update compact durable state: findings, rejected paths, open questions, evidence refs, next boundary.
8. **ROUTE**
   - COMPLETE, CONTINUE, DECOMPOSE, WAIT, REPAIR, or ESCALATE.
9. **YIELD**
   - End the Instant quantum. A later turn/session resumes from durable state.

This loop can execute recursively on child ReasoningProcesses.

## 5. How extra Instant turns approximate more test-time reasoning

Multiple Instant turns can add effective compute when the next turn receives *new useful state*:

- tool observations;
- validator failures;
- alternative hypotheses;
- critic findings;
- child-worker results;
- a refined compact state;
- a narrower unresolved residual.

A repeated turn with unchanged state is not "more reasoning" in a useful sense; it risks correlated repetition.

The system should therefore require one of:
- new evidence;
- new branch;
- new validator feedback;
- changed decomposition;
- changed context slice;
before consuming another same-tier quantum.

## 6. Real-workflow-first calibration policy

Do not spend weeks running isolated synthetic tests before backend implementation.

Primary characterization source:
- real Workspace Control workflows;
- real repository/CI/debug work;
- real research analysis/experiment loops;
- real artifact/document workflows;
- real project planning and architecture tasks.

Every production-like worker quantum should record:
- executor identity;
- task/work phenotype;
- packet/context size;
- dependency count / coupling estimate;
- tool depth;
- child count;
- validator result;
- repair count;
- decomposition decisions;
- escalation decisions;
- final accepted outcome.

The scheduler learns from these traces.

Synthetic fixtures are retained only for:
- regression sentinels after model/surface changes;
- controlled isolation of a specific failure mode discovered in real work;
- authority/security invariants that must remain deterministic.

## 7. Initial architectural hypothesis

Use a three-level reasoning hierarchy:

### Tactical Instant worker
- one bounded leaf or one local decision;
- acts/reasons quickly;
- publishes durable result.

### Instant critic / meta-worker
- independently checks result or progress;
- identifies missing constraints / weak reasoning / bad decomposition;
- does not inherit the worker's private conversational momentum by default.

### Strategic synthesizer
- integrates validated child results;
- if synthesis fan-in becomes too wide, recursively builds intermediate syntheses;
- routes only an irreducibly coupled residual to stronger reasoning.

This is closer to COMPASS + Reflexion + recursive language-model inference than to one giant chat.

## 8. Key design rule

The backend should maximize:

> validated progress per Instant quantum

rather than:
- token count;
- number of turns;
- amount of preserved chat history;
- uninterrupted wall-clock reasoning time.

The orchestrator should keep giving Instant new bounded opportunities to think **only while each new quantum has a changed informational state and an objective path to validation**.

## 9. Open questions to learn online

- How many mutually coupled constraints can GPT-6 Instant reliably integrate?
- How wide can a synthesis node be before hierarchical synthesis is better?
- How many validator-feedback repair cycles are productive?
- When does persistent-chat continuity help versus bias/repetition?
- How aggressively should state be compressed?
- Which failures are fixed by decomposition versus stronger effort?
- When does an independent Instant critic catch failures the same persistent worker misses?
- How much of GPT-6 High's advantage can be recovered by multiple validated Instant quanta?

These are learned from real work first; targeted controlled tests follow only where production traces cannot distinguish the mechanism.
