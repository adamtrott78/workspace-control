# Workspace review automation v1

## Purpose

The review automation removes routine operator copy/paste from exact-head review
plumbing. It does not let the authoring process approve itself.

The flow is:

1. an OWNER/MEMBER/COLLABORATOR posts a tiny machine request-command comment;
   GitHub's issue_comment event runs the workflow from the default branch;
   trusted default-branch code checks the PR head out separately as data only
   and creates the exact changed-path/blob-bound review request;
2. a fresh independent reviewer reads the durable request directly from GitHub
   and posts one machine-readable disposition;
3. issue_comment automatically validates and consumes the disposition and posts
   a durable consumption receipt.

Authority-sensitive reviews require reviewer_attestation=fresh_independent_session
from a GitHub principal different from the automation request principal. The
tool does not claim to cryptographically prove two ChatGPT sessions are
different; that property remains an explicit procedural review contract.

Routine code reviews may optionally request GitHub Copilot review. Copilot is
consumable only from the GitHub PR review API when GitHub reports APPROVED by
copilot-pull-request-reviewer[bot] at the exact requested head and the original
request had request_copilot=true. An issue comment can never claim Copilot
approval. COMMENTED is not acceptance. Copilot never satisfies
authority_sensitive.

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

There is no workflow_dispatch trigger. The only write-capable trigger is
issue_comment, which GitHub resolves against the default branch and only runs
when the workflow exists there. The workflow checks out exact github.sha as the
trusted automation implementation. The PR head is checked out into a separate
target directory only so trusted code can inspect Git objects. No Python, shell,
workflow helper, or other executable from the reviewed PR checkout is invoked
with the write-scoped GitHub token.

Request creation is initiated by a small
WORKSPACE_CONTROL_REVIEW_REQUEST_COMMAND_V1 comment. Routine Copilot state can
be re-checked with WORKSPACE_CONTROL_REVIEW_CONSUME_COMMAND_V1. Both commands
are parsed by trusted default-branch Python; untrusted comment bodies are passed
through environment variables and never interpolated as shell code.
