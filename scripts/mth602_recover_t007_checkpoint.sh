#!/usr/bin/env bash
set -u
set -o pipefail
set +e

JOB_ROOT="/srv/workspace-ci/padataset/jobs/p5-e1067c12-ee3a-57fc-b6fc-830b2453b655"
RUN_NAME="l2o_hpo_tight60_PA3_PA8_t007"
EXPECTED="$JOB_ROOT/runner/_work/_temp/scientific-results/backbone/$RUN_NAME"
DST="$HOME/adamArchives/recovered/mth602-tight60-PA3-PA8-t007-run44954748830"
PY="$HOME/adamArchives/venvs/DNNs/bin/python"

echo "=== T007 CHECKPOINT RECOVERY ==="
echo "EXPECTED=$EXPECTED"
sudo -v || { echo "T007_RECOVERY_ERROR=sudo_auth_failed"; exit 0; }

SRC=""
if sudo test -d "$EXPECTED"; then
  SRC="$EXPECTED"
  echo "RECOVERY_PATH_MODE=exact_expected"
else
  echo "EXPECTED_PATH_PRESENT=NO"
  mapfile -t CANDIDATES < <(
    sudo find "$JOB_ROOT/runner/_work" -xdev -type f -name best_model.pt \
      -path "*/$RUN_NAME/best_model.pt" -printf '%h\n' 2>/dev/null | sort -u
  )
  echo "RECOVERY_CANDIDATE_COUNT=${#CANDIDATES[@]}"
  if ((${#CANDIDATES[@]} == 1)); then
    SRC="${CANDIDATES[0]}"
    echo "RECOVERY_PATH_MODE=bounded_find"
  elif ((${#CANDIDATES[@]} == 0)); then
    echo "T007_RECOVERY_NOT_FOUND=1"
    exit 0
  else
    printf 'AMBIGUOUS_CANDIDATE=%s\n' "${CANDIDATES[@]}"
    echo "T007_RECOVERY_AMBIGUOUS=1"
    exit 0
  fi
fi

echo "RECOVERY_SOURCE=$SRC"
sudo find "$SRC" -maxdepth 1 -type f -printf '%f %s bytes\n' 2>/dev/null | sort

mkdir -p "$DST" || { echo "T007_RECOVERY_ERROR=cannot_create_destination"; exit 0; }
for f in best_model.pt training_state_latest.pt config.json train_progress.json history.json summary.json final_model.pt epoch_20.pt epoch_50.pt; do
  if sudo test -f "$SRC/$f"; then sudo cp -a "$SRC/$f" "$DST/$f"; fi
done
sudo chown -R "$(id -u):$(id -g)" "$DST"

echo "=== RECOVERED FILES ==="
find "$DST" -maxdepth 1 -type f -printf '%f %s bytes\n' | sort
[[ -f "$DST/best_model.pt" ]] || { echo "T007_RECOVERY_ERROR=best_model_missing_after_copy"; exit 0; }

echo "=== SHA256 ==="
sha256sum "$DST"/* 2>/dev/null | sort
[[ -x "$PY" ]] || { echo "T007_RECOVERY_ERROR=dnns_python_missing"; exit 0; }

"$PY" - "$DST" <<'PY'
import json, math, pathlib, sys, torch
d=pathlib.Path(sys.argv[1])
best=torch.load(d/"best_model.pt",map_location="cpu",weights_only=False)
epoch=best.get("best_epoch",best.get("epoch"))
macro=best.get("best_val_macro_f1",best.get("best_val_metric"))
print("BEST_CHECKPOINT_EPOCH =",epoch)
print("BEST_VAL_MACRO_F1 =",macro)
print("BEST_VAL_ACC =",best.get("best_val_acc"))
val=best.get("val_stats") or {}
names=best.get("class_names") or val.get("class_names")
cm=val.get("confusion_matrix")
per={}
if cm is not None and names:
    cm=torch.as_tensor(cm,dtype=torch.float64)
    for i,name in enumerate(names):
        tp=cm[i,i].item(); fp=cm[:,i].sum().item()-tp; fn=cm[i,:].sum().item()-tp
        p=tp/(tp+fp) if tp+fp else 0.0
        r=tp/(tp+fn) if tp+fn else 0.0
        per[str(name)]=2*p*r/(p+r) if p+r else 0.0
if per:
    worst=min(per,key=per.get)
    print("VAL_PER_CLASS_F1 =",json.dumps(per,sort_keys=True))
    print("VAL_MIN_CLASS =",worst)
    print("VAL_MIN_CLASS_F1 =",per[worst])
    print("VAL_MACRO_F1_RECOMPUTED =",sum(per.values())/len(per))
state_epoch=None
sp=d/"training_state_latest.pt"
if sp.exists():
    st=torch.load(sp,map_location="cpu",weights_only=False)
    state_epoch=st.get("epoch")
    print("TRAINING_STATE_EPOCH =",state_epoch)
    print("TRAINING_STATE_BEST_EPOCH =",st.get("best_epoch"))
    print("TRAINING_STATE_BEST_METRIC =",st.get("best_metric"))
pp=d/"train_progress.json"
if pp.exists(): print("LAST_PROGRESS =",pp.read_text().strip())
errors=[]
if epoch!=59: errors.append(f"best_epoch={epoch!r}")
if macro is None or not math.isfinite(float(macro)) or abs(float(macro)-0.99377)>5e-4:
    errors.append(f"best_val_macro_f1={macro!r}")
if state_epoch is not None and state_epoch!=59: errors.append(f"training_state_epoch={state_epoch!r}")
if errors:
    print("T007_CHECKPOINT_RECOVERY=FAIL")
    for e in errors: print("RECOVERY_VALIDATION_ERROR =",e)
else:
    print("T007_CHECKPOINT_RECOVERY=PASS")
PY

echo "RECOVERY_DESTINATION=$DST"
