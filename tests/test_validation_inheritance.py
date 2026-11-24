from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validation_inheritance.py"

spec = importlib.util.spec_from_file_location("validation_inheritance", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class ValidationInheritanceTests(unittest.TestCase):
    def test_match_uses_fail_closed_domain_patterns(self) -> None:
        patterns = ["operator-bridge/**", ".github/workflows/operator-bridge-validation.yml"]
        self.assertTrue(module._match("operator-bridge/src/a.cs", patterns))
        self.assertTrue(module._match(".github/workflows/operator-bridge-validation.yml", patterns))
        self.assertFalse(module._match("architecture/review.json", patterns))

    def test_run_verification_requires_exact_successful_head_and_name(self) -> None:
        payload = b'{"head_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","conclusion":"success","name":"Operator Bridge Validation"}'
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = payload
        with mock.patch("urllib.request.urlopen", return_value=response), mock.patch(
            "json.load",
            return_value={
                "head_sha": "a" * 40,
                "conclusion": "success",
                "name": "Operator Bridge Validation",
            },
        ):
            ok, reason = module._verify_run(
                "owner/repo",
                "token",
                {"run_id": 123, "workflow_name": "Operator Bridge Validation"},
                "a" * 40,
            )
        self.assertTrue(ok)
        self.assertEqual(reason, "validated_run_exact_success")

    def test_bad_receipt_falls_back_to_full_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipt.json"
            path.write_text('{"schema_version":99}', encoding="utf-8")
            result = module.decide(
                receipt_path=str(path),
                domain="operator_bridge",
                current_sha="b" * 40,
                repository="owner/repo",
                token="token",
            )
        self.assertFalse(result["inherited"])
        self.assertTrue(result["reason"].startswith("fail_closed:"))


if __name__ == "__main__":
    unittest.main()
