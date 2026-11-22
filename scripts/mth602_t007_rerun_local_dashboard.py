#!/usr/bin/env python3
"""Zero-GitHub-API host-local dashboard for the PA3-PA8/t007 tight60 rerun.

Observational inputs only:
- local pa_train_one.py process table / process age
- local RUNNER_TEMP scientific-results/backbone tree
- train_progress.json / history.json / train_complete.json / train_error.json
- nvidia-smi
- persistent operator-owned terminal cache

The GitHub workflow/job IDs below are immutable display metadata. This program
does not invoke gh, GitHub REST, GitHub GraphQL, curl, or any provider API.
"""

from __future__ import annotations

import glob
import json
import os
import pwd
import shlex
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

TITLE = "MTH602 H1 — PA3-PA8 / t007 TIGHT60 IDENTICAL RERUN"
RUN_NAME = "l2o_hpo_tight60_PA3_PA8_t007"
WORKFLOW_RUN_ID = 44954748830
ORIGINAL_JOB_ID = 137000252399
RERUN_JOB_ID = 137275754026
CANDIDATE_SHA = "da521eaee997c56012290c9c261ee1831432ebbc"
EXPECTED_EPOCHS = 60
LANE = "GPU1 / lambda-scientific-2"
REFRESH_SEC = 1.0

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

CACHE = OPERATOR_HOME / ".cache/workspace-control/experiment-dashboards/mth602-t007-rerun.json"

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


def terminal_width():
    try:
        return max(92, min(132, os.get_terminal_size().columns))
    except Exception:
        return 112


def progress_bar(frac, width=52):
    if frac is None:
        return "[" + "?" * width + "]"
    frac = max(0.0, min(1.0, float(frac)))
    filled = int(round(frac * width))
    if filled <= 0:
        body = ">" + "·" * (width - 1)
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
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text())
        except Exception:
            pass
    return {}


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
        if len(parts) < 5:
            continue
        idx, name, used, total, util = parts[:5]
        rows.append((idx, name, used, total, util))
    return rows


def process_info():
    """Return matching pa_train_one.py process evidence, if visible."""
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
            if not cfg or cfg.get("run_name") != RUN_NAME:
                continue
            save_root = Path(str(cfg.get("save_root", "")))
            run_dir = save_root / RUN_NAME if str(save_root) else None
            return {
                "pid": pid,
                "elapsed": elapsed,
                "cfg": cfg,
                "cfg_path": str(cfg_path),
                "run_dir": str(run_dir) if run_dir else None,
            }
        except Exception:
            continue
    return None


def candidate_dirs(proc):
    seen = set()
    dirs = []

    if proc and proc.get("run_dir"):
        q = Path(proc["run_dir"])
        if q not in seen:
            seen.add(q)
            dirs.append(q)

    patterns = [
        f"/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/scientific-results/backbone/{RUN_NAME}",
        f"/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/scientific-results/backbone/{RUN_NAME}",
    ]
    for pattern in patterns:
        for item in glob.glob(pattern):
            q = Path(item)
            if q not in seen:
                seen.add(q)
                dirs.append(q)
    return dirs


def newest_local_records(proc):
    best_progress = None
    best_progress_mtime = -1.0
    best_history = None
    best_history_mtime = -1.0
    best_terminal = None
    best_terminal_mtime = -1.0
    newest_dir = None
    newest_dir_mtime = -1.0

    for rd in candidate_dirs(proc):
        try:
            rd_mtime = rd.stat().st_mtime
            if rd_mtime > newest_dir_mtime:
                newest_dir_mtime = rd_mtime
                newest_dir = rd
        except Exception:
            pass

        pp = rd / "train_progress.json"
        p = read_json(pp)
        if p:
            try:
                mt = pp.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt >= best_progress_mtime:
                best_progress_mtime = mt
                best_progress = p

        hp = rd / "history.json"
        h = read_json(hp)
        if h is not None:
            try:
                mt = hp.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt >= best_history_mtime:
                best_history_mtime = mt
                best_history = h

        cp = rd / "train_complete.json"
        complete = read_json(cp)
        if complete:
            try:
                mt = cp.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt >= best_terminal_mtime:
                best_terminal_mtime = mt
                best_terminal = {
                    "status": "SUCCESS",
                    "elapsed_sec": complete.get("elapsed_sec"),
                    "path": str(cp),
                }

        ep = rd / "train_error.json"
        err = read_json(ep)
        if err:
            try:
                mt = ep.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt >= best_terminal_mtime:
                msg = str(err.get("error", ""))
                status = "INFRA-OOM" if ("out of memory" in msg.lower() or "OutOfMemory" in msg) else "ERROR"
                best_terminal_mtime = mt
                best_terminal = {
                    "status": status,
                    "elapsed_sec": err.get("elapsed_sec"),
                    "error": msg,
                    "path": str(ep),
                }

    return newest_dir, best_progress, best_history, best_terminal


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
        frac = ((epoch - 1) + step / max(1, steps)) / epochs
        frac = max(0.0, min(1.0, frac))
    elif epoch > 0 and epochs > 0:
        frac = max(0.0, min(1.0, (epoch - 1) / epochs))

    return epoch, epochs, step, steps, frac


def find_metric(history, progress, names):
    for src in (progress,):
        if isinstance(src, dict):
            for key in names:
                if key in src and src[key] is not None:
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
            if key in row and row[key] is not None:
                try:
                    return float(row[key])
                except Exception:
                    pass
    return None


def status_color(status):
    mapping = {
        "RUNNING": YELLOW,
        "SUCCESS": GREEN,
        "WAITING": CYAN,
        "HIDDEN": MAGENTA,
        "INCOMPLETE": MAGENTA,
        "INFRA-OOM": RED,
        "ERROR": RED,
    }
    return mapping.get(status, GRAY) + status + RESET


def render():
    cache = load_cache()
    sys.stdout.write("\033[?1049h\033[?25l\033[H")
    sys.stdout.flush()

    try:
        while True:
            now = datetime.now().astimezone()
            proc = process_info()
            run_dir, progress, history, terminal = newest_local_records(proc)

            if terminal:
                cache["terminal"] = terminal
                cache["terminal_seen_at"] = now.isoformat()
                try:
                    save_cache(cache)
                except Exception:
                    pass
            elif cache.get("terminal"):
                terminal = cache["terminal"]

            epoch, epochs, step, steps, frac = progress_values(progress)

            if terminal:
                status = terminal.get("status", "SUCCESS")
            elif proc:
                status = "RUNNING"
            elif progress:
                status = "INCOMPLETE"
            elif OBSERVER_ELEVATED:
                status = "WAITING"
            else:
                status = "HIDDEN"

            elapsed = proc.get("elapsed") if proc else None
            if elapsed is None and terminal:
                elapsed = terminal.get("elapsed_sec")

            eta = None
            finish = "-"
            if status == "RUNNING" and elapsed and frac and frac > 0.005:
                eta = elapsed * (1.0 - frac) / frac
                finish_dt = now + timedelta(seconds=eta)
                finish = finish_dt.strftime("%I:%M:%S %p %Z").lstrip("0")

            val_macro = find_metric(
                history,
                progress,
                ("val_macro_f1", "best_val_macro_f1", "macro_f1", "best_metric"),
            )
            val_min = find_metric(
                history,
                progress,
                ("val_min_class_f1", "min_class_f1", "best_val_min_class_f1"),
            )

            width = terminal_width()
            rule = "─" * min(width, 118)
            frac_text = f"{frac * 100:6.2f}%" if frac is not None else "   -   "
            ep_text = f"{epoch}/{epochs}" if epoch and epochs else f"-/{EXPECTED_EPOCHS}"
            batch_text = f"{step}/{steps}" if step and steps else "-"
            source = (
                "HOST ROOT OBSERVER — local process/result telemetry only — GitHub API calls: 0"
                if OBSERVER_ELEVATED
                else "LIMITED USER VIEW — use sudo for isolated runner visibility — GitHub API calls: 0"
            )

            frame = []
            frame.append(BOLD + CYAN + "╔" + "═" * min(width - 2, 116) + "╗" + RESET)
            frame.append(BOLD + f"  {TITLE}" + RESET)
            frame.append(DIM + f"  exact candidate {CANDIDATE_SHA[:12]}… | {LANE} | refresh {REFRESH_SEC:g}s" + RESET)
            frame.append(BOLD + CYAN + "╚" + "═" * min(width - 2, 116) + "╝" + RESET)
            frame.append(DIM + f"Source: {source}" + RESET)
            frame.append(DIM + f"Local time: {now.strftime('%Y-%m-%d %I:%M:%S %p %Z')}" + RESET)
            frame.append("")

            frame.append(
                f"{BOLD}STATUS{RESET}  {status_color(status):<20}   "
                f"{BOLD}EPOCH{RESET} {ep_text:<8}   "
                f"{BOLD}BATCH{RESET} {batch_text:<13}   "
                f"{BOLD}OVERALL{RESET} {frac_text}"
            )
            frame.append(
                (GREEN if status == "SUCCESS" else YELLOW if status == "RUNNING" else CYAN)
                + progress_bar(frac)
                + RESET
            )
            frame.append("")

            frame.append(
                f"{BOLD}ELAPSED{RESET} {fmt_seconds(elapsed):>10}    "
                f"{BOLD}ETA LEFT{RESET} {('~' + fmt_seconds(eta)) if eta is not None else '-':>10}    "
                f"{BOLD}PROJECTED FINISH{RESET} {finish}"
            )
            frame.append(
                f"{BOLD}VAL macro-F1{RESET} "
                + (f"{val_macro:.6f}" if val_macro is not None else "-")
                + "    "
                + f"{BOLD}VAL min-class F1{RESET} "
                + (f"{val_min:.6f}" if val_min is not None else "-")
            )

            frame.append("")
            frame.append(rule)
            frame.append(BOLD + "GPU TELEMETRY" + RESET)
            gpus = gpu_rows()
            if not gpus:
                frame.append("  nvidia-smi unavailable")
            else:
                for idx, name, used, total, util in gpus:
                    marker = " ◀ expected lane" if idx == "1" else ""
                    frame.append(
                        f"  GPU{idx}  util {util:>3}%   mem {used:>6}/{total:<6} MiB   {name}{marker}"
                    )

            frame.append(rule)
            frame.append(BOLD + "IMMUTABLE IDENTITY" + RESET)
            frame.append(
                f"  workflow run {WORKFLOW_RUN_ID} | original failed job {ORIGINAL_JOB_ID} | rerun job {RERUN_JOB_ID}"
            )
            frame.append(f"  run_name: {RUN_NAME}")
            frame.append(f"  local result dir: {str(run_dir) if run_dir else '-'}")
            frame.append("")
            if not OBSERVER_ELEVATED:
                frame.append(
                    RED
                    + "Runner isolation may hide the process/result tree. Restart as: sudo -E python3 <dashboard>"
                    + RESET
                )
            if status == "INCOMPLETE":
                frame.append(
                    MAGENTA
                    + "Progress exists but no matching process is visible. Do not infer provider state from this alone."
                    + RESET
                )
            frame.append(DIM + "ETA = local process age × remaining/observed overall training fraction; it will move as epoch speed changes." + RESET)
            frame.append(BOLD + "Ctrl+B then D" + RESET + " detach tmux  |  " + BOLD + "Ctrl+C" + RESET + " stop dashboard")

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
