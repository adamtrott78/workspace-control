# D4 Real-Instant Retry Procedure v1.7 — LF-safe transport

Status: **REVIEW CANDIDATE — NOT LIVE AUTHORITY**

The accepted Workspace Operator Bridge frontend remains frozen at `a9532ca8b86b7839822939a970e16af1d4a41864`.

v1.6 failed before backend readiness because Windows worktree line endings were transported verbatim to Bash. v1.7 changes only the outer D4 transport:

- read the checked-in remote bootstrap as text;
- normalize CRLF and CR to LF;
- encode UTF-8 without BOM;
- fail closed if any carriage-return byte remains;
- wait for the SSH process to exit before reading its exit code.

The backend-first ready gate and exact A7 frontend bindings are unchanged.

After exact-head validation and fresh one-shot authority, the operator entry remains:

```powershell
wop d4
```

Live attempts authorized by this review alone: **0**.
