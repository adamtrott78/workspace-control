<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json`

## Task
- ID: `workspace-github-actions-control-plane-protocol-redesign-v1`
- Status: IN_PROGRESS
- Parent: `workspace-lambda-self-hosted-execution-v1`

## Goal
Redesign the GitHub Actions self-hosted control plane as a typed protocol and explicit state machine rather than a chain of independently maintained string parsers.

## Immediate rule
No further Lambda control-plane mutation or validation retrigger while the system inventory/protocol model is incomplete. The current workspace-control CPU start-limit state is containment, not a reason to resume incremental hotfixing.

## Core architectural question
Which semantics belong to GitHub's scheduler/Runner Scale Set Client, which belong to our unprivileged controller, which belong to root policy, and which belong to the executor-facing request contract?

## Current hypothesis
The dominant architectural defect is that `jobDisplayName` became an authority-bearing serialization format. The same free-form request is parsed independently by the workflow, controller, and root policy. That creates protocol drift by construction.

## Next safe action
Map every producer, parser, serializer, validator, state transition, durable record, and retry boundary across workspace-control and research-engine; compare that graph against ARC/Runner Scale Set Client and other mature runner-manager architectures; then freeze a canonical typed protocol before implementation.
