# ADR — Firefox MV3 Baseline and Conditional WebView2 Worker Shell v0.1

Status: **ACCEPTED FOR UX-12 IMPLEMENTATION BASELINE**

Parent: `workspace-semantic-execution-migration-v1`

Supersedes the implementation uncertainty in:
- `architecture/workspace-semantic-execution-operator-adr-dedicated-firefox-profile.v0.1.md`

Does not supersede the UX-08 security boundary.

## Decision

Implement **Firefox + WebExtension** as the v0 production browser-adapter baseline.

Implement a **bounded WebView2 custom worker-shell spike** behind the same BrowserPort, but do not promote it unless authentication, security, recovery, performance, and usability gates all pass.

Firefox remains a baseline, not a permanent architectural dependency.

## Firefox target

Target:
- Firefox desktop;
- dedicated `WorkspaceWorkers` profile;
- minimum supported version: **Firefox ESR 153.0**;
- Manifest Version 3;
- one background event-page script in plain JavaScript;
- no content scripts;
- no host permissions.

Firefox ESR 153 is the current ESR family as of this UX-12 review.

## Exact MV3 shape

Candidate manifest core:

```json
{
  "manifest_version": 3,
  "name": "Workspace Control Operator Browser Adapter",
  "version": "0.1.0",
  "permissions": ["nativeMessaging", "tabs", "sessions"],
  "background": {
    "scripts": ["background.js"],
    "persistent": false
  },
  "browser_specific_settings": {
    "gecko": {
      "id": "workspace-control-operator@adamtrott78.local",
      "strict_min_version": "153.0",
      "data_collection_permissions": {
        "required": ["none"]
      }
    }
  }
}
```

No:
- `host_permissions`;
- `optional_host_permissions`;
- `content_scripts`;
- `activeTab`;
- `scripting`;
- `webNavigation`;
- `webRequest`;
- `cookies`;
- extension clipboard permission;
- `externally_connectable`.

Firefox MV3 currently uses `background.scripts`/event pages; extension background service workers are not supported. Do not build the Firefox adapter around `background.service_worker`.

References:
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/background
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/browser_specific_settings

## Validated Firefox API usage

### Native Messaging

Use:
`browser.runtime.connectNative("com.workspacecontrol.operator_bridge")`

The Native Messaging host manifest:
- has `type: "stdio"`;
- points to the fixed installed helper executable path;
- contains exactly the packaged extension ID in `allowed_extensions`;
- is registered under user-scoped Firefox NativeMessagingHosts on Windows.

Reference:
https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging

### Managed-tab URL metadata

The `tabs` permission permits `Tab.url` access without host permissions.

The adapter may inspect URL metadata **only for already-managed bindings** and must immediately reduce it to:
- `CHATGPT_ORIGIN`;
- `OFF_CHATGPT_ORIGIN`;
- `UNKNOWN`.

No raw URL is persisted or sent across the bridge.

`tabs.onUpdated` is sufficient for managed-tab lifecycle/origin updates; `webNavigation` remains unnecessary.

References:
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/onUpdated

### Non-authoritative binding metadata

Use:
- `sessions.setTabValue`;
- `sessions.getTabValue`;
- `sessions.removeTabValue`.

Stored values are bounded opaque metadata:
- slot ID;
- session generation;
- adapter binding generation/version.

Never packet bodies, raw URLs, credentials, or durable authority.

Reference:
https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/sessions/setTabValue

### Discard

Use `tabs.discard` only for managed, inactive, trusted idle bindings.

The active tab is not discardable, and pages with a prompting `beforeunload` handler may resist discard. Treat refusal as a local operation result, not authority failure.

Reference:
https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/discard

## Extension language/tooling

Use **plain JavaScript** with:
- one background script initially;
- JSDoc typedefs generated/checked against the versioned JSON protocol schema;
- no bundler;
- no remote code;
- no npm runtime dependency.

If extension code grows beyond the bounded adapter role, TypeScript may be introduced later through a reviewed build-only toolchain without changing browser permissions.

## Extension signing/distribution

Release/Beta Firefox requires signed extensions.

v0 distribution:
- sign through AMO as **unlisted/self-distributed**;
- use the fixed extension ID above, subject only to one-time AMO uniqueness acceptance;
- install the signed XPI into the dedicated profile;
- no unsigned-production bypass;
- no disabling signature enforcement.

References:
- https://extensionworkshop.com/documentation/publish/signing-and-distribution-overview/
- https://extensionworkshop.com/documentation/publish/install-self-distributed/

Update policy for v0:
- explicit reviewed signed-XPI replacement;
- no custom automatic `update_url` until a separate supply-chain review.

## Dedicated profile launch

The helper uses reviewed local configuration for the `WorkspaceWorkers` profile and a fixed Firefox executable path.

Rules:
- no task/model-supplied profile path;
- no arbitrary task/model-supplied URL;
- never parse Firefox profile databases;
- arbitrary user tabs are not adopted;
- profile launch/inventory failure enters recovery.

The concrete launch implementation must test both named-profile and explicit-profile-path forms on the target Windows host before release. The selected installed profile path becomes local configuration, not durable workflow identity.

## WebView2 custom worker-shell spike

### Stack

If built:
- .NET 10;
- WinForms WebView2;
- Evergreen WebView2 Runtime;
- one shared `CoreWebView2Environment`;
- one dedicated WorkspaceWorkers user-data folder;
- multiple worker views/tabs behind the same BrowserPort;
- no DOM/script injection into ChatGPT.

Microsoft recommends Evergreen and sharing one environment to reduce duplicated resource overhead.

References:
- https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/performance
- https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/process-model

### Authentication hard gate

The shell must complete the operator's normal ChatGPT sign-in path manually, including any external identity-provider redirects used by that account.

It is **rejected** if successful sign-in would require:
- cookie/session copying from another browser;
- token extraction/import;
- request replay;
- private endpoints;
- user-agent spoofing intended to evade a block;
- bypass of an identity-provider/browser restriction.

Google documents `disallowed_useragent` for OAuth shown in embedded user-agents. This makes authentication feasibility a real gate, not an assumption:
https://developers.google.com/identity/protocols/oauth2/web-server

### Promotion gate

The custom shell may replace Firefox only if all are true:
1. normal manual authentication works without workaround;
2. UX-08 security checklist still passes;
3. UX-10 adapter-parity scenarios pass;
4. UX-09 target-machine measurements meet budgets;
5. it beats Firefox materially under the frozen review trigger;
6. UX-11 human-in-loop usability is no worse;
7. Evergreen runtime/update behavior is acceptable.

Otherwise Firefox remains production baseline.

## OpenAI boundary re-check

OpenAI's current individual Terms, reviewed again during UX-12, prohibit automatic/programmatic extraction of data or Output and circumvention of restrictions/protective measures.

Therefore neither browser adapter may:
- scrape Output;
- inspect ChatGPT DOM/content;
- synthesize paste/typing/Send;
- call private consumer endpoints;
- bypass a block.

Current reference:
https://openai.com/policies/terms-of-use/

OpenAI's supported browser automation in ChatGPT Work/desktop browser is product-specific and does not widen this custom consumer-UI bridge's permissions.

## Consequences

The baseline extension can now be implemented without browser-stack ambiguity.

Reopen if:
- target Firefox APIs behave differently in the implementation spike;
- extension signing/deployment cannot be made reliable;
- real-account auth/navigation behavior invalidates the metadata-only recovery signal;
- the WebView2 spike clears every promotion gate.
