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
        gecko = manifest["browser_specific_settings"]["gecko"]
        self.assertEqual("workspace-control-operator@adamtrott78.local", gecko["id"])
        self.assertEqual("153.0", gecko["strict_min_version"])
        self.assertEqual(["none"], gecko["data_collection_permissions"]["required"])

    def test_solution_contains_only_authorized_projects(self):
        tree = ET.parse(SOLUTION)
        projects = {e.attrib["Path"].replace("\\", "/") for e in tree.getroot().findall("Project")}
        self.assertEqual(
            {
                "src/SharedContracts/SharedContracts.csproj",
                "src/WorkspaceOperator/WorkspaceOperator.csproj",
                "tests/WorkspaceOperator.Tests/WorkspaceOperator.Tests.csproj",
                "tests/Protocol.Tests/Protocol.Tests.csproj",
                "tests/Integration.Tests/Integration.Tests.csproj",
            },
            projects,
        )

    def test_child_authority_scope_is_exact(self):
        task = json.loads(TASK.read_text(encoding="utf-8"))
        repo = next(item for item in task["repositories"] if item["name"] == "workspace-control")
        self.assertEqual(
            [
                "tasks/active/workspace-operator-bridge-implementation-v1.json",
                "tasks/active/workspace-operator-bridge-implementation-v1.md",
                "architecture/workspace-semantic-execution-operator-implementation-program.v0.1.md",
                "architecture/workspace-semantic-execution-operator-implementation-stage-plan.v0.1.json",
                "architecture/workspace-semantic-execution-operator-implementation-traceability.v0.1.json",
                "operator-bridge/**",
                ".github/workflows/operator-bridge-validation.yml",
                "benchmarks/workspace-semantic-execution/operator_bridge/**",
                "tests/test_workspace_semantic_execution_operator_bridge*.py",
            ],
            repo["allowed_mutation_scope"],
        )

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
        self.assertIn("VirtualKeyB", source)


if __name__ == "__main__":
    unittest.main()
