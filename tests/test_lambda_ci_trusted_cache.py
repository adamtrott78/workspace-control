import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lambda_ci_trusted_cache",
    ROOT / "scripts" / "lambda_ci_trusted_cache.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def descriptor(**overrides):
    value = {
        "schema_version": 1,
        "project_id": "research-engine",
        "artifact_kind": "test-fixture",
        "source": {
            "kind": "generated-canary",
            "identifier": "workspace-ci-trusted-cache-canary-v1",
            "immutable_revision": "v1",
        },
        "license": {
            "id": "internal-test-only",
            "reviewed": True,
        },
        "serialization": {
            "format": "none",
            "unsafe_deserialization": False,
            "custom_code": False,
        },
        "recipe": {
            "id": "lambda-ci-trusted-cache-v1",
            "implementation_sha": "991b386f8145046b29ea56f26aacf35386e67bde",
        },
    }
    value.update(overrides)
    return value


class TrustedCacheTests(unittest.TestCase):
    def test_descriptor_rejects_mutable_model_revision(self):
        value = descriptor(
            artifact_kind="model",
            source={
                "kind": "huggingface",
                "identifier": "Qwen/Qwen3.5-4B",
                "immutable_revision": "main",
            },
            serialization={
                "format": "safetensors",
                "unsafe_deserialization": False,
                "custom_code": False,
            },
        )
        with self.assertRaisesRegex(mod.CachePolicyError, "mutable"):
            mod.validate_descriptor(value)

    def test_descriptor_accepts_exact_qwen_revision_and_safe_serialization(self):
        value = descriptor(
            artifact_kind="model",
            source={
                "kind": "huggingface",
                "identifier": "Qwen/Qwen3.5-4B",
                "immutable_revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
            },
            license={"id": "apache-2.0", "reviewed": True},
            serialization={
                "format": "safetensors",
                "unsafe_deserialization": False,
                "custom_code": False,
            },
        )
        self.assertEqual(
            mod.validate_descriptor(value)["source"]["immutable_revision"],
            "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
        )

    def test_unsafe_serialization_and_custom_code_fail_closed(self):
        unsafe = descriptor(
            serialization={
                "format": "pickle",
                "unsafe_deserialization": True,
                "custom_code": False,
            }
        )
        with self.assertRaisesRegex(mod.CachePolicyError, "unsafe deserialization"):
            mod.validate_descriptor(unsafe)

        custom = descriptor(
            serialization={
                "format": "safetensors",
                "unsafe_deserialization": False,
                "custom_code": True,
            }
        )
        with self.assertRaisesRegex(mod.CachePolicyError, "custom/remote"):
            mod.validate_descriptor(custom)

    def test_candidate_cannot_acquire_or_promote(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            source = base / "source"
            source.mkdir()
            (source / "canary.txt").write_text("safe\n", encoding="utf-8")
            with mock.patch.object(mod.os, "geteuid", return_value=1000):
                with self.assertRaisesRegex(mod.CachePolicyError, "requires root"):
                    mod.acquire_local(
                        source=source,
                        descriptor=descriptor(),
                        state_root=base / "state",
                    )
                with self.assertRaisesRegex(mod.CachePolicyError, "requires root"):
                    mod.promote(
                        quarantine_id="00000000-0000-4000-8000-000000000000",
                        project_id="research-engine",
                        state_root=base / "state",
                        trusted_root=base / "trusted",
                    )

    def test_acquire_promote_verify_is_content_addressed_and_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            source = base / "source"
            source.mkdir()
            (source / "canary.txt").write_text(
                "workspace-ci-trusted-cache-canary-v1\n",
                encoding="utf-8",
            )
            state = base / "state"
            trusted = base / "trusted"

            with mock.patch.object(mod.os, "geteuid", return_value=0):
                q = mod.acquire_local(
                    source=source,
                    descriptor=descriptor(),
                    state_root=state,
                )
                self.assertEqual(
                    q["tree_digest_sha256"],
                    "5bf1fba5838c38e5ae8e3f69b108d4b3ca9b9090aad435214f55fa30a626c14d",
                )
                receipt = mod.promote(
                    quarantine_id=q["quarantine_id"],
                    project_id="research-engine",
                    state_root=state,
                    trusted_root=trusted,
                )

            self.assertEqual(receipt["decision"], "PASS")
            self.assertTrue(receipt["quarantine_destroyed"])
            object_root = (
                trusted
                / "objects"
                / "test-fixture"
                / "sha256"
                / receipt["object_id"]
            )
            result = mod.verify_object(object_root)
            self.assertEqual(result["decision"], "PASS")
            self.assertTrue(result["offline_complete"])
            self.assertTrue(result["read_only"])
            self.assertFalse(
                (object_root / "payload" / "canary.txt").stat().st_mode & 0o222
            )
            self.assertFalse(
                (state / "research-engine" / "quarantine" / q["quarantine_id"]).exists()
            )
            durable = (
                state
                / "research-engine"
                / "receipts"
                / f"{receipt['object_id']}.json"
            )
            self.assertTrue(durable.is_file())

    def test_promoted_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            source = base / "source"
            source.mkdir()
            (source / "canary.txt").write_text("safe\n", encoding="utf-8")
            with mock.patch.object(mod.os, "geteuid", return_value=0):
                q = mod.acquire_local(
                    source=source,
                    descriptor=descriptor(),
                    state_root=base / "state",
                )
                receipt = mod.promote(
                    quarantine_id=q["quarantine_id"],
                    project_id="research-engine",
                    state_root=base / "state",
                    trusted_root=base / "trusted",
                )

            object_root = (
                base
                / "trusted"
                / "objects"
                / "test-fixture"
                / "sha256"
                / receipt["object_id"]
            )
            payload = object_root / "payload" / "canary.txt"
            payload.chmod(0o644)
            payload.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(mod.CachePolicyError, "digest mismatch"):
                mod.verify_object(object_root)

    def test_symlink_and_secret_material_are_rejected_before_quarantine(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            source = base / "source"
            source.mkdir()
            (source / "plain.txt").write_text("safe\n", encoding="utf-8")
            (source / "link").symlink_to("plain.txt")
            with mock.patch.object(mod.os, "geteuid", return_value=0):
                with self.assertRaisesRegex(mod.CachePolicyError, "symlinks"):
                    mod.acquire_local(
                        source=source,
                        descriptor=descriptor(),
                        state_root=base / "state",
                    )

        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            source = base / "source"
            source.mkdir()
            (source / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            with mock.patch.object(mod.os, "geteuid", return_value=0):
                with self.assertRaisesRegex(mod.CachePolicyError, "secret-bearing"):
                    mod.acquire_local(
                        source=source,
                        descriptor=descriptor(),
                        state_root=base / "state",
                    )


if __name__ == "__main__":
    unittest.main()
