#!/usr/bin/env bash
set -u
set -o pipefail
set +e

ARTIFACT_URL="${1:-}"
EXPECTED_ARTIFACT_SHA256="7c439dc693c96777ec04ded9e76b69a7dc9b8d774cf4192bd502f880cda77f79"
EXPECTED_PAD_HEAD="761deab35e728fba99177ae3f09192caf512fbde"
RUN_NAME="l2o_t007_fullmatrix_PA1_PA2"
ARTIFACT_ID="14765881457"
DATA_ROOT="/srv/workspace-ci/padataset/trusted-cache/scientific-data/ota_core_high_run01_len16384_v1"
WORK="${MTH602_PA1PA2_CPU_WORK:-/tmp/mth602-pa1pa2-cpu-osr}"
REPO="${MTH602_PADATASET_REPO:-$PWD}"
PY="${MTH602_PYTHON:-$(command -v python3)}"

echo "=== MTH602 PA1-PA2 T007 LOCAL CPU OSR ==="
echo "GPU_USE=FORBIDDEN"
echo "EXPECTED_PAD_HEAD=$EXPECTED_PAD_HEAD"
echo "ARTIFACT_ID=$ARTIFACT_ID"
echo "EXPECTED_ARTIFACT_SHA256=$EXPECTED_ARTIFACT_SHA256"
echo "WORK=$WORK"

if [[ -z "$ARTIFACT_URL" ]]; then
  echo "CPU_OSR_ERROR=artifact_url_missing"
  exit 0
fi

git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || {
  echo "CPU_OSR_ERROR=repo_not_git"
  exit 0
}

remote_url="$(git -C "$REPO" remote get-url origin 2>/dev/null || true)"
case "$remote_url" in
  *adamtrott78/PADataset*) ;;
  *)
    echo "CPU_OSR_ERROR=wrong_repo_origin"
    echo "ORIGIN=$remote_url"
    exit 0
    ;;
esac

[[ -x "$PY" ]] || {
  echo "CPU_OSR_ERROR=python_missing"
  exit 0
}

sudo -v || {
  echo "CPU_OSR_ERROR=sudo_auth_failed"
  exit 0
}

sudo rm -rf "$WORK"
sudo mkdir -p "$WORK"
sudo chown "$(id -u):$(id -g)" "$WORK"

echo
echo "=== DOWNLOAD EXACT VERIFIED ARTIFACT ==="
curl -fL --retry 2 --retry-delay 1 "$ARTIFACT_URL" -o "$WORK/artifact.zip"
rc=$?
if [[ $rc -ne 0 ]]; then
  echo "CPU_OSR_ERROR=artifact_download_failed rc=$rc"
  exit 0
fi

actual="$(sha256sum "$WORK/artifact.zip" | awk '{print $1}')"
echo "ARTIFACT_SHA256=$actual"
if [[ "$actual" != "$EXPECTED_ARTIFACT_SHA256" ]]; then
  echo "CPU_OSR_ERROR=artifact_sha256_mismatch"
  exit 0
fi
echo "ARTIFACT_VERIFICATION=PASS"

echo
echo "=== MATERIALIZE EXACT OSR SOURCE ==="
git -C "$REPO" fetch --force --depth=1 origin "$EXPECTED_PAD_HEAD"
rc=$?
if [[ $rc -ne 0 ]]; then
  echo "CPU_OSR_ERROR=source_fetch_failed rc=$rc"
  exit 0
fi
actual_head="$(git -C "$REPO" rev-parse FETCH_HEAD)"
if [[ "$actual_head" != "$EXPECTED_PAD_HEAD" ]]; then
  echo "CPU_OSR_ERROR=source_head_mismatch actual=$actual_head"
  exit 0
fi

git -C "$REPO" worktree remove --force "$WORK/repo" >/dev/null 2>&1 || true
git -C "$REPO" worktree add --detach "$WORK/repo" "$EXPECTED_PAD_HEAD"
rc=$?
if [[ $rc -ne 0 ]]; then
  echo "CPU_OSR_ERROR=worktree_add_failed rc=$rc"
  exit 0
fi

echo
echo "=== REHYDRATE BACKBONE ==="
mkdir -p "$WORK/rehydrated"
unzip -q "$WORK/artifact.zip" -d "$WORK/rehydrated"
RUN_DIR="$WORK/rehydrated/scientific-results/backbone/$RUN_NAME"
for f in config.json best_model.pt summary.json train_complete.json; do
  [[ -f "$RUN_DIR/$f" ]] || {
    echo "CPU_OSR_ERROR=missing_artifact_file file=$f"
    exit 0
  }
done

best_sha="$(sha256sum "$RUN_DIR/best_model.pt" | awk '{print $1}')"
echo "BEST_MODEL_SHA256=$best_sha"
[[ "$best_sha" == "82effeb4d9f669cfdcc16dca2539149c3d6f5ec5a79901153108d509175b48ee" ]] || {
  echo "CPU_OSR_ERROR=best_model_sha_mismatch"
  exit 0
}

sudo test -d "$DATA_ROOT" || {
  echo "CPU_OSR_ERROR=trusted_data_missing"
  exit 0
}
sudo test -r "$DATA_ROOT/promotion.json" || {
  echo "CPU_OSR_ERROR=trusted_data_not_readable"
  exit 0
}

echo
echo "=== PROVE CPU-ONLY RUNTIME ==="
CUDA_VISIBLE_DEVICES="" "$PY" - <<'PY'
import torch
print("CUDA_AVAILABLE=", bool(torch.cuda.is_available()))
print("CUDA_DEVICE_COUNT=", int(torch.cuda.device_count()))
assert not torch.cuda.is_available()
assert torch.cuda.device_count() == 0
print("CPU_ONLY_RUNTIME=PASS")
PY
rc=$?
if [[ $rc -ne 0 ]]; then
  echo "CPU_OSR_ERROR=cpu_only_gate_failed rc=$rc"
  exit 0
fi

run_one () {
  local target="$1"
  local surrogate="$2"
  local request="$WORK/repo/manifests/configs/l2o_directional_eval_v1/PA1-PA2__target${target}__sur${surrogate}.json"
  local out="$WORK/results/target${target}_sur${surrogate}"
  local resolved="$WORK/resolved_${target}_${surrogate}.json"
  mkdir -p "$out"

  echo
  echo "=== CPU OSR ${target}<-${surrogate} ==="

  CUDA_VISIBLE_DEVICES="" "$PY" "$WORK/repo/experiments/l2o_eval_request_contract.py" \
    --request "$request" \
    --matrix "$WORK/repo/manifests/l2o_canonical_backbone_matrix_v1.json" \
    --policy "$WORK/repo/manifests/l2o_directional_eval_policy_v1.json" \
    --run-dir "$RUN_DIR" \
    --out-dir "$out" > "$resolved"
  rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "CPU_OSR_DIRECTION_ERROR=${target}<-${surrogate}:request_contract rc=$rc"
    return
  fi

  mapfile -t eval_args < <(
    "$PY" - "$resolved" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
a=list(d["evaluator_args"])
i=a.index("--device")
assert a[i+1]=="cuda"
a[i+1]="cpu"
print(*a,sep="\n")
PY
  )

  sudo -E env CUDA_VISIBLE_DEVICES="" "$PY" "$WORK/repo/experiments/pa_eval_dqn_guard_surrogate_open.py" \
    "${eval_args[@]}" \
    --data-root "$DATA_ROOT"
  rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "CPU_OSR_DIRECTION_ERROR=${target}<-${surrogate}:evaluator rc=$rc"
    return
  fi

  sudo chown -R "$(id -u):$(id -g)" "$out"

  [[ -f "$out/osr_summary.csv" ]] || {
    echo "CPU_OSR_DIRECTION_ERROR=${target}<-${surrogate}:summary_missing"
    return
  }

  CUDA_VISIBLE_DEVICES="" "$PY" "$WORK/repo/experiments/l2o_eval_result_record.py" \
    --request "$request" \
    --matrix "$WORK/repo/manifests/l2o_canonical_backbone_matrix_v1.json" \
    --policy "$WORK/repo/manifests/l2o_directional_eval_policy_v1.json" \
    --summary-csv "$out/osr_summary.csv" \
    --output "$out/result_record.json"
  rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "CPU_OSR_DIRECTION_ERROR=${target}<-${surrogate}:result_record rc=$rc"
    return
  fi

  "$PY" - "$out/result_record.json" "$target" "$surrogate" <<'PY'
import json,sys
p,target,sur=sys.argv[1:]
d=json.load(open(p))
print(f"CPU_OSR_RESULT_DIRECTION={target}<-{sur}")
print("CPU_OSR_RESULT_JSON="+json.dumps(d,sort_keys=True))
PY
}

run_one PA1 PA2
run_one PA2 PA1

echo
echo "=== CPU OSR COMPLETE ==="
echo "RESULT_ROOT=$WORK/results"
echo "REFERENCE_POLICY_DEVICE=cuda"
echo "EXECUTED_DEVICE=cpu"
echo "EQUIVALENCE_STATUS=PENDING_SAME_BACKBONE_CUDA_REFERENCE"
echo "GPU_TRAINING_TOUCHED=NO"
