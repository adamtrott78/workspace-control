# D4 Real-Instant Retry Procedure v1.10 — bounded chunked POST backend repair

Status: **REVIEW CANDIDATE — NOT LIVE AUTHORITY**

The accepted Workspace Operator Bridge A7 frontend remains frozen at `a9532ca8b86b7839822939a970e16af1d4a41864` with source tree `51480cc44f62d661421e975e67af127ecd0b0417`.

## v1.9 consumed failure

v1.9 reached the live consumption marker, Q1 readiness, accepted A7 startup, adapter connection, and post-A7 backend status revalidation.

Physical Ctrl+Space presses were received. The native helper emitted repeated `dispatch FAILED` records with `HttpRequestException` and no `actionId`. Therefore the hotkey itself was not dead; dispatch failed at the remote claim request before browser creation, clipboard staging, or foregrounding.

## Root cause

The Windows helper uses .NET `PostAsJsonAsync`. Its `JsonContent` does not precompute Content-Length, so HTTP/1.1 uses chunked transfer encoding.

The Python Operator Bridge HTTP adapter previously read only `Content-Length`. With a chunked POST it treated the body as empty `{}`, rejected the missing claim fields, returned a non-success response, and .NET surfaced `HttpRequestException`.

This also explains why v1.9 `GET /operator-bridge/v1/status` revalidation passed: GET has no request body and therefore did not exercise POST framing.

## v1.10 repair

Backend only. A7 is unchanged.

Candidate `020d35156d90e8268fb560a10e67098a146880de`:

- backend HTTP adapter blob: `3b6893c157c9f567c837aa70c110012eb96ee18c`
- chunked transport regression blob: `6ae3d2812809680cedb7570ee230fa0eebb81e53`
- A7 source tree: `51480cc44f62d661421e975e67af127ecd0b0417`
- A7 dev harness: `ac035d2fc898274c32cad43954ce44c15b198207`

The backend now accepts either Content-Length framing or exactly one `Transfer-Encoding: chunked` coding, never both; enforces the existing body limit while decoding; and rejects extensions, trailers, malformed/incomplete chunks, conflicting framing, and unsupported codings.

A regression sends an actual chunked JSON `POST /operator-bridge/v1/actions/claim` and verifies a real action/packet is returned.

Candidate validation:

- Workspace Control #3132 — SUCCESS
- Semantic Execution #434 — SUCCESS
- Operator Bridge #705 — SUCCESS

## Authority boundary

Live attempts authorized by this review alone: **0**.

Before any v1.10 live retry:

1. freeze and exact-head validate this review state;
2. prove the consumed v1.9 Windows runtime is OFFLINE/clean;
3. obtain fresh explicit operator approval for exactly one v1.10 attempt;
4. create and exact-head validate a fresh one-shot authority;
5. no silent retry after `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`.
