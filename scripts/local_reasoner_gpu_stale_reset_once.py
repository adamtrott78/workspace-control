#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, pathlib, pwd, subprocess, tempfile, urllib.request

REPO=pathlib.Path(__file__).resolve().parents[1]
REL=pathlib.Path("scripts/local_reasoner_gpu_stale_reset_once.py")
PROJECT="research-engine"; LANE="gpu"
QID="3eeffae8-2bd0-4344-b89f-02afbf1a445b"
OLD_ID=2
OBS="2026-10-28T05:15:55.833668328Z"
AUTHORITY_MARKER=6462367016
CLEARED_MARKER=6462619666
REG_SHA="9b65a78d83e4849ddb22abd7b14eac8953b00345557f1111f726fdd2a37b3450"
MAN_SHA="5b003fff4045b755be7a14b537e9b56fdb8397f93f45ba66e8c2ef53e011b390"
CONTROL_REPO="adamtrott78/workspace-control"
RUNS=[40636959931,40636967211,40637274575,40637282488,40637418843,40641329629,40643628869,40643739086]

class E(RuntimeError): pass

def run(argv,user=None,check=True,env=None):
    cmd=argv if user is None else ["/usr/sbin/runuser","-u",user,"--",*argv]
    p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,env=env)
    if check and p.returncode: raise E(f"rc={p.returncode} cmd={cmd!r}: {p.stderr.strip()}")
    return p

def home(user): return pwd.getpwnam(user).pw_dir

def git(inv,*args):
    return run(["git","-C",str(REPO),*args],user=inv,env={"PATH":"/usr/bin:/bin","HOME":home(inv),"LANG":"C.UTF-8","LC_ALL":"C.UTF-8"}).stdout.strip()

def canon_sha(path):
    v=json.loads(path.read_text())
    raw=json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def api(path):
    req=urllib.request.Request("https://api.github.com/"+path,headers={"Accept":"application/vnd.github+json","User-Agent":"workspace-control-one-shot-recovery/2","X-GitHub-Api-Version":"2022-11-28"})
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read())

def require_owner_marker(comment_id,prefix):
    m=api(f"repos/{CONTROL_REPO}/issues/comments/{comment_id}")
    if m.get("user",{}).get("login")!="adamtrott78":
        raise E(f"marker actor drift: {comment_id}")
    body=str(m.get("body",""))
    if not body.startswith(prefix):
        raise E(f"marker body drift: {comment_id}")
    return body

def verify(inv,head):
    if os.geteuid()!=0 or not inv or inv=="root": raise E("run via sudo from operator account")
    if pathlib.Path(__file__).resolve()!=(REPO/REL).resolve(): raise E("helper path drift")
    git(inv,"ls-files","--error-unmatch","--",REL.as_posix())
    if git(inv,"rev-parse","HEAD")!=head: raise E("unexpected helper HEAD")
    if git(inv,"status","--porcelain","--untracked-files=no"): raise E("tracked checkout dirty")
    if canon_sha(pathlib.Path("/etc/workspace-ci/lambda-ci-project-registry.v1.json"))!=REG_SHA: raise E("registry digest drift")
    if canon_sha(pathlib.Path("/etc/workspace-ci/projects/research-engine.json"))!=MAN_SHA: raise E("manifest digest drift")
    q=json.loads(pathlib.Path("/var/lib/workspace-ci/controller/state/research-engine-gpu/quarantine.json").read_text())
    exp={"project_id":PROJECT,"lane":LANE,"receipt_id":QID,"scale_set_id":OLD_ID,"scale_set_name":"lambda-research-engine-gpu","status":"ASSIGNMENT_DIVERGENCE_QUARANTINED","observed_at":OBS,"active_count":0,"pending_count":0,"reconstructable_jobs":0,"total_assigned_jobs":1}
    for k,v in exp.items():
        if q.get(k)!=v: raise E(f"quarantine drift {k}: {q.get(k)!r} != {v!r}")

    authority=require_owner_marker(AUTHORITY_MARKER,"LOCAL_REASONER_GPU_STALE_RESET_ONCE_V1")
    if f"Quarantine receipt: {QID}" not in authority or f"Old scale-set id: {OLD_ID}" not in authority:
        raise E("authority marker identity drift")

    cleared=require_owner_marker(CLEARED_MARKER,"LOCAL_REASONER_GPU_STALE_RUNS_CLEARED_V1")
    for rid in RUNS:
        if f"- {rid} completed/cancelled" not in cleared:
            raise E(f"cleared-run evidence missing: {rid}")
    if "No Local Reasoner Resource Probe run from this stale set remains non-terminal." not in cleared:
        raise E("cleared-run terminal assertion missing")

INNER=r'''
import importlib.util,json,pathlib
P="research-engine"; L="gpu"; Q="3eeffae8-2bd0-4344-b89f-02afbf1a445b"; O="2026-10-28T05:15:55.833668328Z"; CID=6462367016
p=pathlib.Path("/opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py")
s=importlib.util.spec_from_file_location("mc",p)
if s is None or s.loader is None: raise SystemExit("import failed")
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
def guard(_client,cmd,obs):
    exp={"action":"reset-stale","project_id":P,"lane":L,"quarantine_receipt_id":Q}
    if cmd!=exp or obs!=O: raise m.MaintenanceControllerError("one-time recovery identity drift")
m.assert_no_replacement_runs=guard
cmd={"action":"reset-stale","project_id":P,"lane":L,"quarantine_receipt_id":Q}
r=m.execute_reset(comment_id=CID,command=cmd,root_socket=pathlib.Path("/run/workspace-ci/maintenance/maintenance.sock"),controller_binary=pathlib.Path("/opt/workspace-ci/controller/lambda-ci-controller"),controllers_dir=pathlib.Path("/etc/workspace-ci/controllers"),runner_token_file=pathlib.Path("/var/lib/workspace-ci/maintenance-controller/runner-token"),github_client=object())
if r.get("status")!="READY_FOR_SINGLE_RETRY" or r.get("quarantine_receipt_id")!=Q or r.get("old_scale_set_id")!=2 or r.get("automatic_workflow_triggered") is not False:
    raise SystemExit("reset receipt mismatch")
print(json.dumps(r,indent=2,sort_keys=True))
'''

def inner():
    u=pwd.getpwnam("ci-maintenance")
    fd,path=tempfile.mkstemp(prefix="local-reasoner-gpu-reset-",suffix=".py",dir="/tmp",text=True)
    try:
        os.write(fd,INNER.encode()); os.close(fd); fd=-1
        os.chown(path,0,u.pw_gid); os.chmod(path,0o550)
        p=run(["/usr/bin/python3",path],user="ci-maintenance",check=False,env={"PATH":"/usr/bin:/bin","HOME":"/var/lib/workspace-ci/maintenance-controller","LANG":"C.UTF-8","LC_ALL":"C.UTF-8"})
        if p.returncode: raise E("reset failed: "+(p.stderr.strip() or p.stdout.strip()))
        return p.stdout
    finally:
        if fd>=0: os.close(fd)
        pathlib.Path(path).unlink(missing_ok=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--expected-head",required=True); a=ap.parse_args()
    inv=os.environ.get("SUDO_USER","")
    verify(inv,a.expected_head)
    out=inner()
    print("LOCAL_REASONER_GPU_STALE_RESET_ONCE=PASS"); print(out.rstrip())
    return 0
if __name__=="__main__": raise SystemExit(main())
