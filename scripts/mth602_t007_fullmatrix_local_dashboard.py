#!/usr/bin/env python3
"""Unified zero-provider dashboard for the 10-pair MTH602 t007 backbone wave.

The view intentionally treats two completed pilot pairs, the active PA3-PA8
identical rerun, and seven newly admitted full-matrix pairs as one logical wave.

Observational inputs only:
- local pa_train_one.py process table / process age
- local RUNNER_TEMP scientific-results/backbone directories
- train_progress.json / history.json / summary.json
- train_complete.json / train_error.json
- nvidia-smi
- persistent operator-owned dashboard cache

No gh invocation, GitHub REST/GraphQL polling, curl, or provider API calls.
"""

from __future__ import annotations

import glob
import json
import os
import pwd
import shlex
import signal
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

TITLE = "MTH602 H1 — T007 FULL-MATRIX BACKBONE WAVE"
SUBTITLE = "10 canonical PA pairs | frozen t007 recipe | 60 epochs each | dual GPU"
REFRESH_SEC = 1.0
EXPECTED_EPOCHS = 60

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

CACHE = OPERATOR_HOME / ".cache/workspace-control/experiment-dashboards/mth602-t007-fullmatrix.json"

# pair, lane, run_name, immutable display identity
RUNS = [
    ("PA1-PA2", "G0", "l2o_t007_fullmatrix_PA1_PA2", "comment 7082541725"),
    ("PA1-PA3", "G1", "l2o_t007_fullmatrix_PA1_PA3", "comment 7082542060"),
    ("PA1-PA4", "G0", "l2o_t007_fullmatrix_PA1_PA4", "comment 7082542513"),
    ("PA1-PA8", "G1", "l2o_t007_fullmatrix_PA1_PA8", "comment 7082542827"),
    ("PA2-PA3", "G1", "l2o_hpo_tight60_PA2_PA3_t007", "run 44954728466"),
    ("PA2-PA4", "G0", "l2o_t007_fullmatrix_PA2_PA4", "comment 7082543180"),
    ("PA2-PA8", "G0", "l2o_hpo_v2_PA2_PA8_t007_finalist", "artifact 14719755202"),
    ("PA3-PA4", "G1", "l2o_t007_fullmatrix_PA3_PA4", "comment 7082543540"),
    ("PA3-PA8", "G1", "l2o_hpo_tight60_PA3_PA8_t007", "rerun job 137275754026"),
    ("PA4-PA8", "G0", "l2o_t007_fullmatrix_PA4_PA8", "comment 7082543821"),
]

# Durable terminal seeds let the unified wave start at 2/10 complete even if
# the original runner temp directories have already been cleaned up.
SEED = {
    "l2o_hpo_tight60_PA2_PA3_t007": {
        "status": "SUCCESS",
        "total": 8587.964884996414,
        "best_epoch": 25,
        "val_macro_f1": 0.9935446126501883,
        "val_min_class_f1": 0.99026518966096,
    },
    "l2o_hpo_v2_PA2_PA8_t007_finalist": {
        "status": "SUCCESS",
        "total": 6780.972130537033,
        "best_epoch": 18,
        "val_macro_f1": 0.9876063834565111,
        "val_min_class_f1": 0.9811405985319028,
    },
}

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
GRAY = "\033[90m"


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def fmt_seconds(sec):
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


def metric(x):
    try:
        return f"{float(x):.4f}"
    except Exception:
        return "-"


def terminal_width():
    try:
        return max(104, min(150, os.get_terminal_size().columns))
    except Exception:
        return 124


def progress_bar(frac, width=58):
    if frac is None:
        return "[" + "?" * width + "]"
    frac = max(0.0, min(1.0, float(frac)))
    filled = int(round(frac * width))
    if filled <= 0:
        body = "▸" + "·" * (width - 1)
    elif filled >= width:
        body = "█" * width
    else:
        body = "█" * max(0, filled - 1) + "▸" + "·" * (width - filled)
    return "[" + body + "]"


def ensure_cache_parent():
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


def load_cache():
    data = {}
    if CACHE.exists():
        try:
            data = json.loads(CACHE.read_text())
        except Exception:
            data = {}
    rows = data.setdefault("runs", {})
    for rn, seed in SEED.items():
        rows.setdefault(rn, dict(seed))
    return data


def save_cache(cache):
    ensure_cache_parent()
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


def gpu_rows():
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    rows = []
    for raw in out.strip().splitlines():
        parts = [x.strip() for x in raw.split(",")]
        if len(parts) >= 5:
            rows.append(tuple(parts[:5]))
    return rows


def process_rows():
    found = {}
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid=,etimes=,args="],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return found

    tracked = {rn for _, _, rn, _ in RUNS}
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
            if not cfg:
                continue
            rn = cfg.get("run_name")
            if rn not in tracked:
                continue
            save_root = Path(str(cfg.get("save_root", "")))
            run_dir = save_root / rn if str(save_root) else None
            found[rn] = {
                "pid": pid,
                "elapsed": elapsed,
                "cfg_path": str(cfg_path),
                "run_dir": str(run_dir) if run_dir else None,
            }
        except Exception:
            continue
    return found


def scan_run_dirs(proc):
    tracked = {rn for _, _, rn, _ in RUNS}
    found = {rn: [] for rn in tracked}
    seen = {rn: set() for rn in tracked}

    for rn, p in proc.items():
        if p.get("run_dir"):
            q = Path(p["run_dir"])
            if q not in seen[rn]:
                seen[rn].add(q)
                found[rn].append(q)

    patterns = [
        "/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/scientific-results/backbone/*",
        "/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/scientific-results/backbone/*",
    ]
    for pattern in patterns:
        for item in glob.glob(pattern):
            q = Path(item)
            rn = q.name
            if rn in tracked and q not in seen[rn]:
                seen[rn].add(q)
                found[rn].append(q)
    return found


def local_record(rn, dirs):
    terminal = None
    terminal_mtime = -1.0
    progress = None
    progress_mtime = -1.0
    history = None
    history_mtime = -1.0
    summary = None
    summary_mtime = -1.0
    newest_dir = None
    newest_dir_mtime = -1.0

    for rd in dirs.get(rn, []):
        try:
            mt = rd.stat().st_mtime
            if mt > newest_dir_mtime:
                newest_dir_mtime = mt
                newest_dir = rd
        except Exception:
            pass

        for name, kind in [
            ("train_progress.json", "progress"),
            ("history.json", "history"),
            ("summary.json", "summary"),
        ]:
            p = rd / name
            d = read_json(p)
            if d is None:
                continue
            try:
                mt = p.stat().st_mtime
            except Exception:
                mt = 0.0
            if kind == "progress" and mt >= progress_mtime:
                progress_mtime, progress = mt, d
            elif kind == "history" and mt >= history_mtime:
                history_mtime, history = mt, d
            elif kind == "summary" and mt >= summary_mtime:
                summary_mtime, summary = mt, d

        cp = rd / "train_complete.json"
        complete = read_json(cp)
        if complete:
            try:
                mt = cp.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt >= terminal_mtime:
                terminal_mtime = mt
                terminal = {
                    "status": "SUCCESS",
                    "total": complete.get("elapsed_sec"),
                    "run_dir": str(rd),
                }

        ep = rd / "train_error.json"
        err = read_json(ep)
        if err:
            try:
                mt = ep.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt >= terminal_mtime:
                msg = str(err.get("error", ""))
                terminal_mtime = mt
                terminal = {
                    "status": "INFRA-OOM" if ("out of memory" in msg.lower() or "OutOfMemory" in msg) else "ERROR",
                    "total": err.get("elapsed_sec"),
                    "error": msg,
                    "run_dir": str(rd),
                }

    return newest_dir, terminal, progress, history, summary


def progress_values(progress):
    if not isinstance(progress, dict):
        return None, None, None, None, None
    try:
        epoch = int(progress.get("epoch", 0) or 0)
    except Exception:
        epoch = 0
    try:
        epochs = int(progress.get("epochs", 0) or 0) or EXPECTED_EPOCHS
    except Exception:
        epochs = EXPECTED_EPOCHS
    try:
        step = int(progress.get("step", 0) or 0)
    except Exception:
        step = 0
    try:
        steps = int(progress.get("steps", 0) or 0)
    except Exception:
        steps = 0

    frac = None
    if epoch > 0 and epochs > 0 and steps > 0:
        frac = ((epoch - 1) + step / max(steps, 1)) / epochs
    elif epoch > 0 and epochs > 0:
        frac = (epoch - 1) / epochs
    if frac is not None:
        frac = max(0.0, min(1.0, frac))
    return epoch, epochs, step, steps, frac


def find_metric(progress, history, summary, names):
    for src in (progress, summary):
        if isinstance(src, dict):
            for key in names:
                if src.get(key) is not None:
                    try:
                        return float(src[key])
                    except Exception:
                        pass

    rows = []
    if isinstance(history, list):
        rows = history
    elif isinstance(history, dict):
        for key in ("history", "epochs", "records"):
            if isinstance(history.get(key), list):
                rows = history[key]
                break
        if not rows:
            rows = [history]

    for row in reversed(rows):
        if not isinstance(row, dict):
            continue
        for key in names:
            if row.get(key) is not None:
                try:
                    return float(row[key])
                except Exception:
                    pass
    return None


def color_status(status):
    colors = {
        "SUCCESS": GREEN,
        "RUNNING": YELLOW,
        "ADMITTED": CYAN,
        "INCOMPLETE": MAGENTA,
        "INFRA-OOM": RED,
        "ERROR": RED,
        "HIDDEN": MAGENTA,
    }
    return colors.get(status, GRAY) + f"{status:<10}" + RESET


def handle_sigint(_signum, _frame):
    if os.environ.get("TMUX"):
        try:
            subprocess.run(
                ["tmux", "detach-client"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        except Exception:
            pass
    raise KeyboardInterrupt


def render():
    cache = load_cache()
    sys.stdout.write("\033[?1049h\033[?25l\033[H")
    sys.stdout.flush()

    try:
        while True:
            now = datetime.now().astimezone()
            proc = process_rows()
            dirs = scan_run_dirs(proc)
            rows = []
            counts = {}
            nominal_samples = []

            for pair, lane, rn, identity in RUNS:
                run_dir, terminal, progress, history, summary = local_record(rn, dirs)
                cached = cache["runs"].get(rn, {})

                if terminal:
                    cached.update(terminal)
                    if summary:
                        cached["best_epoch"] = summary.get("best_epoch", cached.get("best_epoch"))
                        cached["val_macro_f1"] = summary.get("best_val_macro_f1", cached.get("val_macro_f1"))
                    cache["runs"][rn] = cached

                active = proc.get(rn)
                epoch, epochs, step, steps, frac = progress_values(progress)

                val_macro = find_metric(
                    progress, history, summary,
                    ("best_val_macro_f1", "val_macro_f1", "macro_f1", "best_metric"),
                )
                val_min = find_metric(
                    progress, history, summary,
                    ("val_min_class_f1", "best_val_min_class_f1", "min_class_f1"),
                )
                if val_macro is None:
                    val_macro = cached.get("val_macro_f1")
                if val_min is None:
                    val_min = cached.get("val_min_class_f1")

                if active:
                    status = "RUNNING"
                    elapsed = active.get("elapsed")
                    total = None
                    if elapsed and frac and frac > 0.01:
                        nominal_samples.append(elapsed / frac)
                elif cached.get("status") in {"SUCCESS", "INFRA-OOM", "ERROR"}:
                    status = cached["status"]
                    elapsed = None
                    total = cached.get("total")
                    if status == "SUCCESS" and total:
                        nominal_samples.append(float(total))
                    if status == "SUCCESS":
                        frac = 1.0
                        if not epoch and cached.get("best_epoch"):
                            epoch = cached.get("best_epoch")
                            epochs = EXPECTED_EPOCHS
                elif progress:
                    status = "INCOMPLETE"
                    elapsed = None
                    total = None
                elif OBSERVER_ELEVATED:
                    status = "ADMITTED"
                    elapsed = None
                    total = None
                else:
                    status = "HIDDEN"
                    elapsed = None
                    total = None

                eta = None
                if status == "RUNNING" and elapsed and frac and frac > 0.01:
                    eta = elapsed * (1.0 - frac) / frac

                counts[status] = counts.get(status, 0) + 1
                rows.append({
                    "pair": pair,
                    "lane": lane,
                    "rn": rn,
                    "identity": identity,
                    "status": status,
                    "epoch": epoch,
                    "epochs": epochs or EXPECTED_EPOCHS,
                    "step": step,
                    "steps": steps,
                    "frac": frac,
                    "elapsed": elapsed,
                    "eta": eta,
                    "total": total,
                    "val_macro": val_macro,
                    "val_min": val_min,
                    "run_dir": str(run_dir) if run_dir else None,
                })

            cache["updated_at_epoch"] = time.time()
            try:
                save_cache(cache)
            except Exception:
                pass

            pair_progress = sum((r["frac"] or 0.0) for r in rows) / len(rows)
            nominal = statistics.median(nominal_samples) if nominal_samples else None

            lane_eta = {}
            for lane in ("G0", "G1"):
                seconds = 0.0
                for r in rows:
                    if r["lane"] != lane or r["status"] == "SUCCESS":
                        continue
                    if r["status"] == "RUNNING" and r["eta"] is not None:
                        seconds += r["eta"]
                    elif nominal is not None:
                        remaining = 1.0 - (r["frac"] or 0.0)
                        seconds += nominal * max(0.0, remaining)
                lane_eta[lane] = seconds if seconds > 0 else None

            wave_eta = None
            lane_values = [x for x in lane_eta.values() if x is not None]
            if lane_values:
                wave_eta = max(lane_values)
            finish = "-"
            if wave_eta is not None:
                finish = (now + timedelta(seconds=wave_eta)).strftime("%I:%M %p %Z").lstrip("0")

            width = terminal_width()
            rule = "─" * min(width, 136)
            source = (
                "HOST ROOT OBSERVER — local process/result/GPU telemetry + persistent cache — provider API calls: 0"
                if OBSERVER_ELEVATED
                else "LIMITED USER VIEW — isolated jobs may be hidden; use sudo observer mode — provider API calls: 0"
            )

            frame = []
            frame.append(BOLD + CYAN + "╔" + "═" * min(width - 2, 134) + "╗" + RESET)
            frame.append(BOLD + f"  {TITLE}" + RESET)
            frame.append(DIM + f"  {SUBTITLE} | refresh {REFRESH_SEC:g}s" + RESET)
            frame.append(BOLD + CYAN + "╚" + "═" * min(width - 2, 134) + "╝" + RESET)
            frame.append(DIM + f"Source: {source}" + RESET)
            frame.append(DIM + f"Local time: {now.strftime('%Y-%m-%d %I:%M:%S %p %Z')}" + RESET)
            frame.append("")

            summary_order = ["SUCCESS", "RUNNING", "ADMITTED", "INCOMPLETE", "INFRA-OOM", "ERROR", "HIDDEN"]
            summary = "   ".join(f"{k} {counts.get(k,0):2d}" for k in summary_order if counts.get(k,0))
            frame.append(BOLD + "WAVE STATE  " + RESET + (summary or "-"))
            frame.append(
                BOLD + "PAIR-WEIGHTED COMPLETION  " + RESET
                + f"{pair_progress*10:5.2f}/10  ({pair_progress*100:6.2f}%)"
            )
            frame.append(GREEN + progress_bar(pair_progress, 68) + RESET)
            frame.append(
                f"{BOLD}EST. WAVE ETA{RESET} "
                + (f"~{fmt_seconds(wave_eta)}" if wave_eta is not None else "-")
                + f"    {BOLD}PROJECTED FINISH{RESET} {finish}"
                + f"    {BOLD}NOMINAL / PAIR{RESET} "
                + (f"~{fmt_seconds(nominal)}" if nominal is not None else "-")
            )
            frame.append(
                DIM
                + "Wave ETA assumes back-to-back t007 backbone service on each lane; provider/OSR queue overhead is intentionally excluded."
                + RESET
            )
            frame.append("")

            gpus = gpu_rows()
            if gpus:
                gpu_bits = []
                for idx, _name, used, total, util in gpus:
                    gpu_bits.append(f"GPU{idx} mem {used}/{total} MiB util {util}%")
                frame.append(BOLD + "GPU  " + RESET + "   ".join(gpu_bits))
            else:
                frame.append(BOLD + "GPU  " + RESET + "nvidia-smi unavailable")

            frame.append("")
            frame.append(
                BOLD
                + f"{'PAIR':<9} {'LANE':<5} {'STATUS':<10} {'EPOCH':>7} {'PROG':>7} "
                  f"{'ELAPSED':>9} {'ETA':>9} {'TOTAL':>9} {'VAL-MAC':>8} {'MIN-F1':>8}  IDENTITY"
                + RESET
            )
            frame.append(rule)

            for r in rows:
                ep = f"{r['epoch']}/{r['epochs']}" if r["epoch"] else f"-/{EXPECTED_EPOCHS}"
                prog = f"{r['frac']*100:5.1f}%" if r["frac"] is not None else "-"
                eta = "~" + fmt_seconds(r["eta"]) if r["eta"] is not None else "-"
                frame.append(
                    f"{r['pair']:<9} {r['lane']:<5} {color_status(r['status'])} "
                    f"{ep:>7} {prog:>7} {fmt_seconds(r['elapsed']):>9} {eta:>9} "
                    f"{fmt_seconds(r['total']):>9} {metric(r['val_macro']):>8} {metric(r['val_min']):>8}  {r['identity']}"
                )

            frame.append(rule)
            frame.append(
                DIM
                + "ADMITTED = durable immutable request exists but no matching local training process/result is visible yet; this does not claim provider queue position."
                + RESET
            )
            frame.append(
                DIM
                + "Per-run ETA = local process age extrapolated from local epoch/batch progress. Completed rows are retained from durable seed/cache."
                + RESET
            )
            if not OBSERVER_ELEVATED:
                frame.append(RED + "Use the reviewed sudo observer for exact isolated-runner visibility." + RESET)
            frame.append(BOLD + "Ctrl+C" + RESET + " detach + keep dashboard alive  |  "
                         + BOLD + "tmux attach -t mth602-t007-wave" + RESET + " return")

            sys.stdout.write("\033[H" + "\n".join(frame) + "\033[J")
            sys.stdout.flush()
            time.sleep(REFRESH_SEC)
    finally:
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    try:
        render()
    except KeyboardInterrupt:
        print()
