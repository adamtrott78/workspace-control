<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-multirepo-research-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-multirepo-research-v1
- Title: Workspace Shell multi-repo PADataset research access v1
- Status: IN_PROGRESS
- Current stage: implementation_and_validation

## Goal

Extend the accepted Workspace Shell v1 lineage with first-class PADataset access for exact-SHA Git provenance, bounded evidence discovery/read/hash, and sandboxed network-denied research execution without granting a generic shell or writable access to the historical PADataset checkout.

## Security boundary

- Authorized targets: workspace-control and PADataset only.
- PADataset read profiles: git-read, file-list, file-read, file-hash.
- PADataset execution profile: research-bounded only.
- research-bounded runs approved PADataset Python paths in a disposable writable copy with network denied.
- Dirty PADataset snapshots are readable but not executable.
- /home remains outside the hostile-worker namespace.
- Privileged helper trust remains empty/fail-closed.

## Current implementation

- Target/profile policy added to frontend and launcher.
- Evidence profiles added to root-owned profile manifest.
- PADataset source root added to rendered launcher/verifier configuration.
- Fail-closed live upgrade/rollback operator added at plugins/workspace-shell/install/upgrade_multirepo_padataset_v1.sh.
- JS and Python multirepo regression tests added.
- MTH602 Shell authority capsule added at tasks/active/mth602-final-multisurrogate-dqnguard-v1.json.

## Next safe action

Validate the exact branch head with Workspace Control CI. Do not run the live upgrade operator until that exact head passes. Then execute the operator on Lambda against PADataset expected SHA 17e1147614f27702e43565089d618182ff71c5af; any mismatch must abort before runtime mutation.
