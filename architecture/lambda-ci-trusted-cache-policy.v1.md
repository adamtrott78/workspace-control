# Lambda CI Trusted Cache Policy v1

Status: v1 implementation in validation; live model-scale routes remain disabled.

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

## Implemented v1 promotion boundary

The implementation surface is `scripts/lambda_ci_trusted_cache.py`.

Trusted operations are deliberately local and root-only:

- `acquire-local` copies an already obtained source tree into a root-owned
  quarantine under `/var/lib/workspace-ci/cache-manager/<project>/quarantine`;
- acquisition rejects symlinks, non-regular files, common secret-bearing
  filenames/markers, unsafe pickle-style suffixes, mutable model revisions,
  unsafe deserialization declarations, and custom/remote executable model code;
- every quarantined payload is represented by a sorted per-file SHA-256
  manifest and a content tree digest;
- `promote` re-hashes the quarantine before promotion, copies it into
  `trusted-cache/objects/<kind>/sha256/<tree-digest>/`, emits a durable
  non-secret promotion receipt, hardens the object to root-owned read-only
  content, verifies the promoted object, then destroys quarantine;
- duplicate content is idempotent only when the existing content digest and
  descriptor digest both match; metadata/content collisions fail closed;
- `verify` is intentionally non-privileged and recomputes the complete
  manifest/digest offline so candidate jobs can prove a promoted object without
  receiving acquisition or promotion authority.

The descriptor and promotion-receipt contracts are versioned at:

- `schemas/lambda-ci-trusted-cache-descriptor.v1.schema.json`
- `schemas/lambda-ci-trusted-cache-promotion-receipt.v1.schema.json`

The first live object must be a harmless test fixture. Model acquisition,
cache-promotion, and model-eval workload classes remain non-live until the
read-only consumer/adversarial gate passes from the accepted research-engine
runner identity.
