<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/mth602-final-multisurrogate-dqnguard-v1.json`

## Fresh-chat status

Track A backbone training is **complete**.

- PADataset PR #26 exact head: `99ba123e1455566e16d86d6faf67fef3be8ab0b9`
- canonical backbones: **10/10 COMPLETE**
- frozen directional evaluator requests: **20/20**
- final PR #26 candidate-pytest: **35 passed**
- receipt: `job-3d9c726d-aa8a-4e79-8d69-718d5bca6e2b`
- PR #26 remains OPEN/UNMERGED; no merge authority.

Final PA3-PA4 backbone:
- run `43943016274`
- job `133565212672`
- artifact `14277201494`
- artifact digest `sha256:9e4b8ec93e19868cd46c8982503570e406d9b286cd2fa7e715f25e210d0d76b8`
- best model SHA256 `d9fd5db822458e47b04b4efd74b9725a758445a84240d469c2d8fc69ba6c7580`
- config SHA256 `cfb3294c3a176a2a03b0882928fade4dd18e5aad0e0641241aaed4887c2ae3bb`
- best epoch 24
- known-test macro-F1 1.0
- `target_test_consumed=false`
- target quarantine preserved.

## GPU2 evaluator / trusted workflow state

Corrected trusted GPU2 workflow is already merged on PADataset:

- PADataset main: `dbf167b23e6a1777a31ad5c4bccde44d26d0aad6`
- workflow: `.github/workflows/lambda-ci-scientific-2.yml`
- workflow blob: `85e8deef5240e2d6d7db34318e6b2c35947a83f3`
- PR #30 added the process-substitution shell-syntax fix plus `bash -n` regression coverage.
- workflow candidate receipt `job-1bf22e23-4965-499e-8482-c517e5c8c560`: **7 passed**.

Real GPU2 provisioning has already been proven twice:
- run `43967496290` / job `133650662301`
- run `43969575701` / job `133657867208`

Both reached an actual GPU2 runner. Neither produced evaluator science:
1. first failed before science because of `PYY` instead of heredoc terminator `PY`; PR #29 fixed it.
2. second passed exact-head verification, bounded-runner proof, exact checkout, and frozen-request validation, then failed before science because Bash could not parse a nested heredoc/process-substitution block; PR #30 fixed it.

Do not infer scientific metrics from either acceptance attempt.

## Live lane-B root state

Refresh v1 is live and successful:
- policy `8c4a2d3d... -> 669aa487...`
- transaction `refresh-e8be5357-316f-40f0-9302-56856e98325a`
- active receipt SHA256 `7b2c4af51cbcb8d42a5432920769d19d131df5dbb9601110d78c32fbf403502d`

Refresh v2 is live and successful:
- policy `669aa487... -> 70f49bf44a638460eb7fe209b1a313740955a25627ff012abf99671b9de5634d`
- transaction `refresh-69d6b04f-e5d7-47c1-9ae7-8015be78d354`
- active receipt SHA256 `67875d5c10c337584400ff41f0c5e46ee2ad0ecb7d1b057c8d3058225634a8ab`

Therefore **live lane-B trust is still refresh-v2**, not v3.

## Refresh-v3 corrected candidate

The receipt-binding bug is repaired and candidate validation is complete.

- branch: `mth602-laneb-workflow-refresh-v3-binding-fix-v1`
- exact base: `9ea2444d54d97c0e2a740c660589e6675e1c207d`
- exact candidate head: `5a7134056fef65b44e25bf06ac66f975f1903bff`
- effective helper diff: exactly two receipt-binding lines replaced
- regression: exact-line assertions for V2 predecessor and V3 output receipt bindings
- candidate-pytest receipt: `job-250a3ad2-69ef-4adf-8e2e-92aaf4748e3b`
- result: **33 passed**

Correct bindings are:

```python
PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT
REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT
```

No root/control-plane mutation has been performed by this repair candidate.

GitHub zero-work observation at checkpoint time:
- PADataset main: `dbf167b23e6a1777a31ad5c4bccde44d26d0aad6`
- trusted workflow blob on main: `85e8deef5240e2d6d7db34318e6b2c35947a83f3`
- requested/queued/in-progress/waiting/pending Actions runs: **0**

The failed old v3 operator block must **not** be rerun unchanged.

## Refresh-v3 second pre-mutation failure and corrected candidate

The first binding repair passed candidate validation but the fresh operator attempt exposed one additional copy/lineage typo **before any mutation**:

- refresh-v2 actually writes receipt mode `V3_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2`
- refresh-v3 incorrectly required its predecessor mode to equal `V3_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3`
- runtime failure: `ERROR: lane-B workflow refresh v2 predecessor binding invalid`
- the later `rm ... __pycache__ Permission denied` messages were temporary-checkout cleanup only.

Corrected child candidate:
- branch: `mth602-laneb-workflow-refresh-v3-predecessor-mode-fix-v2`
- base: `5a7134056fef65b44e25bf06ac66f975f1903bff`
- exact head: `fc6c1cbac894d9350d11bae4859cbbb27b2da175`
- code delta from base: one predecessor-mode line changed V3 -> V2
- regression added for exact V2 predecessor mode
- candidate-pytest receipt: `job-4cf75745-3a81-407b-bfa0-1b9319b54bca`
- result: **34 passed**

No root/control-plane mutation occurred in either failed v3 attempt.

## Immediate next action

1. Run a **new** refresh-v3 root/operator transaction bound to candidate `fc6c1cbac894d9350d11bae4859cbbb27b2da175`.
2. Recompute a fresh zero-work preflight immediately before execution.
3. Require predecessor receipt mode `V3_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2` and live predecessor policy SHA `70f49bf44a638460eb7fe209b1a313740955a25627ff012abf99671b9de5634d`.
4. Advance only lane-B workflow trust from `8da00f39284745cf6c9032620d63574052cd6d61` to `85e8deef5240e2d6d7db34318e6b2c35947a83f3` at PADataset main `dbf167b23e6a1777a31ad5c4bccde44d26d0aad6`.
5. Verify active v3 receipt and live lane-B policy after the transaction.
6. Only after PASS, run exactly one frozen PA1->PA2 evaluator acceptance cell at PR #26 head `99ba123e1455566e16d86d6faf67fef3be8ab0b9`.

## Other lanes

- Track B Architecture B remains separate; do not let Track A replace it.
- STFT remains a separate representation diagnostic and is still gated on the repaired PA1 provenance preflight.
- Preserve the first 120 completed STFT overlay records.
- Do not merge PR #26, PR #23, PR #21, or unrelated workspace-control branches without separate explicit authority.

## Chat/runtime note

The current task Heartbeat is still owned by the prior conversation. The next chat should treat this Git/task state as authoritative and must not depend on inheriting that heartbeat writer.
