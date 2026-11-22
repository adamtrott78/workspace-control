#!/usr/bin/env python3
"""Recover PA1-PA2/t007 workflow run ID from host-local job UUID evidence.

Read-only and zero-provider: no network, gh, GitHub API, curl, retries, or
process mutation. Intended to run under sudo because host journals and isolated
workspace-ci files may require root visibility.

This v2 resolver uses the durable job UUID recovered from the dashboard cache
and searches:
  1. the exact job root (even if runner temp was cleaned);
  2. recent small text files anywhere under /srv/workspace-ci/padataset that
     mention the exact job UUID / run name / admission comment;
  3. a bounded local journal window around the observed completion.

It emits a workflow run ID only when one candidate is unambiguous or strongly
dominant. Otherwise it exits 0 with UNRESOLVED so the operator shell stays open.
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
JOB_UUID = "p5-a5b5e2fb-53d6-5862-878a-153556b6aca6"
JOB_ROOT = Path("/srv/workspace-ci/padataset/jobs") / JOB_UUID
SEARCH_ROOT = Path("/srv/workspace-ci/padataset")
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_FILES = 12000

if os.geteuid() == 0 and os.environ.get("SUDO_USER"):
    pw = pwd.getpwnam(os.environ["SUDO_USER"])
    OPERATOR_HOME = Path(pw.pw_dir)
else:
    OPERATOR_HOME = Path.home()

CACHE = OPERATOR_HOME / ".cache/workspace-control/experiment-dashboards/mth602-t007-fullmatrix.json"

RUN_PATTERNS = [
    re.compile(rb"padataset-scientific-([0-9]{6,})"),
    re.compile(rb"GITHUB_RUN_ID[=:'\" ]+([0-9]{6,})", re.I),
    re.compile(rb"github\.run_id[^0-9]{0,80}([0-9]{6,})", re.I),
    re.compile(rb"/actions/runs/([0-9]{6,})", re.I),
    re.compile(rb"\"run_id\"\s*:\s*\"?([0-9]{6,})", re.I),
    re.compile(rb"run[_ -]?id[^0-9]{0,40}([0-9]{6,})", re.I),
]


def load_cache():
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return {}


def parse_candidates(blob: bytes, weight: int, scores: dict[str, int], src: str, evidence: list[dict]):
    found = set()
    for pat in RUN_PATTERNS:
        for m in pat.finditer(blob):
            found.add(m.group(1).decode())
    if not found:
        return
    boost = weight
    if RUN_NAME.encode() in blob:
        boost += 10
    if COMMENT_ID.encode() in blob:
        boost += 10
    if JOB_UUID.encode() in blob:
        boost += 12
    for rid in found:
        scores[rid] = scores.get(rid, 0) + boost
    evidence.append({
        "source": src,
        "candidate_run_ids": sorted(found),
        "contains_run_name": RUN_NAME.encode() in blob,
        "contains_comment_id": COMMENT_ID.encode() in blob,
        "contains_job_uuid": JOB_UUID.encode() in blob,
    })


def candidate_files():
    seen = set()
    count = 0

    roots = []
    if JOB_ROOT.exists():
        roots.append(JOB_ROOT)
    roots.append(SEARCH_ROOT)

    for root in roots:
        if not root.exists():
            continue
        for base, dirs, files in os.walk(root):
            # Avoid recursively reading trusted model/data caches.
            dirs[:] = [
                d for d in dirs
                if d not in {"trusted-cache", "staging-cache", ".git", "__pycache__"}
            ]
            for name in files:
                if count >= MAX_FILES:
                    return
                p = Path(base) / name
                key = str(p)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    st = p.stat()
                except Exception:
                    continue
                if st.st_size <= 0 or st.st_size > MAX_FILE_BYTES:
                    continue
                # Focus global scan on recent files; exact job root is always accepted.
                if JOB_ROOT not in p.parents and p != JOB_ROOT:
                    # completion was ~13:27 EST; accept files touched within this day.
                    if st.st_mtime < 1795345200:  # 2026-11-22 00:00 EST-ish safety floor
                        continue
                count += 1
                yield p


def scan_files(scores, evidence):
    for p in candidate_files():
        try:
            blob = p.read_bytes()
        except Exception:
            continue
        if (
            JOB_UUID.encode() not in blob
            and RUN_NAME.encode() not in blob
            and COMMENT_ID.encode() not in blob
            and b"GITHUB_RUN_ID" not in blob
            and b"padataset-scientific-" not in blob
            and b"/actions/runs/" not in blob
        ):
            continue
        weight = 4 if JOB_ROOT in p.parents else 1
        parse_candidates(blob, weight, scores, str(p), evidence)


def scan_journal(scores, evidence):
    try:
        cp = subprocess.run(
            [
                "journalctl",
                "--since", "2026-11-22 12:10:00",
                "--until", "2026-11-22 13:45:00",
                "--no-pager", "-o", "short-iso",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
        blob = cp.stdout or b""
    except Exception:
        return

    # Build bounded context around lines mentioning the exact UUID/run/comment.
    lines = blob.splitlines()
    idxs = []
    needles = [JOB_UUID.encode(), RUN_NAME.encode(), COMMENT_ID.encode()]
    for i, line in enumerate(lines):
        if any(n in line for n in needles):
            idxs.append(i)

    chunks = []
    for i in idxs[:100]:
        lo = max(0, i - 12)
        hi = min(len(lines), i + 25)
        chunks.extend(lines[lo:hi])
    if chunks:
        parse_candidates(b"\n".join(chunks), 8, scores, "journal-context", evidence)


def cache_direct(scores, evidence):
    d = load_cache()
    rec = (d.get("runs") or {}).get(RUN_NAME) or {}
    direct = rec.get("github_run_id")
    if direct and str(direct).isdigit():
        scores[str(direct)] = scores.get(str(direct), 0) + 100
        evidence.append({"source": str(CACHE), "candidate_run_ids": [str(direct)], "cache_direct": True})
    return rec


def main():
    print("=== PA1-PA2 T007 LOCAL RUN-ID RECOVERY V2 ===")
    print("NETWORK_CALLS=0")
    print(f"JOB_UUID={JOB_UUID}")
    print(f"JOB_ROOT={JOB_ROOT}")
    print(f"JOB_ROOT_EXISTS={'YES' if JOB_ROOT.exists() else 'NO'}")

    scores: dict[str, int] = {}
    evidence: list[dict] = []
    rec = cache_direct(scores, evidence)
    print("CACHE_RECORD=" + json.dumps(rec, sort_keys=True))

    scan_files(scores, evidence)
    scan_journal(scores, evidence)

    for ev in evidence[:40]:
        print("LOCAL_EVIDENCE=" + json.dumps(ev, sort_keys=True))

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    for rid, score in ranked[:15]:
        print(f"CANDIDATE_RUN_ID={rid} SCORE={score}")

    if not ranked:
        print("PA1_PA2_LOCAL_RUNID_RECOVERY=UNRESOLVED")
        print("No mutation occurred. Paste this output back; do not use gh/API polling.")
        return

    if len(ranked) == 1 or ranked[0][1] >= ranked[1][1] + 12:
        rid = ranked[0][0]
        print(f"PA1_PA2_WORKFLOW_RUN_ID={rid}")
        print("RUN_ID_SOURCE=host_local_job_uuid_evidence")
        print("PA1_PA2_LOCAL_RUNID_RECOVERY=PASS")
        return

    print("PA1_PA2_LOCAL_RUNID_RECOVERY=AMBIGUOUS")
    print("No mutation occurred. Paste this output back; do not use gh/API polling.")


if __name__ == "__main__":
    main()
