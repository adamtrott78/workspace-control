# Workspace Semantic Execution — Operator Bridge Production Transport v0.1

Status: **SELECTED FOR IMPLEMENTATION; NOT YET LIVE**

Owner: `workspace-semantic-execution-backend-v1` for the server contract.  
Windows client implementation owner: `workspace-operator-bridge-implementation-v1`.

## Decision

Select **outbound-only HTTPS over the existing authenticated Tailscale tailnet, fronted by Tailscale Serve, with the Workspace Control backend listening on localhost only**.

The Windows helper initiates every connection. The helper opens no inbound listener and stores no GitHub token, OpenAI credential, Workspace Control bearer token, or reusable application secret.

This transport exists only to carry the already-frozen `OperatorBridgePort` commands/queries. It creates no execution authority.

## Why this transport

The frozen operator design requires:

- Workspace Control remains authoritative for OperatorAction lifecycle and session state;
- the helper is a low-attention local adapter, not an orchestrator;
- no Git polling/hot runtime state;
- no embedded GitHub credential merely to fabricate transport;
- no unauthenticated inbound helper listener;
- no browser/page-content authority expansion.

Tailscale Serve is a good fit because it exposes a local service only inside the tailnet, supports HTTPS, applies tailnet access controls, strips spoofed Tailscale identity headers, and forwards authenticated Tailscale identity headers to a proxied backend. Tailscale explicitly recommends that a backend relying on these identity headers listen only on localhost.

External evidence reviewed 2026-11-15:
- https://tailscale.com/docs/features/tailscale-serve
- https://tailscale.com/docs/concepts/tailscale-identity
- https://tailscale.com/docs/how-to/set-up-https-certificates

The production activation must re-run a local version/configuration preflight rather than assuming those external properties remain unchanged.

## Network topology

```text
Windows WorkspaceOperator helper
    |
    | outbound HTTPS only
    | authenticated/encrypted tailnet connection
    v
Tailscale Serve on Workspace Control host
    |
    | loopback proxy only
    | adds authenticated Tailscale identity header
    v
127.0.0.1:<reviewed-port>
Workspace Control OperatorBridge HTTP adapter
    |
    v
OperatorActionService
    |
    v
durable PostgreSQL-backed semantic execution state
```

**Forbidden topology:**

- public internet endpoint;
- Tailscale Funnel;
- helper inbound listener;
- backend listener on LAN/tailnet wildcard while trusting identity headers;
- GitHub issue/comment polling as the action queue;
- helper-stored reusable application bearer secret.

## Authentication contract

Before activation, all of these must be true:

1. Both operator workstation and Workspace Control host are authenticated members of the intended tailnet.
2. Tailnet grants/ACLs permit only the reviewed operator source to reach the Workspace Control Serve endpoint.
3. Tailscale HTTPS/Serve is enabled and operational.
4. The proxied application backend binds **only to localhost**.
5. The application requires the expected Tailscale identity header on every request and fails closed when it is absent.
6. The expected identity value is supplied through deployment/runtime configuration, never committed to Git and never written to ordinary logs/receipts.
7. Incoming requests containing application-supplied identity headers cannot reach the backend directly because the backend has no non-loopback listener.
8. The helper stores no additional service credential.

If the operator workstation cannot supply the required Tailscale user identity header, activation is **BLOCKED**. A tagged-device/app-capability or mTLS alternative requires a separately reviewed transport revision; do not silently fall back to unauthenticated HTTP.

## HTTP surface

Base path: `/operator-bridge/v1`.

The adapter exposes only the frozen OperatorBridge operations:

| Method | Path | Purpose |
|---|---|---|
| GET | `/status` | Return `ReadyManualCycles` and `SentUnconfirmed`. |
| POST | `/actions/claim` | Atomically claim next eligible OperatorAction and return its exact local action envelope. |
| POST | `/actions/{id}/revalidate` | Revalidate exact action generation + worker slot + session generation immediately before clipboard preparation. |
| POST | `/actions/{id}/local-prepared` | Record successful local preparation / manual-submit handoff. |
| POST | `/actions/{id}/local-failure` | Record bounded local failure code/message. |
| POST | `/actions/{id}/blocked` | Record an explicit judgment/recovery/local block. |
| POST | `/actions/{id}/local-completed` | Record completion of a local-only maintenance action. |

There is **no helper endpoint for granting authority** and no arbitrary command, URL, shell, GitHub, model, or browser-control endpoint.

Durable worker acknowledgment is observed by Workspace Control itself and is not asserted by the helper.

## Claim response

A claim response contains only the fields needed by the frozen Windows `IOperatorActionPort` contract:

- `ActionId`
- action generation
- `WorkerSlotId`
- `SessionGeneration`
- action type
- ephemeral `PacketText` when required
- `PayloadRef`
- `PayloadSha256`

The durable OperatorAction record stores **only** the payload reference/hash. Packet text is reconstructed deterministically from durable typed state after claim and is never written into the OperatorAction store, transport logs, task capsules, Git, or receipts.

## Lifecycle and concurrency

Workspace Control owns the lifecycle:

```text
QUEUED
  -> CLAIMED_LOCAL
  -> AWAITING_DURABLE_ACK
  -> ACKNOWLEDGED
  -> COMPLETED
```

Fail-closed side states remain:
`FAILED_LOCAL`, `CLAIM_EXPIRED`, `BLOCKED`, `STALE`, `SUPERSEDED`.

Claim ordering is deterministic:

```text
(priority_rank, queue_sequence, action_id)
```

A service action is claimable only while its exact process generation and exact session generation are current. Revalidation repeats that check immediately before local preparation.

Process recovery or session-generation advancement marks old actions stale. A stale helper acknowledgment cannot revive current work.

## Content/logging contract

Server and helper logs may contain:

- action ID;
- action generation;
- worker slot ID;
- session generation;
- action type;
- bounded error/status code;
- counts and timing.

They may **not** contain:

- packet text;
- clipboard content;
- ChatGPT page content;
- raw model output;
- Tailscale user identity;
- OpenAI/GitHub credentials/tokens;
- browser cookies;
- arbitrary URLs.

## Availability behavior

Network loss is not authority to guess.

- claim/status request failure -> helper reports unavailable/fail-closed;
- an already-claimed action remains durable;
- claim expiry or recovery is resolved by Workspace Control;
- helper restart may reconnect and request current status;
- no local replay of cached packet text after process/session generation changes.

## Activation gates

Before the transport can replace `NoWorkOperatorActionPort` in production:

1. backend OperatorAction store/lifecycle tests pass;
2. PostgreSQL restart persistence passes;
3. exact transport contract tests pass with a fake HTTP client/server;
4. Tailscale/Serve configuration preflight passes on the real two hosts;
5. Operator Bridge implementation task adds the production client under its own authority;
6. fake-worker Stage-10 regressions remain green;
7. no new Firefox permission or ChatGPT content automation is introduced;
8. bounded real-account Stage-12 calibration passes before production promotion.

## Rollback

Production binding is configuration-gated. Rollback disables the production OperatorBridge transport and returns the helper to the non-dispatching/no-work baseline; it does not delete durable OperatorAction or session state.

No rollback path may re-enable Git polling, embedded credentials, browser content access, or unauthenticated transport.
