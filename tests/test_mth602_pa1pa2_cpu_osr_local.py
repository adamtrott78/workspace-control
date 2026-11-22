from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/mth602_pa1pa2_cpu_osr_local.sh"

def test_direct_cpu_osr_is_exact_and_gpu_hidden():
    text=SCRIPT.read_text()
    required=[
        'EXPECTED_ARTIFACT_SHA256="7c439dc693c96777ec04ded9e76b69a7dc9b8d774cf4192bd502f880cda77f79"',
        'EXPECTED_PAD_HEAD="761deab35e728fba99177ae3f09192caf512fbde"',
        'ARTIFACT_ID="14765881457"',
        'RUN_NAME="l2o_t007_fullmatrix_PA1_PA2"',
        'CUDA_VISIBLE_DEVICES=""',
        'a[i+1]="cpu"',
        'CPU_OSR_RESULT_DIRECTION=',
        'EQUIVALENCE_STATUS=PENDING_SAME_BACKBONE_CUDA_REFERENCE',
        'GPU_TRAINING_TOUCHED=NO',
    ]
    for marker in required:
        assert marker in text

def test_direct_cpu_osr_has_no_training_or_gpu_device():
    text=SCRIPT.read_text()
    assert "pa_train_one.py" not in text
    assert "--device cuda" not in text
    assert "nvidia-smi" not in text
