#!/usr/bin/env bash
set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }

[[ "${CONDA_DEFAULT_ENV:-}" == "DNNs" ]] || fail "activate the DNNs Conda environment before running this installer"
[[ -n "${CONDA_PREFIX:-}" ]] || fail "CONDA_PREFIX is missing"
[[ -d "$CONDA_PREFIX" ]] || fail "DNNs CONDA_PREFIX does not exist: $CONDA_PREFIX"

CONDA_EXE_PATH="${CONDA_EXE:-}"
if [[ -z "$CONDA_EXE_PATH" ]]; then
  CONDA_EXE_PATH="$(command -v conda || true)"
fi
[[ -n "$CONDA_EXE_PATH" && -x "$CONDA_EXE_PATH" ]] || fail "conda executable is unavailable"

SOURCE_PREFIX="$(readlink -f "$CONDA_PREFIX")"
SOURCE_PYTHON="$SOURCE_PREFIX/bin/python"
[[ -x "$SOURCE_PYTHON" ]] || fail "DNNs Python missing: $SOURCE_PYTHON"

PADATASET_CHECKOUT="${PADATASET_CHECKOUT:-$HOME/adamArchives/Adam/varMax/PADataset}"
[[ -d "$PADATASET_CHECKOUT/.git" || -f "$PADATASET_CHECKOUT/.git" ]] || fail "PADataset checkout not found: $PADATASET_CHECKOUT"

SOURCE_CACHE="$PADATASET_CHECKOUT/_feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01"
[[ -d "$SOURCE_CACHE" ]] || fail "Stage 03 feature cache missing: $SOURCE_CACHE"
find "$SOURCE_CACHE" -maxdepth 1 -type f -name '*.h5' -print -quit | grep -q . || fail "Stage 03 feature cache has no H5 files"

PROJECT_ROOT="/srv/workspace-ci/padataset"
TRUSTED_CACHE="$PROJECT_ROOT/trusted-cache"
RUNTIME_BASE="$PROJECT_ROOT/expanded-runtimes/padataset-dnns-v1"
RECEIPT_ROOT="/var/lib/workspace-ci/expanded-runtime-receipts"
DATA_PROFILE_ID="ota_core_high_run01_len16384_v1"
DATA_DEST="$TRUSTED_CACHE/scientific-data/$DATA_PROFILE_ID"
SOURCE_OBJECT_BASE="/var/lib/workspace-ci/padataset-runtime-sources/sha256"

command -v sudo >/dev/null || fail "sudo is required for one-time root promotion"
command -v sha256sum >/dev/null || fail "sha256sum is required"
command -v cp >/dev/null || fail "cp is required"
command -v find >/dev/null || fail "find is required"

TMP="$(mktemp -d /tmp/padataset-dnns-promotion.XXXXXX)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "=== SOURCE DNNs PREFLIGHT ==="
"$SOURCE_PYTHON" - <<'PY'
import json
import h5py, matplotlib, numpy, pandas, scipy, sklearn, torch
payload={
    "torch_version": torch.__version__,
    "torch_cuda_version": torch.version.cuda,
    "cuda_available": bool(torch.cuda.is_available()),
    "cuda_device_count": int(torch.cuda.device_count()),
    "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}
if not payload["cuda_available"] or payload["cuda_device_count"] < 1:
    raise SystemExit(f"DNNs CUDA preflight failed: {payload}")
print(json.dumps(payload, indent=2, sort_keys=True))
PY
echo "SOURCE_DNNS_IMPORT_CUDA=PASS"

"$CONDA_EXE_PATH" list --explicit --prefix "$SOURCE_PREFIX" > "$TMP/environment.explicit.txt"
[[ -s "$TMP/environment.explicit.txt" ]] || fail "conda explicit manifest is empty"
MANIFEST_SHA="$(sha256sum "$TMP/environment.explicit.txt" | awk '{print $1}')"
[[ "$MANIFEST_SHA" =~ ^[0-9a-f]{64}$ ]] || fail "invalid DNNs manifest SHA"

RUNTIME_PATH="$RUNTIME_BASE/$MANIFEST_SHA"
RUNTIME_RECEIPT="$RECEIPT_ROOT/$MANIFEST_SHA.json"
SOURCE_OBJECT="$SOURCE_OBJECT_BASE/$MANIFEST_SHA"

echo "DNN_SOURCE_PREFIX=$SOURCE_PREFIX"
echo "DNN_MANIFEST_SHA256=$MANIFEST_SHA"
echo "DNN_RUNTIME_PATH=$RUNTIME_PATH"

if sudo test -e "$RUNTIME_PATH"; then
  sudo test -f "$RUNTIME_RECEIPT" || fail "runtime exists without promotion receipt"
  echo "DNN_RUNTIME_ALREADY_PRESENT=YES"
else
  echo "=== CLONE DNNs INTO FINAL CANONICAL PREFIX ==="
  sudo install -d -o root -g root -m 0755 "$RUNTIME_BASE"
  sudo mkdir "$RUNTIME_PATH"
  sudo chown "$(id -u):$(id -g)" "$RUNTIME_PATH"
  CLONE_OK=0
  if CONDA_OFFLINE=true "$CONDA_EXE_PATH" create --yes --offline --prefix "$RUNTIME_PATH" --clone "$SOURCE_PREFIX"; then
    CLONE_OK=1
  fi
  if [[ "$CLONE_OK" != "1" ]]; then
    sudo rm -rf "$RUNTIME_PATH"
    fail "DNNs exact-prefix conda clone failed; do not fall back to the mutable source environment"
  fi

  [[ -x "$RUNTIME_PATH/bin/python" ]] || fail "cloned DNNs Python missing"
  "$RUNTIME_PATH/bin/python" - <<'PY'
import json
import h5py, matplotlib, numpy, pandas, scipy, sklearn, torch
payload={
    "torch_version": torch.__version__,
    "torch_cuda_version": torch.version.cuda,
    "cuda_available": bool(torch.cuda.is_available()),
    "cuda_device_count": int(torch.cuda.device_count()),
    "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}
if not payload["cuda_available"] or payload["cuda_device_count"] < 1:
    raise SystemExit(f"promoted DNNs CUDA preflight failed: {payload}")
print(json.dumps(payload, indent=2, sort_keys=True))
PY
  echo "PROMOTED_DNNS_IMPORT_CUDA=PASS"

  sudo install -d -o root -g root -m 0700 "$(dirname "$SOURCE_OBJECT_BASE")"
  sudo install -d -o root -g root -m 0700 "$SOURCE_OBJECT_BASE"
  sudo install -d -o root -g root -m 0700 "$SOURCE_OBJECT"
  sudo install -o root -g root -m 0400 "$TMP/environment.explicit.txt" "$SOURCE_OBJECT/environment.explicit.txt"

  SOURCE_META="$TMP/source-runtime.json"
  SOURCE_PREFIX="$SOURCE_PREFIX" SOURCE_OBJECT="$SOURCE_OBJECT" MANIFEST_SHA="$MANIFEST_SHA" "$SOURCE_PYTHON" - "$SOURCE_META" <<'PY'
import json, os, pathlib, sys
out=pathlib.Path(sys.argv[1])
out.write_text(json.dumps({
    "schema":"padataset.dnns-source-manifest.v1",
    "environment_name":"DNNs",
    "source_prefix":os.environ["SOURCE_PREFIX"],
    "manifest_identity_sha256":os.environ["MANIFEST_SHA"],
    "source_trusted_runtime_object":os.environ["SOURCE_OBJECT"],
},indent=2,sort_keys=True)+"\n")
PY
  sudo install -o root -g root -m 0400 "$SOURCE_META" "$SOURCE_OBJECT/source.json"

  # Reject relocations that still point into mutable user-home content.
  if sudo python3 - "$RUNTIME_PATH" <<'PY'
import pathlib, sys
root=pathlib.Path(sys.argv[1]).resolve()
allowed={pathlib.Path("/usr/bin/python3"),pathlib.Path("/usr/bin/python3.12")}
bad=[]
for p in root.rglob("*"):
    if not p.is_symlink():
        continue
    target=p.resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError:
        if target not in allowed:
            bad.append((str(p),str(target)))
if bad:
    for p,t in bad[:50]:
        print(f"EXTERNAL_SYMLINK {p} -> {t}", file=sys.stderr)
    raise SystemExit(1)
PY
  then
    :
  else
    sudo rm -rf "$RUNTIME_PATH"
    fail "promoted DNNs contains unsupported external symlinks"
  fi

  sudo chown -R root:root "$RUNTIME_PATH"
  sudo chmod -R a-w "$RUNTIME_PATH"
  sudo find "$RUNTIME_PATH" -type d -exec chmod a+rx {} +
  sudo find "$RUNTIME_PATH" -type f -perm /111 -exec chmod a+rx {} +
  sudo find "$RUNTIME_PATH" -type f ! -perm /111 -exec chmod a+r {} +

  sudo install -d -o root -g root -m 0755 "$RECEIPT_ROOT"
  sudo python3 - "$RUNTIME_PATH" "$RUNTIME_RECEIPT" "$MANIFEST_SHA" "$SOURCE_OBJECT" <<'PY'
import hashlib, json, os, pathlib, stat, sys
runtime=pathlib.Path(sys.argv[1]).resolve()
receipt=pathlib.Path(sys.argv[2])
manifest_sha=sys.argv[3]
source_object=sys.argv[4]

h=hashlib.sha256()
file_count=0
directory_count=1
symlink_count=0
for path in sorted(runtime.rglob("*"), key=lambda p:p.relative_to(runtime).as_posix()):
    rel=path.relative_to(runtime).as_posix()
    st=path.lstat()
    mode=stat.S_IMODE(st.st_mode)
    if stat.S_ISDIR(st.st_mode):
        directory_count += 1
        h.update(f"D\0{rel}\0{mode:o}\n".encode())
    elif stat.S_ISLNK(st.st_mode):
        symlink_count += 1
        h.update(f"L\0{rel}\0{os.readlink(path)}\n".encode())
    elif stat.S_ISREG(st.st_mode):
        file_count += 1
        d=hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda:f.read(8*1024*1024), b""):
                d.update(block)
        h.update(f"F\0{rel}\0{mode:o}\0{st.st_size}\0{d.hexdigest()}\n".encode())
    else:
        raise SystemExit(f"special runtime inode rejected: {path}")
    if mode & 0o222:
        raise SystemExit(f"writable runtime inode rejected: {path}")
root_st=runtime.lstat()
if root_st.st_uid != 0 or root_st.st_gid != 0 or stat.S_IMODE(root_st.st_mode)&0o222:
    raise SystemExit("runtime root ownership/mode invalid")
tree=h.hexdigest()
payload={
    "schema":"padataset.expanded-runtime-receipt.v1",
    "runtime_path":str(runtime),
    "runtime_contract_version":"padataset-dnns-v1",
    "source_manifest_identity_sha256":manifest_sha,
    "source_trusted_runtime_object":source_object,
    "tree_digest_sha256":tree,
    "read_only_hardened":True,
    "receipt_committed_after_all_assertions":True,
    "model_weights_loaded":False,
    "model_inference_performed":False,
    "file_count":file_count,
    "directory_count":directory_count,
    "symlink_count":symlink_count,
}
receipt.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
os.chown(receipt,0,0)
os.chmod(receipt,0o444)
print(json.dumps(payload,sort_keys=True))
PY
fi

echo "=== PROMOTE EXACT STAGE03 FEATURE CACHE ==="
if sudo test -e "$DATA_DEST"; then
  sudo test -f "$DATA_DEST/promotion.json" || fail "scientific data destination exists without promotion receipt"
  echo "SCIENTIFIC_DATA_ALREADY_PRESENT=YES"
else
  SOURCE_FILE_COUNT="$(find "$SOURCE_CACHE" -maxdepth 1 -type f -name '*.h5' | wc -l)"
  SOURCE_BYTES="$(du -sb "$SOURCE_CACHE" | awk '{print $1}')"
  [[ "$SOURCE_FILE_COUNT" -gt 0 ]] || fail "no source cache files"

  sudo install -d -o root -g root -m 0755 "$(dirname "$DATA_DEST")"
  DATA_TMP="$DATA_DEST.next.$$"
  sudo rm -rf "$DATA_TMP"
  sudo mkdir "$DATA_TMP"
  sudo cp -a --reflink=auto "$SOURCE_CACHE/." "$DATA_TMP/"
  sudo chown -R root:root "$DATA_TMP"
  sudo chmod -R a-w "$DATA_TMP"
  sudo find "$DATA_TMP" -type d -exec chmod a+rx {} +
  sudo find "$DATA_TMP" -type f -exec chmod a+r {} +

  sudo python3 - "$DATA_TMP" "$SOURCE_FILE_COUNT" "$SOURCE_BYTES" <<'PY'
import hashlib, json, os, pathlib, stat, sys
root=pathlib.Path(sys.argv[1]).resolve()
expected_count=int(sys.argv[2])
source_bytes=int(sys.argv[3])
files=[]
tree=hashlib.sha256()
for p in sorted(root.glob("*.h5"), key=lambda x:x.name):
    st=p.lstat()
    if not stat.S_ISREG(st.st_mode):
        raise SystemExit(f"non-regular cache entry: {p}")
    if stat.S_IMODE(st.st_mode)&0o222:
        raise SystemExit(f"writable cache file: {p}")
    d=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(8*1024*1024), b""):
            d.update(block)
    row={"name":p.name,"bytes":st.st_size,"sha256":d.hexdigest()}
    files.append(row)
    tree.update(f"{p.name}\0{st.st_size}\0{row['sha256']}\n".encode())
if len(files)!=expected_count:
    raise SystemExit(f"cache count mismatch {len(files)} != {expected_count}")
payload={
    "schema":"padataset.scientific-data-promotion.v1",
    "profile_id":"ota_core_high_run01_len16384_v1",
    "cache_len":16384,
    "source_type":"ota",
    "source_name":"ota_core_high_run01",
    "dataset_tag":"ota_core_high_run01",
    "noise_tag":"high_run01",
    "file_count":len(files),
    "source_tree_bytes":source_bytes,
    "tree_digest_sha256":tree.hexdigest(),
    "files":files,
    "read_only_hardened":True,
}
(root/"promotion.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
os.chown(root/"promotion.json",0,0)
os.chmod(root/"promotion.json",0o444)
print(json.dumps({
    "profile_id":payload["profile_id"],
    "file_count":payload["file_count"],
    "tree_digest_sha256":payload["tree_digest_sha256"],
},sort_keys=True))
PY

  sudo mv "$DATA_TMP" "$DATA_DEST"
fi

echo "=== FINAL VERIFY / EMIT BINDINGS ==="
sudo test -x "$RUNTIME_PATH/bin/python" || fail "promoted runtime Python unavailable"
[[ -z "$(sudo find "$RUNTIME_PATH" -xdev -perm /222 -print -quit)" ]] || fail "promoted runtime contains write bits"
[[ -z "$(sudo find "$DATA_DEST" -xdev -perm /222 -print -quit)" ]] || fail "promoted scientific data contains write bits"
sudo test -f "$RUNTIME_RECEIPT" || fail "runtime receipt missing"

sudo python3 - "$RUNTIME_RECEIPT" "$DATA_DEST/promotion.json" <<'PY'
import json, pathlib, sys
runtime_receipt=pathlib.Path(sys.argv[1])
data_receipt=pathlib.Path(sys.argv[2])
r=json.loads(runtime_receipt.read_text())
d=json.loads(data_receipt.read_text())
binding={
    "runtime_id":"padataset-dnns-v1",
    "canonical_path":r["runtime_path"],
    "python_path":str(pathlib.Path(r["runtime_path"])/"bin/python"),
    "receipt_path":str(runtime_receipt),
    "tree_digest_sha256":r["tree_digest_sha256"],
    "manifest_identity_sha256":r["source_manifest_identity_sha256"],
    "source_trusted_runtime_object":r["source_trusted_runtime_object"],
    "required_controls":[
        "root_owned_no_write_bits",
        "private_systemd_mount_namespace",
        "read_only_bind",
        "no_new_privileges",
        "restrict_suid_sgid",
        "device_policy_closed",
        "job_local_mutable_caches",
    ],
}
print("PADATASET_DNNS_RUNTIME_BINDING_JSON="+json.dumps(binding,separators=(",",":")))
print("PADATASET_SCIENTIFIC_DATA_JSON="+json.dumps({
    "profile_id":d["profile_id"],
    "path":str(data_receipt.parent),
    "tree_digest_sha256":d["tree_digest_sha256"],
    "file_count":d["file_count"],
},separators=(",",":")))
print("PADATASET_SCIENTIFIC_PROMOTION=PASS")
PY
