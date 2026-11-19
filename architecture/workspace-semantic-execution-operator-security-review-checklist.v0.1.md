# Workspace Semantic Execution Operator Security Review Checklist v0.1

Status: **UX-08 SECURITY REVIEW CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Every MUST item must pass before production-worthy implementation. Any permission/interaction-boundary expansion reopens UX-08.

## Authority/state

- [ ] Browser/helper state is non-authoritative.
- [ ] Model/semantic output cannot create Permission, remove Prohibition, satisfy ReviewRequirement, or mint execution authority.
- [ ] Every local operation is bound to action ID/generation and slot ID/generation.
- [ ] Unknown continuity fails closed.
- [ ] Old-generation results cannot advance current state.
- [ ] Local preparation never implies durable acknowledgment.

## Firefox manifest

- [ ] Required permissions are exactly `nativeMessaging`, `tabs`, `sessions`.
- [ ] `host_permissions` absent/empty.
- [ ] `optional_host_permissions` absent/empty.
- [ ] No `content_scripts`.
- [ ] No `activeTab`, `scripting`, `webNavigation`, `webRequest`, `cookies`, `clipboardRead`, or `clipboardWrite`.
- [ ] No `externally_connectable`.
- [ ] Fixed packaged extension ID matches Native Messaging allowlist.
- [ ] Manifest diff is security-reviewed.

## Browser behavior

- [ ] Only bridge-managed tabs are operated on.
- [ ] Arbitrary existing ChatGPT tabs are not adopted.
- [ ] Create/navigate target is fixed reviewed ChatGPT base origin, never model/task text.
- [ ] Raw tab ID is not durable identity.
- [ ] Managed tabs carry non-authoritative slot/generation marker via `sessions`.
- [ ] URL metadata is reduced immediately to CHATGPT_ORIGIN/OFF_CHATGPT_ORIGIN/UNKNOWN.
- [ ] Full URL/path/query/fragment/title/favicon are not persisted/logged.
- [ ] No DOM/accessibility/screenshot/page-source/output inspection.
- [ ] Off-origin/unknown managed-tab navigation triggers fail-closed recovery.

## Native helper

- [ ] Standard-user execution; no routine admin/root.
- [ ] Only configured global hotkey is registered.
- [ ] No global keystroke logging.
- [ ] Clipboard access is write-only.
- [ ] Previous clipboard is never read/snapshotted.
- [ ] No UIAutomation/SendInput/synthetic mouse/keyboard.
- [ ] Firefox executable/profile comes only from reviewed local config.
- [ ] No browser profile cookie/token/password DB parsing.
- [ ] Native host allows only exact extension ID.
- [ ] Extension messages cannot claim work or command authority-affecting helper actions.
- [ ] Any additional IPC is authenticated/bounded/reviewed.

## Packet/logging privacy

- [ ] Packet body is memory/clipboard only.
- [ ] Receipts contain only IDs/generations/refs/hashes/enums/timestamps/redacted errors.
- [ ] Credentials/tokens/passwords are never stored.
- [ ] Raw URLs and ChatGPT Output are never logged.
- [ ] Logs are bounded/rotated.
- [ ] Crash diagnostics are content-redacted.

## OpenAI interaction boundary

- [ ] Current Terms reviewed before first real-account test.
- [ ] Current Usage Policies/product guidance reviewed before first real-account test.
- [ ] No automatic/programmatic extraction of ChatGPT data or Output.
- [ ] No automatic paste/submit/Send.
- [ ] No synthetic typing/mouse/human-mimic interaction.
- [ ] No private ChatGPT endpoint/request replay.
- [ ] No rate-limit/restriction/CAPTCHA/auth/safety safeguard circumvention.
- [ ] Product block causes stop/fail-closed, not evasion.
- [ ] Real-account tests preserve manual Ctrl+V + Enter.

## Recovery/security tests

- [ ] Tab ID reuse cannot rebind stale generation.
- [ ] Extension restart with lost mapping yields UNKNOWN/rotation.
- [ ] Firefox crash/restart reconciles durable state.
- [ ] All-tabs auth refresh freezes reuse and advances generations only once.
- [ ] Late old-generation ack cannot advance current state.
- [ ] Stale/replayed native message rejected.
- [ ] Unknown/duplicate correlation ID rejected.
- [ ] Wrong profile rejected.
- [ ] Arbitrary URL command rejected.
- [ ] Clipboard failure never presents READY_TO_PASTE.
- [ ] Helper crash during claim cannot auto-requeue ambiguous local effects.

## Change-control gate

- [ ] Any request for page content, host permission, scripting, webNavigation, webRequest, cookies, clipboard read, synthetic input, broader OS privilege, or new network listener is a new security architecture decision.
- [ ] UX-13 confirms no unresolved security/interaction blocker.

## Current assessment

Design review: **PASS**.

Implementation verification: **NOT YET RUN**; owned by UX-10/UX-12/UX-13.
