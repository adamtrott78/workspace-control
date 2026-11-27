# D4 Real-Instant Retry Procedure v1.3 — WOP path restoration

Status: **REVIEW CANDIDATE — NOT LIVE AUTHORITY**

This repair restores the already-validated operator UX instead of maintaining a separate Stage-12 Windows launcher.

## Operator contract

After this candidate is validated and fresh one-shot authority is established, the normal command is:

```powershell
wop d4
```

For the first repaired run only, an already-installed older WOP driver can bootstrap the new shim and launch the same path in one line:

```powershell
wop online <validated-sha>
```

That bootstrap command checks out the exact validated SHA, the new `online` compatibility path syncs the owned WOP command shims, and the live path then runs through the same `workspace-operator-dev.ps1` DevRuntime used by the accepted fast-loop UX.

## What the one line does

- starts the persistent WOP Windows runtime in remote/online mode;
- requires a real helper startup receipt proving Bridge ON / Ctrl+Space registration;
- opens the persistent WorkspaceWorkers Firefox profile;
- asks only for the manual auth/Instant readiness boundary;
- launches the reviewed Linux calibration over the user's existing Tailscale SSH path;
- keeps Linux output in the same PowerShell terminal;
- leaves worker service manual: **Ctrl+Space -> Ctrl+V -> Enter**;
- automatically tears down the WOP Windows runtime after the Linux calibration exits.

No separate Bash block, second Linux terminal, manual marker copy, DOM scraping, credential automation, automatic paste, automatic Enter, Funnel, public listener, or paid API fallback is introduced.

## Failure visibility

A remote/claim/browser/clipboard/focus failure after Ctrl+Space must produce a visible warning balloon instead of appearing as a no-op.

## Authority

Live attempts authorized by this review: **0**.

The predecessor v1.2 attempt is consumed and failed. A new attempt may be armed only after exact-head validation. Under the durable operator WOP-approval policy, executing the exact reviewed WOP command may serve as the approval signal for that one attempt.
