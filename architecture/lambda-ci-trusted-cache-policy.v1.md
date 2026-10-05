# Lambda CI Trusted Cache Policy v1

Status: static P1 design.

## Objective

Avoid repeated large downloads/builds without allowing candidate jobs to persist
mutable executable state across trust boundaries.

## Roots

For research-engine:

- candidate staging: `/srv/workspace-ci/research-engine/staging-cache`
- trusted promoted cache: `/srv/workspace-ci/research-engine/trusted-cache`

Candidate jobs may write only staging. Trusted cache is read-only to the runner.

## Promotion authority

Only a separately reviewed trusted cache-management operation may promote an
object from staging or public source into the trusted cache.

Candidate workflow code cannot invoke promotion directly.

Promotion requires:

1. declared artifact kind;
2. immutable upstream identity (release/version/revision/commit);
3. SHA-256 or stronger digest of downloaded/archive content;
4. source URL/repository/model identifier;
5. license/usage review where relevant;
6. extraction/build recipe identity;
7. resulting tree/content digest;
8. malware/custom-code risk classification where relevant;
9. promotion receipt.

## Model cache

For Hugging Face-style models, prefer immutable revision snapshots and hashed
blob storage. A promoted model identity must include the exact repository
revision/commit.

If model loading requires remote custom Python code, that code is treated as
executable dependency material and must be separately pinned/reviewed.

Candidate jobs may download model files into job-local/staging space for a
bounded experiment. They may not automatically promote those files.

## Package/runtime cache

Python wheels, Go modules, npm packages, compiled extensions, CUDA extensions,
and similar executable inputs are untrusted when candidate-written.

The pilot may cache them only in ephemeral staging. Persistent promotion is a
separate trusted operation.

## Eviction

Cache eviction may delete any trusted object not currently pinned by an active
project manifest. Deletion must not change project scientific/source truth.

## Cross-project reuse

No writable cross-project cache in v1.

A later cache manager may expose identical content-addressed objects read-only to
multiple projects, while preserving project-specific manifests and promotion
receipts.

## Secret exclusion

Never cache:

- GitHub App private keys or tokens;
- JIT runner configs;
- GITHUB_TOKEN values;
- SSH keys;
- database credentials;
- environment files containing secrets;
- runner registration/configuration files.
