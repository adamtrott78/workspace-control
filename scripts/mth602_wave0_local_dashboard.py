#!/usr/bin/env python3
"""Host-local MTH602 H1 wave0 dashboard.

No GitHub API calls. Telemetry sources:
- local pa_train_one.py processes
- RUNNER_TEMP scientific-results/backbone run directories
- train_progress.json
- train_complete.json
- train_error.json
- persistent local dashboard cache

The immutable admission/run-ID mapping is retained only as identity metadata.
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
from pathlib import Path

TITLE = "MTH602 H1 WEAK-BACKBONE HPO — WAVE 0 LOCAL DASHBOARD"
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

CACHE = OPERATOR_HOME / ".cache/workspace-control/experiment-dashboards/mth602-h1-wave0.json"

# Immutable admission mapping. lane is the experiment lane, not nvidia-smi index.
RUNS = [
    ("PA2-PA3", "t000", 0, 44343583046),
    ("PA2-PA8", "t000", 0, 44343586571),
    ("PA3-PA8", "t000", 0, 44343593644),
    ("PA2-PA3", "t001", 1, 44343604175),
    ("PA2-PA8", "t001", 1, 44343612614),
    ("PA3-PA8", "t001", 1, 44343618795),
    ("PA2-PA3", "t002", 0, 44343625925),
    ("PA2-PA8", "t002", 0, 44343634712),
    ("PA3-PA8", "t002", 0, 44343640671),
    ("PA2-PA3", "t003", 1, 44343647186),
    ("PA2-PA8", "t003", 1, 44343655822),
    ("PA3-PA8", "t003", 1, 44343668555),
    ("PA2-PA3", "t004", 0, 44343691752),
    ("PA2-PA8", "t004", 0, 44343698092),
    ("PA3-PA8", "t004", 0, 44343707552),
    ("PA2-PA3", "t005", 1, 44343716800),
    ("PA2-PA8", "t005", 1, 44343721573),
    ("PA3-PA8", "t005", 1, 44343731277),
    ("PA2-PA3", "t006", 0, 44343738180),
    ("PA2-PA8", "t006", 0, 44343747081),
    ("PA3-PA8", "t006", 0, 44343756497),
    ("PA2-PA3", "t007", 1, 44343766238),
    ("PA2-PA8", "t007", 1, 44343773182),
    ("PA3-PA8", "t007", 1, 44343778619),
]

# Exact terminal evidence already observed before switching away from GitHub.
# Successful totals are pa_train_one.py elapsed_sec (local training duration).
SEED = {
    "l2o_hpo_v2_PA2_PA3_t000_screen": {"status": "INFRA-OOM"},
    "l2o_hpo_v2_PA2_PA8_t000_screen": {"status": "INFRA-OOM"},
    "l2o_hpo_v2_PA3_PA8_t000_screen": {"status": "INFRA-OOM"},
    "l2o_hpo_v2_PA2_PA3_t001_screen": {"status": "SUCCESS", "total": 2047.9},
    "l2o_hpo_v2_PA2_PA8_t001_screen": {"status": "SUCCESS", "total": 2055.8},
    "l2o_hpo_v2_PA3_PA8_t001_screen": {"status": "SUCCESS", "total": 2056.4},
    "l2o_hpo_v2_PA2_PA3_t002_screen": {"status": "INFRA-OOM"},
    "l2o_hpo_v2_PA2_PA8_t002_screen": {"status": "INFRA-OOM"},
    "l2o_hpo_v2_PA3_PA8_t002_screen": {"status": "INFRA-OOM"},
    "l2o_hpo_v2_PA2_PA3_t003_screen": {"status": "SUCCESS", "total": 2076.7},
    "l2o_hpo_v2_PA2_PA3_t004_screen": {"status": "SUCCESS", "total": 2019.8},
    "l2o_hpo_v2_PA2_PA8_t004_screen": {"status": "SUCCESS", "total": 2021.4},
    "l2o_hpo_v2_PA2_PA3_t006_screen": {"status": "SUCCESS", "total": 2010.2},
    "l2o_hpo_v2_PA2_PA8_t006_screen": {"status": "SUCCESS", "total": 2021.9},
}

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
GRAY = "\033[90m"


def run_name(pair: str, trial: str) -> str:
    return f"l2o_hpo_v2_{pair.replace('-', '_')}_{trial}_screen"


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


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
    d = {}
    if CACHE.exists():
        try:
            d = json.loads(CACHE.read_text())
        except Exception:
            d = {}
    rows = d.setdefault("runs", {})
    for rn, seed in SEED.items():
        rows.setdefault(rn, dict(seed))
    return d


def save_cache(cache):
    # When invoked with sudo, keep the persistent cache owned by the operator,
    # not root, so later unprivileged inspection remains possible.
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


def process_rows():
    """Map run_name -> process elapsed/config/run_dir where readable."""
    found = {}
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid=,etimes=,args="],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return found

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
            if not rn:
                continue
            save_root = Path(cfg.get("save_root", ""))
            rd = save_root / rn if str(save_root) else None
            found[rn] = {
                "pid": pid,
                "elapsed": elapsed,
                "cfg_path": str(cfg_path),
                "run_dir": str(rd) if rd else None,
            }
        except Exception:
            continue
    return found


def candidate_dirs(rn: str, proc):
    seen = set()
    dirs = []

    p = proc.get(rn)
    if p and p.get("run_dir"):
        q = Path(p["run_dir"])
        if q not in seen:
            seen.add(q)
            dirs.append(q)

    patterns = [
        f"/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/scientific-results/backbone/{rn}",
        f"/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/scientific-results/backbone/{rn}",
    ]
    for pattern in patterns:
        for item in glob.glob(pattern):
            q = Path(item)
            if q not in seen:
                seen.add(q)
                dirs.append(q)
    return dirs


def best_local_record(rn, proc):
    # Multiple workflow attempts can leave multiple runner-temp directories for
    # the same immutable run_name. Select the newest observed terminal/progress
    # record so an attempt-2 success supersedes an older attempt-1 OOM.
    terminal = None
    terminal_mtime = -1.0
    progress = None

    for rd in candidate_dirs(rn, proc):
        complete_path = rd / "train_complete.json"
        complete = read_json(complete_path)
        if complete:
            try:
                mtime = complete_path.stat().st_mtime
            except Exception:
                mtime = 0.0
            if mtime >= terminal_mtime:
                terminal_mtime = mtime
                terminal = {
                    "status": "SUCCESS",
                    "total": complete.get("elapsed_sec"),
                    "run_dir": str(rd),
                    "_mtime": mtime,
                }

        err_path = rd / "train_error.json"
        err = read_json(err_path)
        if err:
            try:
                mtime = err_path.stat().st_mtime
            except Exception:
                mtime = 0.0
            if mtime >= terminal_mtime:
                msg = str(err.get("error", ""))
                status = "INFRA-OOM" if ("OutOfMemory" in msg or "out of memory" in msg.lower()) else "ERROR"
                terminal_mtime = mtime
                terminal = {
                    "status": status,
                    "total": err.get("elapsed_sec"),
                    "error": msg,
                    "run_dir": str(rd),
                    "_mtime": mtime,
                }

        progress_path = rd / "train_progress.json"
        p = read_json(progress_path)
        if p:
            try:
                mtime = progress_path.stat().st_mtime
            except Exception:
                mtime = 0.0
            if progress is None or mtime > progress["_mtime"]:
                p["_mtime"] = mtime
                p["_run_dir"] = str(rd)
                progress = p

    if terminal is not None:
        terminal.pop("_mtime", None)
    return terminal, progress


def progress_fields(progress, elapsed):
    if not progress:
        return "-", None, None

    try:
        epoch = int(progress.get("epoch", 0) or 0)
        epochs = int(progress.get("epochs", 0) or 0)
        step = int(progress.get("step", 0) or 0)
        steps = int(progress.get("steps", 0) or 0)
        ep_pct = float(progress.get("pct", 0.0) or 0.0)

        ep = f"{epoch}/{epochs}" if epoch and epochs else "-"
        overall = None
        if epoch > 0 and epochs > 0 and steps > 0:
            overall = ((epoch - 1) + step / max(steps, 1)) / epochs
            overall = max(0.0, min(1.0, overall))

        eta = None
        if elapsed and overall and overall > 0.01:
            eta = elapsed * (1.0 - overall) / overall

        pct = overall * 100.0 if overall is not None else ep_pct
        return ep, pct, eta
    except Exception:
        return "-", None, None


def color_status(status):
    if status == "SUCCESS":
        return GREEN + f"{status:<10}" + RESET
    if status == "RUNNING":
        return YELLOW + f"{status:<10}" + RESET
    if status == "INFRA-OOM":
        return RED + f"{status:<10}" + RESET
    if status in {"ERROR", "INCOMPLETE"}:
        return MAGENTA + f"{status:<10}" + RESET
    if status == "WAITING":
        return CYAN + f"{status:<10}" + RESET
    if status == "HIDDEN":
        return MAGENTA + f"{status:<10}" + RESET
    return GRAY + f"{status:<10}" + RESET


def render():
    cache = load_cache()

    # Use the terminal alternate screen so refreshes overwrite one fixed frame
    # instead of adding a new dashboard to tmux scrollback every second.
    sys.stdout.write("\033[?1049h\033[?25l\033[H")
    sys.stdout.flush()

    try:
        while True:
            proc = process_rows()
            counts = {}
            rows_out = []

            for pair, trial, lane, rid in sorted(RUNS, key=lambda x: (x[0], x[1])):
                rn = run_name(pair, trial)
                local_terminal, progress = best_local_record(rn, proc)

                cached = cache["runs"].get(rn, {})
                if local_terminal:
                    cached.update(local_terminal)
                    cache["runs"][rn] = cached

                active = proc.get(rn)
                if active:
                    status = "RUNNING"
                    elapsed = active.get("elapsed")
                    epoch, pct, eta = progress_fields(progress, elapsed)
                    total = None
                else:
                    status = cached.get("status")
                    elapsed = None
                    eta = None
                    total = cached.get("total")
                    epoch, pct, _ = progress_fields(progress, None)

                    if not status:
                        # Without root, systemd ProtectProc/runner directory isolation can hide
                        # a real scientific job. Never mislabel that as WAITING.
                        if progress:
                            status = "INCOMPLETE"
                        elif OBSERVER_ELEVATED:
                            status = "WAITING"
                        else:
                            status = "HIDDEN"

                counts[status] = counts.get(status, 0) + 1
                rows_out.append(
                    (pair, trial, lane, status, epoch, pct, elapsed, eta, total, rid)
                )

            cache["updated_at_epoch"] = time.time()
            try:
                save_cache(cache)
            except Exception:
                pass

            frame = []
            frame.append(BOLD + TITLE + RESET)
            frame.append(
                f"{len(RUNS)} immutable screen experiments | refresh {REFRESH_SEC:g}s | "
                f"{time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
            )
            frame.append(
                DIM
                + (
                    "Source: HOST ROOT OBSERVER — isolated runner process/result telemetry + persistent local cache; GitHub API calls: 0"
                    if OBSERVER_ELEVATED
                    else "Source: LIMITED USER VIEW — isolated runners may be hidden; rerun with sudo for exact local state; GitHub API calls: 0"
                )
                + RESET
            )
            if not OBSERVER_ELEVATED:
                frame.append(
                    RED
                    + "WARNING: this user cannot reliably observe ci-padataset/ci-padataset-2 runner state. Use: sudo -E python3 <dashboard>"
                    + RESET
                )
            frame.append(gpu_line())
            frame.append("")
            frame.append(
                BOLD
                + f"{'EXPERIMENT':<19} {'GPU':<4} {'STATUS':<10} {'EPOCH':>7} "
                  f"{'PROG':>7} {'ELAPSED':>10} {'ETA LEFT':>10} {'TOTAL':>10} {'RUN ID':>12}"
                + RESET
            )
            frame.append("-" * 105)

            for pair, trial, lane, status, epoch, pct, elapsed, eta, total, rid in rows_out:
                prog = f"{pct:5.1f}%" if pct is not None else "-"
                frame.append(
                    f"{pair + ' ' + trial:<19} "
                    f"G{lane:<3} "
                    f"{color_status(status)} "
                    f"{epoch:>7} "
                    f"{prog:>7} "
                    f"{fmt(elapsed):>10} "
                    f"{('~' + fmt(eta)) if eta is not None else '-':>10} "
                    f"{fmt(total):>10} "
                    f"{rid:>12}"
                )

            frame.append("-" * 105)
            order = ["SUCCESS", "INFRA-OOM", "ERROR", "RUNNING", "WAITING", "INCOMPLETE", "HIDDEN"]
            summary = "   ".join(
                f"{k} {counts.get(k, 0):2d}"
                for k in order
                if counts.get(k, 0)
            )
            frame.append(summary or "No states observed")
            frame.append("")
            frame.append(
                DIM
                + "RUNNING elapsed = local process age. ETA = local progress fraction extrapolation."
                + RESET
            )
            frame.append(
                DIM
                + "SUCCESS/ERROR total = pa_train_one.py elapsed_sec when locally observed/cached."
                + RESET
            )
            frame.append(
                DIM
                + (
                    "WAITING = admitted experiment not dispatched on this host yet; it does NOT claim GitHub queue state."
                    if OBSERVER_ELEVATED
                    else "HIDDEN = exact runner state is protected from the current user; use sudo observer mode."
                )
                + RESET
            )
            frame.append("Ctrl+B then D = detach tmux | Ctrl+C = stop dashboard")

            # Home cursor, overwrite the fixed frame, then erase any remnants
            # from a previously longer frame. Nothing is appended to scrollback.
            sys.stdout.write("\033[H" + "\n".join(frame) + "\033[J")
            sys.stdout.flush()

            time.sleep(REFRESH_SEC)
    finally:
        # Restore cursor and the user's normal tmux screen/scrollback.
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()


if __name__ == "__main__":
    try:
        render()
    except KeyboardInterrupt:
        print()
