# ADR — Native Helper + Firefox WebExtension Split v0.1

Status: **ACCEPTED FOR UX DESIGN BASELINE / NOT IMPLEMENTATION-FROZEN**

Parent: `workspace-semantic-execution-migration-v1`

## Context

The operator bridge needs:
- a system-global hotkey available while Chrome, VS Code, Jupyter, or another application has focus;
- Windows system-tray presence;
- clipboard staging;
- Firefox worker-tab creation/focus/retirement/discard;
- no ChatGPT page-content automation.

A Firefox extension alone is the wrong owner for OS-global concerns. A native process alone is the wrong owner for browser-chrome extension APIs and would push implementation toward fragile UI automation.

## Decision

Split the adapter into:

1. **Native Operator Helper**
   - Windows-global hotkey;
   - master bridge toggle;
   - clipboard;
   - tray/console shell;
   - local dispatch receipts;
   - browser-adapter command initiation.

2. **Firefox WebExtension**
   - worker-profile/window/tab inventory;
   - create/activate/remove/discard/reload tabs;
   - ephemeral tab/window mappings;
   - browser-operation receipts.

The logical interface between them is a typed BrowserPort. Concrete IPC/Native Messaging topology is deferred to UX-12.

## Consequences

Positive:
- clean separation of OS and browser responsibilities;
- least privilege;
- easier testing with fake BrowserPort/HotkeyPort;
- future browser replacement does not affect orchestration core;
- no need for desktop mouse/keyboard automation.

Costs:
- two local components and an IPC boundary;
- packaging/update complexity;
- reconnect/restart scenarios must be designed.

## Rejected alternatives

### Firefox extension only
Rejected because a robust always-available system-global hotkey/tray/OS integration should not be coupled to browser focus/lifecycle.

### Native desktop automation only
Rejected because controlling Firefox tabs via generic desktop UI automation is less reliable, less testable, and more likely to cross into prohibited content interaction.

### Automate ChatGPT DOM directly
Rejected for v0 due safety/product-policy risk and because it makes the adapter depend on consumer-page implementation details.

## Revisit conditions

Revisit if:
- OpenAI provides a supported programmatic Chat Instant invocation surface;
- Firefox exposes a sufficiently robust supported global operator surface that removes the native helper need;
- target OS changes.

