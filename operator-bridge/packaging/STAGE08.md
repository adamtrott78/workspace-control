# Stage 08 Packaging / Install / Update / Rollback Implementation

Status: implementation artifact for impl_08_packaging_install_update_rollback.

Stage 08 packages the frozen production helper and Firefox adapter without changing UX-00 through UX-13, browser permissions, extension identity, native-host identity, dispatch authority, recovery semantics, or the manual Ctrl+Space -> Ctrl+V -> Enter operator workflow.

Production installation is per-user only. Files live under %LOCALAPPDATA%\WorkspaceControl\OperatorBridge by default. Native Messaging registration uses only HKCU\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge. The installer never writes Firefox profiles, profiles.ini, extension databases, cookies, credentials, tokens, local storage, IndexedDB, or page content. No administrator elevation, service, scheduled task, machine-wide registry key, network listener, or automatic updater is introduced.

build-package.ps1 performs a self-contained win-x64 dotnet publish of WorkspaceOperator. A package contains payload/helper, payload/extension/workspace-control-operator.xpi, management/install.ps1, management/uninstall.ps1, management/rollback.ps1, management/SIGNED-XPI-INSTALL.md, and package.json.

package.json binds the exact source SHA, release version, runtime, file hashes, frozen Firefox extension ID, exact permission list, native-host identity, extension version, and XPI mode. The builder opens the XPI and requires manifest.json, adapter_core.js, and background.js to match the repository production FirefoxAdapter source. Production signature validity is intentionally delegated to Firefox during the manual signed-XPI install flow.

install.ps1 verifies the package inventory and hashes before mutation, creates an immutable versioned release under the owned install root, writes a content-free native-host manifest bound to the release helper, updates only the dedicated HKCU Native Messaging host key, and records only release/source SHA metadata. Existing releases are never overwritten. An upgrade records the old active release as previous_version and does not delete it.

rollback.ps1 re-verifies the previous release, switches the dedicated HKCU Native Messaging registration back to it, swaps active_version and previous_version, and reports the previous XPI path. Firefox extension rollback remains a manual signed-XPI reinstall from that path.

uninstall.ps1 requires the ownership marker before recursive removal. If the dedicated Native Messaging registry value does not point inside the owned install root, uninstall fails closed. It removes only the dedicated host key and the owned install root. Firefox add-on removal is manual.

stage08-smoke.ps1 uses an explicitly marked CI-only unsigned XPI fixture built from the exact production adapter source. Production install rejects that fixture unless the explicit CI switch is supplied. The smoke performs clean install, upgrade, rollback, and uninstall and checks unrelated filesystem, sibling registry, and Firefox-profile sentinels remain unchanged. It emits content-free evidence plus package manifests bound to the exact tested Git SHA.

The CI unsigned fixture is not Mozilla-signing evidence. Production signed-XPI acceptance requires a Mozilla-signed XPI whose embedded production files match the exact source tree, followed by manual Firefox installation so Firefox performs signature validation.
