# PADataset Autonomous Scientific Execution v0.1

Status: **DESIGN FROZEN FOR IMPLEMENTATION**

## Goal

Give ChatGPT an autonomous, durable execution path for PADataset scientific experiments on the existing self-hosted Lambda GPU infrastructure without requiring the operator to open a terminal for each run.

The execution path is intentionally separate from the existing `gpu-ci` canary. The canary remains CI-only. Scientific jobs receive a new semantic execution contract and a new trusted workflow.

## Chosen topology

- Scheduler/control plane: existing PADataset self-hosted Lambda controller.
- Compute: existing single-GPU PADataset lane on the accepted Lambda host.
- Runtime: exact root-owned read-only snapshot derived once from the operator's verified isolated `DNNs` Python venv, with the exact root-controlled base interpreter digest bound in the promotion receipt.
- Source: exact head of an open same-repository PADataset PR.
- Request: one bounded token carried by the trusted issue-comment trigger after the exact candidate SHA. The controller independently proves that SHA is the head of an open same-repository PR.
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

Read-only host diagnosis established that the live DNNs source at `/home/atrott/adamArchives/venvs/DNNs` is a standard Python venv, not a Conda environment: `pyvenv.cfg` exists, `conda-meta/` does not, `sys.prefix` is the DNNs prefix, `sys.base_prefix` is `/usr`, and the venv interpreter resolves to the root-controlled system Python. Core scientific imports and CUDA are valid in that source environment.

The live user venv is a source artifact, not a runtime mount.

A root-owned installer:
- discovers exactly one valid DNNs prefix and requires the verified isolated Python-venv shape;
- binds the exact root-controlled base Python path and SHA-256 because the venv interpreter is a system-Python symlink;
- records a deterministic installed-distribution inventory and an exact pre-copy source-tree digest in root-private source metadata;
- copies the venv byte-for-byte into project-owned staging storage and requires the copied tree digest to equal the source digest;
- rechecks the source digest after copy so source mutation during promotion fails closed;
- removes copied bytecode caches, rewrites only UTF-8 text references from the mutable source prefix to the final canonical runtime prefix, and rejects binary source-prefix references;
- allows no external runtime symlink except the exact bound base Python and rejects external import paths outside the venv or its base Python prefix;
- verifies `python`, `torch`, CUDA availability, and core PADataset imports before and after relocation;
- changes the promoted tree to root ownership, removes write bits, hashes the frozen runtime tree, and writes an immutable promotion/expansion receipt;
- revalidates both the promoted runtime-tree digest and base-Python digest before emitting bindings;
- keeps source package/prefix metadata under root-private `/var/lib/workspace-ci`, never candidate-readable trusted cache;
- never grants candidate jobs write access to the promoted runtime.

The v1 promoter does not re-resolve dependencies with Conda or pip. It preserves the already-installed venv payload and fails closed on any relocation hazard it cannot prove safe. Routine jobs never fall back to the mutable source environment.

## Scientific request v1

The trusted trigger grammar is:

- `/lambda-scientific <exact-candidate-sha> smoke`
- `/lambda-scientific <exact-candidate-sha> train_backbone:manifests/configs/<config>.json`
- `/lambda-scientific <exact-candidate-sha> stage03_archc:manifests/configs/<config>.json`

The candidate SHA is not repeated inside candidate-controlled file content. The controller independently binds it to the exact head of an open same-repository PR, so duplicating the SHA inside the commit would create an impossible self-reference. The third token is a bounded semantic request, not generic argv or shell authority. Training config paths remain repository-relative under `manifests/configs/` and are revalidated by the trusted workflow before execution.

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

## Stage 5 additive live-v3 activation design

The dedicated scientific class is added to an already-live v3 production generation. Activation therefore MUST be an additive expansion; the original v2→v3 migration/cutover transaction is historical and MUST NOT be replayed.

### Frozen identities

- target class: `padataset-scientific-single-gpu-v1`
- target route: `padataset:scientific-single-gpu`
- target scale set: `lambda-padataset-scientific-single-gpu`
- target controller user: `ci-ctl-pad-science`
- target command: `/lambda-scientific`
- trusted workflow: `.github/workflows/lambda-ci-scientific.yml`
- trusted workflow blob: `e70412f3ccdc70826f56f7ba0255518f1f95224f`
- exact runtime: `padataset-dnns-v1`, manifest identity `57b0cd8d0f3d2c5f353891237ad52d118458a4cff1f9b403321754ae4fcbe579`
- exact scientific data profile: `ota_core_high_run01_len16384_v1`, digest `a76730a886909f9896e7cb7e9d1aede3d2301240f9ce08a4080e24d637406bf5`

### Compatibility proof

The current compiler intentionally excludes `control_plane_generation_sha256` from each class's `root_envelope_sha256`. The additive transaction MUST prove that every pre-existing runner class has the same root envelope before and after expansion. A changed global generation or root-policy digest is expected because a tenth class is added; a changed pre-existing class envelope is not.

The candidate generation MUST be exactly the effective installed class set plus one class, `padataset-scientific-single-gpu-v1`, and the effective installed route set plus one route, `padataset:scientific-single-gpu`. Existing controller policy authority, existing route admission state, containment state, class lifecycle state, systemd units, scale-set names, runner prefixes, and exclusive resource envelopes MUST remain unchanged.

### Phase A — expand shared root policy, scientific class inactive

Phase A installs the tenth class into the shared v3 root policy without granting scientific admission.

Preconditions:

1. Candidate source is an exact, clean, repository-validated Workspace Control head.
2. The current installed generation and all existing live overrides verify before mutation.
3. Existing production controllers/routes remain the accepted live set; the scientific class/route are absent from effective live authority.
4. The candidate compiler proves the exact-superset compatibility condition above.
5. The shared provisioner has no active/held durable reservation records and no active v3 runner/supervisor transient.
6. Existing class controller units are NOT stopped or restarted.

Race closure and mutation:

1. Stop only `workspace-ci-v3-provisioner.service`. This closes new root reservations while existing class controllers remain running; their root RPC retry behavior cannot grant work while the socket is absent.
2. Re-prove zero active/held reservations and zero v3 runner/supervisor transients after the provisioner stops.
3. Install only the reviewed additive generation artifacts: expanded root policy/executor/compatibility projections, an overlay that preserves every existing state while adding the scientific class as `INSTALLED/INACTIVE` and route as `DISABLED`, the scientific controller policy/drop-in, and the sysusers/tmpfiles additions required for `ci-ctl-pad-science` and its state directory.
4. Do not replace the shared controller binary, runner runtime, production class policies, existing controller identities, or existing class service units.
5. Restart the shared provisioner on the expanded 10-class root policy and verify its socket, UID map, and effective-generation binding.
6. Prove the previously live class controller processes were not restarted by the expansion transaction.
7. Commit a root-owned additive-generation receipt. After this point the 10-class provisioner generation is a safe committed intermediate state even if scientific activation is deferred.

Phase-A failure before the expanded provisioner is verified MUST restore the exact pre-expansion files and restart the old provisioner. After Phase A commits, later scientific activation failure MUST NOT roll the shared provisioner back; it leaves the target class installed/inactive and route disabled.

### Effective-generation attestation

The immutable historical install manifest remains the base attestation. Existing production-cutover/controller/runtime/helper override receipts remain historical authority for their exact prior deltas.

A new root-owned scientific additive override receipt MUST attest the chain from that verified effective generation to the expanded generation. It MUST bind:

- base install-manifest SHA-256 and base source head;
- prior effective production override identity when present;
- reviewed additive source head;
- expanded catalog generation and root-policy SHA-256;
- exact preserved root-envelope digests for every pre-existing class;
- exact target class/route identities;
- exact digests and modes for each changed base-managed artifact;
- exact digests and modes for each newly introduced managed artifact;
- the current target phase: `INSTALLED_INACTIVE` or `ACTIVE`.

The installed reconciler MUST understand and verify this override chain before Phase A is considered committed. The additive transaction may update only the reconciler verifier needed to understand this receipt; that verifier update must itself remain exactly bound to the immutable base manifest and reviewed source head.

### Phase B — activate only the scientific class and route

Phase B is separately authorized after Phase A commits.

Preconditions:

1. Effective-generation verification passes with the scientific target `INSTALLED_INACTIVE` and route `DISABLED`.
2. The exact promoted DNNs runtime tree/base-Python binding and exact scientific-data digest re-attest successfully.
3. The PADataset trusted workflow on default branch has exact blob `e70412f3ccdc70826f56f7ba0255518f1f95224f`.
4. No queued/in-progress scientific workflow run exists.
5. The existing reviewed v3 scale-set preflight creates `lambda-padataset-scientific-single-gpu` if absent and then proves its exact repository/name/group identity with zero assigned and zero running jobs.
6. The PADataset controller credential remains project-scoped; no new secret class is introduced.
7. A fresh one-shot root-owned activation authority receipt is bound to the exact expanded generation, target controller policy, workflow blob, scale-set confirmation, runtime/data identities, and target class/route.

Activation mutates only:

- scientific overlay class state `INACTIVE → ACTIVE`;
- scientific route state `DISABLED → ENABLED`;
- `workspace-ci-v3-controller@padataset-scientific-single-gpu-v1.service`, which is started/enabled only after the exact preflights above.

Every other class, route, controller, v2 retirement state, containment state, scale set, and workflow remains unchanged.

If Phase B fails, stop/disable only the scientific controller and restore the scientific overlay/active receipt to `INSTALLED_INACTIVE / DISABLED`. The shared 10-class provisioner remains installed and live.

### First live proof

After Phase B succeeds, verify the dedicated controller/scale-set identity and exact runtime/data bindings before issuing `/lambda-scientific`.

The execution sequence remains:

1. non-destructive scientific smoke;
2. one bounded training smoke;
3. full PA2 Stage 03 backbone training;
4. Architecture C evaluation;
5. final cleanup, runtime-integrity, and residue receipt.

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
- No direct mutable access to the operator's home DNNs environment.
- No GitHub-hosted runner dependency.
- No multi-GPU scientific execution in v1.
- No automatic promotion of candidate-written executable dependencies.


## Post-activation trusted-workflow refresh

The first live-proof review found that the original trusted scientific workflow required a candidate-controlled request file to contain the SHA of the commit that itself contained that file. That is a cryptographic self-reference and therefore cannot be used as a practical admission contract.

PADataset PR #15 corrected only the request transport while preserving exact open same-repository PR-head attestation and all scientific operation/config bounds. The reviewed replacement workflow blob is `4cf390ec334b0569dbfc2399ff86c2d892f97586` on PADataset main `a7e3eb3718820f6fa3183ebc6b8990da2b49f61f`.

Live adoption is a separate, one-shot, root-owned workflow-refresh transaction layered on top of the immutable Phase-A/Phase-B activation receipt. It may replace only the dedicated scientific controller policy and the installed reconciler verifier needed to understand the refresh receipt; it must stop/restart only the dedicated scientific controller, preserve the shared provisioner and every other controller identity, prove zero scientific assigned/running work before mutation, and roll back to the prior trusted workflow on failure.
