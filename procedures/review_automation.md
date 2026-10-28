# Workspace review automation v1

## Purpose

The review automation removes routine operator copy/paste from exact-head review
plumbing. It does not let the authoring process approve itself.

The flow is:

1. workflow_dispatch executes the request generator only from the trusted
   workflow commit (github.workflow_sha), checks the PR head out separately as
   data only, and creates a review request from exact changed-path/blob bindings;
2. a fresh independent reviewer reads the durable request directly from GitHub
   and posts one machine-readable disposition;
3. issue_comment automatically validates and consumes the disposition and posts
   a durable consumption receipt.

Authority-sensitive reviews require reviewer_attestation=fresh_independent_session
from a GitHub principal different from the automation request principal. The
tool does not claim to cryptographically prove two ChatGPT sessions are
different; that property remains an explicit procedural review contract.

Routine code reviews may optionally request GitHub Copilot review. Copilot is
consumable only when GitHub reports APPROVED at the exact requested head.
COMMENTED is not acceptance. Copilot never satisfies authority_sensitive.

## Fail-closed rules

The consumer rejects edited request/disposition comments, stale PR heads,
stale PR bases, malformed/extra/missing machine-block keys, request digest
mismatch, duplicate
matching dispositions, same request/reviewer principal, and authority-sensitive
reviews without the fresh-independent-session attestation.

## Runtime boundary

This is GitHub-only. It does not SSH to Lambda, read controller credentials,
call systemctl, mutate registries/manifests, start/restart controllers, widen
capacity, issue maintenance commands, or merge PRs automatically.

## Trusted requester execution boundary

The request job pins its executable automation checkout to github.workflow_sha.
The PR head is checked out into a separate target directory only so trusted code
can inspect Git objects. No Python, shell, workflow helper, or other executable
from the reviewed PR checkout is invoked with the write-scoped GitHub token.
