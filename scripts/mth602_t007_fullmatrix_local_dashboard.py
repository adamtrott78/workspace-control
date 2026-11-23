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
import re
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
    ("PA1-PA2", "G0", "l2o_t007_fullmatrix_PA1_PA2", "run 45047242656"),
    ("PA1-PA3", "G1", "l2o_t007_fullmatrix_PA1_PA3", "run 45084249815"),
    ("PA1-PA4", "G0", "l2o_t007_fullmatrix_PA1_PA4", "run 45047248043"),
    ("PA1-PA8", "G1", "l2o_t007_fullmatrix_PA1_PA8", "run 45084251371"),
    ("PA2-PA3", "G1", "l2o_hpo_tight60_PA2_PA3_t007", "run 44954728466"),
    ("PA2-PA4", "G0", "l2o_t007_fullmatrix_PA2_PA4", "run 45047254352"),
    ("PA2-PA8", "G0", "l2o_hpo_v2_PA2_PA8_t007_finalist", "run 44924427484"),
    ("PA3-PA4", "G0", "l2o_t007_fullmatrix_PA3_PA4", "run 45085768587"),
    ("PA3-PA8", "G0", "l2o_hpo_tight60_PA3_PA8_t007", "run 45100307460"),
    ("PA4-PA8", "G0", "l2o_t007_fullmatrix_PA4_PA8", "run 45047260602"),
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


# Post-freeze t007 directional OSR wave. GPU1 executes these through the
# already-reviewed /lambda-l2o-eval-2 workflow while GPU0 may continue backbone
# training. The dashboard remains provider-API-free: local process/result
# telemetry plus persistent cache only.
OSR_OVERLAY = "PADataset PR54 db35a153"
OSR_DIRECTIONS = [
    ("PA1<-PA2", 14765881457),
    ("PA2<-PA1", 14765881457),
    ("PA1<-PA3", 14783316485),
    ("PA3<-PA1", 14783316485),
    ("PA1<-PA4", 14769480157),
    ("PA4<-PA1", 14769480157),
    ("PA1<-PA8", 14785061977),
    ("PA8<-PA1", 14785061977),
    ("PA2<-PA3", 14736363148),
    ("PA3<-PA2", 14736363148),
    ("PA2<-PA4", 14770958092),
    ("PA4<-PA2", 14770958092),
    ("PA2<-PA8", 14719755202),
    ("PA8<-PA2", 14719755202),
    ("PA3<-PA4", 14784971329),
    ("PA4<-PA3", 14784971329),
    ("PA4<-PA8", 14773056923),
    ("PA8<-PA4", 14773056923),
]
OSR_SEED = {
    "PA2<-PA8": {
        "status": "SUCCESS",
        "artifact_id": 14719755202,
        "unknown_f1": 0.984758990646242,
        "unknown_auroc": 0.9950973911571004,
        "known_reject_rate": 0.0562064363043155,
        "github_run_id": 44944519746,
    },
    "PA8<-PA2": {
        "status": "SUCCESS",
        "artifact_id": 14719755202,
        "unknown_f1": 0.9792627621225628,
        "unknown_auroc": 0.9882538493077788,
        "known_reject_rate": 0.0618419101290226,
        "github_run_id": 44949531116,
    },
}

OSR_RUN_IDS = {
    "PA1<-PA2": 45102051232,
    "PA2<-PA1": 45102053615,
    "PA1<-PA3": 45102058238,
    "PA3<-PA1": 45102060140,
    "PA1<-PA4": 45102062857,
    "PA4<-PA1": 45102067059,
    "PA1<-PA8": 45102069338,
    "PA8<-PA1": 45102072243,
    "PA2<-PA3": 45102074619,
    "PA3<-PA2": 45102077778,
    "PA2<-PA4": 45102082224,
    "PA4<-PA2": 45102085345,
    "PA2<-PA8": 44944519746,
    "PA8<-PA2": 44949531116,
    "PA3<-PA4": 45102088341,
    "PA4<-PA3": 45102090059,
    "PA4<-PA8": 45102093066,
    "PA8<-PA4": 45102097294,
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


ANSI_CSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def terminal_width():
    """Return the real pane width; never pretend a narrow tmux pane is wider."""
    try:
        cols = os.get_terminal_size(sys.stdout.fileno()).columns
    except Exception:
        try:
            cols = os.get_terminal_size().columns
        except Exception:
            cols = 124
    return max(20, min(150, int(cols)))


def fit_ansi_line(text, width):
    """Truncate by visible terminal columns while preserving ANSI control codes."""
    width = max(1, int(width))
    out = []
    visible = 0
    i = 0
    while i < len(text) and visible < width:
        if text[i] == "\\x1b":
            match = ANSI_CSI_RE.match(text, i)
            if match:
                out.append(match.group(0))
                i = match.end()
                continue
        out.append(text[i])
        visible += 1
        i += 1
    # Always terminate style state even if truncation removed a trailing RESET.
    out.append(RESET)
    return "".join(out)


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
    osr = data.setdefault("osr", {})
    for direction, seed in OSR_SEED.items():
        row = osr.setdefault(direction, {})
        for key, value in seed.items():
            if row.get(key) is None and value is not None:
                row[key] = value
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


def proc_env(pid):
    """Read a small provenance subset from /proc without any network calls."""
    try:
        raw = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
    except Exception:
        return {}
    env = {}
    wanted = {"GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_WORKFLOW", "GITHUB_REPOSITORY"}
    for item in raw:
        if b"=" not in item:
            continue
        k, v = item.split(b"=", 1)
        try:
            key = k.decode()
        except Exception:
            continue
        if key in wanted:
            env[key] = v.decode(errors="replace")
    return env


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
            pe = proc_env(pid)
            found[rn] = {
                "pid": pid,
                "elapsed": elapsed,
                "cfg_path": str(cfg_path),
                "run_dir": str(run_dir) if run_dir else None,
                "github_run_id": pe.get("GITHUB_RUN_ID"),
                "github_run_attempt": pe.get("GITHUB_RUN_ATTEMPT"),
                "github_workflow": pe.get("GITHUB_WORKFLOW"),
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



def osr_process_rows():
    """Observe live frozen directional evaluators without provider calls."""
    found = {}
    tracked = {direction for direction, _artifact_id in OSR_DIRECTIONS}
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid=,etimes=,args="],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return found

    for raw in out.splitlines():
        if "pa_eval_dqn_guard_surrogate_open.py" not in raw:
            continue
        parts = raw.strip().split(None, 2)
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
            elapsed = int(parts[1])
            argv = shlex.split(parts[2])
            ti = argv.index("--target-open-pa")
            si = argv.index("--surrogate-open-pa")
            direction = f"{argv[ti + 1]}<-{argv[si + 1]}"
            if direction not in tracked:
                continue
            pe = proc_env(pid)
            found[direction] = {
                "pid": pid,
                "elapsed": elapsed,
                "github_run_id": pe.get("GITHUB_RUN_ID"),
                "github_run_attempt": pe.get("GITHUB_RUN_ATTEMPT"),
            }
        except Exception:
            continue
    return found


def scan_osr_results():
    """Return newest result record for each expected t007 direction/artifact."""
    expected = dict(OSR_DIRECTIONS)
    found = {}
    patterns = [
        "/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/l2o-directional-results/eval/result_record.json",
        "/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/l2o-directional-results/eval/result_record.json",
    ]
    for pattern in patterns:
        for raw in glob.glob(pattern):
            p = Path(raw)
            d = read_json(p)
            if not isinstance(d, dict) or d.get("status") != "COMPLETE":
                continue
            direction = f"{d.get('evaluation_target')}<-{d.get('evaluation_surrogate')}"
            if direction not in expected:
                continue
            artifact = d.get("artifact") or {}
            try:
                artifact_id = int(artifact.get("id", 0))
            except Exception:
                continue
            if artifact_id != int(expected[direction]):
                continue
            try:
                mt = p.stat().st_mtime
            except Exception:
                mt = 0.0
            prior = found.get(direction)
            if prior is not None and prior.get("_mtime", -1.0) > mt:
                continue
            metrics = d.get("metrics") or {}
            found[direction] = {
                "_mtime": mt,
                "status": "SUCCESS",
                "artifact_id": artifact_id,
                "unknown_f1": metrics.get("unknown_f1"),
                "unknown_auroc": metrics.get("unknown_auroc"),
                "known_reject_rate": metrics.get("known_reject_rate"),
                "result_path": str(p),
            }
    return found


def build_osr_rows(cache, active, results):
    rows = []
    store = cache.setdefault("osr", {})
    for direction, artifact_id in OSR_DIRECTIONS:
        cached = store.setdefault(direction, {})
        if not cached.get("github_run_id") and direction in OSR_RUN_IDS:
            cached["github_run_id"] = OSR_RUN_IDS[direction]
        result = results.get(direction)
        if result:
            cached.update({k: v for k, v in result.items() if not k.startswith("_")})
        proc = active.get(direction)
        if proc:
            cached["status"] = "RUNNING"
            if proc.get("github_run_id"):
                cached["github_run_id"] = proc.get("github_run_id")
            store[direction] = cached
            status = "RUNNING"
            elapsed = proc.get("elapsed")
        elif cached.get("status") == "SUCCESS":
            status = "SUCCESS"
            elapsed = None
        else:
            status = "ADMITTED"
            elapsed = None
        rows.append({
            "direction": direction,
            "artifact_id": artifact_id,
            "status": status,
            "elapsed": elapsed,
            "unknown_f1": cached.get("unknown_f1"),
            "unknown_auroc": cached.get("unknown_auroc"),
            "known_reject_rate": cached.get("known_reject_rate"),
            "github_run_id": cached.get("github_run_id"),
        })
    return rows

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
            osr_active = osr_process_rows()
            osr_results = scan_osr_results()
            osr_rows = build_osr_rows(cache, osr_active, osr_results)
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
                    if active.get("github_run_id"):
                        cached["github_run_id"] = active.get("github_run_id")
                        cached["github_run_attempt"] = active.get("github_run_attempt")
                        cached["github_workflow"] = active.get("github_workflow")
                        cache["runs"][rn] = cached
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
                    "github_run_id": active.get("github_run_id") if active else cached.get("github_run_id"),
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
            # Reserve one physical column so the terminal never enters its
            # pending-autowrap state at the right edge.
            safe_width = max(1, width - 1)
            rule = "─" * min(safe_width, 136)
            source = (
                "HOST ROOT OBSERVER — local process/result/GPU telemetry + persistent cache — provider API calls: 0"
                if OBSERVER_ELEVATED
                else "LIMITED USER VIEW — isolated jobs may be hidden; use sudo observer mode — provider API calls: 0"
            )

            frame = []
            frame.append(BOLD + CYAN + "╔" + "═" * max(1, min(safe_width - 2, 134)) + "╗" + RESET)
            frame.append(BOLD + f"  {TITLE}" + RESET)
            frame.append(DIM + f"  {SUBTITLE} | refresh {REFRESH_SEC:g}s" + RESET)
            frame.append(BOLD + CYAN + "╚" + "═" * max(1, min(safe_width - 2, 134)) + "╝" + RESET)
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
                    f"{fmt_seconds(r['total']):>9} {metric(r['val_macro']):>8} {metric(r['val_min']):>8}  "
                    + ((f"run {r['github_run_id']} | ") if r.get("github_run_id") else "")
                    + f"{r['identity']}"
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

            frame.append("")
            osr_counts = {}
            for r in osr_rows:
                osr_counts[r["status"]] = osr_counts.get(r["status"], 0) + 1
            osr_summary = "   ".join(
                f"{k} {osr_counts.get(k,0):2d}"
                for k in ("SUCCESS", "RUNNING", "ADMITTED", "ERROR")
                if osr_counts.get(k, 0)
            )
            frame.append(
                BOLD + "GPU1 T007 OSR  " + RESET
                + (osr_summary or "-")
                + DIM + f"   | 18 directions | {OSR_OVERLAY}" + RESET
            )
            frame.append(
                BOLD
                + f"{'DIRECTION':<12} {'STATUS':<10} {'ELAPSED':>9} "
                  f"{'U-F1':>8} {'AUROC':>8} {'K-REJ':>8}  IDENTITY"
                + RESET
            )
            frame.append(rule)
            for r in osr_rows:
                identity = (
                    f"run {r['github_run_id']}"
                    if r.get("github_run_id")
                    else f"artifact {r['artifact_id']}"
                )
                frame.append(
                    f"{r['direction']:<12} {color_status(r['status'])} "
                    f"{fmt_seconds(r['elapsed']):>9} "
                    f"{metric(r['unknown_f1']):>8} {metric(r['unknown_auroc']):>8} "
                    f"{metric(r['known_reject_rate']):>8}  {identity}"
                )
            frame.append(rule)
            frame.append(
                DIM
                + "OSR is post-freeze diagnostic only: target/test/OSR evidence cannot alter recipe, checkpoint, retry, or pair freeze."
                + RESET
            )
            if not OBSERVER_ELEVATED:
                frame.append(RED + "Use the reviewed sudo observer for exact isolated-runner visibility." + RESET)
            frame.append(BOLD + "Ctrl+C" + RESET + " detach + keep dashboard alive  |  "
                         + BOLD + "tmux attach -t mth602-t007-wave" + RESET + " return")

            # Full-clear each frame instead of relying on cursor-up/logical-row
            # arithmetic. Every line is width-bounded so tmux/terminal autowrap
            # cannot create extra physical rows and corrupt later redraws.
            fitted = [fit_ansi_line(line, safe_width) for line in frame]
            sys.stdout.write("\033[2J\033[H" + "\n".join(fitted))
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
