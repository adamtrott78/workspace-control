# D4 Real-Instant Retry Procedure v1.8 — interactive A7 launch

Status: **REVIEW CANDIDATE — NOT LIVE AUTHORITY**

The accepted Workspace Operator Bridge frontend remains frozen at `a9532ca8b86b7839822939a970e16af1d4a41864`.

v1.7 successfully reached the real backend and `STAGE12_Q1_READY`, but D4 launched the accepted frontend from a PowerShell `Start-Job` background context. Firefox opened while the accepted Ctrl+Space / clipboard / focus / Temporary Chat loop did not operate.

v1.8 changes only D4 orchestration:

- start the remote backend first;
- poll the backend-ready endpoint from the interactive parent PowerShell;
- once Q1 is ready, invoke the exact accepted A7 `workspace-operator-dev.ps1 online` directly from that same interactive parent session;
- keep the exact A7 frontend tree and dev harness blobs unchanged;
- preserve the LF-safe remote transport from v1.7.

Live attempts authorized by this review alone: **0**.
