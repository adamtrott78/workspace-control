#!/usr/bin/env python3
"""Recover PA1-PA2/t007 workflow run identity from host-local runner evidence.

Read-only. No network, gh, GitHub API, curl, provider calls, mutation, retry,
or process control. Designed to be run with sudo so isolated runner files and
/proc/journal evidence are visible.

The only required output is PA1_PA2_WORKFLOW_RUN_ID. Once recovered, connected
control-plane tooling can resolve the job/artifact binding by exact run ID.
"""

from __future__ import annotations

import json
import os
import pwd
import re
import subprocess
from pathlib import Path

RUN_NAME = "l2o_t007_fullmatrix_PA1_PA2"
COMMENT_ID = "7082541725"
JOBS_ROOT = Path("/srv/workspace-ci/padataset/jobs")
MAX_TEXT_BYTES = 12 * 1024 * 1024
MAX_FILES = 4000

if os.geteuid() == 0 and os.environ.get("SUDO_USER"):
    pw = pwd.getpwnam(os.environ["SUDO_USER"])
    operator_home = Path(pw.pw_dir)
else:
    operator_home = Path.home()

CACHE = operator_home / ".cache/workspace-control/experiment-dashboards/mth602-t007-fullmatrix.json"

RUN_PATTERNS = [
    re.compile(rb"padataset-scientific-([0-9]{6,})"),
    re.compile(rb"GITHUB_RUN_ID[=:'\" ]+([0-9]{6,})", re.I),
    re.compile(rb"github\.run_id[^0-9]{0,80}([0-9]{6,})", re.I),
    re.compile(rb"\"run_id\"\s*:\s*\"?([0-9]{6,})", re.I),
]

TEXT_SUFFIXES = {
    ".log", ".txt", ".json", ".yml", ".yaml", ".out", ".err",
    ".trace", ".env", ".md",
}


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def cache_record():
    data = read_json(CACHE) or {}
    return (data.get("runs") or {}).get(RUN_NAME) or {}


def result_dirs():
    out = []
    rec = cache_record()
    cached = rec.get("run_dir")
    if cached:
        p = Path(str(cached))
        if p.exists():
            out.append(p)

    if JOBS_ROOT.is_dir():
        # Bounded exact-name traversal: runner work trees only.
        for job in JOBS_ROOT.iterdir():
            if not job.is_dir():
                continue
            for runner_name in ("runner", "runner2"):
                root = job / runner_name / "_work" / "_temp" / "scientific-results" / "backbone" / RUN_NAME
                if root.is_dir():
                    out.append(root)

    uniq = {}
    for p in out:
        try:
            mt = p.stat().st_mtime
        except Exception:
            mt = 0.0
        uniq[str(p)] = (mt, p)
    return [x[1] for x in sorted(uniq.values(), reverse=True)]


def runner_root_from_result(run_dir: Path):
    parts = run_dir.parts
    for i, part in enumerate(parts):
        if part.startswith("runner"):
            return Path(*parts[: i + 1])
    return None


def candidate_text_files(root: Path):
    if not root or not root.is_dir():
        return
    count = 0
    preferred = [root / "_diag", root / "_work" / "_temp"]
    for base in preferred:
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if count >= MAX_FILES:
                return
            if not p.is_file():
                continue
            try:
                st = p.stat()
            except Exception:
                continue
            if st.st_size > MAX_TEXT_BYTES:
                continue
            # Diagnostic logs often have no useful suffix guarantees, so accept
            # small files in _diag and text-ish files under _temp.
            if base.name != "_diag" and p.suffix.lower() not in TEXT_SUFFIXES:
                continue
            count += 1
            yield p


def scan_files(root: Path):
    scores = {}
    evidence = []
    for p in candidate_text_files(root):
        try:
            b = p.read_bytes()
        except Exception:
            continue

        relevant = (
            RUN_NAME.encode() in b
            or COMMENT_ID.encode() in b
            or b"padataset-scientific-" in b
            or b"GITHUB_RUN_ID" in b
            or b"github.run_id" in b
        )
        if not relevant:
            continue

        found_here = set()
        for pat in RUN_PATTERNS:
            for m in pat.finditer(b):
                rid = m.group(1).decode()
                found_here.add(rid)

        if found_here:
            weight = 1
            if RUN_NAME.encode() in b:
                weight += 8
            if COMMENT_ID.encode() in b:
                weight += 8
            for rid in found_here:
                scores[rid] = scores.get(rid, 0) + weight
            evidence.append((str(p), sorted(found_here), RUN_NAME.encode() in b, COMMENT_ID.encode() in b))

    return scores, evidence


def journal_candidates():
    # Read-only, bounded to the local completion window supplied by operator
    # evidence (roughly 12:30-13:35 EST on 2026-11-22).
    try:
        cp = subprocess.run(
            [
                "journalctl",
                "--since", "2026-11-22 12:20:00",
                "--until", "2026-11-22 13:40:00",
                "--no-pager", "-o", "cat",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
        b = cp.stdout or b""
    except Exception:
        return {}, []

    if RUN_NAME.encode() not in b and COMMENT_ID.encode() not in b and b"padataset-scientific-" not in b:
        return {}, []

    scores = {}
    hits = []
    for pat in RUN_PATTERNS:
        for m in pat.finditer(b):
            rid = m.group(1).decode()
            scores[rid] = scores.get(rid, 0) + 2
            hits.append(rid)
    return scores, sorted(set(hits))


def main():
    print("=== PA1-PA2 T007 LOCAL RUN-ID RECOVERY ===")
    print("NETWORK_CALLS=0")
    print(f"RUN_NAME={RUN_NAME}")
    print(f"CACHE={CACHE}")

    rec = cache_record()
    if rec:
        print("CACHE_RECORD=" + json.dumps(rec, sort_keys=True))
        direct = rec.get("github_run_id")
        if direct and str(direct).isdigit():
            print(f"PA1_PA2_WORKFLOW_RUN_ID={direct}")
            print("RUN_ID_SOURCE=dashboard_cache")
            print("PA1_PA2_LOCAL_RUNID_RECOVERY=PASS")
            return

    dirs = result_dirs()
    print(f"RESULT_DIR_CANDIDATE_COUNT={len(dirs)}")
    for d in dirs:
        print(f"RESULT_DIR={d}")

    combined = {}
    all_evidence = []
    roots = []
    for d in dirs:
        rr = runner_root_from_result(d)
        if rr and rr not in roots:
            roots.append(rr)

    # If result temp was already cleaned but cache preserved the old path,
    # derive the runner root from that path even when the leaf no longer exists.
    cached_path = rec.get("run_dir") if rec else None
    if cached_path:
        rr = runner_root_from_result(Path(str(cached_path)))
        if rr and rr not in roots and rr.exists():
            roots.append(rr)

    print(f"RUNNER_ROOT_COUNT={len(roots)}")
    for rr in roots:
        print(f"RUNNER_ROOT={rr}")
        scores, evidence = scan_files(rr)
        for rid, score in scores.items():
            combined[rid] = combined.get(rid, 0) + score
        all_evidence.extend(evidence)

    jscores, jhits = journal_candidates()
    for rid, score in jscores.items():
        combined[rid] = combined.get(rid, 0) + score

    for p, ids, has_run, has_comment in all_evidence[:25]:
        print(
            "LOCAL_EVIDENCE="
            + json.dumps(
                {
                    "path": p,
                    "candidate_run_ids": ids,
                    "contains_run_name": has_run,
                    "contains_comment_id": has_comment,
                },
                sort_keys=True,
            )
        )
    if jhits:
        print("JOURNAL_CANDIDATE_RUN_IDS=" + ",".join(jhits))

    ranked = sorted(combined.items(), key=lambda kv: (-kv[1], kv[0]))
    for rid, score in ranked[:10]:
        print(f"CANDIDATE_RUN_ID={rid} SCORE={score}")

    if len(ranked) == 1:
        print(f"PA1_PA2_WORKFLOW_RUN_ID={ranked[0][0]}")
        print("RUN_ID_SOURCE=host_local_runner_evidence")
        print("PA1_PA2_LOCAL_RUNID_RECOVERY=PASS")
        return

    if ranked and (len(ranked) == 1 or ranked[0][1] >= ranked[1][1] + 8):
        print(f"PA1_PA2_WORKFLOW_RUN_ID={ranked[0][0]}")
        print("RUN_ID_SOURCE=host_local_runner_evidence_high_confidence")
        print("PA1_PA2_LOCAL_RUNID_RECOVERY=PASS")
        return

    print("PA1_PA2_LOCAL_RUNID_RECOVERY=UNRESOLVED")
    print("No mutation occurred. Paste this output back; do not use gh/API polling.")


if __name__ == "__main__":
    main()
