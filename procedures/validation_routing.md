# Validation Routing Procedure

Status: **v1 candidate**

## Purpose

Choose the cheapest validation path sufficient for the changed state while
failing closed to full integration when dependency/risk radius is unknown.

This procedure implements
`architecture/throughput-ci-efficiency-v1.md`. Project-specific path/risk truth
belongs in a project-owned validation profile; the planner mechanism stays
generic.

## Inputs

Establish repository identity, exact changed-path evidence, the complete changed
path set, the project validation profile, and whether `force_full` applies.
Do not classify from a remembered or partial diff.

## Planner

For workspace-control:

```bash
python scripts/validation_plan.py \
  --profile policies/workspace-control.validation-profile.v1.json \
  --changed-path path/one \
  --changed-path path/two \
  --json
```

Use `--force-full` whenever the owning workflow, operator, or uncertainty
requires complete integration.

The planner is monotonic:

- `FAST_STATIC < TARGETED_PR < FULL_INTEGRATION < CANONICAL_REGRESSION`;
- the highest matching changed-path tier wins;
- unknown paths use the fail-closed default;
- mixed changes escalate to the highest applicable tier;
- force-full selects at least the configured full-integration floor.

The planner chooses requirements; it does not execute or waive them.

## Workspace-control profile

`policies/workspace-control.validation-profile.v1.json` classifies task state
and architecture/README prose as `FAST_STATIC`, test-only mutations as
`TARGETED_PR`, and shared policy/procedure/workflow/schema or executable
control-plane mutations as `FULL_INTEGRATION`. Unknown paths are
`FULL_INTEGRATION`.

Changes to the classifier, profile, schemas, or shared authority contracts
therefore self-escalate.

## Mutation orchestration

For one logical mutation batch:

1. verify the branch head and reviewed base tree;
2. create independent blobs in parallel;
3. create one tree and one commit for the complete reviewed path set;
4. immediately recheck the branch head before moving the ref;
5. move the ref;
6. reread the resulting branch/commit/tree and changed files.

The current GitHub connector accepts plain `update_ref` but rejects its
advertised `expected_sha` argument. Until repaired, step 4 plus immediate
post-write verification is mandatory; do not claim lease-protected mutation.

Do not run concurrent writes to the same path.

## PR timing and status reads

Open a PR only after the logical mutation batch is stable and cheap deterministic
preflight has passed. After a CI failure, inspect the failed job/log and prefer
one bounded repair batch over speculative drip commits.

Prefer one high-level run/status read first. Fetch jobs only when job-level state
matters and logs only for diagnosis. Do useful independent work while CI runs;
do not poll merely because a short interval elapsed.

## Tested-tree rule

A passed PR check can unblock subsequent conversation work only when it tested
the synthetic merge result (or equivalent tested-latest-target tree), all checks
selected by the plan passed, the merged tree is proven equal to the tested tree
or equivalent merge-queue/strict semantics apply, and the next operation does
not depend on canonical-only deployment/release behavior.

Otherwise canonical validation remains a dependency. Asynchronous
post-submit/scheduled regression remains authoritative; asynchronous does not
mean optional.

## Full-validation escape hatch

Escalate to `FULL_INTEGRATION` or stronger for unknown paths/dependencies,
incomplete base/head evidence, profile/planner parse failure, mixed risk,
security/persistence/provenance/deployment/shared-authority changes, or an
explicit full-validation request. A model may not infer its way around these
gates.
