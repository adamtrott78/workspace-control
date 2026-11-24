# Workspace Semantic Execution Operator Usability Feedback Checklist v0.1

Status: **UX-11 OPERATOR FEEDBACK CONTRACT CANDIDATE**

Parent task: `workspace-semantic-execution-migration-v1`

Use after each human-in-loop usability trial. Record no packet contents, ChatGPT text, passwords, or unrelated work content.

## Trial identification

- Trial ID:
- Adapter ID/version:
- Configured scheduler hotkey:
- Date/time:
- Result: PASS / FAIL / INVALID

## Objective counters

- Intended service actions:
- Valid durable acknowledgments:
- Wrong-worker dispatches:
- Wrong-packet dispatches:
- Manual tab searches:
- Manual prompt edits:
- Routine scheduler-state interpretation events:
- Abandoned cycles:
- Manual durable-state relay events:
- Recovery state-reconstruction events:
- Accidental scheduler dispatches:
- Required application-local shortcut collisions:
- Unexpected background focus steals:
- Unexpected background clipboard mutations:

Any nonzero wrong-worker, wrong-packet, stale-generation advancement, automatic resend, background focus steal, or background clipboard mutation is a hard failure.

## 1–7 ratings

Use:
- 1 = none / extremely easy / no interference
- 7 = severe / extremely difficult / severe interference

For confidence/clarity questions:
- 1 = no confidence / unclear
- 7 = complete confidence / completely clear

### Routine trials

- Routine rhythm friction (target <=2):
- Clipboard disruption concern (target <=2):
- Worker-selection confidence (target >=6):
- Scheduler-state clarity (target >=6):

### Recovery trials

- Recovery clarity (target >=6):
- State-reconstruction burden (target <=2):
- Confidence that old/stale workers would not be reused (target >=6):

### Hotkey trial

- Hotkey interference with normal work (target <=2):
- Physical comfort of repeated scheduler-hotkey → Ctrl+V → Enter rhythm (target >=6):

## Yes/no questions

- Did you ever manually choose which worker/tab should receive the next packet? YES / NO
- Did you ever inspect multiple worker tabs to reconstruct system state? YES / NO
- Did you ever edit a generated worker packet before pasting? YES / NO
- Did you ever hesitate because you were unsure what Ctrl+B would do? YES / NO
- Did the system ever move focus without an explicit scheduler/recovery/judgment action? YES / NO
- Did recovery return you to the ordinary scheduler-hotkey → Ctrl+V → Enter loop? YES / NO / N/A
- Would you keep the current scheduler hotkey for daily use? YES / NO

## Hotkey decision

`Ctrl+B` (or the current candidate) is retained only if:
- accidental scheduler dispatches = 0;
- required native shortcut collisions = 0;
- interference <=2/7.

If rejected:
- replacement binding tested:
- reason:
- required reruns completed: UT-01 / UT-02 / UT-03 / UT-09 / UT-10

## Optional redacted notes

Describe friction, confusion, or desired presentation changes without reproducing packet contents, worker responses, credentials, or unrelated work content.
