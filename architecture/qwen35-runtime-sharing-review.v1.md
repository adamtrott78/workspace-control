# Qwen Runtime Sharing Architecture Review v1

Status: decision record for `workspace-lambda-execution-policy-v1`.

## Why filesystem reflink failed

The Lambda host stores both `/var/tmp` and the trusted cache on the same ext4 filesystem.
That satisfies the same-filesystem requirement for Linux FICLONE/reflink, but ext4 does not
implement the reflink/FICLONE facility used by `cp --reflink`. The observed
`Operation not supported` result is therefore expected, not a permissions or mount-option issue.

Linux FICLONE provides block-sharing with copy-on-write only on filesystems that implement it.
Current Linux documentation names XFS and Btrfs as examples of filesystems with this behavior;
current ext4 feature documentation does not expose a reflink feature.

Changing an ext4 mount option cannot enable reflink. Obtaining true filesystem reflink semantics
would require a reflink-capable filesystem (for example XFS/Btrfs) or a separately mounted
reflink-capable filesystem/image, which would be a host-storage architecture change.

References:
- https://man7.org/linux/man-pages/man2/ioctl_ficlone.2.html
- https://www.kernel.org/doc/html/latest/admin-guide/ext4.html

## Established zero-copy pattern

The relevant established pattern is an immutable shared lower/runtime tree plus per-job isolation,
not repeated package installation.

Nix uses cryptographically addressed read-only store objects and exposes them into sandboxed builds.
Container runtimes use read-only image/lower layers and thin per-container writable layers.
Linux OverlayFS implements this directly with a `lowerdir` and optional writable
`upperdir`/`workdir`; unchanged lower files are read directly, and writes are copied up into
the private upper layer.

References:
- https://wiki.nixos.org/wiki/Nix_store
- https://docs.kernel.org/filesystems/overlayfs.html
- https://docs.docker.com/engine/storage/drivers/

## Options

### 1. Root-owned immutable expanded runtime + read-only job mount

Preferred first choice.

Build the exact 196-package environment once from the already-trusted wheel bundle under root
authority. The expanded runtime becomes a root-owned immutable trusted object.

For each job:
- create a private mount namespace;
- expose the expanded runtime read-only at a stable execution path;
- expose the trusted model read-only;
- provide separate writable HOME, TMPDIR, XDG cache, Torch/vLLM compile caches, and job workspace;
- disable Python bytecode writes into the runtime tree or redirect them to job-local state;
- execute the runtime directly without package reconstruction.

This avoids copying ~11 GB per job and does not rely on inode sharing between writable candidate
paths and the trusted store.

Linux mount-namespace semantics lock read-only mount flags when propagated from a more privileged
namespace into a less privileged namespace, preventing the less-privileged job from remounting
that shared runtime writable.

Reference:
- https://man7.org/linux/man-pages/man7/mount_namespaces.7.html

### 2. OverlayFS over the immutable expanded runtime

Use only if runtime compatibility testing proves that some component must write beneath the runtime
tree itself.

Create, under root/provisioner authority:
- lowerdir = immutable expanded trusted runtime;
- upperdir = unique per-job writable directory;
- workdir = unique per-job work directory;
- merged = stable runtime path inside the private job mount namespace.

Unmodified files remain shared from the lower layer. A write copies the affected file into the
job-local upper layer, preserving the trusted lower object. This is the same copy-on-write layering
model used by container storage drivers and does not require ext4 reflink support.

### 3. Hardlinks

Not preferred.

Hardlinks are multiple names for the same inode. They are not copy-on-write. Candidate-created
hardlinks to root-owned read-only files may also be blocked by Linux `protected_hardlinks`.
A privileged provisioner could create them, but the architecture is less clean because file identity,
ownership, permission changes, and lifecycle remain coupled to the shared inode.

Reference:
- https://www.kernel.org/doc/html/latest/admin-guide/sysctl/fs.html

### 4. Symlinks

Not preferred.

Symlinks are path references to the shared object. They introduce path-coupling and traversal
complexity without adding mutation isolation. uv itself discourages symlink cache mode because
environment correctness becomes tightly coupled to cache lifetime.

### 5. Move runtime storage to XFS/Btrfs for true reflinks

Technically attractive but disproportionate for the current task.

A reflink-capable filesystem would provide ideal independent inodes backed by shared blocks, but
migrating/reformatting host storage or introducing a loop-mounted filesystem is a new host-storage
boundary. It is not justified while read-only mounts/OverlayFS already supply the needed sharing
semantics on ext4.

## Decision

Do not continue optimizing package installers.

The pip (84.46 s) and uv copy (~24 s cold and warm) measurements prove that repeated environment
materialization is the wrong steady-state abstraction.

Next:
1. build one expanded runtime from the trusted wheel bundle under root authority;
2. verify exact package/runtime identity;
3. harden it read-only as a trusted expanded-runtime object;
4. launch a no-inference compatibility canary directly from that read-only runtime with all mutable
   caches/state redirected to the job workspace;
5. if and only if a component requires writes under the runtime path, add a per-job OverlayFS upper;
6. then run adversarial acceptance on that final execution path.

Do not use hardlinks or symlinks as the primary production design.
