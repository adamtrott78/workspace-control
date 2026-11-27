"""Tests for the control-owned evaluator sealed-store primitive."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.evaluator import (  # noqa: E402
    FilesystemEvaluatorSealedStore,
    SealedStoreError,
    stage_ephemeral_bundle,
)

GENERATOR = ROOT / "benchmarks/workspace-semantic-execution/resumable_reasoning_ephemeral_fixture_v1.py"
spec = importlib.util.spec_from_file_location("ephemeral_fixture", GENERATOR)
ephemeral = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(ephemeral)


class EvaluatorSealedStoreTests(unittest.TestCase):
    SEED = "11" * 32
    NONCE = "22" * 32

    def make_store(self, root: Path) -> FilesystemEvaluatorSealedStore:
        root.mkdir(mode=0o700)
        os.chmod(root, 0o700)
        return FilesystemEvaluatorSealedStore(root, owner_uid=os.getuid())

    def test_stage_persists_secrets_but_returns_worker_safe_projection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "sealed"
            store = self.make_store(root)
            bundle = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
            staged = stage_ephemeral_bundle(store=store, bundle=bundle, seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
            serialized_worker = json.dumps(staged.worker_material, sort_keys=True)
            self.assertNotIn(self.SEED, serialized_worker)
            self.assertNotIn(self.NONCE, serialized_worker)
            self.assertNotIn("evaluator_oracle", serialized_worker)
            self.assertNotIn(str(root), serialized_worker)
            self.assertIn("oracle_commitment_sha256", serialized_worker)
            restored = store.load(staged.record.fixture_id)
            self.assertEqual(restored.evaluator_oracle, bundle["evaluator_oracle"])
            self.assertEqual(restored.seed_hex, self.SEED)
            self.assertEqual(restored.seal_nonce_hex, self.NONCE)

    def test_root_and_record_modes_are_strict(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "sealed"
            store = self.make_store(root)
            bundle = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
            staged = stage_ephemeral_bundle(store=store, bundle=bundle, seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
            record = root / (staged.record.fixture_id + ".sealed.json")
            self.assertEqual(stat.S_IMODE(os.lstat(root).st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(os.lstat(record).st_mode), 0o600)
            self.assertEqual(os.lstat(record).st_uid, os.getuid())

    def test_store_rejects_permissive_or_wrong_owner_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "sealed"
            root.mkdir(mode=0o700)
            os.chmod(root, 0o755)
            with self.assertRaisesRegex(SealedStoreError, "mode_must_be_0700"):
                FilesystemEvaluatorSealedStore(root, owner_uid=os.getuid())
            os.chmod(root, 0o700)
            with self.assertRaisesRegex(SealedStoreError, "owner_mismatch"):
                FilesystemEvaluatorSealedStore(root, owner_uid=os.getuid() + 100000)

    def test_store_rejects_symlink_root(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            actual = base / "actual"
            actual.mkdir(mode=0o700)
            os.chmod(actual, 0o700)
            link = base / "sealed"
            link.symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(SealedStoreError, "must_be_real_directory"):
                FilesystemEvaluatorSealedStore(link, owner_uid=os.getuid())

    def test_record_is_create_once_and_fixture_id_is_path_safe(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "sealed"
            store = self.make_store(root)
            bundle = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
            stage_ephemeral_bundle(store=store, bundle=bundle, seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
            with self.assertRaisesRegex(SealedStoreError, "already_exists"):
                stage_ephemeral_bundle(store=store, bundle=bundle, seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
            with self.assertRaisesRegex(SealedStoreError, "fixture_id:invalid"):
                store.load("../escape")

    def test_restored_secret_material_verifies_public_commitment(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "sealed"
            store = self.make_store(root)
            bundle = ephemeral.generate_bundle(seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
            staged = stage_ephemeral_bundle(store=store, bundle=bundle, seed_hex=self.SEED, seal_nonce_hex=self.NONCE)
            restored = store.load(staged.record.fixture_id)
            self.assertTrue(ephemeral.verify_bundle(
                public_fixture=staged.worker_material["public_fixture"],
                evaluator_oracle=restored.evaluator_oracle,
                public_seal=staged.worker_material["public_seal"],
                seal_nonce_hex=restored.seal_nonce_hex,
            ))


if __name__ == "__main__":
    unittest.main()
