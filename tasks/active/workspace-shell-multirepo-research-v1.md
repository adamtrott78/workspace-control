<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-multirepo-research-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-multirepo-research-v1
- Title: Workspace Shell multi-repo PADataset research access v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Extend the live Workspace Shell v1 lineage with a first-class PADataset target that supports exact-SHA/task-bound Git provenance, bounded read-only evidence inspection, and sandboxed network-denied research execution without exposing a generic shell or making the historical PADataset checkout writable.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-multirepo-research-v1
- Remote checkpoint: c8eca3ddc7915b6bc5ce1e40bc0f8866c8d7be89
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 17e1147614f27702e43565089d618182ff71c5af
- Remote verified: true

## Next safe action

Restore the accepted node_modules closure from the retained 20261110T174933Z upgrade backup into /opt/workspace-shell/runtime/plugins/workspace-shell/node_modules, restart workspace-shell-mcp.service, verify a listener on 127.0.0.1:8797, then use Manage -> Refresh tools. The durable upgrade operator has been patched to preserve and verify the dependency closure; exact-head validation is running for 857bc13bf00d785f7af4be462c12b0ffea62ebfd.

## Remaining work

- Capture concise workspace-shell-mcp.service startup exception; do not collect additional tunnel logs unless the MCP frontend becomes healthy but discovery still fails.
- Implement and exact-head validate the smallest MCP frontend crash fix without changing the frozen external MCP schema.
- Deploy the server-side fix and verify 127.0.0.1:8797 is listening and the MCP service is active.
- Use Manage -> Refresh tools on the existing Workspace Shell app and verify PADataset plus file-list/file-read/file-hash/research-bounded in the model-visible schema.
- Run live positive and negative Workspace Shell acceptance for PADataset.
- Hand control back to the MTH602 Stage 00 provenance recovery task.
- Wire research-bounded to the real DNNs/CUDA runtime internally without changing the external MCP schema.

## Blockers / gates

- Live workspace-shell-mcp.service crash-loop root cause identified: multirepo upgrade replaced the runtime plugin directory with Git-tracked source but did not restore the accepted node_modules dependency closure. server.js therefore fails at startup with ERR_MODULE_NOT_FOUND for @modelcontextprotocol/ext-apps. Tunnel remains healthy and resolves main to 127.0.0.1:8797.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
