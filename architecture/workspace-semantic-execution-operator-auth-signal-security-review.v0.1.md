# Workspace Semantic Execution Browser Navigation and Authentication Signal Review v0.1

Status: **UX-08 SECURITY/PRIVACY REVIEW CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

## Question

Can the bridge detect a likely login/navigation disruption without reading ChatGPT page content?

**Yes, at the browser-chrome metadata layer, with limits.**

Firefox exposes tab lifecycle and URL-change metadata through the Tabs API. The `tabs` permission allows access to `Tab.url`, and `tabs.onUpdated` can report URL changes. Firefox tab IDs are session-local and may be reused after restart; `sessions.setTabValue` / `getTabValue` provide a safer non-authoritative binding marker.

Reviewed evidence:
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/onUpdated
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/sessions/setTabValue
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/sessions/getTabValue
- https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging
- https://support.mozilla.org/en-US/kb/profile-manager-create-remove-switch-firefox-profiles

## v0 permission decision

Do **not** request `webNavigation` in v0.

Reason:
- v0 already needs `tabs` for managed-tab URL metadata/inventory;
- `tabs.onUpdated` can detect URL changes;
- adding `webNavigation` widens API surface without a demonstrated requirement.

Also do not request host permissions, `activeTab`, `scripting`, content scripts, `webRequest`, or `cookies`.

UX-12 must validate exact target-version behavior.

## Metadata minimization algorithm

For a tab already carrying the bridge-managed slot/generation marker:

```text
receive tab URL metadata
  |
  +-- unavailable/parse failure -> UNKNOWN
  |
  +-- origin == configured ChatGPT base origin -> CHATGPT_ORIGIN
  |
  +-- otherwise -> OFF_CHATGPT_ORIGIN

discard raw URL immediately
emit only classification + managed binding identity + local time
```

Do not inspect page title, pathname semantics, query parameters, fragments, DOM, rendered text, forms, or auth-provider contents.

## Recovery signal interpretation

### AUTH_NAVIGATION_DETECTED

Candidate implementation:
- a managed worker tab changes from CHATGPT_ORIGIN to OFF_CHATGPT_ORIGIN or UNKNOWN.

Effect:
- treat the WorkspaceWorkers authentication/continuity domain as suspect;
- freeze reuse per UX-07;
- do not infer why navigation occurred;
- do not automate authentication.

False positive is acceptable because the dedicated profile exists only for managed worker sessions and recovery is fail-closed.

### AUTH_RETURN_ORIGIN_OBSERVED

Candidate implementation:
- managed/recovery tab returns to CHATGPT_ORIGIN.

Effect:
- permit durable reconciliation;
- do not restore old generations to TRUSTED;
- do not infer authentication success.

### OPERATOR_REPORT_AUTH_REFRESH

Required fallback when:
- metadata is ambiguous;
- Firefox behavior changes;
- extension unavailable;
- operator visibly observes login/all-tabs refresh.

## Origin return is not continuity proof

A `chatgpt.com` URL does not prove:
- which conversation is loaded;
- whether account/session survived;
- whether prior context survived;
- whether packet was submitted;
- whether correct model/tool configuration is active.

Old generations therefore remain fenced. Replacement sessions recover from the last durable acknowledged checkpoint.

## OpenAI interaction-boundary review

Reviewed 2026-11-09.

Terms effective 2026-01-01 prohibit automatically/programmatically extracting data or Output and prohibit circumventing rate limits/restrictions/protective measures:
https://openai.com/policies/terms-of-use/

Current Usage Policies revision effective 2025-10-29 prohibits circumventing safeguards:
https://openai.com/policies/usage-policies/revisions/2025-10-29/

Announced revision effective 2026-11-20 was reviewed for forward compatibility:
https://openai.com/policies/usage-policies/

OpenAI documents browser automation as a product-specific capability in ChatGPT Work:
https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt

That product-specific surface is not treated as authorization to automate the ordinary consumer ChatGPT page. v0 remains manual at the content boundary.

## Allowed/forbidden ChatGPT-facing mechanics

Allowed:
- launch/focus dedicated Firefox profile;
- create tab at configured ChatGPT base origin;
- activate/reload/discard/close managed tab;
- observe minimized origin classification;
- hand control to user with exact packet on clipboard.

Forbidden:
- DOM/content read or response extraction;
- composer injection;
- automatic paste/typing/Enter/Send;
- synthetic clicks intended to mimic a person;
- authentication/CAPTCHA automation;
- private endpoint/request replay;
- product-limit/safeguard circumvention.

## UX-08 conclusion

The UX-07 auth/navigation recovery concept is **security-approved as a metadata-only design candidate** using the already-required Tabs API, with raw-URL minimization and operator fallback.

It is **not yet technically frozen**. UX-12 owns exact Firefox/API behavior validation and the pre-real-account OpenAI-policy re-check.
