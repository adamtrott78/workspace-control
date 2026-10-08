# Lambda CI Runtime Packaging Review v1

Status: decision record for `workspace-lambda-execution-policy-v1`.

## Question

Should the Qwen/vLLM runtime be persisted as a copied virtualenv, rebuilt from an
immutable wheel bundle, packaged as a Python executable/archive, moved to Nix/Conda,
or replaced by a GPU container image?

## External standards / established practice

### Python virtual environments are intentionally disposable

The Python standard-library `venv` documentation explicitly says virtual
environments are disposable, should be easy to recreate, and are not considered
movable/copyable. That matches the observed qwen runtime: absolute shebangs,
absolute-prefix references, symlinks, and other relocation hazards make persisting
the live venv itself the wrong trust object.

Reference:
- https://docs.python.org/3/library/venv.html

### Wheelhouse + offline installation is an established pip deployment pattern

pip documents "Using a wheelhouse (AKA Installation Bundles)" as a repeatable
installation strategy. It recommends prebuilding/downloading wheels into a local
directory and installing later without index access. pip also documents
`--no-index --find-links=<wheelhouse>`, and its secure-install guidance recommends
`--require-hashes` plus `--only-binary :all:` to prevent source builds and ensure
every installed archive is locally hash-pinned.

References:
- https://pip.pypa.io/en/latest/topics/repeatable-installs/
- https://pip.pypa.io/en/stable/topics/secure-installs/
- https://pip.pypa.io/en/stable/user_guide/

### Standard Python lock files now exist

PEP 751 / the PyPA `pylock.toml` specification defines a standardized lock file
for reproducible Python environments. pip's current `pip lock` command emits
`pylock.toml` but remains marked experimental. uv can also export PEP 751
`pylock.toml`.

References:
- https://packaging.python.org/en/latest/specifications/pylock-toml/
- https://pip.pypa.io/en/stable/cli/pip_lock/
- https://docs.astral.sh/uv/concepts/projects/export/

### Faster cache-backed environment materialization exists

uv uses aggressive package caching and can install from its cache using clone/COW,
copy, hardlink, or symlink modes. Its documentation specifically discourages
symlink mode because it tightly couples environments to the cache. This makes
clone/COW or hardlink-based materialization an attractive future optimization
candidate after the security-correct pip baseline is measured.

References:
- https://docs.astral.sh/uv/concepts/cache/
- https://docs.astral.sh/uv/reference/cli/

### GPU containers are mainstream, but are a different trust architecture

vLLM publishes an official NVIDIA Docker image, and NVIDIA's NGC / Container
Toolkit ecosystem treats containers as the normal way to ship complete
GPU-accelerated software stacks. Containers can eliminate per-job Python install
time by moving the runtime into immutable image layers.

References:
- https://docs.vllm.ai/en/stable/deployment/docker/
- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/
- https://docs.nvidia.com/ngc/latest/ngc-catalog-user-guide.html

However, adopting containers here would not be a neutral packaging substitution.
It would introduce a container runtime, image trust/supply-chain policy, GPU-device
mapping through that runtime, image-layer cleanup, and a new privilege boundary.
The accepted Lambda execution-policy architecture intentionally keeps candidate
workflow code away from host/container administrative authority. A container route
therefore requires its own design and acceptance gate rather than replacing the
current wheel bundle opportunistically.

### Other established options are less aligned with this runtime

- PEX packages Python applications into self-contained executable environments and
  is proven in large production deployments, but it is application-centric and
  still has interpreter/platform concerns. It does not remove the need to reason
  carefully about the large CUDA/native-library stack.
- conda-pack exists specifically because Conda environments are not directly
  relocatable. Adopting it would require moving the certified pip/venv runtime to a
  different package manager and cache model.
- Nix provides immutable/hash-addressed package stores and reproducible build
  environments, but would introduce a much larger system-level package/build
  architecture than this task currently requires.

References:
- https://pex.readthedocs.io/
- https://conda.github.io/conda-pack/
- https://wiki.nixos.org/wiki/Nix_store

## Decision for the accepted runner

Keep the accepted architecture:

1. persistent root-owned content-addressed model object;
2. persistent root-owned content-addressed wheelhouse/runtime object;
3. exact per-wheel SHA-256 manifest;
4. network-disabled per-job environment materialization;
5. exact identity verification before GPU use;
6. disposable per-job execution environment;
7. destruction of job-local state after completion.

This is not a novel packaging guess. The core pattern is the documented Python/pip
wheelhouse + disposable-venv deployment model with stricter trust, provenance, and
candidate-isolation controls layered around it.

## Improvements to adopt after correctness acceptance

### A. Move future runtime definitions from reverse freeze to a first-class lock

The currently accepted bundle is trustworthy because every exact wheel is already
materialized, hashed, and promoted. Do not invalidate or rebuild it solely to
change lock formats.

For the next runtime revision, prefer a source dependency definition plus a
standard lock artifact (`pylock.toml` when tool support is sufficiently stable),
and preserve the final wheel manifest as the authoritative installation artifact
identity.

### B. Benchmark job-local reconstruction before optimizing

Measure:
- venv creation time;
- pip offline install time;
- bytes written;
- cold-cache versus warm-page-cache behavior;
- total time from runner admission to runtime-ready.

If reconstruction is negligible relative to model startup, keep pip.

If reconstruction is a meaningful bottleneck, evaluate a bounded uv/COW prototype
using the same trusted wheel object and exact hashes. Do not introduce a global
candidate-writable cache.

### C. Consider root-controlled OCI/container images only as a separate future path

If runtime reconstruction becomes the dominant cost or more heterogeneous GPU
stacks are needed, compare a root-controlled, digest-pinned OCI image against the
wheelhouse route. Candidate code must never receive Docker/container-runtime
administrative authority. Any container path requires separate admission,
isolation, cleanup, GPU binding, image provenance, and replay acceptance.

## Current conclusion

No architecture pivot is warranted before adversarial acceptance.

The wheelhouse runtime object now promoted for
`qwen35-vllm-cu129-image-native-sampler-v3` is aligned with established Python
deployment practice, and the Python standard library explicitly supports the
choice to recreate rather than move a virtualenv.

The next task remains offline reconstruction and adversarial acceptance. Performance
optimization of reconstruction should be evidence-driven after one measured
trusted run.
