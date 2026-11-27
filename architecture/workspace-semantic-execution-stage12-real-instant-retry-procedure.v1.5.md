# D4 Real-Instant Retry Procedure v1.5 - parser-safe WOP transport

Status: **REVIEW CANDIDATE - NOT LIVE AUTHORITY**

The v1.4 attempt failed before any runtime launch because `run-stage12-wop.ps1` embedded Bash in a PowerShell here-string and that file was missing from the mandatory Windows PowerShell 5.1 parser gate.

v1.5 removes embedded Bash from the PowerShell file. The remote bootstrap is checked in at:

`operator-bridge/tools/run-stage12-remote-bootstrap.sh`

The WOP launcher reads those exact bytes, base64-encodes them, and sends them over the existing Tailscale SSH path. Operator Bridge Validation now parses `run-stage12-wop.ps1` using Windows PowerShell 5.1 before the rest of the suite.

After validation and one-shot authority staging, the operator command remains:

```powershell
wop d4
```

No second terminal, manual Bash block, or separate approval prompt is introduced.

Live attempts authorized by this review alone: **0**.
