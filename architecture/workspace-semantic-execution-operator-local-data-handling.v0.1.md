# Workspace Semantic Execution Operator Local Data Handling Rules v0.1

Status: **UX-08 SECURITY REVIEW CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

## Principle

Collect and retain only what is required to route a scheduler-selected action to the correct managed tab and recover local failures. Local state is disposable convenience state, never workflow truth.

## Allowed local durable-reference cache

Allowed:
- action ID/generation;
- logical slot ID/generation;
- payload ref and SHA-256;
- recovery incident ID;
- typed browser operation/result;
- redacted error class;
- timestamps/latencies.

Rules:
- cache is non-authoritative;
- restart reconciliation re-reads Workspace Control;
- stale cache cannot authorize a new action.

## Worker packet body

Allowed only:
- in helper process memory while preparing explicit Ctrl+B dispatch;
- in OS clipboard after final revalidation/staging.

Forbidden:
- packet body in logs, telemetry, extension storage, session values, local receipts, intentional crash diagnostics, or packet-history DB.

After staging, helper releases its packet-body reference. Restaging uses the durable payload ref.

Residual risk: v0 cannot know when the human pasted/submitted, so auto-clearing clipboard is unsafe; packet remains in clipboard until overwritten.

## Browser metadata

For managed worker tabs only:
1. process URL metadata in memory;
2. reduce immediately to `CHATGPT_ORIGIN`, `OFF_CHATGPT_ORIGIN`, or `UNKNOWN`;
3. report only enum + managed binding identity/timing.

Never retain:
- full URL/path/query/fragment;
- title/favicon;
- navigation history/auth-provider URL;
- DOM/text/output.

## Extension tab/session metadata

Allowed:
- opaque managed-binding ID;
- slot ID;
- generation;
- local lifecycle enum.

Forbidden:
- task secrets;
- prompt/response text;
- authorization material;
- credentials/tokens;
- durable Permission objects.

## Local configuration

Allowed:
- bridge ON/OFF preference;
- configured hotkey;
- fixed Firefox executable/profile;
- fixed extension/native-host IDs;
- fixed ChatGPT base origin;
- fixed OperatorBridge endpoint/transport selected by UX-12;
- later-reviewed telemetry preference.

Configuration cannot contain model-generated executable paths, arbitrary URLs, or plaintext credentials.

## Data never read/stored by v0

- pre-existing clipboard;
- ChatGPT conversation/Output;
- DOM/accessibility tree/screenshots;
- cookies/tokens/passwords/browser credential stores;
- localStorage/IndexedDB;
- raw HTTP bodies;
- arbitrary browsing history;
- global keystrokes beyond configured hotkey edge.

## Logging allowlist

Allowed fields:
- protocol/component version;
- request/correlation ID;
- action ID/generation;
- slot ID/generation;
- operation/result enum;
- redacted error class;
- payload hash/ref, never body;
- origin classification enum, never raw URL;
- timestamps/durations.

Every new log field is a data-collection change and must be reviewed.

## Storage protections and retention

- helper files user-scoped and not world-writable;
- no routine admin/root mutable state;
- extension state never authoritative;
- native-host manifest points to fixed reviewed executable;
- local corruption causes reconciliation/fail-closed recovery.

Design targets:
- packet body: memory/clipboard only;
- raw URL: callback scope only;
- session marker: managed-tab/session lifetime;
- local receipts/logs: bounded rolling diagnostic retention.

Exact limits are UX-12 implementation choices and may not weaken the prohibitions above.

## Privacy acceptance

The design requires no ChatGPT content collection, clipboard reading, credential collection, or general browsing-history collection. The only ChatGPT-facing observation is minimized origin classification for managed tabs in the dedicated profile.
