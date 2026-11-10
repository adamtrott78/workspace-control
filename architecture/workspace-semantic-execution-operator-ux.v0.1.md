# Workspace Semantic Execution Operator UX v0.1

Status: **PROPOSED / NON-AUTHORITATIVE UX DESIGN**

Parent task: `workspace-semantic-execution-migration-v1`

## 1. UX objective

The human-operated Chat Instant bridge should require essentially no interpretation.

Primary target loop:

```text
GLOBAL HOTKEY
→ orchestrator selects next operator action
→ browser focuses/creates/closes the correct worker tab
→ orchestrator loads the correct worker packet into clipboard
→ human presses Ctrl+V, Enter
→ return to normal work
```

The same global hotkey MUST be used for every scheduler-driven browser-management action.

The human should not:
- read tab titles to decide where to go;
- choose which worker is next;
- choose whether a new worker tab is needed;
- choose whether a worker tab should be retired;
- copy SHAs, JSON, result objects, logs, or experiment data;
- edit prompts;
- inspect scheduler state to decide what action to perform.

## 2. Proposed architecture

Use three cooperating pieces:

1. **Workspace Control orchestrator**
   - owns durable operator-action queue;
   - generates exact worker packets;
   - assigns logical worker/session slots;
   - decides reuse/create/retire;
   - validates durable worker output;
   - tracks progress and pending manual actions.

2. **Native operator helper**
   - lightweight local process;
   - owns the system-wide global hotkey;
   - requests the next operator action from Workspace Control;
   - writes the packet to the system clipboard only when the hotkey is pressed;
   - sends a small command to the Firefox extension through Native Messaging;
   - optionally exposes tray/taskbar status.

3. **Firefox WebExtension**
   - manages only browser/window/tab state;
   - creates, focuses, activates, discards, or removes assigned worker tabs;
   - maintains mapping from logical worker slot to Firefox tab/window ID;
   - shows a badge with pending operator-action count;
   - does NOT inject text into ChatGPT;
   - does NOT click Send;
   - does NOT scrape ChatGPT responses;
   - does NOT simulate keyboard/mouse behavior.

This split provides a true global hotkey without requiring the extension to behave like a bot on chatgpt.com.

## 3. Single-hotkey contract

Define one command, for example:

`Ctrl+Alt+Space`

Exact binding remains user-configurable.

On every press:

1. Native helper asks orchestrator for `next_operator_action`.
2. Orchestrator returns exactly one typed action.
3. Native helper loads `clipboard_payload` only when present.
4. Firefox extension performs the browser-management part.
5. Focus lands on the correct ChatGPT worker tab when human input is required.
6. Human performs `Ctrl+V`, `Enter`.

The hotkey's meaning is always:

> Perform the next scheduler-selected non-content action.

The human never needs to memorize action-specific hotkeys.

## 4. Operator action types

### SERVICE_EXISTING

Use an already assigned worker session.

Effect:
- focus Firefox worker window;
- activate the assigned worker tab;
- load next packet into clipboard;
- show short confirmation overlay/badge.

Human action:
- Ctrl+V
- Enter

### CREATE_AND_SERVICE

A new worker/session is required.

Effect:
- create a new ChatGPT tab in the designated worker window/profile;
- assign the new Firefox tab ID to the logical worker slot;
- focus the tab;
- load bootstrap/worker packet into clipboard.

Human action:
- Ctrl+V
- Enter

The extension does not attempt to choose a model by DOM automation. The worker browser/profile should be configured so the expected Chat Instant configuration is the normal/default setup, and the console should fail closed if the observed/manual setup does not match the required executor identity.

### RETIRE

A worker session is no longer needed.

Effect:
- close/remove the assigned browser tab;
- clear its session-slot mapping;
- no clipboard mutation unless the orchestrator intentionally combines retirement with the next service action.

Preferred optimization:
- retire obsolete tab and immediately advance to the next serviceable worker in the same hotkey press when safe, so retirement does not consume an extra operator action.

### ROTATE_AND_SERVICE

Context/session policy requires replacement.

Effect:
- retire or park old tab according to retention policy;
- create replacement worker tab;
- bind same/new logical slot as specified;
- focus replacement;
- load resume packet into clipboard.

Human action:
- Ctrl+V
- Enter

### NO_ACTION

Nothing requires human service.

Effect:
- do not steal focus;
- do not mutate clipboard;
- optional quiet notification such as “0 actions pending”.

### AUTHORITY_OR_JUDGMENT_GATE

The next step requires an actual human decision rather than mechanical transport.

Effect:
- open operator console;
- show the exact decision/gate;
- do NOT disguise it as an ordinary paste action.

## 5. Global-hotkey behavior

A Firefox extension shortcut alone is not sufficient for the desired UX because the operator wants the command to work while another application has focus.

The native helper therefore owns the OS-level hotkey.

When invoked from any application:
- it contacts the orchestrator;
- writes the packet to clipboard if required;
- asks Firefox to focus the dedicated worker window;
- asks the extension to activate/create/retire the assigned tab;
- returns focus to the worker tab ready for manual paste.

The helper MUST NOT intercept normal Ctrl+C/Ctrl+V behavior.
The clipboard changes only on the explicit orchestrator hotkey.

## 6. Clipboard behavior

Normal clipboard use must remain unaffected.

Rules:
- never modify clipboard in the background;
- only replace clipboard on explicit global-hotkey invocation when the next action requires a packet;
- store packet hash/action ID in local helper state, not in clipboard metadata;
- never read arbitrary clipboard contents unless a future feature explicitly requires it and the user enables it.

Optional later feature:
- save the pre-hotkey clipboard value locally and offer a separate restore command.
Do not automatically restore based on monitoring the ChatGPT page or user keystrokes.

## 7. Worker browser layout

Prefer one dedicated Firefox worker window or optional dedicated Firefox profile.

Logical slots:
- `instant-general-1`
- `instant-general-2`
- `critic-1`
- `synthesizer-1`
- future domain-specific slots only when justified

The user should never need to identify a slot by reading its tab title.

Workspace Control stores:
- logical slot ID;
- task/process affinity;
- executor identity requirement;
- Firefox tab ID;
- Firefox window ID;
- session generation;
- durable checkpoint last acknowledged;
- state: ACTIVE / IDLE / ROTATE / RETIRE / LOST.

Do not depend on the visible ChatGPT conversation title for routing.

## 8. Persistent indicator

Provide at least one always-visible count.

Preferred options:
- system-tray/taskbar icon from native helper;
- Firefox extension badge;
- optional tiny always-on-top status widget.

Minimum badge:
- total pending manual actions.

Expanded status:
- `3 actions`
- `1 new chat`
- `2 existing chats`
- `0 judgment gates`

The primary count should be the number of hotkey/paste cycles the user can service now.

Example:

```text
READY: 4
NEW: 1
REUSE: 3
GATES: 0
```

After each worker writes durable state and the orchestrator advances, the indicator updates without the user reading worker tabs.

## 9. Batch-service mode

The intended daily interaction is:

```text
see badge: 6
hotkey
Ctrl+V Enter
hotkey
Ctrl+V Enter
hotkey
Ctrl+V Enter
...
badge: 0
return to normal work
```

The operator does not press “continue” in the orchestrator.

The hotkey MUST always fetch fresh scheduler state before acting so the queue can change between worker submissions.

Do not pre-stage a long blind sequence of packets whose validity depends on previous workers completing.

## 10. RAM / browser resource policy

Avoid dozens of simultaneously live ChatGPT tabs.

Policy:
- keep only a small active session pool;
- retire completed sessions promptly;
- allow Firefox to auto-discard inactive tabs;
- explicitly discard inactive/parked worker tabs when safe;
- reload discarded tabs only when they are the next scheduled worker;
- avoid a heavy extension background process;
- use event-driven WebExtension background handling;
- store state in the orchestrator/native helper, not in many live pages.

Suggested initial active-session cap:
- 2 general Instant sessions;
- 1 critic slot only while required;
- 1 synthesizer slot only while required.

This cap should be benchmarked rather than assumed permanent.

## 11. OpenAI-safe automation boundary

The bridge should stay deliberately conservative.

Allowed local/browser-management automation target:
- open a browser tab;
- focus a Firefox window;
- activate a tab;
- close a tab;
- discard/reload a tab;
- write the orchestrator-generated packet to the local clipboard;
- display local status/badges.

Explicitly out of scope:
- injecting text into ChatGPT's input box;
- programmatically clicking Send;
- simulating keypresses/mouse motion on ChatGPT;
- reading/scraping model output from the ChatGPT page;
- inspecting hidden DOM/network state to infer completion;
- attempting to mimic human timing;
- bypassing rate limits, safeguards, account restrictions, or usage limits.

Worker completion is detected from the worker's authorized durable GitHub/state mutation, not from scraping the ChatGPT UI.

This boundary is intended to minimize account risk, but no implementation can guarantee that OpenAI will never change product rules. Re-check current OpenAI terms/documentation before release or any expansion of the browser-facing behavior.

## 12. Extension permissions minimization

Aim for the narrowest Firefox permissions compatible with tab management.

Likely permissions:
- `tabs`
- `clipboardWrite`
- `nativeMessaging`
- extension storage

Avoid ChatGPT host/content-script permissions unless a later reviewed feature demonstrates a necessary supported use.

The extension should not need page-content access for the v0 UX.

## 13. UX acceptance criteria

A workflow qualifies for the low-attention bridge when:

- the same global hotkey handles all routine browser/session actions;
- the user never searches tab titles manually;
- the user never chooses the next worker;
- the user never manually copies scheduler-generated prompts;
- the user never relays worker result state back to the orchestrator;
- one worker service cycle requires at most:
  - one global hotkey;
  - Ctrl+V;
  - Enter;
- ordinary clipboard behavior remains unaffected outside the global hotkey;
- a persistent count shows serviceable manual actions;
- tab rotation/retirement is scheduler-driven;
- session loss is recoverable from durable state;
- no consumer ChatGPT content automation is required;
- active browser memory remains bounded by a small worker-session pool.

## 14. Build order

1. Specify `OperatorAction` schema.
2. Implement orchestrator-side operator-action queue.
3. Prototype native helper with global hotkey + clipboard write.
4. Prototype Firefox extension with native messaging + focus/create/remove/activate tab.
5. Implement logical slot ↔ tab mapping.
6. Add extension badge and tray indicator.
7. Add small worker-window/session pool.
8. Add tab discard/retire policy.
9. Integrate with session broker.
10. Run a fake-ChatGPT local web-page simulation first.
11. Test with real ChatGPT only after confirming that the extension performs no page-content automation.
12. Measure manual actions, wrong-tab rate, RAM usage, and recovery effort.

## 15. Success experience

The desired operator experience is:

> I see that several workers need service. I repeatedly press one hotkey, then Ctrl+V and Enter. Workspace Control decides whether that hotkey focuses an existing worker, creates a new worker, rotates a worker, or retires an obsolete tab. I do not read tab titles, edit prompts, relay state, or manage the queue. When the count reaches zero, I return to what I was doing.
