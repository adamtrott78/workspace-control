import hashlib
import json
import os
from pathlib import Path
import stat
import unittest


HELPER = Path("/opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py")
MANIFEST = Path("/etc/workspace-ci/v3/install-manifest.json")
AUTHORITY_ID = "14e58009-7bf3-43d1-8ad8-7616e70edaa3"
AUTHORITY = Path(f"/var/lib/workspace-ci/v3/migration/root-reactivation-authority-{AUTHORITY_ID}.json")
CONSUMED = Path(f"/var/lib/workspace-ci/v3/migration-authority/{AUTHORITY_ID}.json")
CONTROLLER_OVERRIDE = Path("/var/lib/workspace-ci/v3/controller-refresh/active.json")


def _probe(path: Path, *, digest: bool = False) -> dict:
    result = {"path": str(path)}
    try:
        st = path.lstat()
    except (FileNotFoundError, PermissionError, OSError) as exc:
        result.update({"exists": False, "error": f"{type(exc).__name__}: {exc}"})
        return result
    result.update(
        {
            "exists": True,
            "is_symlink": stat.S_ISLNK(st.st_mode),
            "uid": st.st_uid,
            "gid": st.st_gid,
            "mode": f"{stat.S_IMODE(st.st_mode):04o}",
            "size": st.st_size,
        }
    )
    if digest:
        try:
            result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        except (PermissionError, OSError) as exc:
            result["sha256_error"] = f"{type(exc).__name__}: {exc}"
    return result


class TestV3RootReactivationLivePrestateProbe(unittest.TestCase):
    def test_emit_exact_live_prestate_on_lambda_workspace_control_runner(self):
        runner = os.environ.get("RUNNER_NAME", "")
        if not runner.startswith("lambda-workspace-control-") or not HELPER.exists():
            self.skipTest("live Lambda workspace-control helper prestate is not mounted here")

        evidence = {
            "runner_name": runner,
            "helper": _probe(HELPER, digest=True),
            "manifest": _probe(MANIFEST, digest=True),
            "authority_receipt": _probe(AUTHORITY, digest=True),
            "authority_consumption_marker": _probe(CONSUMED, digest=True),
            "controller_override_receipt": _probe(CONTROLLER_OVERRIDE, digest=True),
        }

        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            evidence["manifest_source_head"] = manifest.get("source_head")
            evidence["manifest_root_policy_sha256"] = manifest.get("root_policy_sha256")
            entries = manifest.get("entries", [])
            evidence["helper_manifest_entry"] = next(
                (entry for entry in entries if entry.get("destination") == str(HELPER)),
                None,
            )
        except Exception as exc:
            evidence["manifest_parse_error"] = f"{type(exc).__name__}: {exc}"

        self.fail(
            "V3_ROOT_REACTIVATION_LIVE_PRESTATE_PROBE="
            + json.dumps(evidence, sort_keys=True)
        )


if __name__ == "__main__":
    unittest.main()
