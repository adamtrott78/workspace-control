#!/usr/bin/env bash
set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }

declare -a DNNS_CANDIDATES=()

add_dnns_candidate() {
  local raw="$1"
  [[ -n "$raw" ]] || return 0
  local prefix
  prefix="$(readlink -f "$raw" 2>/dev/null || true)"
  [[ -n "$prefix" && -d "$prefix" ]] || return 0
  [[ "$(basename "$prefix")" == "DNNs" ]] || return 0
  local py="$prefix/bin/python"
  [[ -x "$py" ]] || return 0
  local reported
  reported="$("$py" - <<'PY' 2>/dev/null || true
import pathlib, sys
print(pathlib.Path(sys.prefix).resolve())
PY
)"
  [[ -n "$reported" && "$reported" == "$prefix" ]] || return 0
  DNNS_CANDIDATES+=("$prefix")
}

for pycmd in python python3; do
  py="$(type -P "$pycmd" 2>/dev/null || true)"
  if [[ -n "$py" ]]; then
    prefix="$("$py" - <<'PY' 2>/dev/null || true
import pathlib, sys
print(pathlib.Path(sys.prefix).resolve())
PY
)"
    add_dnns_candidate "$prefix"
  fi
done

IFS=':' read -r -a PATH_PARTS <<< "${PATH:-}"
for part in "${PATH_PARTS[@]}"; do
  [[ -n "$part" ]] || continue
  if [[ "$(basename "$part")" == "bin" && "$(basename "$(dirname "$part")")" == "DNNs" ]]; then
    add_dnns_candidate "$(dirname "$part")"
  fi
done

CONDA_EXE_PATH="${CONDA_EXE:-}"
if [[ -n "$CONDA_EXE_PATH" && ! -x "$CONDA_EXE_PATH" ]]; then
  CONDA_EXE_PATH=""
fi
if [[ -z "$CONDA_EXE_PATH" ]]; then
  CONDA_EXE_PATH="$(type -P conda 2>/dev/null || true)"
fi
if [[ -z "$CONDA_EXE_PATH" ]]; then
  for candidate in     "$HOME/miniconda3/bin/conda"     "$HOME/anaconda3/bin/conda"     "$HOME/miniforge3/bin/conda"     "$HOME/mambaforge/bin/conda"
  do
    if [[ -x "$candidate" ]]; then
      CONDA_EXE_PATH="$candidate"
      break
    fi
  done
fi

if [[ -n "$CONDA_EXE_PATH" && -x "$CONDA_EXE_PATH" ]]; then
  ENV_LIST_JSON="$("$CONDA_EXE_PATH" env list --json 2>/dev/null || true)"
  if [[ -n "$ENV_LIST_JSON" ]]; then
    while IFS= read -r prefix; do
      add_dnns_candidate "$prefix"
    done < <(
      ENV_LIST_JSON="$ENV_LIST_JSON" python3 - <<'PY'
import json, os
try:
    data=json.loads(os.environ["ENV_LIST_JSON"])
except Exception:
    raise SystemExit(0)
for raw in data.get("envs", []):
    print(raw)
PY
    )
  fi
fi

for prefix in   "$HOME/miniconda3/envs/DNNs"   "$HOME/anaconda3/envs/DNNs"   "$HOME/miniforge3/envs/DNNs"   "$HOME/mambaforge/envs/DNNs"   "$HOME/.conda/envs/DNNs"   "$HOME/adamArchives/venvs/DNNs"
do
  add_dnns_candidate "$prefix"
done

mapfile -t DNNS_UNIQUE < <(printf '%s\n' "${DNNS_CANDIDATES[@]}" | awk 'NF && !seen[$0]++')
if [[ "${#DNNS_UNIQUE[@]}" -ne 1 ]]; then
  printf 'DNNs candidates discovered (%s):\n' "${#DNNS_UNIQUE[@]}" >&2
  printf '  %s\n' "${DNNS_UNIQUE[@]}" >&2
  fail "expected exactly one valid DNNs Python prefix"
fi

SOURCE_PREFIX="${DNNS_UNIQUE[0]}"
SOURCE_PYTHON="$SOURCE_PREFIX/bin/python"
[[ -x "$SOURCE_PYTHON" ]] || fail "resolved DNNs environment lacks bin/python: $SOURCE_PREFIX"

if ! SOURCE_ENV_JSON="$(SOURCE_PREFIX="$SOURCE_PREFIX" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="" PYTHONNOUSERSITE=1 "$SOURCE_PYTHON" - <<'PY'
import json, os, pathlib, site, stat, sys
expected=pathlib.Path(os.environ["SOURCE_PREFIX"]).resolve()
actual=pathlib.Path(sys.prefix).resolve()
base=pathlib.Path(sys.base_prefix).resolve()
base_python=pathlib.Path(sys.executable).resolve()
cfg=expected/"pyvenv.cfg"
conda_meta=expected/"conda-meta"
if actual != expected:
    raise SystemExit(f"DNNs Python prefix mismatch: {actual} != {expected}")
if not cfg.is_file():
    raise SystemExit(f"DNNs source is not a Python venv: missing {cfg}")
if conda_meta.exists():
    raise SystemExit(f"DNNs source unexpectedly contains Conda metadata: {conda_meta}")
if base == expected:
    raise SystemExit("DNNs source does not have a distinct Python base prefix")
cfg_text=cfg.read_text(errors="replace")
if "include-system-site-packages = false" not in cfg_text.lower():
    raise SystemExit("DNNs venv must disable system site-packages")
if bool(site.ENABLE_USER_SITE):
    raise SystemExit("DNNs venv unexpectedly enables the user site")
base_st=base_python.stat()
base_mode=stat.S_IMODE(base_st.st_mode)
if base_st.st_uid != 0 or base_st.st_gid != 0 or base_mode & 0o022:
    raise SystemExit(f"DNNs base Python is not root-controlled: {base_python} mode={base_mode:o}")
print(json.dumps({
    "environment_type":"PYTHON_VENV",
    "sys_prefix":str(actual),
    "sys_base_prefix":str(base),
    "python_executable_realpath":str(base_python),
    "base_python_root_controlled":True,
    "pyvenv_cfg":True,
    "conda_meta":False,
},sort_keys=True))
PY
)"; then
  fail "resolved DNNs prefix is not the verified isolated Python venv contract"
fi
echo "$SOURCE_ENV_JSON"

SOURCE_BASE_PYTHON="$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="" PYTHONNOUSERSITE=1 "$SOURCE_PYTHON" - <<'PY'
import pathlib, sys
print(pathlib.Path(sys.executable).resolve())
PY
)"
[[ -n "$SOURCE_BASE_PYTHON" && -x "$SOURCE_BASE_PYTHON" ]] || fail "DNNs venv base Python is unavailable: $SOURCE_BASE_PYTHON"

echo "SOURCE_DNNS_PREFIX_BINDING=PASS"
echo "SOURCE_DNNS_VENV_BINDING=PASS"
echo "SOURCE_DNNS_PREFIX=$SOURCE_PREFIX"
echo "SOURCE_DNNS_BASE_PYTHON=$SOURCE_BASE_PYTHON"

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
RUNTIME_STAGING=""
DATA_TMP=""
cleanup() {
  rm -rf "$TMP"
  if [[ -n "$RUNTIME_STAGING" ]]; then
    sudo rm -rf "$RUNTIME_STAGING" >/dev/null 2>&1 || true
  fi
  if [[ -n "$DATA_TMP" ]]; then
    sudo rm -rf "$DATA_TMP" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "=== SOURCE DNNs PREFLIGHT ==="
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="" PYTHONNOUSERSITE=1 MPLCONFIGDIR="$TMP/matplotlib" XDG_CACHE_HOME="$TMP/xdg" TORCH_HOME="$TMP/torch" SOURCE_PREFIX="$SOURCE_PREFIX" "$SOURCE_PYTHON" - <<'PY'
import json, os, pathlib
import h5py, matplotlib, numpy, pandas, scipy, sklearn, torch
expected=pathlib.Path(os.environ["SOURCE_PREFIX"]).resolve()
modules={
    "h5py":h5py,
    "matplotlib":matplotlib,
    "numpy":numpy,
    "pandas":pandas,
    "scipy":scipy,
    "sklearn":sklearn,
    "torch":torch,
}
locations={}
for name,module in modules.items():
    raw=getattr(module,"__file__",None)
    if not raw:
        raise SystemExit(f"scientific module lacks __file__: {name}")
    path=pathlib.Path(raw).resolve()
    try:
        path.relative_to(expected)
    except ValueError:
        raise SystemExit(f"scientific module escaped DNNs venv: {name} -> {path}")
    locations[name]=str(path)
payload={
    "torch_version":torch.__version__,
    "torch_cuda_version":torch.version.cuda,
    "cuda_available":bool(torch.cuda.is_available()),
    "cuda_device_count":int(torch.cuda.device_count()),
    "cuda_device_name":torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "module_locations":locations,
}
if not payload["cuda_available"] or payload["cuda_device_count"] < 1:
    raise SystemExit(f"DNNs CUDA preflight failed: {payload}")
print(json.dumps(payload,indent=2,sort_keys=True))
PY
echo "SOURCE_DNNS_IMPORT_CUDA=PASS"

TREE_DIGEST_HELPER="$TMP/tree_digest.py"
cat > "$TREE_DIGEST_HELPER" <<'PY'
import hashlib, os, pathlib, stat, sys
root=pathlib.Path(sys.argv[1]).resolve()
h=hashlib.sha256()
for path in sorted(root.rglob("*"),key=lambda p:p.relative_to(root).as_posix()):
    rel=path.relative_to(root).as_posix()
    st=path.lstat()
    mode=stat.S_IMODE(st.st_mode)
    if stat.S_ISDIR(st.st_mode):
        h.update(f"D\0{rel}\0{mode:o}\n".encode())
    elif stat.S_ISLNK(st.st_mode):
        h.update(f"L\0{rel}\0{os.readlink(path)}\n".encode())
    elif stat.S_ISREG(st.st_mode):
        d=hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda:f.read(8*1024*1024),b""):
                d.update(block)
        h.update(f"F\0{rel}\0{mode:o}\0{st.st_size}\0{d.hexdigest()}\n".encode())
    else:
        raise SystemExit(f"special runtime inode rejected: {path}")
print(h.hexdigest())
PY

SOURCE_TREE_DIGEST_PRE="$(PYTHONDONTWRITEBYTECODE=1 python3 "$TREE_DIGEST_HELPER" "$SOURCE_PREFIX")"
[[ "$SOURCE_TREE_DIGEST_PRE" =~ ^[0-9a-f]{64}$ ]] || fail "invalid source DNNs tree digest"
SOURCE_BASE_PYTHON_SHA="$(sha256sum "$SOURCE_BASE_PYTHON" | awk '{print $1}')"
[[ "$SOURCE_BASE_PYTHON_SHA" =~ ^[0-9a-f]{64}$ ]] || fail "invalid base Python digest"

SOURCE_PACKAGES="$TMP/packages.json"
SOURCE_PREFIX="$SOURCE_PREFIX" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="" PYTHONNOUSERSITE=1 "$SOURCE_PYTHON" - "$SOURCE_PACKAGES" <<'PY'
import importlib.metadata as md
import json, os, pathlib, sys
prefix=pathlib.Path(os.environ["SOURCE_PREFIX"]).resolve()
out=pathlib.Path(sys.argv[1])
rows=[]
for dist in md.distributions():
    name=dist.metadata.get("Name")
    if not name:
        raise SystemExit("installed distribution missing Name metadata")
    location=pathlib.Path(dist.locate_file("")).resolve()
    try:
        location.relative_to(prefix)
    except ValueError:
        raise SystemExit(f"distribution metadata escaped DNNs venv: {name} -> {location}")
    rows.append({"name":name,"version":dist.version})
rows.sort(key=lambda row:(row["name"].lower(),row["version"]))
out.write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
print(f"SOURCE_DNNS_DISTRIBUTIONS={len(rows)}")
PY

SOURCE_MANIFEST="$TMP/runtime-manifest.json"
SOURCE_PREFIX="$SOURCE_PREFIX" SOURCE_TREE_DIGEST_PRE="$SOURCE_TREE_DIGEST_PRE" SOURCE_BASE_PYTHON="$SOURCE_BASE_PYTHON" SOURCE_BASE_PYTHON_SHA="$SOURCE_BASE_PYTHON_SHA" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="" PYTHONNOUSERSITE=1 "$SOURCE_PYTHON" - "$SOURCE_MANIFEST" "$SOURCE_PACKAGES" <<'PY'
import hashlib, json, os, pathlib, sys
out=pathlib.Path(sys.argv[1])
packages=json.loads(pathlib.Path(sys.argv[2]).read_text())
prefix=pathlib.Path(os.environ["SOURCE_PREFIX"]).resolve()
cfg=prefix/"pyvenv.cfg"
payload={
    "schema":"padataset.dnns-source-manifest.v2",
    "environment_name":"DNNs",
    "environment_type":"PYTHON_VENV",
    "promotion_method":"python-venv-copy-rewrite-v1",
    "source_prefix":str(prefix),
    "source_python_path":str(prefix/"bin/python"),
    "python_version":sys.version,
    "sys_base_prefix":str(pathlib.Path(sys.base_prefix).resolve()),
    "base_python_path":os.environ["SOURCE_BASE_PYTHON"],
    "base_python_sha256":os.environ["SOURCE_BASE_PYTHON_SHA"],
    "pyvenv_cfg_sha256":hashlib.sha256(cfg.read_bytes()).hexdigest(),
    "source_tree_digest_sha256":os.environ["SOURCE_TREE_DIGEST_PRE"],
    "packages":packages,
}
out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PY

MANIFEST_SHA="$(sha256sum "$SOURCE_MANIFEST" | awk '{print $1}')"
[[ "$MANIFEST_SHA" =~ ^[0-9a-f]{64}$ ]] || fail "invalid DNNs manifest SHA"

RUNTIME_PATH="$RUNTIME_BASE/$MANIFEST_SHA"
RUNTIME_RECEIPT="$RECEIPT_ROOT/$MANIFEST_SHA.json"
SOURCE_OBJECT="$SOURCE_OBJECT_BASE/$MANIFEST_SHA"

echo "DNN_SOURCE_PREFIX=$SOURCE_PREFIX"
echo "DNN_SOURCE_TREE_SHA256=$SOURCE_TREE_DIGEST_PRE"
echo "DNN_BASE_PYTHON=$SOURCE_BASE_PYTHON"
echo "DNN_BASE_PYTHON_SHA256=$SOURCE_BASE_PYTHON_SHA"
echo "DNN_MANIFEST_SHA256=$MANIFEST_SHA"
echo "DNN_RUNTIME_PATH=$RUNTIME_PATH"

if sudo test -e "$RUNTIME_PATH"; then
  sudo test -f "$RUNTIME_RECEIPT" || fail "runtime exists without promotion receipt"
  echo "DNN_RUNTIME_ALREADY_PRESENT=YES"
else
  echo "=== SNAPSHOT VERIFIED PYTHON VENV ==="
  sudo install -d -o root -g root -m 0755 "$RUNTIME_BASE"
  RUNTIME_STAGING="$RUNTIME_BASE/.${MANIFEST_SHA}.next.$$"
  sudo test ! -e "$RUNTIME_STAGING" || fail "runtime staging path unexpectedly exists: $RUNTIME_STAGING"
  sudo mkdir "$RUNTIME_STAGING"
  sudo cp -a --reflink=auto "$SOURCE_PREFIX/." "$RUNTIME_STAGING/"

  COPY_TREE_DIGEST="$(sudo python3 "$TREE_DIGEST_HELPER" "$RUNTIME_STAGING")"
  [[ "$COPY_TREE_DIGEST" == "$SOURCE_TREE_DIGEST_PRE" ]] || fail "copied DNNs tree differs from verified source tree"
  SOURCE_TREE_DIGEST_POST="$(PYTHONDONTWRITEBYTECODE=1 python3 "$TREE_DIGEST_HELPER" "$SOURCE_PREFIX")"
  [[ "$SOURCE_TREE_DIGEST_POST" == "$SOURCE_TREE_DIGEST_PRE" ]] || fail "source DNNs tree changed during promotion"

  echo "SOURCE_DNNS_COPY_EQUIVALENCE=PASS"
  echo "SOURCE_DNNS_PRE_POST_INTEGRITY=PASS"

  sudo python3 - "$RUNTIME_STAGING" "$SOURCE_PREFIX" "$RUNTIME_PATH" "$SOURCE_BASE_PYTHON" <<'PY'
import json, os, pathlib, shutil, stat, sys
root=pathlib.Path(sys.argv[1]).resolve()
source=pathlib.Path(sys.argv[2]).resolve()
dest=pathlib.Path(sys.argv[3]).resolve()
allowed_base=pathlib.Path(sys.argv[4]).resolve()
source_bytes=str(source).encode()
dest_bytes=str(dest).encode()

removed_bytecode=0
for cache in sorted(
    [p for p in root.rglob("__pycache__") if p.is_dir()],
    key=lambda p:len(p.parts),
    reverse=True,
):
    shutil.rmtree(cache)
for path in list(root.rglob("*.pyc")):
    if path.is_file():
        path.unlink()
        removed_bytecode += 1

rewritten=[]
binary_refs=[]
bad_symlinks=[]
for path in sorted(root.rglob("*"),key=lambda p:p.relative_to(root).as_posix()):
    st=path.lstat()
    if stat.S_ISLNK(st.st_mode):
        raw=os.readlink(path)
        if str(source) in raw:
            bad_symlinks.append((str(path),raw,"source-prefix-target"))
            continue
        target=path.resolve(strict=False)
        try:
            target.relative_to(root)
        except ValueError:
            if target != allowed_base:
                bad_symlinks.append((str(path),str(target),"external-target"))
        continue
    if not stat.S_ISREG(st.st_mode):
        continue
    data=path.read_bytes()
    if source_bytes not in data:
        continue
    if b"\0" in data:
        binary_refs.append(str(path))
        continue
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        binary_refs.append(str(path))
        continue
    path.write_bytes(data.replace(source_bytes,dest_bytes))
    rewritten.append(path.relative_to(root).as_posix())

if binary_refs:
    for path in binary_refs[:50]:
        print(f"BINARY_SOURCE_PREFIX_REF {path}",file=sys.stderr)
    raise SystemExit("source prefix remains in non-text runtime content")
if bad_symlinks:
    for path,target,reason in bad_symlinks[:50]:
        print(f"UNSAFE_SYMLINK {reason} {path} -> {target}",file=sys.stderr)
    raise SystemExit("promoted venv contains unsupported symlink targets")

residual=[]
for path in sorted(root.rglob("*"),key=lambda p:p.relative_to(root).as_posix()):
    st=path.lstat()
    if stat.S_ISREG(st.st_mode) and source_bytes in path.read_bytes():
        residual.append(str(path))
    elif stat.S_ISLNK(st.st_mode) and str(source) in os.readlink(path):
        residual.append(str(path))
if residual:
    for path in residual[:50]:
        print(f"RESIDUAL_SOURCE_PREFIX_REF {path}",file=sys.stderr)
    raise SystemExit("promoted venv still discloses mutable source prefix")

print(json.dumps({
    "promotion_method":"python-venv-copy-rewrite-v1",
    "removed_bytecode_files":removed_bytecode,
    "rewritten_text_files":len(rewritten),
    "external_base_python":str(allowed_base),
},sort_keys=True))
PY
  echo "PROMOTED_DNNS_RELOCATION=PASS"

  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="" PYTHONNOUSERSITE=1 MPLCONFIGDIR="$TMP/matplotlib-staging" XDG_CACHE_HOME="$TMP/xdg-staging" TORCH_HOME="$TMP/torch-staging" "$RUNTIME_STAGING/bin/python" - "$RUNTIME_STAGING" <<'PY'
import json, pathlib, sys
import h5py, matplotlib, numpy, pandas, scipy, sklearn, torch
expected=pathlib.Path(sys.argv[1]).resolve()
actual=pathlib.Path(sys.prefix).resolve()
base=pathlib.Path(sys.base_prefix).resolve()
if actual != expected:
    raise SystemExit(f"staging venv prefix mismatch: {actual} != {expected}")
bad_paths=[]
for raw in sys.path:
    if not raw:
        continue
    path=pathlib.Path(raw).resolve(strict=False)
    try:
        path.relative_to(expected)
        continue
    except ValueError:
        pass
    try:
        path.relative_to(base)
        continue
    except ValueError:
        bad_paths.append(str(path))
if bad_paths:
    raise SystemExit(f"staging venv exposes external import paths: {bad_paths}")
payload={
    "torch_version":torch.__version__,
    "torch_cuda_version":torch.version.cuda,
    "cuda_available":bool(torch.cuda.is_available()),
    "cuda_device_count":int(torch.cuda.device_count()),
    "cuda_device_name":torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}
if not payload["cuda_available"] or payload["cuda_device_count"] < 1:
    raise SystemExit(f"promoted staging DNNs CUDA preflight failed: {payload}")
print(json.dumps(payload,indent=2,sort_keys=True))
PY
  echo "PROMOTED_DNNS_STAGING_IMPORT_CUDA=PASS"

  sudo chown -hR root:root "$RUNTIME_STAGING"
  sudo find -P "$RUNTIME_STAGING" -type d -exec chmod a-w,a+rx {} +
  sudo find -P "$RUNTIME_STAGING" -type f -perm /111 -exec chmod a-w,a+rx {} +
  sudo find -P "$RUNTIME_STAGING" -type f ! -perm /111 -exec chmod a-w,a+r {} +

  sudo mv "$RUNTIME_STAGING" "$RUNTIME_PATH"
  RUNTIME_STAGING="$RUNTIME_PATH"

  [[ "$(sha256sum "$SOURCE_BASE_PYTHON" | awk '{print $1}')" == "$SOURCE_BASE_PYTHON_SHA" ]] || fail "base Python changed during promotion"

  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="" PYTHONNOUSERSITE=1 MPLCONFIGDIR="$TMP/matplotlib-final" XDG_CACHE_HOME="$TMP/xdg-final" TORCH_HOME="$TMP/torch-final" "$RUNTIME_PATH/bin/python" - "$RUNTIME_PATH" <<'PY'
import json, pathlib, sys
import h5py, matplotlib, numpy, pandas, scipy, sklearn, torch
expected=pathlib.Path(sys.argv[1]).resolve()
actual=pathlib.Path(sys.prefix).resolve()
base=pathlib.Path(sys.base_prefix).resolve()
if actual != expected:
    raise SystemExit(f"final venv prefix mismatch: {actual} != {expected}")
bad_paths=[]
for raw in sys.path:
    if not raw:
        continue
    path=pathlib.Path(raw).resolve(strict=False)
    try:
        path.relative_to(expected)
        continue
    except ValueError:
        pass
    try:
        path.relative_to(base)
        continue
    except ValueError:
        bad_paths.append(str(path))
if bad_paths:
    raise SystemExit(f"final venv exposes external import paths: {bad_paths}")
payload={
    "torch_version":torch.__version__,
    "torch_cuda_version":torch.version.cuda,
    "cuda_available":bool(torch.cuda.is_available()),
    "cuda_device_count":int(torch.cuda.device_count()),
    "cuda_device_name":torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}
if not payload["cuda_available"] or payload["cuda_device_count"] < 1:
    raise SystemExit(f"promoted final DNNs CUDA preflight failed: {payload}")
print(json.dumps(payload,indent=2,sort_keys=True))
PY
  echo "PROMOTED_DNNS_IMPORT_CUDA=PASS"

  sudo install -d -o root -g root -m 0700 "$(dirname "$SOURCE_OBJECT_BASE")"
  sudo install -d -o root -g root -m 0700 "$SOURCE_OBJECT_BASE"
  sudo install -d -o root -g root -m 0700 "$SOURCE_OBJECT"
  sudo install -o root -g root -m 0400 "$SOURCE_MANIFEST" "$SOURCE_OBJECT/runtime-manifest.json"

  SOURCE_META="$TMP/source-runtime.json"
  SOURCE_PREFIX="$SOURCE_PREFIX" SOURCE_OBJECT="$SOURCE_OBJECT" MANIFEST_SHA="$MANIFEST_SHA" SOURCE_TREE_DIGEST_PRE="$SOURCE_TREE_DIGEST_PRE" SOURCE_BASE_PYTHON="$SOURCE_BASE_PYTHON" SOURCE_BASE_PYTHON_SHA="$SOURCE_BASE_PYTHON_SHA" "$SOURCE_PYTHON" - "$SOURCE_META" <<'PY'
import json, os, pathlib, sys
out=pathlib.Path(sys.argv[1])
out.write_text(json.dumps({
    "schema":"padataset.dnns-source-manifest-pointer.v2",
    "environment_name":"DNNs",
    "environment_type":"PYTHON_VENV",
    "promotion_method":"python-venv-copy-rewrite-v1",
    "source_prefix":os.environ["SOURCE_PREFIX"],
    "manifest_identity_sha256":os.environ["MANIFEST_SHA"],
    "source_tree_digest_sha256":os.environ["SOURCE_TREE_DIGEST_PRE"],
    "base_python_path":os.environ["SOURCE_BASE_PYTHON"],
    "base_python_sha256":os.environ["SOURCE_BASE_PYTHON_SHA"],
    "source_trusted_runtime_object":os.environ["SOURCE_OBJECT"],
},indent=2,sort_keys=True)+"\n")
PY
  sudo install -o root -g root -m 0400 "$SOURCE_META" "$SOURCE_OBJECT/source.json"

  sudo install -d -o root -g root -m 0755 "$RECEIPT_ROOT"
  sudo python3 - "$RUNTIME_PATH" "$RUNTIME_RECEIPT" "$MANIFEST_SHA" "$SOURCE_OBJECT" "$SOURCE_TREE_DIGEST_PRE" "$SOURCE_BASE_PYTHON" "$SOURCE_BASE_PYTHON_SHA" <<'PY'
import hashlib, json, os, pathlib, stat, sys
runtime=pathlib.Path(sys.argv[1]).resolve()
receipt=pathlib.Path(sys.argv[2])
manifest_sha=sys.argv[3]
source_object=sys.argv[4]
source_tree_sha=sys.argv[5]
base_python=pathlib.Path(sys.argv[6]).resolve()
base_python_sha=sys.argv[7]

h=hashlib.sha256()
file_count=0
directory_count=1
symlink_count=0
for path in sorted(runtime.rglob("*"),key=lambda p:p.relative_to(runtime).as_posix()):
    rel=path.relative_to(runtime).as_posix()
    st=path.lstat()
    mode=stat.S_IMODE(st.st_mode)
    if st.st_uid != 0 or st.st_gid != 0:
        raise SystemExit(f"non-root-owned runtime inode rejected: {path}")
    if stat.S_ISDIR(st.st_mode):
        directory_count += 1
        if mode & 0o222:
            raise SystemExit(f"writable runtime directory rejected: {path}")
        h.update(f"D\0{rel}\0{mode:o}\n".encode())
    elif stat.S_ISLNK(st.st_mode):
        symlink_count += 1
        h.update(f"L\0{rel}\0{os.readlink(path)}\n".encode())
    elif stat.S_ISREG(st.st_mode):
        file_count += 1
        if mode & 0o222:
            raise SystemExit(f"writable runtime file rejected: {path}")
        d=hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda:f.read(8*1024*1024),b""):
                d.update(block)
        h.update(f"F\0{rel}\0{mode:o}\0{st.st_size}\0{d.hexdigest()}\n".encode())
    else:
        raise SystemExit(f"special runtime inode rejected: {path}")
root_st=runtime.lstat()
if root_st.st_uid != 0 or root_st.st_gid != 0 or stat.S_IMODE(root_st.st_mode)&0o222:
    raise SystemExit("runtime root ownership/mode invalid")
d=hashlib.sha256()
with base_python.open("rb") as f:
    for block in iter(lambda:f.read(8*1024*1024),b""):
        d.update(block)
if d.hexdigest() != base_python_sha:
    raise SystemExit("base Python digest changed before receipt commit")
payload={
    "schema":"padataset.expanded-runtime-receipt.v2",
    "runtime_path":str(runtime),
    "runtime_contract_version":"padataset-dnns-v1",
    "promotion_method":"python-venv-copy-rewrite-v1",
    "source_manifest_identity_sha256":manifest_sha,
    "source_tree_digest_sha256":source_tree_sha,
    "source_trusted_runtime_object":source_object,
    "base_python_path":str(base_python),
    "base_python_sha256":base_python_sha,
    "tree_digest_sha256":h.hexdigest(),
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
  RUNTIME_STAGING=""
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
[[ -z "$(sudo find -P "$RUNTIME_PATH" -xdev \( -type f -o -type d \) -perm /222 -print -quit)" ]] || fail "promoted runtime contains write bits"
[[ -z "$(sudo find -P "$DATA_DEST" -xdev \( -type f -o -type d \) -perm /222 -print -quit)" ]] || fail "promoted scientific data contains write bits"
sudo test -f "$RUNTIME_RECEIPT" || fail "runtime receipt missing"

CURRENT_RUNTIME_TREE_SHA="$(sudo python3 "$TREE_DIGEST_HELPER" "$RUNTIME_PATH")"
sudo python3 - "$RUNTIME_RECEIPT" "$CURRENT_RUNTIME_TREE_SHA" <<'PY'
import hashlib, json, pathlib, sys
receipt=pathlib.Path(sys.argv[1])
current_tree=sys.argv[2]
r=json.loads(receipt.read_text())
if r["tree_digest_sha256"] != current_tree:
    raise SystemExit(f"runtime tree digest mismatch: {current_tree} != {r['tree_digest_sha256']}")
base=pathlib.Path(r["base_python_path"]).resolve()
d=hashlib.sha256()
with base.open("rb") as f:
    for block in iter(lambda:f.read(8*1024*1024),b""):
        d.update(block)
if d.hexdigest() != r["base_python_sha256"]:
    raise SystemExit("base Python digest no longer matches promoted runtime receipt")
print("PROMOTED_DNNS_RUNTIME_INTEGRITY=PASS")
PY

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
    "promotion_method":r["promotion_method"],
    "base_python_path":r["base_python_path"],
    "base_python_sha256":r["base_python_sha256"],
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
