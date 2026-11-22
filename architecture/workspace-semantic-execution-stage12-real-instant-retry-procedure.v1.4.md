# D4 Real-Instant Retry Procedure v1.4 — WOP parser repair

Status: **REVIEW CANDIDATE — NOT LIVE AUTHORITY**

The persistent WOP shim is now installed. The v1.3 bootstrap reached the new code but failed before runtime launch because Windows PowerShell parsed the Bash revision expression `"$SOURCE_SHA:$LINUX_REL"` as an invalid PowerShell variable reference.

v1.4 changes only that expression to:

```text
"${SOURCE_SHA}:$LINUX_REL"
```

and adds a PowerShell parser regression test.

After exact-head validation and conditional authority staging, the operator command is simply:

```powershell
wop d4
```

Executing that exact reviewed command is the operator approval signal. No separate approval prompt is required.

Live attempts authorized by this review alone: **0**.
