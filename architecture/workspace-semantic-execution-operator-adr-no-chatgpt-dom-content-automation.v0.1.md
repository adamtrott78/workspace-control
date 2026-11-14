# ADR: No ChatGPT DOM or Content Automation in Operator Bridge v0

Status: **ACCEPTED FOR UX-08 DESIGN BASELINE**

Parent task: `workspace-semantic-execution-migration-v1`

## Context

The operator bridge reduces mechanical attention while preserving:

```text
Ctrl+B
Ctrl+V
Enter
```

The bridge does not need ChatGPT page contents to select work, compile packets, choose session generations, detect durable completion, or recover authoritative task state.

Current OpenAI Terms prohibit automatically/programmatically extracting data or Output and prohibit circumventing rate limits/restrictions/protective measures. Browser-content automation would also increase credential/privacy and prompt-injection attack surface.

Firefox browser-chrome APIs are sufficient for v0 tab lifecycle/focus, metadata-only origin classification, and Native Messaging.

## Decision

v0 SHALL NOT automate or inspect ChatGPT page content.

v0 SHALL NOT include:
- ChatGPT content scripts;
- ChatGPT/OpenAI host permissions;
- `activeTab`;
- `scripting`;
- `webNavigation` unless a future reviewed requirement proves `tabs.onUpdated` insufficient;
- `webRequest`;
- cookie/storage access;
- DOM/accessibility reads;
- screenshots/pixel inspection;
- conversation/response extraction;
- composer injection;
- automatic paste/typing;
- Send/Enter clicking or synthetic input;
- private consumer endpoint calls;
- human-mimic/stealth behavior.

The human remains the content-boundary actor for paste and submit.

The only ChatGPT-facing observation allowed in v0 is browser-chrome metadata for bridge-managed tabs, reduced immediately to an origin classification and never treated as continuity or execution proof.

## Consequences

Benefits:
- least privilege;
- no automated Output extraction;
- no page prompt-injection command channel into helper;
- less coupling to ChatGPT DOM changes;
- durable acknowledgment stays outside browser;
- browser adapter remains replaceable;
- explicit human submission remains.

Costs:
- bridge cannot know whether Ctrl+V/Enter occurred;
- SENT/UNCONFIRMED remains necessary;
- auth recovery may require operator fallback;
- executor/model configuration cannot be scraped;
- some ergonomics remain manual.

These costs are intentional and already handled by UX-03/04/05/07.

## Upgrade gate

Any future proposal to read ChatGPT content or automate submission requires:
1. new ADR superseding this one;
2. current OpenAI terms/product-guidance review;
3. explicit threat/privacy review;
4. least-privilege permission analysis;
5. proof the behavior is supported/allowed for selected product surface;
6. updated simulator/usability/security tests;
7. explicit task authority for expanded scope.

Absent those conditions: **NO_BY_DEFAULT**.
