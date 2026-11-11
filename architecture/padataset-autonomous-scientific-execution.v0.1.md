# PADataset Autonomous Scientific Execution v0.1

Status: **DESIGN FROZEN FOR IMPLEMENTATION**

## Goal

Give ChatGPT an autonomous, durable execution path for PADataset scientific experiments on the existing self-hosted Lambda GPU infrastructure without requiring the operator to open a terminal for each run.

The execution path is intentionally separate from the existing `gpu-ci` canary. The canary remains CI-only. Scientific jobs receive a new semantic execution contract and a new trusted workflow.

## Chosen topology

- Scheduler/control plane: existing PADataset self-hosted Lambda controller.
- Compute: existing single-GPU PADataset lane on the accepted Lambda host.
- Runtime: exact root-owned read-only snapshot derived once from the operator's existing `DNNs` Conda environment.
- Source: exact head of an open same-repository PADataset PR.
- Request: `.workspace-ci/scientific-request.json` at that exact candidate SHA.
- Dataset/cache: root-owned project trusted-cache material exposed read-only; candidate code receives no persistent write authority.
- Outputs: job-local experiment directory uploaded as a GitHub artifact plus a machine-readable scientific receipt.
- Orchestration: ChatGPT updates/creates the candidate PR, triggers the trusted issue-comment route, monitors the job, reads artifacts/receipts, and continues automatically.

## Authority invariants

1. No generic shell route is introduced.
2. The trusted workflow accepts only schema-validated experiment requests.
3. First implementation allowlists:
   - `experiments/pa_train_one.py` with one repository-relative config path; and
   - `experiments/pa_eval_multisurrogate_dqnguard.py` with explicit repository-relative run/checkpoint/output arguments.
4. Candidate SHA must equal the head of an open same-repository PR.
5. Fork PRs remain denied.
6. Exactly one root-authorized GPU is visible.
7. The scientific runtime is exact-bound and read-only before/after execution.
8. The PADataset trusted-cache root is read-only to the job.
9. Candidate writes are limited to ephemeral job/staging roots. Durable experiment outputs leave the runner only through GitHub artifact upload.
10. The project runner receives no GitHub App private key, SSH key, Docker socket, controller socket, Workspace Shell socket, or production service credential.
11. Historical user-home paths remain inaccessible during scientific jobs.
12. Runtime and dataset/cache promotion are one-time root/operator installation tasks; routine experiments require no operator action.

## DNNs promotion model

The live user Conda environment is a source artifact, not a runtime mount.

A root-owned installer:
- requires the operator to invoke it while `CONDA_DEFAULT_ENV=DNNs`;
- records the source `CONDA_PREFIX`;
- copies the environment into project-owned root storage;
- preserves the source prefix as the sandbox-visible prefix when needed for Conda prefix compatibility;
- verifies `python`, `torch`, CUDA availability, and core PADataset imports before acceptance;
- hashes the frozen runtime tree and writes an immutable promotion/expansion receipt;
- removes write bits and changes ownership to root;
- never grants candidate jobs write access to the promoted runtime.

If a direct copied environment fails relocation/prefix validation, installation fails closed and the next implementation step is a conda-pack/offline-rebuild recipe. Routine jobs never fall back to the mutable source environment.

## Scientific request v1

The candidate request file contains only:
- schema_version = 1
- operation = `train_backbone` or `evaluate_architecture_c`
- config_path / run_dir / checkpoint / out_dir as applicable
- bounded integer controls already permitted by the operation schema
- expected PADataset candidate SHA

Paths must be repository-relative and must remain inside fixed allowlisted prefixes.

## Execution contract

New semantic contract: `scientific-single-gpu-v1`.

Initial properties:
- execution_plane: jit_runner
- execution_profile: gpu-small
- resource_class: scientific_gpu_single_v1
- state_effect_class: SCIENTIFIC_EXPERIMENT_EPHEMERAL_ARTIFACTS
- filesystem_class: EPHEMERAL_JOB_PLUS_TRUSTED_CACHE_READONLY
- cache_access_class: TRUSTED_RUNTIME_READONLY
- model_binding_mode: FORBIDDEN
- runtime_binding_mode: REQUIRED_EXPANDED_RUNTIME_EXACT
- gpu_count: 1
- candidate_payload_allowed: true

The contract is introduced disabled/planned, validated, then activated only after the DNNs runtime promotion receipt and a non-destructive scientific smoke canary pass.

## First acceptance sequence

1. Repository/schema/policy tests.
2. DNNs promotion installer static tests.
3. Trusted workflow exact-blob validation.
4. Root promotion of DNNs runtime.
5. Controller/reconciliation activation.
6. Scientific smoke request that imports torch, verifies one GPU, loads the Stage 03 config, and writes a tiny artifact without training.
7. One bounded training smoke (1 epoch) from an exact candidate PR.
8. Full frozen PA2 Stage 03 backbone training.
9. Architecture C evaluation.
10. Final cleanup/residue/runtime-integrity receipt.

## Non-goals

- No arbitrary shell/command execution.
- No direct mutable access to the operator's home Conda environment.
- No GitHub-hosted runner dependency.
- No multi-GPU scientific execution in v1.
- No automatic promotion of candidate-written executable dependencies.
