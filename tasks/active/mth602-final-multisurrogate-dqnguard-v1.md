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

## Refresh-v3 candidate and exact failure

Workspace-control refresh-v3 branch:
- branch: `mth602-laneb-workflow-refresh-v3`
- exact head: `9ea2444d54d97c0e2a740c660589e6675e1c207d`
- candidate-pytest receipt: `job-bea40700-793d-4e55-b15d-5d0d812319fc`
- result: **32 passed**

The operator attempted the v3 preflight, but it failed **before any mutation**:

```
FileNotFoundError:
  /var/lib/workspace-ci/v3/padataset-scientific/dual-lane/workflow-refresh-v3/active.json
```

Exact source bug in
`scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v3.py`:

- line 27 currently:
  `PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT`
- line 28 currently:
  `REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT`

Those are reversed.

Correct bindings must be:

```python
PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT
REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT
```

The failed old v3 operator block must **not** be rerun unchanged.

## Immediate next action

1. Branch from exact refresh-v3 head `9ea2444d54d97c0e2a740c660589e6675e1c207d`.
2. Change only the two reversed receipt bindings in the v3 helper.
3. Add a regression test asserting those exact constant bindings.
4. Run the complete dual-lane + refresh-v1 + refresh-v2 + refresh-v3 control suite through Workspace Shell `candidate-pytest`.
5. If PASS, prepare a **new** v3 root/operator block using a fresh zero-work preflight.
6. Successful v3 must advance trust:
   - old workflow blob: `8da00f39284745cf6c9032620d63574052cd6d61`
   - new workflow blob: `85e8deef5240e2d6d7db34318e6b2c35947a83f3`
   - PADataset main: `dbf167b23e6a1777a31ad5c4bccde44d26d0aad6`
   - live predecessor policy SHA: `70f49bf44a638460eb7fe209b1a313740955a25627ff012abf99671b9de5634d`
7. After v3 PASS, rerun **exactly one** frozen PA1->PA2 evaluator cell from PR #26 head `99ba123e1455566e16d86d6faf67fef3be8ab0b9`.
8. Inspect artifact transport, rehydration, `result_record.json`, `target_labels_used_for_tuning=false`, GPU UUID, and scientific receipt before scheduling any additional cells.
9. If that acceptance cell passes, schedule the remaining Track-A matrix without retraining any backbone.

## Other lanes

- Track B Architecture B remains separate; do not let Track A replace it.
- STFT remains a separate representation diagnostic and is still gated on the repaired PA1 provenance preflight.
- Preserve the first 120 completed STFT overlay records.
- Do not merge PR #26, PR #23, PR #21, or unrelated workspace-control branches without separate explicit authority.

## Chat/runtime note

The current task Heartbeat is still owned by the prior conversation. The next chat should treat this Git/task state as authoritative and must not depend on inheriting that heartbeat writer.
