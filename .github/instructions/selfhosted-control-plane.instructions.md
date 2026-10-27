---
applyTo: "architecture/**,.github/workflows/**,controller/**,scripts/lambda_ci_*.py,schemas/lambda-ci-*.json,templates/lambda-ci/**,systemd/workspace-ci-*.service,tasks/active/workspace-github-actions-selfhosted-control-plane-v1.*"
---

When reviewing GitHub Actions / Lambda self-hosted runner control-plane changes, prioritize correctness and authority boundaries over style.

Treat the following as blocking if present:

- Any bootstrap cycle where a runner or policy must already be hydrated by the same reconciliation decision it is supposed to validate.
- Any path that lets candidate PR code, fork code, runner labels, or graph/model output create or widen execution authority.
- Any weakening of exact repository/workflow/blob/PR-head/actor attestation without a separately reviewed replacement.
- Any self-hosted public-repository path that can execute untrusted fork pull-request code.
- Any control job that can access GPUs, /home/atrott, Docker sockets, sibling project roots, provisioner/reconciler state, or research trusted caches without an explicit reviewed need.
- Any unbounded concurrency or resource-policy change that could starve research workloads.
- Any migration that removes the last independently recoverable bootstrap path before the replacement is validated.
- Any conflation of VALIDATION_UNAVAILABLE (including zero-step/pre-runner failure) with PASS.
- Any review automation that allows the authoring executor to silently satisfy an independence requirement.

For design-only pull requests, do not demand live activation. Verify that planned phases, rollback gates, resource ceilings, and exact future authority boundaries are sufficient before implementation begins.

For organization-runner designs, verify that GitHub-side runner groups restrict repository access and, where supported, exact workflow access, while preserving project-specific operating-system identities and filesystem isolation.
