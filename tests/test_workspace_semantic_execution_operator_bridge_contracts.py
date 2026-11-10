import json
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "operator-bridge"
TASK = ROOT / "tasks/active/workspace-operator-bridge-implementation-v1.json"
FROZEN_PROTOCOL = ROOT / "architecture/workspace-semantic-execution-operator-native-messaging-protocol.v0.1.json"
IMPLEMENTATION_PROTOCOL = BRIDGE / "protocol/browser_adapter_v1.schema.json"
MANIFEST = BRIDGE / "src/FirefoxAdapter/manifest.json"
WORKFLOW = ROOT / ".github/workflows/operator-bridge-validation.yml"
SOLUTION = BRIDGE / "WorkspaceOperatorBridge.slnx"
CLIPBOARD_ADAPTER = BRIDGE / "src/WorkspaceOperator/Windows/Clipboard/WinFormsClipboardWriter.cs"
HOTKEY_ADAPTER = BRIDGE / "src/WorkspaceOperator/Windows/Hotkey/WindowsHotkeyRegistrar.cs"
IPC_SERVER = BRIDGE / "src/WorkspaceOperator/Ipc/LocalIpcServer.cs"
PROTOCOL_VALIDATOR = BRIDGE / "src/SharedContracts/Protocol/ProtocolValidator.cs"


class OperatorBridgeContractTests(unittest.TestCase):
    def test_protocol_copy_matches_frozen_contract(self):
        self.assertEqual(
            json.loads(FROZEN_PROTOCOL.read_text(encoding="utf-8")),
            json.loads(IMPLEMENTATION_PROTOCOL.read_text(encoding="utf-8")),
        )

    def test_firefox_manifest_is_least_privilege_baseline(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(3, manifest["manifest_version"])
        self.assertEqual(["nativeMessaging", "tabs", "sessions"], manifest["permissions"])
        for forbidden_key in (
            "host_permissions",
            "optional_host_permissions",
            "content_scripts",
            "externally_connectable",
        ):
            self.assertNotIn(forbidden_key, manifest)
        forbidden_permissions = {
            "activeTab", "scripting", "webNavigation", "webRequest",
            "cookies", "clipboardRead", "clipboardWrite",
        }
        self.assertTrue(forbidden_permissions.isdisjoint(manifest["permissions"]))

    def test_child_authority_scope_is_exact(self):
        task = json.loads(TASK.read_text(encoding="utf-8"))
        repo = next(item for item in task["repositories"] if item["name"] == "workspace-control")
        self.assertIn("operator-bridge/**", repo["allowed_mutation_scope"])
        self.assertNotIn("architecture/workspace-semantic-execution-operator-native-messaging-protocol.v0.1.json", repo["allowed_mutation_scope"])

    def test_dedicated_ci_has_no_account_secret_dependency(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        lowered = workflow.lower()
        self.assertNotIn("secrets.", lowered)
        self.assertNotIn("openai_api_key", lowered)
        self.assertNotIn("chatgpt", lowered)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("runs-on: windows-latest", workflow)

    def test_clipboard_adapter_is_write_only(self):
        source = CLIPBOARD_ADAPTER.read_text(encoding="utf-8")
        self.assertIn("Clipboard.SetText", source)
        self.assertNotIn("Clipboard.Get", source)
        self.assertNotIn("GetText(", source)
        self.assertNotIn("GetDataObject(", source)

    def test_hotkey_adapter_enforces_no_repeat(self):
        source = HOTKEY_ADAPTER.read_text(encoding="utf-8")
        self.assertIn("ModControl | ModNoRepeat", source)

    def test_named_pipe_is_current_user_only_and_not_network_listening(self):
        source = IPC_SERVER.read_text(encoding="utf-8")
        self.assertIn("PipeOptions.CurrentUserOnly", source)
        combined = "\n".join(
            p.read_text(encoding="utf-8")
            for p in (BRIDGE / "src/WorkspaceOperator").rglob("*.cs")
        )
        self.assertNotIn("TcpListener", combined)
        self.assertNotIn("HttpListener", combined)
        self.assertNotIn("Socket.Listen", combined)

    def test_protocol_validator_has_explicit_content_denylist(self):
        source = PROTOCOL_VALIDATOR.read_text(encoding="utf-8")
        for forbidden in (
            '"packet_text"', '"clipboard_content"', '"raw_url"',
            '"page_content"', '"credentials"', '"token"', '"cookies"',
        ):
            self.assertIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
