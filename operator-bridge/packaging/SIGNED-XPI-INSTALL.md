# Signed Firefox XPI Installation, Upgrade, Rollback, and Uninstall

This flow is intentionally manual at the Firefox boundary. The bridge does not edit Firefox profile files or extension databases and does not synthesize browser input.

## Build a production package

1. Build the extension from the exact reviewed source SHA and submit that exact XPI source to Mozilla's add-on signing service.
2. Obtain the Mozilla-signed XPI without changing manifest.json, adapter_core.js, or background.js.
3. From the exact source checkout, run build-package.ps1 using the exact 40-character Git source SHA and -SignedXpiPath.
4. The builder rejects an XPI whose frozen extension ID, permission set, minimum Firefox version, data-collection declaration, or three production source files do not match the checkout.

The package builder binds source content and hashes. It does not claim to cryptographically validate Mozilla's signature. Firefox validates the signed XPI when you manually install it.

## First install

1. Run management\install.ps1 from the reviewed package.
2. The script prints the active XPI path.
3. In Firefox, open Add-ons and Themes, choose Install Add-on From File, select the printed XPI, and accept Firefox's normal signed-extension confirmation.
4. Confirm the installed add-on is Workspace Control Operator Browser Adapter with extension ID workspace-control-operator@adamtrott78.local.
5. Start the helper from the active release payload\helper\WorkspaceOperator.exe.

Do not use unsigned-extension bypasses, profile-file copying, enterprise-policy overrides, credential automation, or private browser databases.

## Upgrade

1. Build a new package from the new exact source SHA with a Mozilla-signed XPI.
2. Run that package's management\install.ps1. The old active release becomes previous_version.
3. Manually install the newly reported signed XPI through Firefox Add-ons and Themes.
4. Start the helper from the new active release.

There is no automatic self-updater.

## Rollback

1. Run %LOCALAPPDATA%\WorkspaceControl\OperatorBridge\management\rollback.ps1.
2. The script re-verifies the previous package, switches the native-host registration back to the previous helper, and prints the previous XPI path.
3. Manually install that previous signed XPI through Firefox Add-ons and Themes.
4. Start the helper from the restored active release.

Rollback never imports cookies, tokens, credentials, local storage, IndexedDB, or other profile data.

## Uninstall

1. In Firefox Add-ons and Themes, remove Workspace Control Operator Browser Adapter manually.
2. Run %LOCALAPPDATA%\WorkspaceControl\OperatorBridge\management\uninstall.ps1.
3. The script removes only the operator-owned install root and the dedicated HKCU native-host key. It fails closed if that registry key points outside the owned install root.
