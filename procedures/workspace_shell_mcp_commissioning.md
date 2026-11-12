# Workspace Shell MCP v1 commissioning

Status: repository implementation ready for live commissioning; live activation remains operator-controlled.

## Frozen boundaries

- Workspace Shell is independent of Workspace Heartbeat.
- Target workspace-control source snapshot is the final attested host source:
  `f999b25a866f25c95243cbbd6d1377a799fafb78`.
- The final Lambda host attestation is stored at:
  `plugins/workspace-shell/install/evidence/lambda-host-attestation.f999b25a.json`.
- Its deterministic SHA-256 is:
  `d44cda1f6f13f814e093bef9228410f319d504c76cf80ba8e6d2ecbb8d321353`.
- Runtime implementation provenance is separate from the target snapshot. The activation operator records its exact Git head as `runtime_source_sha`.
- Fixed service identities:
  - `workspace-shell-mcp`: uid/gid 41010
  - `workspace-shell-exec`: uid/gid 41011
  - `workspace-shell-tunnel`: uid/gid 41012
- Port 8797 is the dedicated loopback HTTPS/mTLS frontend.
- Privileged helper registry is empty at initial commissioning.
- Operator trust/revocation stores are empty/fail-closed at initial commissioning.
- All Workspace Shell systemd units remain disabled at boot until live ChatGPT acceptance is complete.

## Account-side prerequisite

Create a **new dedicated OpenAI Secure MCP Tunnel** for Workspace Shell. Do not reuse the Workspace Heartbeat tunnel.

Use OpenAI Platform tunnel settings and associate the tunnel with the ChatGPT workspace that will use Workspace Shell.

Create a dedicated runtime API key whose principal has only the permissions required to run/select the tunnel (Tunnels Read + Use). The activation operator asks for the runtime key with hidden terminal input and writes it only to the Lambda host at:

`/etc/workspace-shell/tunnel/runtime-key`

with owner `workspace-shell-tunnel` and mode 0600.

Never paste the runtime key into ChatGPT, GitHub, task capsules, receipts, or shell history.

Official reference:
https://developers.openai.com/api/docs/guides/secure-mcp-tunnels

## Live activation transaction

Use the exact reviewed PR #573 head and verify the blob of:

`plugins/workspace-shell/install/activate_live.sh`

before execution.

The operator performs a read-only preflight first:

1. prove the repository checkout is clean;
2. prove the final attestation evidence digest;
3. reconstruct the exact target source snapshot at `f999b25a...`;
4. rerun the current host attestation and require all names, numeric UIDs/GIDs, paths, units, port 8797 and namespace gates to remain clean;
5. render an unsealed install bundle from the committed attestation;
6. bind the runtime implementation to the exact operator head;
7. verify the accepted Node v20.20.2 environment, Node dependency tree and tunnel-client v0.0.18;
8. require a valid dedicated tunnel ID.

No host mutation occurs before the explicit prompt:

`ACTIVATE_WORKSPACE_SHELL`

After authorization the operator:

1. creates only the three fixed Workspace Shell principals;
2. creates the isolated Workspace Shell paths;
3. installs the root-owned exact target source snapshot;
4. stages a root-owned copy of the accepted Node runtime and dependencies;
5. stages the accepted tunnel-client;
6. installs the fail-closed config with empty helper/trust stores;
7. generates a dedicated local CA, loopback server certificate, tunnel client certificate and frontend Ed25519 signing identity;
8. deletes the temporary CA private key after issuing the two runtime certificates;
9. prompts for the dedicated tunnel runtime key with hidden input;
10. creates a tunnel profile using local HTTPS/mTLS to `https://127.0.0.1:8797/mcp`;
11. scans the profile to ensure no inline `sk-` credential is present;
12. seals the previously non-runnable bundle using the public client certificate DER SHA-256;
13. installs all four systemd units disabled-at-boot;
14. starts launcher -> root broker -> MCP frontend;
15. proves local mTLS health;
16. runs `tunnel-client doctor --explain`;
17. starts the dedicated tunnel service and proves `/readyz`;
18. proves all four services are active but not boot-enabled;
19. records a root-owned commissioning receipt.

Any error after mutation begins and before terminal commit triggers automatic rollback of the new units, paths and principals.

## Emergency disable

Successful activation installs:

`/opt/workspace-shell/bin/workspace-shell-disable`

Run with sudo to stop all four Workspace Shell services without relying on Workspace Shell itself.

This emergency stop does not delete runtime state or credentials.

## Post-activation live acceptance

Do not enable Workspace Shell at boot yet.

After the local activation transaction passes:

1. add a private ChatGPT custom MCP/plugin using the dedicated Workspace Shell tunnel;
2. verify tool discovery;
3. call `workspace_shell_inspect` for runtime inventory and exact workspace-control Git identity;
4. execute one bounded `git-read` command;
5. execute one bounded test/validation command;
6. verify unauthorized path, credential and arbitrary-shell attempts fail closed;
7. verify privileged helper invocation fails closed because the helper registry and approval trust stores are intentionally empty;
8. inspect the resulting receipts;
9. only after this acceptance decide whether the four services should become boot-enabled.

## After v1 acceptance

The next capability increment is **not** arbitrary root shell access.

Add only concrete reviewed helper operations required by the GitRunner migration, each with exact executable digest, parameter grammar, task/source binding, signed operator approval and replay protection. The initial candidate should cover the narrow live GitRunner controller operations that currently require manual sudo/terminal relay.
