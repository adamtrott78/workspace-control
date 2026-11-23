# D4 Real-Instant Retry Procedure v1.12 — reviewed candidate baseline refresh

Status: **REVIEW CANDIDATE — NOT LIVE AUTHORITY**

v1.11 aborted before `STAGE12_SEMANTIC_LIVE_BINDING=PASS` and before the live consumption marker because the Stage12 shell still expected the initial candidate namespace head `0bc1bc0e…`.

The isolated candidate branch now legitimately points to `7bab6ff51202b3d0c3190d1351e8578d22c4f2f1`, a single child of the initialization commit that adds only `worker-results/stage12/5dda87c416484e45ae5a22f0bccf97f4/q1.json`.

v1.12 therefore preserves candidate history and updates the reviewed preflight baseline to `7bab6ff…`. It does not reset or rewrite the candidate branch.

The in-harness CandidateWatcher safety contract is unchanged: each quantum captures its current baseline and accepts only one new commit whose parent equals that baseline and whose changed path equals the expected immutable result path.

The v1.11 semantic live-binding repair remains in place, and A7 remains unchanged.

This review grants zero live authority. Exact-head validation and fresh explicit approval are required before a new one-shot attempt.
