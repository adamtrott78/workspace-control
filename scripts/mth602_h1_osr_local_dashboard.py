#!/usr/bin/env python3
"""Host-local MTH602 H1 frozen-pair directional OSR dashboard.

No GitHub API calls. Telemetry sources:
- local ci-padataset-2 workflow/evaluator processes
- exact-head runner temp/result directories
- l2o pre-resolve / rehydrate / result files
- osr_summary.csv
- persistent local dashboard cache
- nvidia-smi

Only the four corrected PR #38 admissions at the exact repaired head are tracked.
Stale pre-repair runs are intentionally excluded.
"""

from __future__ import annotations

import csv
import glob
import json
import os
import pwd
import shlex
import subprocess
import sys
import time
from pathlib import Path

TITLE = "MTH602 H1 — FROZEN-PAIR DQNGUARD OSR OVERLAP DASHBOARD"
REFRESH_SEC = 1.0
EXPECTED_SHA = "d7ba2c754d7d281651f4119ba79544ec6f6e89f6"

OBSERVER_ELEVATED = os.geteuid() == 0
if OBSERVER_ELEVATED and os.environ.get("SUDO_USER"):
    _pw = pwd.getpwnam(os.environ["SUDO_USER"])
    OPERATOR_HOME = Path(_pw.pw_dir)
    OPERATOR_UID = _pw.pw_uid
    OPERATOR_GID = _pw.pw_gid
else:
    OPERATOR_HOME = Path.home()
    OPERATOR_UID = os.getuid()
    OPERATOR_GID = os.getgid()

CACHE = OPERATOR_HOME / ".cache/workspace-control/experiment-dashboards/mth602-h1-osr-overlap.json"

# direction label, target, surrogate, lane, corrected workflow run ID, repaired baseline Unknown-F1
RUNS = [
    ("PA2<-PA8", "PA2", "PA8", 1, 44939698874, 0.801033),
    ("PA8<-PA2", "PA8", "PA2", 1, 44939701110, 0.757011),
    ("PA3<-PA8", "PA3", "PA8", 1, 44939702954, 0.054209),
    ("PA8<-PA3", "PA8", "PA3", 1, 44939705618, 0.424513),
]
RUN_IDS = {str(x[4]) for x in RUNS}
FINALIST_RUN_NAME = "l2o_hpo_v2_PA2_PA3_t005_finalist"
FINALIST_RUN_ID = 44924828921

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
GRAY = "\033[90m"


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None

def finalist_process():
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid=,etimes=,args="],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None
    for raw in out.splitlines():
        if "pa_train_one.py" not in raw or "--cfg" not in raw:
            continue
        parts = raw.strip().split(None, 2)
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
            elapsed = int(parts[1])
            argv = shlex.split(parts[2])
            pos = argv.index("--cfg")
            cfg_path = Path(argv[pos + 1])
            cfg = read_json(cfg_path)
            if not cfg or cfg.get("run_name") != FINALIST_RUN_NAME:
                continue
            save_root = Path(cfg.get("save_root", ""))
            run_dir = save_root / FINALIST_RUN_NAME if str(save_root) else None
            return {"pid": pid, "elapsed": elapsed, "run_dir": run_dir}
        except Exception:
            continue
    return None


def finalist_candidate_dirs(proc):
    seen = set()
    out = []
    if proc and proc.get("run_dir"):
        q = Path(proc["run_dir"])
        if q not in seen:
            seen.add(q)
            out.append(q)
    for pattern in [
        f"/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/scientific-results/backbone/{FINALIST_RUN_NAME}",
        f"/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/scientific-results/backbone/{FINALIST_RUN_NAME}",
    ]:
        for item in glob.glob(pattern):
            q = Path(item)
            if q not in seen:
                seen.add(q)
                out.append(q)
    return out


def finalist_progress(proc):
    best = None
    best_mtime = -1.0
    terminal = None
    terminal_mtime = -1.0
    for rd in finalist_candidate_dirs(proc):
        p = rd / "train_progress.json"
        d = read_json(p)
        if d:
            try:
                mt = p.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt >= best_mtime:
                best = d
                best_mtime = mt
        c = rd / "train_complete.json"
        d = read_json(c)
        if d:
            try:
                mt = c.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt >= terminal_mtime:
                terminal = {"status": "SUCCESS", "total": d.get("elapsed_sec")}
                terminal_mtime = mt
        e = rd / "train_error.json"
        d = read_json(e)
        if d:
            try:
                mt = e.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt >= terminal_mtime:
                terminal = {"status": "ERROR", "total": d.get("elapsed_sec")}
                terminal_mtime = mt
    return terminal, best


def finalist_fields(progress, elapsed):
    if not progress:
        return "-", None, None
    try:
        epoch = int(progress.get("epoch", 0) or 0)
        epochs = int(progress.get("epochs", 0) or 0)
        step = int(progress.get("step", 0) or 0)
        steps = int(progress.get("steps", 0) or 0)
        ep = f"{epoch}/{epochs}" if epoch and epochs else "-"
        overall = None
        if epoch > 0 and epochs > 0 and steps > 0:
            overall = ((epoch - 1) + step / max(steps, 1)) / epochs
            overall = max(0.0, min(1.0, overall))
        pct = overall * 100.0 if overall is not None else float(progress.get("pct", 0.0) or 0.0)
        eta = None
        if elapsed and overall and overall > 0.01:
            eta = elapsed * (1.0 - overall) / overall
        return ep, pct, eta
    except Exception:
        return "-", None, None



def fmt(sec):
    if sec is None:
        return "-"
    try:
        sec = max(0, int(float(sec)))
    except Exception:
        return "-"
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def load_cache():
    if not CACHE.exists():
        return {"runs": {}}
    try:
        d = json.loads(CACHE.read_text())
        d.setdefault("runs", {})
        return d
    except Exception:
        return {"runs": {}}


def save_cache(cache):
    chain = [
        OPERATOR_HOME / ".cache",
        OPERATOR_HOME / ".cache/workspace-control",
        OPERATOR_HOME / ".cache/workspace-control/experiment-dashboards",
    ]
    for d in chain:
        d.mkdir(exist_ok=True)
        if OBSERVER_ELEVATED:
            try:
                os.chown(d, OPERATOR_UID, OPERATOR_GID)
            except OSError:
                pass
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")
    if OBSERVER_ELEVATED:
        try:
            os.chown(tmp, OPERATOR_UID, OPERATOR_GID)
        except OSError:
            pass
    tmp.replace(CACHE)
    if OBSERVER_ELEVATED:
        try:
            os.chown(CACHE, OPERATOR_UID, OPERATOR_GID)
        except OSError:
            pass


def gpu_line():
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        vals = []
        for line in out.strip().splitlines():
            idx, used, total, util = [x.strip() for x in line.split(",")]
            vals.append(f"GPU{idx} mem {used}/{total} MiB util {util}%")
        return "  ".join(vals)
    except Exception:
        return "GPU telemetry unavailable"


def proc_snapshot():
    """Return active corrected run IDs and active directional evaluator process ages."""
    active_runs = {}
    evals = {}
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid=,etimes=,user=,args="],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return active_runs, evals

    for raw in out.splitlines():
        parts = raw.strip().split(None, 3)
        if len(parts) < 4:
            continue
        try:
            pid = int(parts[0])
            elapsed = int(parts[1])
            user = parts[2]
            args = parts[3]
        except Exception:
            continue

        # Exact local workflow binding via the process environment. Root can
        # observe isolated ci-padataset-2 descendants without weakening ProtectProc.
        if OBSERVER_ELEVATED and user == "ci-padataset-2":
            try:
                env_raw = Path(f"/proc/{pid}/environ").read_bytes()
                env = {}
                for item in env_raw.split(b"\0"):
                    if b"=" in item:
                        k, v = item.split(b"=", 1)
                        env[k.decode(errors="ignore")] = v.decode(errors="ignore")
                rid = env.get("GITHUB_RUN_ID")
                if rid in RUN_IDS:
                    cur = active_runs.get(rid)
                    if cur is None or elapsed > cur["elapsed"]:
                        active_runs[rid] = {
                            "elapsed": elapsed,
                            "runner_temp": env.get("RUNNER_TEMP"),
                        }
            except Exception:
                pass

        if "pa_eval_dqn_guard_surrogate_open.py" not in args:
            continue
        try:
            argv = shlex.split(args)
            ti = argv.index("--target-open-pa")
            si = argv.index("--surrogate-open-pa")
            target = argv[ti + 1]
            surrogate = argv[si + 1]
            evals[(target, surrogate)] = {"elapsed": elapsed, "pid": pid}
        except Exception:
            continue

    return active_runs, evals


def checkout_sha(job_root: Path):
    head = job_root / "runner/_work/PADataset/PADataset/.git/HEAD"
    try:
        value = head.read_text().strip()
        if value.startswith("ref: "):
            ref = value[5:]
            p = head.parent / ref
            if p.exists():
                return p.read_text().strip()
            packed = head.parent / "packed-refs"
            if packed.exists():
                for line in packed.read_text().splitlines():
                    if line and not line.startswith("#") and " " in line:
                        sha, name = line.split(" ", 1)
                        if name == ref:
                            return sha
        return value
    except Exception:
        return None


def direction_from_pre_resolved(path: Path):
    d = read_json(path)
    if not d:
        return None
    target = d.get("evaluation_target")
    surrogate = d.get("evaluation_surrogate")
    if target and surrogate:
        return str(target), str(surrogate)
    return None


def exact_head_temp_dirs():
    """Map (target,surrogate) to newest exact-head RUNNER_TEMP directory."""
    found = {}
    patterns = [
        "/srv/workspace-ci/padataset/jobs/*",
    ]
    for pattern in patterns:
        for raw in glob.glob(pattern):
            job_root = Path(raw)
            if checkout_sha(job_root) != EXPECTED_SHA:
                continue
            temp = job_root / "runner/_work/_temp"
            pre = temp / "l2o-pre-resolved.json"
            direction = direction_from_pre_resolved(pre)
            if not direction:
                continue
            try:
                mtime = max(
                    [p.stat().st_mtime for p in temp.glob("l2o-*") if p.exists()] +
                    [pre.stat().st_mtime]
                )
            except Exception:
                mtime = 0.0
            prev = found.get(direction)
            if prev is None or mtime >= prev["mtime"]:
                found[direction] = {"temp": temp, "mtime": mtime}
    return found


def read_metrics(eval_dir: Path):
    csv_path = eval_dir / "osr_summary.csv"
    if not csv_path.is_file():
        return {}
    try:
        with csv_path.open(newline="") as f:
            row = next(csv.DictReader(f))
        def num(k):
            v = row.get(k)
            return None if v in (None, "") else float(v)
        return {
            "unknown_f1": num("unknown_f1"),
            "known_reject_rate": num("known_reject_rate"),
            "elapsed_sec": num("elapsed_sec"),
        }
    except Exception:
        return {}


def local_record(target, surrogate, active_runs, evals, exact_dirs, run_id):
    direction = (target, surrogate)
    active = active_runs.get(str(run_id))
    evaluator = evals.get(direction)
    entry = exact_dirs.get(direction)
    temp = Path(entry["temp"]) if entry else None

    stage = "-"
    metrics = {}
    terminal = False

    if temp:
        result_root = temp / "scientific-results"
        eval_dir = result_root / "l2o_eval"
        metrics = read_metrics(eval_dir)
        if (result_root / "scientific-receipt.json").is_file() and (eval_dir / "result_record.json").is_file():
            stage = "DONE"
            terminal = True
        elif (eval_dir / "result_record.json").is_file():
            stage = "RECORD"
        elif (eval_dir / "osr_summary.csv").is_file():
            stage = "FINALIZE"
        elif evaluator:
            stage = "EVALUATE"
        elif (temp / "l2o-resolved.json").is_file():
            stage = "EVAL-READY"
        elif (temp / "l2o-rehydrate.json").is_file():
            stage = "REHYDRATE"
        elif (temp / "l2o-backbone-artifact.zip").is_file():
            stage = "REHYDRATE"
        elif (temp / "l2o-artifact-metadata.json").is_file():
            stage = "FETCH"
        elif (temp / "l2o-pre-resolved.json").is_file():
            stage = "VALIDATE"

    if terminal:
        status = "SUCCESS"
        elapsed = None
    elif active or evaluator:
        status = "RUNNING"
        if evaluator:
            elapsed = evaluator["elapsed"]
        else:
            elapsed = active.get("elapsed") if active else None
        if stage == "-":
            stage = "SETUP"
    elif entry:
        status = "INCOMPLETE"
        elapsed = None
    else:
        status = "WAITING" if OBSERVER_ELEVATED else "HIDDEN"
        elapsed = None

    return status, stage, elapsed, metrics


def color_status(status):
    if status == "SUCCESS":
        return GREEN + f"{status:<10}" + RESET
    if status == "RUNNING":
        return YELLOW + f"{status:<10}" + RESET
    if status == "WAITING":
        return CYAN + f"{status:<10}" + RESET
    if status == "INCOMPLETE":
        return MAGENTA + f"{status:<10}" + RESET
    if status == "HIDDEN":
        return MAGENTA + f"{status:<10}" + RESET
    if status == "ERROR":
        return RED + f"{status:<10}" + RESET
    return GRAY + f"{status:<10}" + RESET


def metric(v, digits=4):
    if v is None:
        return "-"
    return f"{float(v):.{digits}f}"


def render():
    cache = load_cache()
    sys.stdout.write("\033[?1049h\033[?25l\033[H")
    sys.stdout.flush()

    try:
        while True:
            active_runs, evals = proc_snapshot()
            exact_dirs = exact_head_temp_dirs() if OBSERVER_ELEVATED else {}
            finalist_proc = finalist_process()
            finalist_terminal, finalist_prog = finalist_progress(finalist_proc)
            finalist_cache = cache["runs"].get(str(FINALIST_RUN_ID), {})
            if finalist_terminal:
                finalist_cache.update(finalist_terminal)
                cache["runs"][str(FINALIST_RUN_ID)] = finalist_cache
            if finalist_proc:
                finalist_status = "RUNNING"
                finalist_elapsed = finalist_proc.get("elapsed")
                finalist_total = None
            elif finalist_cache.get("status"):
                finalist_status = finalist_cache.get("status")
                finalist_elapsed = None
                finalist_total = finalist_cache.get("total")
            else:
                finalist_status = "WAITING" if OBSERVER_ELEVATED else "HIDDEN"
                finalist_elapsed = None
                finalist_total = None
            finalist_epoch, finalist_pct, finalist_eta = finalist_fields(finalist_prog, finalist_elapsed)

            counts = {}
            rows = []

            for label, target, surrogate, lane, rid, baseline in RUNS:
                status, stage, elapsed, metrics = local_record(
                    target, surrogate, active_runs, evals, exact_dirs, rid
                )
                key = str(rid)
                cached = cache["runs"].get(key, {})

                if status == "SUCCESS":
                    cached = {
                        "status": "SUCCESS",
                        "stage": "DONE",
                        "metrics": metrics,
                    }
                    cache["runs"][key] = cached
                elif cached.get("status") == "SUCCESS":
                    status = "SUCCESS"
                    stage = "DONE"
                    elapsed = None
                    metrics = cached.get("metrics", {})

                unknown_f1 = metrics.get("unknown_f1")
                known_reject = metrics.get("known_reject_rate")
                total = metrics.get("elapsed_sec")
                delta = None if unknown_f1 is None else unknown_f1 - baseline

                counts[status] = counts.get(status, 0) + 1
                rows.append(
                    (label, lane, status, stage, elapsed, total, unknown_f1, delta, known_reject, rid)
                )

            cache["updated_at_epoch"] = time.time()
            try:
                save_cache(cache)
            except Exception:
                pass

            frame = []
            frame.append(BOLD + TITLE + RESET)
            frame.append(
                f"{len(RUNS)} immutable directional evaluations | standard DQNGuard | target-open diagnostic only | "
                f"refresh {REFRESH_SEC:g}s | {time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
            )
            frame.append(
                DIM
                + (
                    "Source: HOST ROOT OBSERVER — exact-head runner/process/result telemetry + persistent local cache; GitHub API calls: 0"
                    if OBSERVER_ELEVATED
                    else "Source: LIMITED USER VIEW — rerun with sudo for exact isolated-runner state; GitHub API calls: 0"
                )
                + RESET
            )
            frame.append(DIM + f"Candidate: PR #38 @ {EXPECTED_SHA}" + RESET)
            if not OBSERVER_ELEVATED:
                frame.append(
                    RED
                    + "WARNING: isolated runner state may be hidden. Use sudo -E python3 <dashboard>."
                    + RESET
                )
            frame.append(gpu_line())
            frame.append("")
            frame.append(BOLD + "GPU0 FINALIST TRAINING" + RESET)
            frame.append(
                BOLD
                + f"{'EXPERIMENT':<19} {'GPU':<4} {'STATUS':<10} {'EPOCH':>7} {'PROG':>7} "
                  f"{'ELAPSED':>10} {'ETA LEFT':>10} {'TOTAL':>10} {'RUN ID':>12}"
                + RESET
            )
            frame.append("-" * 105)
            fpct = f"{finalist_pct:5.1f}%" if finalist_pct is not None else "-"
            frame.append(
                f"{'PA2-PA3 t005':<19} G0  {color_status(finalist_status)} "
                f"{finalist_epoch:>7} {fpct:>7} {fmt(finalist_elapsed):>10} "
                f"{('~' + fmt(finalist_eta)) if finalist_eta is not None else '-':>10} "
                f"{fmt(finalist_total):>10} {FINALIST_RUN_ID:>12}"
            )
            frame.append("")
            frame.append(BOLD + "GPU1 FROZEN-PAIR DIRECTIONAL OSR" + RESET)
            frame.append(
                BOLD
                + f"{'DIRECTION':<12} {'GPU':<4} {'STATUS':<10} {'STAGE':<10} "
                  f"{'ELAPSED':>9} {'TOTAL':>9} {'UNK-F1':>8} {'DELTA':>8} {'K-REJ':>8} {'RUN ID':>12}"
                + RESET
            )
            frame.append("-" * 103)

            for label, lane, status, stage, elapsed, total, uf1, delta, krej, rid in rows:
                delta_s = "-" if delta is None else f"{delta:+.4f}"
                frame.append(
                    f"{label:<12} G{lane:<3} {color_status(status)} {stage:<10} "
                    f"{fmt(elapsed):>9} {fmt(total):>9} {metric(uf1):>8} "
                    f"{delta_s:>8} {metric(krej):>8} {rid:>12}"
                )

            frame.append("-" * 103)
            order = ["SUCCESS", "RUNNING", "WAITING", "INCOMPLETE", "HIDDEN", "ERROR"]
            frame.append(
                "   ".join(f"{k} {counts.get(k, 0):2d}" for k in order if counts.get(k, 0))
                or "No states observed"
            )
            frame.append("")
            frame.append(DIM + "UNK-F1 = final target-open Unknown-F1. DELTA = change vs repaired Track-A directional baseline." + RESET)
            frame.append(DIM + "K-REJ = final known reject rate. Target-open metrics are diagnostic only and cannot feed back into HPO." + RESET)
            frame.append(DIM + "GPU0 finalist progress/ETA uses host-local train_progress.json exactly like the original finalist dashboard." + RESET)
            frame.append(DIM + "OSR RUNNING elapsed = host-local process/workflow age; TOTAL = evaluator elapsed_sec from osr_summary.csv." + RESET)
            frame.append(DIM + "WAITING means admitted but not visible on this host; it does not claim provider queue state." + RESET)
            frame.append("Ctrl+B then D = detach tmux | Ctrl+C = stop dashboard")

            sys.stdout.write("\033[H" + "\n".join(frame) + "\033[J")
            sys.stdout.flush()
            time.sleep(REFRESH_SEC)
    finally:
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()


if __name__ == "__main__":
    try:
        render()
    except KeyboardInterrupt:
        print()
