#!/usr/bin/env python3
"""Pretty host-local dual-GPU H1 directional OSR dashboard.

No GitHub API calls. Root observation only:
- nvidia-smi
- local runner/evaluator processes
- RUNNER_TEMP L2O files
- scientific result/receipt files
- persistent operator-owned cache

The static admissions are only the latest known queue snapshot. Any locally
observed lane-A/lane-B process or terminal receipt supersedes that snapshot.
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

TITLE = "MTH602 H1 — DUAL-GPU FROZEN-PAIR DQNGUARD OSR DASHBOARD"
REFRESH_SEC = 1.0
CACHE = None

CELLS = [
    ("PA2<-PA3", "PA2", "PA3", 0.027741, 44944515567, "G1"),
    ("PA3<-PA2", "PA3", "PA2", 0.001426, 44944517585, "G1"),
    ("PA2<-PA8", "PA2", "PA8", 0.801033, 44944519746, "G1"),
    ("PA8<-PA2", "PA8", "PA2", 0.757011, 44949531116, "G0"),
    ("PA3<-PA8", "PA3", "PA8", 0.054209, 44947121549, "G1"),
    ("PA8<-PA3", "PA8", "PA3", 0.424513, 44949535061, "G0"),
]

COMPLETED_SEED = {
    "PA2<-PA3": {
        "run_id": 44944515567, "lane": "G1", "unknown_f1": 0.1502975148757437,
        "known_reject_rate": 0.0718522912650155, "total": 337.47395634651184,
        "sha": "573be0e7281f18c42c5f0ec326e4090a52f80d93",
    },
    "PA3<-PA2": {
        "run_id": 44944517585, "lane": "G1", "unknown_f1": 0.3841282467035825,
        "known_reject_rate": 0.067403232982352, "total": 343.37676215171814,
        "sha": "573be0e7281f18c42c5f0ec326e4090a52f80d93",
    },
    "PA2<-PA8": {
        "run_id": 44944519746, "lane": "G1", "unknown_f1": 0.984758990646242,
        "known_reject_rate": 0.0562064363043155, "total": 344.2536709308624,
        "sha": "573be0e7281f18c42c5f0ec326e4090a52f80d93",
    },
    "PA3<-PA8": {
        "run_id": 44947121549, "lane": "G1", "unknown_f1": 0.0,
        "known_reject_rate": 0.049855330514133, "total": None,
        "sha": "0067a419c855ae659a4a4f00f1e0bfb6dc2d5b62",
    },
}

RESET="\033[0m"; BOLD="\033[1m"; DIM="\033[2m"
GREEN="\033[32m"; RED="\033[31m"; YELLOW="\033[33m"
CYAN="\033[36m"; MAGENTA="\033[35m"; GRAY="\033[90m"

OBSERVER_ELEVATED = os.geteuid() == 0
if OBSERVER_ELEVATED and os.environ.get("SUDO_USER"):
    pw = pwd.getpwnam(os.environ["SUDO_USER"])
    OP_HOME = Path(pw.pw_dir); OP_UID = pw.pw_uid; OP_GID = pw.pw_gid
else:
    OP_HOME = Path.home(); OP_UID = os.getuid(); OP_GID = os.getgid()
CACHE = OP_HOME / ".cache/workspace-control/experiment-dashboards/mth602-h1-dual-osr.json"


def read_json(p: Path):
    try: return json.loads(p.read_text())
    except Exception: return None


def fmt(sec):
    if sec is None: return "-"
    try: sec=max(0,int(float(sec)))
    except Exception: return "-"
    h,r=divmod(sec,3600); m,s=divmod(r,60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def load_cache():
    d=read_json(CACHE) if CACHE.exists() else None
    if not isinstance(d,dict):
        d={"cells":{}}
    d.setdefault("cells", {})
    for key, value in COMPLETED_SEED.items():
        current=d["cells"].get(key, {})
        if current.get("unknown_f1") is None:
            d["cells"][key]=dict(value)
    return d


def save_cache(d):
    CACHE.parent.mkdir(parents=True,exist_ok=True)
    if OBSERVER_ELEVATED:
        try: os.chown(CACHE.parent,OP_UID,OP_GID)
        except OSError: pass
    tmp=CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    if OBSERVER_ELEVATED:
        try: os.chown(tmp,OP_UID,OP_GID)
        except OSError: pass
    tmp.replace(CACHE)
    if OBSERVER_ELEVATED:
        try: os.chown(CACHE,OP_UID,OP_GID)
        except OSError: pass


def gpu_snapshot():
    out={}
    try:
        raw=subprocess.check_output([
            "nvidia-smi",
            "--query-gpu=index,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],text=True,stderr=subprocess.DEVNULL)
        for line in raw.strip().splitlines():
            idx,used,total,util=[x.strip() for x in line.split(",")]
            out[int(idx)]={"used":used,"total":total,"util":util}
    except Exception: pass
    return out


def proc_snapshot():
    """Map direction -> active local evaluator, with exact lane/run/SHA/temp."""
    found={}
    try:
        raw=subprocess.check_output(
            ["ps","-eo","pid=,etimes=,user=,args="],
            text=True,stderr=subprocess.DEVNULL,
        )
    except Exception:
        return found

    for line in raw.splitlines():
        parts=line.strip().split(None,3)
        if len(parts)<4: continue
        try:
            pid=int(parts[0]); elapsed=int(parts[1]); user=parts[2]; args=parts[3]
        except Exception: continue
        if "pa_eval_dqn_guard_surrogate_open.py" not in args: continue
        lane = "G0" if user=="ci-padataset" else ("G1" if user=="ci-padataset-2" else "?")
        try:
            argv=shlex.split(args)
            target=argv[argv.index("--target-open-pa")+1]
            surrogate=argv[argv.index("--surrogate-open-pa")+1]
        except Exception:
            continue
        env={}
        if OBSERVER_ELEVATED:
            try:
                for item in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
                    if b"=" in item:
                        k,v=item.split(b"=",1)
                        env[k.decode(errors="ignore")]=v.decode(errors="ignore")
            except Exception: pass
        found[(target,surrogate)]={
            "pid":pid,"elapsed":elapsed,"lane":lane,
            "run_id":env.get("GITHUB_RUN_ID"),
            "sha":env.get("EXPECTED_SHA"),
            "temp":env.get("RUNNER_TEMP"),
        }
    return found


def stage_for(temp):
    if not temp: return "EVALUATE"
    t=Path(temp); root=t/"scientific-results"; ev=root/"l2o_eval"
    if (root/"scientific-receipt.json").is_file() and (ev/"result_record.json").is_file(): return "DONE"
    if (ev/"result_record.json").is_file(): return "RECORD"
    if (ev/"osr_summary.csv").is_file(): return "FINALIZE"
    if (t/"l2o-resolved.json").is_file(): return "EVAL-READY"
    if (t/"l2o-rehydrate.json").is_file(): return "REHYDRATE"
    if (t/"l2o-backbone-artifact.zip").is_file(): return "FETCH"
    if (t/"l2o-pre-resolved.json").is_file(): return "VALIDATE"
    return "EVALUATE"


def terminal_scan():
    """Newest provenance-valid local terminal record per direction."""
    out={}
    patterns=[
        "/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/scientific-results/l2o_eval/result_record.json",
        "/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/scientific-results/l2o_eval/result_record.json",
    ]
    for pat in patterns:
        for raw in glob.glob(pat):
            p=Path(raw); rec=read_json(p)
            if not isinstance(rec,dict) or rec.get("status")!="COMPLETE": continue
            if rec.get("schema")!="padataset.l2o-directional-eval-result.v1": continue
            target=rec.get("evaluation_target"); surrogate=rec.get("evaluation_surrogate")
            if not target or not surrogate: continue
            sci=p.parent.parent/"scientific-receipt.json"
            sr=read_json(sci)
            if not isinstance(sr,dict) or sr.get("decision")!="PASS" or sr.get("operation")!="l2o_directional_eval":
                continue
            try: mt=max(p.stat().st_mtime,sci.stat().st_mtime)
            except Exception: mt=0
            metrics=rec.get("metrics") or {}
            resolved=read_json(p.parent/"resolved-request.json") or {}
            run_id=None
            # Runtime path itself does not encode GitHub ID reliably; cache can retain it
            # when the active process was observed.
            item={
                "mtime":mt,
                "lane":"G0" if sr.get("gpu_uuid")=="GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea" else "G1",
                "sha":sr.get("candidate_sha"),
                "unknown_f1":metrics.get("unknown_f1"),
                "known_reject_rate":metrics.get("known_reject_rate"),
                "total":None,
                "artifact_id":(rec.get("artifact") or {}).get("id"),
            }
            csvp=p.parent/"osr_summary.csv"
            try:
                with csvp.open(newline="") as h:
                    row=next(csv.DictReader(h))
                item["total"]=float(row.get("elapsed_sec")) if row.get("elapsed_sec") else None
            except Exception: pass
            key=(str(target),str(surrogate))
            if key not in out or mt>=out[key]["mtime"]: out[key]=item
    return out


def status_color(s):
    if s=="SUCCESS": return GREEN+f"{s:<9}"+RESET
    if s=="RUNNING": return YELLOW+f"{s:<9}"+RESET
    if s=="WAITING": return CYAN+f"{s:<9}"+RESET
    if s=="IDLE": return GRAY+f"{s:<9}"+RESET
    if s=="ACTIVATE": return MAGENTA+f"{s:<9}"+RESET
    return MAGENTA+f"{s:<9}"+RESET


def metric(x):
    return "-" if x is None else f"{float(x):.4f}"


def render():
    cache=load_cache()
    sys.stdout.write("\033[?1049h\033[?25l\033[H"); sys.stdout.flush()
    try:
        while True:
            gpu=gpu_snapshot(); active=proc_snapshot(); terminals=terminal_scan()
            rows=[]
            lane_active={"G0":None,"G1":None}
            for label,target,surrogate,baseline,default_run,default_lane in CELLS:
                key=f"{target}<-{surrogate}"
                a=active.get((target,surrogate))
                t=terminals.get((target,surrogate))
                cached=cache["cells"].get(key,{})
                if a:
                    lane=a["lane"]; lane_active[lane]=label
                    run_id=a.get("run_id") or cached.get("run_id") or default_run
                    cached.update({"run_id":run_id,"lane":lane,"sha":a.get("sha")})
                    cache["cells"][key]=cached
                    rows.append((label,lane,"RUNNING",stage_for(a.get("temp")),a["elapsed"],None,None,None,run_id,a.get("sha")))
                elif t:
                    lane=t["lane"]; run_id=cached.get("run_id") or default_run
                    cached.update({"run_id":run_id,"lane":lane,"sha":t.get("sha"),"unknown_f1":t.get("unknown_f1"),"known_reject_rate":t.get("known_reject_rate"),"total":t.get("total")})
                    cache["cells"][key]=cached
                    uf=t.get("unknown_f1"); delta=None if uf is None else float(uf)-baseline
                    rows.append((label,lane,"SUCCESS","DONE",None,t.get("total"),uf,t.get("known_reject_rate"),run_id,t.get("sha")))
                elif cached.get("unknown_f1") is not None:
                    uf=cached.get("unknown_f1"); lane=cached.get("lane",default_lane)
                    rows.append((label,lane,"SUCCESS","DONE",None,cached.get("total"),uf,cached.get("known_reject_rate"),cached.get("run_id",default_run),cached.get("sha")))
                else:
                    if default_lane == "G0" and not default_run:
                        rows.append((label,default_lane,"ACTIVATE","TRUST",None,None,None,None,"-",None))
                    else:
                        rows.append((label,default_lane,"WAITING","-",None,None,None,None,default_run,None))

            try: save_cache(cache)
            except Exception: pass

            frame=[BOLD+TITLE+RESET]
            frame.append(f"6 frozen directional cells | standard DQNGuard | target-open diagnostic only | refresh {REFRESH_SEC:g}s | {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            frame.append(DIM+"Source: HOST ROOT OBSERVER — local runner/process/result telemetry + persistent cache; GitHub API calls: 0"+RESET)
            g0=gpu.get(0,{}); g1=gpu.get(1,{})
            frame.append(f"GPU0 mem {g0.get('used','-')}/{g0.get('total','-')} MiB util {g0.get('util','-')}%   GPU1 mem {g1.get('used','-')}/{g1.get('total','-')} MiB util {g1.get('util','-')}%")
            frame.append("")
            frame.append(BOLD+"LIVE LANES"+RESET)
            waiting_by_lane={"G0":0,"G1":0}
            for row in rows:
                if row[2] == "WAITING" and row[1] in waiting_by_lane:
                    waiting_by_lane[row[1]] += 1
            for lane,gidx in (("G0",0),("G1",1)):
                active_label=lane_active.get(lane)
                if active_label:
                    st="RUNNING"; detail=active_label
                elif waiting_by_lane[lane]:
                    st="WAITING"; detail=f"{waiting_by_lane[lane]} exact-head job(s) queued; no local runner visible"
                elif lane == "G0" and any(r[1]=="G0" and r[2]=="ACTIVATE" for r in rows):
                    st="ACTIVATE"; detail="lane-A L2O trust activation required before re-admission"
                else:
                    st="IDLE"; detail="no local evaluator visible"
                frame.append(f"{lane}  {status_color(st)}  {detail}")
            frame.append("")
            frame.append(BOLD+f"{'DIRECTION':<12} {'LANE':<5} {'STATUS':<9} {'STAGE':<10} {'ELAPSED':>9} {'TOTAL':>9} {'UNK-F1':>8} {'DELTA':>8} {'K-REJ':>8} {'RUN ID':>12}"+RESET)
            frame.append("-"*112)
            for label,lane,status,stage,elapsed,total,uf,krej,run_id,sha in rows:
                baseline=next(x[3] for x in CELLS if x[0]==label)
                delta=None if uf is None else float(uf)-baseline
                ds="-" if delta is None else f"{delta:+.4f}"
                frame.append(f"{label:<12} {lane:<5} {status_color(status)} {stage:<10} {fmt(elapsed):>9} {fmt(total):>9} {metric(uf):>8} {ds:>8} {metric(krej):>8} {str(run_id):>12}")
            frame.append("-"*112)
            frame.append(DIM+"UNK-F1 = final target-open Unknown-F1; DELTA = change vs repaired Track-A directional baseline; K-REJ = final known reject rate."+RESET)
            frame.append(DIM+"Target-open metrics are diagnostic only and cannot feed back into backbone/HPO/checkpoint selection."+RESET)
            frame.append(DIM+"WAITING is the last known admission snapshot when no local runner is visible; active/terminal host evidence supersedes it."+RESET)
            frame.append("Ctrl+B then D = detach tmux | Ctrl+C = stop dashboard")
            sys.stdout.write("\033[H"+"\n".join(frame)+"\033[J"); sys.stdout.flush()
            time.sleep(REFRESH_SEC)
    finally:
        sys.stdout.write("\033[?25h\033[?1049l"); sys.stdout.flush()


if __name__=="__main__":
    try: render()
    except KeyboardInterrupt: print()
