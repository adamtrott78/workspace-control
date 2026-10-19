import hashlib
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "runtime_tree_projection.py"


def tree_digest(root: pathlib.Path) -> str:
    tree_hash = hashlib.sha256()
    for path in sorted(
        root.rglob("*"),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        rel = path.relative_to(root).as_posix()
        st = path.lstat()
        mode = stat.S_IMODE(st.st_mode)
        if stat.S_ISDIR(st.st_mode):
            tree_hash.update(f"D\0{rel}\0{mode:o}\n".encode())
        elif stat.S_ISLNK(st.st_mode):
            tree_hash.update(
                f"L\0{rel}\0{os.readlink(path)}\n".encode()
            )
        else:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            tree_hash.update(
                (
                    f"F\0{rel}\0{mode:o}\0{st.st_size}\0"
                    f"{digest}\n"
                ).encode()
            )
    return tree_hash.hexdigest()


class RuntimeTreeProjectionTests(unittest.TestCase):
    def prepare(self, base: pathlib.Path):
        accepted = base / "accepted"
        live = base / "live"
        reference = base / "reference"
        evidence = base / "evidence"

        for root in (accepted, live, reference):
            (root / "pkg").mkdir(parents=True)
            (root / "pkg" / "__pycache__").mkdir()
            (root / "pkg" / "module.py").write_text("value = 1\n")
            (root / "pkg" / "__pycache__" / "base.pyc").write_bytes(b"base")
            os.symlink("/usr/bin/python3", root / "python")

        for root in (accepted, reference):
            for path in [root, *root.rglob("*")]:
                if path.is_symlink():
                    continue
                os.chmod(path, stat.S_IMODE(path.stat().st_mode) & ~0o222)

        return accepted, live, reference, evidence

    def run_projection(
        self,
        live: pathlib.Path,
        reference: pathlib.Path,
        evidence: pathlib.Path,
        accepted: pathlib.Path,
    ):
        files = sum(p.is_file() and not p.is_symlink() for p in accepted.rglob("*"))
        dirs = 1 + sum(p.is_dir() and not p.is_symlink() for p in accepted.rglob("*"))
        symlinks = sum(p.is_symlink() for p in accepted.rglob("*"))
        materialized = sum(
            p.stat().st_size
            for p in accepted.rglob("*")
            if p.is_file() and not p.is_symlink()
        )
        digest = tree_digest(accepted)

        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--live-root", str(live),
                "--reference-root", str(reference),
                "--evidence-dir", str(evidence),
                "--expected-files", str(files),
                "--expected-directories", str(dirs),
                "--expected-symlinks", str(symlinks),
                "--expected-bytes", str(materialized),
                "--expected-digest", digest,
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_exact_projection_passes_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            accepted, live, reference, evidence = self.prepare(pathlib.Path(tmp))
            extra_dir = live / "pkg" / "__pycache__" / "later"
            extra_dir.mkdir()
            extra = extra_dir / "drift.pyc"
            extra.write_bytes(b"drift")

            before = extra.read_bytes()
            proc = self.run_projection(live, reference, evidence, accepted)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("RECOVERY_PROJECTION=PASS", proc.stdout)
            self.assertIn("LIVE_RUNTIME_MUTATED=false", proc.stdout)
            self.assertTrue(extra.exists())
            self.assertEqual(extra.read_bytes(), before)

    def test_retained_byte_drift_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            accepted, live, reference, evidence = self.prepare(pathlib.Path(tmp))
            (live / "pkg" / "module.py").write_text("value = 2\n")

            proc = self.run_projection(live, reference, evidence, accepted)

            self.assertEqual(proc.returncode, 10)
            self.assertIn("RECOVERY_PROJECTION=REJECT", proc.stdout)
            self.assertIn("LIVE_RUNTIME_MUTATED=false", proc.stdout)

    def test_non_pycache_extra_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            accepted, live, reference, evidence = self.prepare(pathlib.Path(tmp))
            (live / "unexpected.bin").write_bytes(b"x")

            proc = self.run_projection(live, reference, evidence, accepted)

            self.assertEqual(proc.returncode, 10)
            self.assertIn("NON_PYCACHE_EXTRA_COUNT=1", proc.stdout)
            self.assertIn("RECOVERY_PROJECTION=REJECT", proc.stdout)


if __name__ == "__main__":
    unittest.main()
