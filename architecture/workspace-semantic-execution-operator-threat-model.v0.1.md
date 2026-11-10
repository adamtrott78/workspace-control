# Workspace Semantic Execution Operator Bridge Threat Model v0.1

Status: **UX-08 SECURITY REVIEW CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

## Security objective

Preserve the routine operator rhythm:

```text
Ctrl+B
Ctrl+V
Enter
```

while ensuring browser/helper convenience cannot become execution authority, cannot read ChatGPT content, cannot extract model Output, cannot bypass product safeguards, and cannot turn stale local state into a valid control transition.

The bridge is a convenience adapter around Workspace Control. Durable task/workflow state, authority, generation fencing, and durable acknowledgments remain outside Firefox and the native helper.

## Reviewed interaction boundary

Allowed in v0:
- register/unregister the configured global hotkey;
- launch/focus the dedicated Firefox `WorkspaceWorkers` profile;
- create, activate, reload, discard, or close bridge-managed worker tabs;
- associate opaque logical slot/generation metadata with managed tabs;
- observe browser-chrome URL metadata for managed tabs only and immediately reduce it to an allowlisted origin classification;
- write the scheduler-selected worker packet to the OS clipboard after action/generation revalidation;
- show tray/console status and recovery guidance;
- exchange typed messages with the exact native-messaging peer;
- report local operation receipts/recovery signals to Workspace Control.

The human remains responsible for Ctrl+V, Enter, authentication, and substantive judgment/authority gates.

Forbidden in v0:
- ChatGPT DOM/accessibility-tree/rendered-text/conversation/response/page-source/screenshot/network-body inspection;
- composer injection or response extraction;
- synthetic typing/mouse/paste/Enter/Send;
- undocumented/private ChatGPT consumer endpoints or request replay;
- cookies/localStorage/IndexedDB/auth-token/password/profile-credential access;
- automatic/programmatic extraction of ChatGPT data or Output;
- rate-limit, restriction, CAPTCHA, authentication, safety-mitigation, or other safeguard circumvention;
- arbitrary user ChatGPT-tab adoption;
- treating model/browser/URL/semantic state as execution authority.

## Current OpenAI-policy review

Reviewed 2026-11-09:
- Terms of Use, effective 2026-01-01: https://openai.com/policies/terms-of-use/
- current Usage Policies revision, effective 2025-10-29: https://openai.com/policies/usage-policies/revisions/2025-10-29/
- announced Usage Policies update effective 2026-11-20: https://openai.com/policies/usage-policies/
- ChatGPT Work cloud-browser guidance: https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt

Conclusion:
- Terms prohibit automatically/programmatically extracting data or Output and prohibit circumventing rate limits/restrictions/protective measures;
- current Usage Policies prohibit circumventing safeguards;
- a supported automated browser surface in ChatGPT Work is product-specific and is not treated as permission to automate the ordinary consumer ChatGPT page;
- v0 therefore stays outside ChatGPT content and submission mechanics.

Before any real-account implementation test, UX-12 MUST re-check then-current OpenAI terms/product guidance. If product behavior blocks the bridge, fail closed rather than evade it.

## Assets and trust boundaries

Security-critical assets:
- durable task/workflow/authority state;
- OperatorAction lifecycle;
- logical session slot/generation;
- worker packet confidentiality/integrity;
- durable acknowledgment;
- ChatGPT account/session credentials;
- clipboard;
- local non-authoritative receipts/cache;
- managed-tab binding;
- native-helper/WebExtension channel.

Trust boundaries:
1. Workspace Control ↔ native helper.
2. Native helper ↔ WebExtension through Native Messaging.
3. WebExtension ↔ Firefox browser chrome.
4. Browser chrome ↔ untrusted web content.
5. Native helper ↔ OS clipboard/hotkey/window facilities.
6. Local non-authoritative state ↔ durable authoritative state.
7. Human operator ↔ ChatGPT page.

Web content is always untrusted. No content-script bridge crosses that boundary.

## Threats and controls

| ID | Threat | Required control |
|---|---|---|
| T-01 | Malicious webpage commands helper | no content scripts; no externally-connectable page channel; Native Messaging only from fixed extension ID |
| T-02 | Compromised extension acts as confused deputy | helper treats extension as browser adapter only; results must match outstanding request IDs; extension cannot claim work, mint authority, or command clipboard writes |
| T-03 | Stale/replayed browser command | protocol version + correlation/request ID + action ID + slot + generation; current-generation revalidation |
| T-04 | Tab ID reuse | raw tab ID never durable identity; use `sessions.setTabValue` slot/generation marker; mismatch => UNKNOWN |
| T-05 | Arbitrary URL opening | fixed reviewed ChatGPT base origin only; never model/task-supplied URL |
| T-06 | Auth/navigation metadata leaks secrets | managed tabs only; classify URL in memory as CHATGPT_ORIGIN/OFF_CHATGPT_ORIGIN/UNKNOWN; never persist raw URL/path/query/fragment/title/favicon |
| T-07 | Credential theft | no cookies/host permissions/content scripts/webRequest/profile DB access/clipboard read |
| T-08 | Clipboard leakage | write only after explicit Ctrl+B/final revalidation; never read prior clipboard; packet body not logged |
| T-09 | Wrong packet/target | action/gen/payload-ref/SHA binding; clipboard success check; final focus after staging |
| T-10 | Synthetic-input creep | no UIAutomation/SendInput/scripting/content permissions; manual Ctrl+V + Enter invariant |
| T-11 | Local IPC abuse | Native Messaging exact extension allowlist; no unauthenticated non-loopback listener |
| T-12 | Model output widens authority | helper/extension accept only already-authorized typed OperatorActions |
| T-13 | Safeguard circumvention | no auto-submit/request replay/stealth/human-mimic automation |
| T-14 | Sensitive logs | IDs/enums/timings/hashes/error classes only; no packet body/output/raw URLs/credentials |
| T-15 | Permission creep | manifest/helper privilege diff blocks release without security review |

Residual clipboard risk is explicit: v0 cannot know when manual paste occurred, so it cannot safely auto-clear the clipboard.

## Security invariants

1. Browser-local state is never authoritative.
2. Unknown continuity fails closed.
3. Local preparation cannot become durable acknowledgment without durable evidence.
4. Old-generation evidence cannot advance current control state.
5. No ChatGPT content crosses into the bridge.
6. No webpage can directly invoke the native helper.
7. Extension messages cannot create scheduler authority.
8. No clipboard read is required.
9. No automatic submit is permitted.
10. Permission expansion requires a reviewed change.
11. Product blocks/restrictions are never bypassed.
12. Recovery reconstructs from durable Workspace Control state, not browser contents.

## Acceptance assessment

UX-08 threat-model acceptance: **PASS at design level**.

Technical API/package validation remains UX-12, including a fresh OpenAI-policy review before any real-account test.
