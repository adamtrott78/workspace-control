"""Live, zero-inference Codex subscription preflight for the reserved control runner."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import unittest


from pathlib import Path as _Path
import sys

ROOT = _Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    CodexSubscriptionAuthGuard,
    default_codex_usage_collector,
)


RUNNER_PREFIX = "lambda-workspace-control-control-small-"
EXPECTED_HOME = Path("/srv/workspace-ci/workspace-control/home")


@unittest.skipUnless(
    os.environ.get("RUNNER_NAME", "").startswith(RUNNER_PREFIX),
    "live Codex preflight runs only on the reserved Workspace Control runner",
)
class LiveCodexSubscriptionPreflight(unittest.TestCase):
    def test_chatgpt_plus_auth_and_read_only_account_telemetry(self):
        # This is deliberately zero-inference: no prompt, no codex exec, and no
        # model call. It only reads account identity type/plan and usage state.
        self.assertNotIn("OPENAI_API_KEY", os.environ)

        codex = shutil.which("codex")
        self.assertIsNotNone(codex, "Codex CLI is not installed on control runner")

        self.assertEqual(
            Path.home().resolve(),
            EXPECTED_HOME,
            "Codex credentials must remain inside the Workspace Control project home",
        )

        auth = CodexSubscriptionAuthGuard().require_authorized()
        self.assertEqual(auth.account_type, "chatgpt")
        self.assertEqual(auth.plan_type, "plus")

        snapshot = default_codex_usage_collector().read_snapshot()
        self.assertIsInstance(snapshot.captured_at, str)
        self.assertTrue(snapshot.captured_at)
        # Unknown/null upstream metrics are valid. The important live contract
        # is that the two official read RPCs complete without credentials,
        # billing keys, or model inference.
        self.assertIsNotNone(snapshot.rate_limit_buckets)


if __name__ == "__main__":
    unittest.main()
