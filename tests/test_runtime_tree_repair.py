import hashlib
import json
import os
import pathlib
import stat
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import runtime_tree_projection as projection
import runtime_tree_repair as repair


def harden(root: pathlib.Path):
    for path in [root, *root.rglob("*")]:
        if path.is_symlink():
            continue
        os.chmod(path, stat.S_IMODE(path.stat().st_mode) & ~0o222)


def digest(root: pathlib.Path):
    records, _ = projection.scan_tree(root, hash_regular_files=True)
    return projection.projected_digest(records, set())[0]


class RuntimeTreeRepairTests(unittest.TestCase):
    def fixture(self, base: pathlib.Path):
        accepted = base / "accepted"
        live = base / "live"
        evidence = base / "candidate.json"
        quarantine = base / "quarantine"

        for root in (accepted, live):
            (root / "pkg" / "__pycache__").mkdir(parents=True)
            (root / "pkg" / "module.py").write_text("value = 1\n")
            (root / "pkg" / "__pycache__" / "base.pyc").write_bytes(b"base")
            os.symlink("/usr/bin/python3", root / "python")

        extra_dir = live / "pkg" / "__pycache__" / "later"
        extra_dir.mkdir()
        (extra_dir / "drift.pyc").write_bytes(b"drift")

        harden(accepted)
        harden(live)

        candidate = {
            "candidate_extras": [
                "pkg/__pycache__/later",
                "pkg/__pycache__/later/drift.pyc",
            ],
            "reference_only": [],
            "type_mismatches": [],
            "non_pycache_extras": [],
        }
        evidence.write_text(json.dumps(candidate))

        accepted_records, accepted_counts = projection.scan_tree(
            accepted, hash_regular_files=True
        )
        accepted_digest, accepted_actual = projection.projected_digest(
            accepted_records, set()
        )

        return {
            "accepted": accepted,
            "live": live,
            "evidence": evidence,
            "quarantine": quarantine,
            "expected_files": accepted_actual["file_count"],
            "expected_directories": accepted_actual["directory_count"],
            "expected_symlinks": accepted_actual["symlink_count"],
            "expected_bytes": accepted_actual["materialized_bytes"],
            "expected_digest": accepted_digest,
        }

    def test_apply_then_rollback_is_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = self.fixture(pathlib.Path(tmp))
            uid = os.getuid()
            gid = os.getgid()
            pre = digest(fx["live"])

            result = repair.apply_repair(
                live_root=fx["live"],
                candidate_path=fx["evidence"],
                quarantine_root=fx["quarantine"],
                expected_files=fx["expected_files"],
                expected_directories=fx["expected_directories"],
                expected_symlinks=fx["expected_symlinks"],
                expected_bytes=fx["expected_bytes"],
                expected_digest=fx["expected_digest"],
                expected_extra_files=1,
                expected_extra_directories=1,
                expected_extra_symlinks=0,
                required_uid=uid,
                required_gid=gid,
            )

            self.assertEqual(result["decision"], "PASS")
            self.assertEqual(
                result["post_actual_digest"],
                fx["expected_digest"],
            )
            self.assertFalse(
                (fx["live"] / "pkg/__pycache__/later").exists()
            )
            self.assertTrue(
                (fx["quarantine"] / "payload/pkg/__pycache__/later").is_dir()
            )

            rolled = repair.rollback_repair(
                manifest_path=pathlib.Path(result["manifest_path"]),
                required_uid=uid,
                required_gid=gid,
            )
            self.assertEqual(rolled["decision"], "PASS")
            self.assertEqual(digest(fx["live"]), pre)
            self.assertTrue(
                (fx["live"] / "pkg/__pycache__/later/drift.pyc").is_file()
            )

    def test_retained_byte_drift_rejects_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = self.fixture(pathlib.Path(tmp))
            uid = os.getuid()
            gid = os.getgid()
            (fx["live"] / "pkg/module.py").chmod(0o600)
            (fx["live"] / "pkg/module.py").write_text("value = 2\n")
            (fx["live"] / "pkg/module.py").chmod(0o400)

            with self.assertRaises(RuntimeError):
                repair.apply_repair(
                    live_root=fx["live"],
                    candidate_path=fx["evidence"],
                    quarantine_root=fx["quarantine"],
                    expected_files=fx["expected_files"],
                    expected_directories=fx["expected_directories"],
                    expected_symlinks=fx["expected_symlinks"],
                    expected_bytes=fx["expected_bytes"],
                    expected_digest=fx["expected_digest"],
                    expected_extra_files=1,
                    expected_extra_directories=1,
                    expected_extra_symlinks=0,
                    required_uid=uid,
                    required_gid=gid,
                )

            self.assertTrue(
                (fx["live"] / "pkg/__pycache__/later/drift.pyc").is_file()
            )
            self.assertFalse(fx["quarantine"].exists())

    def test_non_pycache_candidate_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = self.fixture(pathlib.Path(tmp))
            data = json.loads(fx["evidence"].read_text())
            data["non_pycache_extras"] = ["unexpected.bin"]
            fx["evidence"].write_text(json.dumps(data))

            with self.assertRaises(RuntimeError):
                repair.validate_projection(
                    live_root=fx["live"],
                    candidate_path=fx["evidence"],
                    expected_files=fx["expected_files"],
                    expected_directories=fx["expected_directories"],
                    expected_symlinks=fx["expected_symlinks"],
                    expected_bytes=fx["expected_bytes"],
                    expected_digest=fx["expected_digest"],
                    expected_extra_files=1,
                    expected_extra_directories=1,
                    expected_extra_symlinks=0,
                    required_uid=os.getuid(),
                    required_gid=os.getgid(),
                )


if __name__ == "__main__":
    unittest.main()
