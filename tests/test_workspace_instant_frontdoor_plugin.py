"""Private ChatGPT Workspace Control front-door plugin package contract."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters" / "chatgpt-frontdoor"
MANIFEST = PLUGIN / "plugin.json"
SKILL = PLUGIN / "skills" / "workspace-control-frontdoor" / "SKILL.md"
OPENAI = (
    PLUGIN
    / "skills"
    / "workspace-control-frontdoor"
    / "agents"
    / "openai.yaml"
)


class WorkspaceControlFrontDoorPluginTests(unittest.TestCase):
    def test_manifest_is_valid_skills_only_private_package_source(self) -> None:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            data["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        self.assertEqual(data["name"], "workspace-control-frontdoor")
        self.assertEqual(data["version"], "0.1.0")
        interface = data["extensions"]["com.openai"]["interface"]
        self.assertEqual(interface["displayName"], "Workspace Control")
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertEqual(interface["category"], "Productivity")
        self.assertEqual(interface["capabilities"], ["Interactive"])
        self.assertFalse((PLUGIN / "mcp.json").exists())

    def test_skill_keeps_chat_non_authoritative_and_token_economical(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: workspace-control-frontdoor\n"))
        for required in (
            "authorization_state=UNDECIDED",
            "schemas/frontdoor_intake.v1.schema.json",
            "schemas/frontdoor_control.v1.schema.json",
            "WAITING is a control-plane state",
            "REF_ONLY",
            "DELTA",
            "FULL_RECOVERY",
            "do not depend on it for recovery",
            "Do not claim a tool action succeeded unless the tool returned evidence",
        ):
            self.assertIn(required, text)
        for forbidden in (
            "OPENAI_API_KEY=",
            "api.openai.com",
            "grant execution authority",
            "automatically approve",
        ):
            self.assertNotIn(forbidden, text)

    def test_openai_metadata_targets_chat_and_allows_persistent_frontdoor_use(self) -> None:
        text = OPENAI.read_text(encoding="utf-8")
        self.assertIn("display_name: Workspace Control", text)
        self.assertIn("short_description: Persistent Instant control", text)
        self.assertIn("allow_implicit_invocation: true", text)
        self.assertIn("    - CHAT", text)
        self.assertNotIn("    - CODEX", text)
        self.assertNotIn("    - HERMES", text)


if __name__ == "__main__":
    unittest.main()
