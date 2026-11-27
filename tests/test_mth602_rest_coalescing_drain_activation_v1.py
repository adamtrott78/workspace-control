from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / "scripts" / "mth602_activate_v3_rest_backfill_liveness_v1.py"
REPAIR = ROOT / "scripts" / "lambda_ci_v3_live_controller_repair_v1.py"


def test_drain_happens_before_authority_and_binds_restore_set():
    boot = BOOT.read_text()
    repair = REPAIR.read_text()

    assert "DRAIN_QUIESCE_BEGIN" in boot
    assert "DRAIN_COMPLETE live_work=0" in boot
    assert "--drain-timeout-seconds" in boot
    assert boot.index("DRAIN_QUIESCE_BEGIN") < boot.index('"authorization_id"')
    assert '"active_controller_set_before": active_before' in boot

    assert "--prequiesced-active-controller" in repair
    assert '"active_controller_set_before":active_before' in repair
    assert "prequiesced activation requires all controller units inactive" in repair


def test_drain_activation_scripts_compile():
    py_compile.compile(str(BOOT), doraise=True)
    py_compile.compile(str(REPAIR), doraise=True)


def test_resume_prequiesced_drain_requires_explicit_restore_set():
    boot = BOOT.read_text()

    assert "--resume-prequiesced-active-controller" in boot
    assert "DRAIN_RESUME_PREQUIESCED" in boot
    assert "resume-prequiesced requires every controller unit inactive" in boot
    assert "PADataset scientific lane A is not in restore set" in boot
    assert '"active_controller_set_before": active_before' in boot
