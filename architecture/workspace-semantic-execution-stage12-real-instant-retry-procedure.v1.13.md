# D4 Real-Instant Retry Procedure v1.13 — exact stale Tailscale route normalization

Status: **REPAIR CANDIDATE — NOT LIVE AUTHORITY**

v1.12 passed the reviewed candidate-baseline gate but aborted before semantic live binding and before authority consumption. The Lambda Tailscale Serve state contained the preserved Jupyter root plus the exact Stage12 Operator Bridge route.

The prior preflight compared the full handler map to a root-only map before checking for the Stage12 route, so it reported a generic root mapping mismatch.

v1.13 normalizes only the exact known stale Stage12 route:
- Jupyter root must remain `/ -> http://127.0.0.1:8888`.
- The only optional extra handler is `/operator-bridge/v1 -> http://127.0.0.1:8765/operator-bridge/v1`.
- If that route exists, TCP port 8765 must have no listener.
- Only then may the exact route be removed.
- A fresh clean root-only Serve/Funnel snapshot is taken after normalization and remains the rollback baseline.
- Any other drift fails closed.

Candidate baseline `7bab6ff…`, repaired semantic backend `020d35156… / 3b6893c1…`, and accepted A7 frontend remain unchanged.

This review grants zero live authority. Exact-head validation and fresh explicit one-shot approval are required before another D4 execution.
