#!/usr/bin/env python3
"""Read-only P1 compatibility probe for Lambda CI foundation.

Writes only a JSON receipt under workspace-control-tmp. It does not create users,
services, runners, firewall rules, cgroups, mounts, or package installations.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone


def run(argv):
    try:
        p = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        return {"argv": argv, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as exc:
        return {"argv": argv, "rc": None, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def main():
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    out = pathlib.Path.home() / "adamArchives" / "Adam" / "workspace-control-tmp" / f"lambda-runner-p1-probe-{stamp}"
    if len(sys.argv) > 1:
        out = pathlib.Path(sys.argv[1]).expanduser()
    out.mkdir(parents=True, exist_ok=False)
    report = out / "lambda-runner-p1-probe.json"

    pg_config = shutil.which("pg_config")
    pg_bindir = run([pg_config, "--bindir"]) if pg_config else {"argv": [], "rc": None, "stdout": "", "stderr": "pg_config not found"}
    bindir = pathlib.Path(pg_bindir["stdout"]) if pg_bindir.get("rc") == 0 and pg_bindir.get("stdout") else None

    postgres_bins = {}
    for name in ("initdb", "pg_ctl", "postgres", "psql", "createdb", "dropdb"):
        path = None
        if bindir:
            candidate = bindir / name
            if candidate.exists():
                path = str(candidate)
        if path is None:
            path = shutil.which(name)
        postgres_bins[name] = path

    facts = {
        "schema_version": 1,
        "probe": "workspace-lambda-self-hosted-execution-v1:P1_COMPATIBILITY_PROBE",
        "timestamp_utc": now.isoformat(),
        "writes_performed": [str(out), str(report)],
        "host_mutation_performed": False,
        "runner_registered": False,
        "filesystem": {
            "root": run(["findmnt", "-J", "-T", "/", "-o", "TARGET,SOURCE,FSTYPE,OPTIONS"]),
            "home_atrott": run(["findmnt", "-J", "-T", "/home/atrott", "-o", "TARGET,SOURCE,FSTYPE,OPTIONS"]),
            "srv": run(["findmnt", "-J", "-T", "/srv", "-o", "TARGET,SOURCE,FSTYPE,OPTIONS"]),
            "df_srv": run(["df", "-B1", "-T", "/srv"]),
            "quota_tools": {name: shutil.which(name) for name in ("quota", "setquota", "xfs_quota", "btrfs")},
        },
        "postgresql": {
            "pg_config": pg_config,
            "bindir_query": pg_bindir,
            "binaries": postgres_bins,
        },
        "firewall": {
            "nft_list_ruleset_unprivileged": run(["nft", "list", "ruleset"]) if shutil.which("nft") else None,
            "iptables_save_unprivileged": run(["iptables-save"]) if shutil.which("iptables-save") else None,
            "ufw_status_unprivileged": run(["ufw", "status"]) if shutil.which("ufw") else None,
        },
        "systemd": {
            "version": run(["systemd", "--version"]),
            "analyze_security_available": shutil.which("systemd-analyze") is not None,
            "run_available": shutil.which("systemd-run") is not None,
            "known_properties": {
                "ProtectProc": run(["systemd-analyze", "security", "--offline=yes", "/dev/null"]) if False else "not executed: requires unit file",
                "note": "Actual transient DevicePolicy/IPAddressDeny compatibility is a P1 follow-up execution gate, not performed by this read-only probe."
            },
        },
        "network": {
            "routes_v4": run(["ip", "-4", "route", "show"]),
            "routes_v6": run(["ip", "-6", "route", "show"]),
            "addresses": run(["ip", "-br", "addr", "show"]),
            "listeners_tcp": run(["ss", "-H", "-lntp"]),
        },
        "gpu": {
            "devices": run(["bash", "-lc", "stat -c '%n %a %u %g %t:%T' /dev/nvidia* 2>/dev/null || true"]),
            "inventory": run(["nvidia-smi", "--query-gpu=index,uuid,name,memory.total,driver_version", "--format=csv,noheader,nounits"]),
        },
        "toolchain": {
            name: shutil.which(name)
            for name in (
                "go", "gcc", "make", "curl", "git", "python3", "systemd-run",
                "systemd-analyze", "nft", "iptables", "ip", "ss"
            )
        }
    }

    report.write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("=== LAMBDA RUNNER P1 COMPATIBILITY PROBE ===")
    print(f"REPORT={report}")
    print(f"PG_BINDIR={pg_bindir.get('stdout','')}")
    print(f"GO={facts['toolchain']['go']}")
    print("HOST_MUTATION_PERFORMED=false")
    print("RUNNER_REGISTERED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
